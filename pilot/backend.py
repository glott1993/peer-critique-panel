"""Model backends.

OpenRouterBackend talks to https://openrouter.ai (one key, every lab).
MockBackend answers every prompt type with canned, seeded output so the
whole harness can be run offline (python run_pilot.py --mock).

Every call is appended to results/calls.jsonl with model, tokens, cost,
latency, and the task/condition/step it belonged to, and totals are kept
per (task, condition) so the runner can charge each answer its real cost.
"""
import json, random, re, threading, time

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


class Accounting:
    def __init__(self, log_path):
        self.log_path = log_path
        self.lock = threading.Lock()
        self.totals = {}

    def record(self, ctx, model, usage, cost, latency, ok, error=None, finish=None):
        ctx = ctx or {}
        key = (ctx.get("task"), ctx.get("condition"))
        entry = {"ts": time.time(), "task": ctx.get("task"), "condition": ctx.get("condition"), "step": ctx.get("step"),
                 "model": model, "prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0),
                 "cost": cost, "latency": round(latency, 3), "ok": ok, "error": error, "finish": finish}
        with self.lock:
            t = self.totals.setdefault(key, {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0, "errors": 0})
            t["calls"] += 1
            t["prompt_tokens"] += entry["prompt_tokens"]; t["completion_tokens"] += entry["completion_tokens"]
            t["cost"] += cost or 0.0
            if not ok:
                t["errors"] += 1
            if self.log_path:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(entry) + "\n")

    def take(self, task, condition):
        """Return and reset the totals for one (task, condition)."""
        with self.lock:
            return self.totals.pop((task, condition), {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0, "errors": 0})


class _EmptyReply(RuntimeError):
    pass


class OpenRouterBackend:
    def __init__(self, api_key, accounting, max_retries=6, timeout=180, title="Peer-critique pilot", provider_pins=None, reasoning=None, reasoning_json=None):
        self.provider_pins = provider_pins or {}  # {"anthropic/": {"order": ["anthropic"], "allow_fallbacks": False}}
        self.reasoning = reasoning or {}  # {"default": {"effort": "low"}, "anthropic/claude-opus-5": None}; longest matching prefix wins
        self.reasoning_json = reasoning_json or {}  # same shape; used instead of `reasoning` on JSON-capped steps for the models it names (e.g. {"deepseek/": {"effort": "none"}})
        import requests  # imported here so --mock works without it
        self.requests = requests
        self.key = api_key
        self.acc = accounting
        self.max_retries = max_retries
        self.timeout = timeout
        self.headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json", "X-Title": title}
        self.include_usage = True  # OpenRouter usage accounting; switched off automatically if the API rejects it

    @staticmethod
    def _lookup(table, model):
        matches = [k for k in table if k != "default" and model.startswith(k)]
        return table[max(matches, key=len)] if matches else table.get("default")

    def _reasoning_for(self, model, json_step):
        """The reasoning setting for one call. On a JSON-capped step, `reasoning_json` wins when it names the
        model's prefix (or has a default); otherwise `reasoning` applies. None means no reasoning parameter is sent.
        Why: a reasoning model can spend the whole JSON cap thinking and return nothing (DeepSeek V4 Pro did, on
        44% of its critique, vote, compare and bid calls at 5,000 tokens with effort low), while the same model
        at the answer cap writes fine. Turning thinking off for the short steps only keeps its answers as they were."""
        if json_step:
            matches = [k for k in self.reasoning_json if k != "default" and model.startswith(k)]
            if matches or "default" in self.reasoning_json:
                return self._lookup(self.reasoning_json, model)
        return self._lookup(self.reasoning, model)

    def chat(self, model, system, user, temperature=0.5, max_tokens=1500, ctx=None, json_step=False):
        body = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.include_usage:
            body["usage"] = {"include": True}
        for prefix, prefs in self.provider_pins.items():
            if model.startswith(prefix):
                body["provider"] = prefs
        rsn = self._reasoning_for(model, json_step)
        if rsn:
            body["reasoning"] = rsn
        delay = 1.5
        last_err = None
        for attempt in range(self.max_retries + 1):
            t0 = time.time()
            try:
                r = self.requests.post(OPENROUTER_URL, headers=self.headers, json=body, timeout=self.timeout)
                if r.status_code in (429, 500, 502, 503, 504, 524):
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
                data = r.json()
                if "error" in data:
                    msg = data["error"].get("message", str(data["error"]))
                    code = data["error"].get("code", 0)
                    if code in (429, 502, 503) or "rate" in msg.lower() or "overloaded" in msg.lower():
                        raise RuntimeError(msg)
                    if self.include_usage and "usage" in msg.lower():
                        self.include_usage = False  # provider does not accept the usage parameter; retry without it
                        body.pop("usage", None)
                        continue
                    self.acc.record(ctx, model, {}, 0.0, time.time() - t0, False, msg)
                    raise ValueError(f"{model}: {msg}")
                choice = data["choices"][0]
                text = (choice.get("message") or {}).get("content") or ""
                if isinstance(text, list):  # some providers return content parts
                    text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
                usage = data.get("usage") or {}
                cost = usage.get("cost")
                if cost is None:
                    cost = 0.0
                finish = choice.get("finish_reason")
                served_by = data.get("provider")
                if not text.strip() or finish in ("content_filter", "error"):
                    self.acc.record(ctx, model, usage, float(cost), time.time() - t0, False, f"empty reply (finish={finish}, provider={served_by})", finish=f"{finish} via {served_by}")
                    raise _EmptyReply(f"empty reply (finish={finish}, provider={served_by})")
                self.acc.record(ctx, model, usage, float(cost), time.time() - t0, True, finish=f"{finish} via {served_by}")
                return text
            except ValueError:
                raise
            except _EmptyReply as e:  # already recorded with its real usage; retry
                last_err = e
            except Exception as e:  # transient: retry with backoff
                last_err = e
                self.acc.record(ctx, model, {}, 0.0, time.time() - t0, False, str(e)[:200])
                if attempt == self.max_retries:
                    break
                time.sleep(delay + random.random())
                delay = min(delay * 2, 40)
        raise RuntimeError(f"{model}: gave up after {self.max_retries} retries: {last_err}")

    def list_models(self):
        r = self.requests.get(OPENROUTER_MODELS_URL, headers=self.headers, timeout=60)
        r.raise_for_status()
        return r.json().get("data", [])


class MockBackend:
    """Offline stand-in. Correctness per model is a fixed probability so the
    scoring, gating, and reporting code paths all get exercised."""

    def __init__(self, tasks, accounting, quality=None, seed=1):
        self.tasks = {t["id"]: t for t in tasks}
        self.acc = accounting
        self.quality = quality or {}
        self.rng = random.Random(seed)
        self.lock = threading.Lock()

    def _p(self, model):
        for k, v in self.quality.items():
            if k in model:
                return v
        return 0.6

    def _answer(self, task, model):
        with self.lock:
            good = self.rng.random() < self._p(model)
        if task["answer_type"] == "code":
            import task_bank, task_bank2
            ref = next(t["reference"] for t in task_bank.CODE_TASKS + task_bank2.CODE_TASKS2 if t["id"] == task["id"])
            if not good:
                ref = ref.replace("return ", "return None  # ", 1)
            return "Here is the function.\n\n```python\n" + ref.strip() + "\n```\n"
        exp = task["expected"]
        if task["answer_type"] == "multi":
            vals = [e["expected"] if good else (round(float(e["expected"]) * 1.07 + 1, e.get("precision", 0)) if e["answer_type"] == "number" else "Wednesday") for e in exp]
            return "Working.\nFINAL: " + "; ".join(str(v) for v in vals)
        if task["answer_type"] == "number":
            val = exp if good else round(float(exp) * 1.07 + 1, task.get("precision", 0))
        else:
            val = exp if good else ("Wednesday" if exp != "Wednesday" else "Friday")
        return f"Working shown here.\nFINAL: {val}"

    def chat(self, model, system, user, temperature=0.5, max_tokens=1500, ctx=None, json_step=False):
        task = self.tasks.get((ctx or {}).get("task"))
        u = user
        with self.lock:
            r = self.rng.random()
        if 'JSON: {"components"' in u and "changed" not in u:
            out = json.dumps({"components": [{"id": "c1", "title": "Whole request", "what": "Answer the request in full."}]})
        elif 'JSON: {"changed"' in u:
            out = json.dumps({"changed": "none", "components": [{"id": "c1", "title": "Whole request", "what": "Answer the request in full."}]})
        elif 'JSON: {"bids"' in u:
            out = json.dumps({"bids": ["c1"], "why": "I can answer this."})
        elif "Write your draft for this component" in u or "Stitch them into one complete answer" in u:
            out = self._answer(task, model)
        elif 'JSON: {"keep"' in u:
            out = json.dumps({"keep": "X" if r < 0.5 else "Y", "why": "Better evidence."})
        elif "designated dissenter" in u or "Challenge this draft" in u:
            if r < 0.45:
                out = json.dumps({"challenges": [{"claim": "the final figure", "problem": "the arithmetic may be off", "check": "recompute it"}], "verdict": "revise"})
            else:
                out = json.dumps({"challenges": [], "verdict": "ready"})
        elif "Revise the draft" in u:
            out = json.dumps({"answer": self._answer(task, model), "accepted": [1], "rejected": []})
        elif "Is this ready to submit to the hub" in u:
            out = json.dumps({"ready": r < 0.85, "objection": "" if r < 0.85 else "one figure still unsupported"})
        elif "Ask your questions now" in u:
            m = re.search(r"FINAL:\s*([-\d.]+)", u)
            claimed = float(m.group(1)) if m else 4
            if r < 0.6:
                out = json.dumps({"questions": ["What is the source of the final figure?"], "checks": [{"expr": "2+2", "claimed": 4}] if not m else [{"expr": str(claimed), "claimed": claimed}]})
            else:
                out = json.dumps({"questions": [], "checks": []})
        elif "The hub asks:" in u:
            corrected = self._answer(task, model) if r < 0.5 else None
            out = json.dumps({"replies": [{"n": 1, "reply": "Recomputed; see the figure."}], "correctedAnswer": corrected})
        elif "Which are now resolved" in u:
            nums = [int(x) for x in re.findall(r"^(\d+)\. Q:", u, re.M)]
            out = json.dumps({"resolved": nums, "open": [], "questions": []})
        elif "Write the note that goes to the user" in u:
            out = "Seats disagreed on the final figure; Seat B's recomputation prevailed. Check the arithmetic yourself."
        elif "Check this answer for errors" in u or "Pick the best candidate" in u:
            out = self._answer(task, model)
        else:  # baseline and plain answers
            out = self._answer(task, model)
        usage = {"prompt_tokens": max(1, len(user) // 4), "completion_tokens": max(1, len(out) // 4)}
        self.acc.record(ctx, model, usage, (usage["prompt_tokens"] * 1e-6 + usage["completion_tokens"] * 5e-6), 0.01, True)
        return out
