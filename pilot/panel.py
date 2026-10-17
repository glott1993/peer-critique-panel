"""The panel protocol, ported from prototype/peer-critique-panel.html.

Six steps: decomposition, bidding, mandatory critique, iterative molding to
agreement, hub interrogation (with checks computed outside the panel), and
release with three gates. The prompts are the prototype's, so the pilot
tests the same protocol the prototype demonstrates.
"""
import json, random, re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import checkers

LETTERS = "ABCDEFGHIJKL"
ANSWER_TOKENS = 6000  # cap for calls that write or rewrite an answer
JSON_TOKENS = 5000    # cap for JSON-only steps (bids, critiques, votes, hub questions); reasoning models spend part of it thinking


@dataclass
class Seat:
    letter: str
    model: str
    label: str = ""
    weight: float = 1.0
    tier_class: str = "mid"
    lens: str = ""
    key: str = ""

    def __post_init__(self):
        self.key = self.key or self.model
        self.label = self.label or self.model


def seat_system(s, n):
    return (f"You are Seat {s.letter} on a panel of {n} AI models answering one user's request together. "
            "The other seats are anonymous to you; refer to them only by seat letter. Attack content, not labels. "
            "Every challenge must point at evidence: a specific claim, a missing source, a figure to recompute, code to run. "
            "Be concrete and brief." + (" Your lens on this panel: " + s.lens if s.lens else "") +
            " When asked for JSON, reply with JSON only: no prose before or after, no code fences, and write line breaks inside strings as \\n.")


class P:
    @staticmethod
    def decompose(req):
        return (f"Request:\n{req}\n\nPropose a breakdown into 1 to 4 components that together answer it. Simple requests get one component. "
                "Each component: id (c1, c2, ...), title (under 8 words), what (one sentence).\n"
                'JSON: {"components":[{"id":"c1","title":"...","what":"..."}]}')

    @staticmethod
    def decompose_review(req, comps):
        return (f"Request:\n{req}\n\nA seat proposed this breakdown:\n{json.dumps(comps)}\n\n"
                "Critique it as you would a draft: anything missing, redundant, or mis-scoped? Return the breakdown you would accept, amended if needed (1 to 4 components), and say what you changed.\n"
                'JSON: {"changed":"none or a one-sentence description","components":[{"id":"c1","title":"...","what":"..."}]}')

    @staticmethod
    def bid(req, comps):
        cl = "\n".join(f"{c['id']}. {c['title']}: {c['what']}" for c in comps)
        return f"Request:\n{req}\n\nComponents:\n{cl}\n\nWhich components are you prepared to answer? Bid on any number, including all of them.\nJSON: {{\"bids\":[\"c1\"],\"why\":\"one sentence\"}}"

    @staticmethod
    def draft(req, c):
        return (f"Request:\n{req}\n\nYou bid on component {c['id']}: {c['title']}. {c['what']}\n"
                "Write your draft for this component only. Under 250 words of prose; code blocks do not count. Give a source or a way to check every factual claim and figure. Follow the answer format the request asks for. Plain text, no JSON.")

    @staticmethod
    def compare(req, c, x, y):
        return (f"Request:\n{req}\n\nTwo anonymous drafts for component {c['id']} ({c['title']}).\n\nDraft X:\n{x}\n\nDraft Y:\n{y}\n\n"
                'Which should the panel keep? Judge on evidence and correctness, not style.\nJSON: {"keep":"X","why":"one sentence that points at evidence"}')

    @staticmethod
    def assemble(req, parts):
        pl = "\n\n".join(f"[{p['c']['id']}: {p['c']['title']}]\n{p['text']}" for p in parts)
        return (f"Request:\n{req}\n\nThe panel chose these component drafts:\n{pl}\n\n"
                "Stitch them into one complete answer to the request. Keep every factual claim and its source; resolve contradictions between parts; add no new claims. Under 300 words of prose; code blocks do not count. Follow the answer format the request asks for. Plain text, no JSON.")

    @staticmethod
    def critique(req, draft):
        return (f"Request:\n{req}\n\nCurrent draft:\n{draft}\n\n"
                "Challenge this draft. Each challenge must name the claim and the evidence problem (missing source, wrong figure, untested code, unsupported inference, omission) and how to check it. If you find nothing wrong, return no challenges.\n"
                'JSON: {"challenges":[{"claim":"...","problem":"...","check":"..."}],"verdict":"ready or revise"}')

    @staticmethod
    def dissent(req, draft):
        return ("You are this round's designated dissenter. Your only job is to attack the consensus: find the strongest case that the draft is wrong, incomplete, or answers the wrong question. Ground every point in evidence the panel could check.\n\n"
                f"Request:\n{req}\n\nCurrent draft:\n{draft}\n\n"
                'JSON: {"challenges":[{"claim":"...","problem":"...","check":"..."}],"verdict":"revise"}')

    @staticmethod
    def revise(req, draft, ch):
        cl = "\n".join(f"{i + 1}. {(x['claim'] + ' : ') if x['claim'] else ''}{x['problem']}{(' (check: ' + x['check'] + ')') if x['check'] else ''}" for i, x in enumerate(ch))
        return (f"Request:\n{req}\n\nCurrent draft:\n{draft}\n\nChallenges from other seats:\n{cl}\n\n"
                "Revise the draft. Accept a challenge only if its evidence holds; reject it with a reason otherwise. Keep the answer under 300 words of prose (code blocks do not count) and keep the answer format the request asks for.\n"
                'JSON: {"answer":"full revised answer","accepted":[1],"rejected":[{"n":2,"why":"..."}]}')

    @staticmethod
    def vote(req, draft):
        return f"Request:\n{req}\n\nDraft:\n{draft}\n\nIs this ready to submit to the hub?\nJSON: {{\"ready\":true,\"objection\":\"empty if ready, else the one thing that must change\"}}"

    @staticmethod
    def hub_system(budget):
        return ("You are the hub. You never write, edit, propose, or reword an answer, and you never suggest what it should say. You only ask questions and request checks. "
                "Ask about sources, disputed points, edge cases (what happens if X), and any figure or code that can be verified. Ask only what is still open; never ask what the record already answers. "
                f"Your budget for this request is {budget} questions in total. When asked for JSON, reply with JSON only: no prose, no code fences, and write line breaks inside strings as \\n.")

    @staticmethod
    def hub_ask(req, answer, record_text, digest, k, remaining):
        return (f"Request:\n{req}\n\nSubmitted answer:\n{answer}\n\nPanel record:\n{record_text}\n\nCatalogue (patterns from past runs):\n{digest}\n\n"
                f"Ask your questions now: at most {k} this round, {remaining} left in your budget. Where the answer contains arithmetic, add a check: an expression using only numbers and + - * / ( ), plus the value the answer claims.\n"
                'JSON: {"questions":["..."],"checks":[{"expr":"0.07*1200","claimed":84}]}\nIf nothing is open: {"questions":[],"checks":[]}')

    @staticmethod
    def panel_reply(req, answer, batch, failing):
        ql = "\n".join(f"{b['n']}. {b['q']}" for b in batch)
        fl = ("\n\nChecks computed outside the panel that failed:\n" + "\n".join(failing)) if failing else ""
        return (f"Request:\n{req}\n\nSubmitted answer:\n{answer}\n\nThe hub asks:\n{ql}{fl}\n\n"
                "Answer each question with evidence: a source, a computation, or a plain statement that no source exists. If answering reveals an error in the answer, correct it and include the full corrected answer (same format as the request asks for).\n"
                'JSON: {"replies":[{"n":1,"reply":"..."}],"correctedAnswer":null}')

    @staticmethod
    def hub_review(req, answer, batch, remaining):
        ql = "\n".join(f"{b['n']}. Q: {b['q']}\n   A: {b.get('reply', '')}" for b in batch)
        return (f"Request:\n{req}\n\nCurrent answer:\n{answer}\n\nYour questions and the panel's replies:\n{ql}\n\n"
                "Some of these may be earlier questions you left open, shown again with their replies. Which are now resolved with evidence? Mark the rest open and say why. "
                f"Ask a follow-up only where a reply is missing evidence; {remaining} questions remain in your budget.\n"
                'JSON: {"resolved":[1],"open":[{"n":2,"why":"..."}],"questions":["follow-up"]}')

    @staticmethod
    def split_note(req, answer, record_text, agreed):
        return (f"Request:\n{req}\n\nFinal answer:\n{answer}\n\nRecord of dispute:\n{record_text}\nPanel agreement before submission: {'reached' if agreed else 'not reached within the round budget'}.\n\n"
                "Write the note that goes to the user on where the panel split: what was disputed, which seat letters held what, and what the user should check for themselves. Under 90 words. If nothing was disputed, one sentence saying so. Plain text, no JSON.")

    baseline_system = "Answer the user's request as well as you can. Plain text. Follow the answer format the request asks for."


def parse_json(text, fallback):
    if not text:
        return fallback
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S).strip()
    for cand in (t, t[t.find("{"): t.rfind("}") + 1] if "{" in t and "}" in t else ""):
        if not cand:
            continue
        try:
            v = json.loads(cand)
            if isinstance(v, dict):
                return v
        except Exception:
            try:
                v = json.loads(cand.replace("\n", "\\n"))
                if isinstance(v, dict):
                    return v
            except Exception:
                pass
    return fallback


def extract_questions(text):
    return [l.strip("-*0123456789. ").strip() for l in (text or "").splitlines() if l.strip().endswith("?")][:3]


def pool(jobs, n=4):
    if not jobs:
        return []
    with ThreadPoolExecutor(max_workers=min(n, len(jobs))) as ex:
        return list(ex.map(lambda f: f(), jobs))


def record_text(r):
    lines = []
    if r["accepted"]:
        lines.append("Challenges accepted in revision: " + " | ".join(f"[Seat {c['from'].letter}] {c['problem']}" for c in r["accepted"]))
    if r["rejected"]:
        lines.append("Challenges rejected in revision: " + " | ".join(f"[Seat {c['from'].letter}] {c['problem']} (rejected: {c['why']})" for c in r["rejected"]))
    if r["objections"]:
        lines.append("Objections at the final vote: " + " | ".join(f"[Seat {o['from'].letter}] {o['objection']}" for o in r["objections"]))
    if r.get("hub_open"):
        lines.append("Hub questions left open: " + " | ".join(f"{o['q']} ({o['why']})" for o in r["hub_open"]))
    if r.get("checks"):
        lines.append("Checks: " + " | ".join(f"{c['expr']} = {c['value'] if c['valid'] else 'n/a'} vs claimed {c['claimed']}: {('pass' if c['ok'] else 'fail') if c['valid'] else 'skipped'}" for c in r["checks"]))
    return "\n".join(lines) if lines else "No disputes recorded."


def catalogue_digest(seats, cat):
    lines = []
    for s in seats:
        c = cat.get(s.key)
        if not c or c["runs"] < 2:
            continue
        if c["corrected"] or c["overruled"] or c["checksFailed"]:
            lines.append(f"Seat {s.letter} ({c['label']}): {c['runs']} runs; drafts corrected {c['corrected']} times; challenges overruled {c['overruled']} times; checks failed {c['checksFailed']} times." + (" Recent corrections: " + " | ".join(c["recent"]) if c["recent"] else ""))
    return "\n".join(lines) if lines else "No prior patterns recorded."


def norm_comps(lst, req):
    out = []
    for i, c in enumerate((lst if isinstance(lst, list) else [])[:4]):
        if isinstance(c, dict) and (c.get("title") or c.get("what")):
            out.append({"id": f"c{len(out) + 1}", "title": str(c.get("title") or f"Component {i + 1}")[:80], "what": str(c.get("what") or "")[:300]})
    return out or [{"id": "c1", "title": "Whole request", "what": req[:300]}]


def well_formed(task, text):
    """Does the text carry the answer format the request asks for: a code block for a code task, a FINAL line otherwise?
    With no task (the prototype's free-form use) anything passes."""
    if task is None or not isinstance(text, str):
        return True
    if task.get("answer_type") == "code":
        return checkers.extract_code(text) is not None
    return checkers.extract_final(text) is not None


def keeps_format(task, old, new):
    """May `new` replace `old` as the panel's answer? Added October 17, 2026: a revision or a correction under
    interrogation used to replace the answer unchecked, and in pilot 2 six of the panel's 26 wrong answers were right
    values whose revision or hub reply had dropped the FINAL line or the code block. The rule: a new text that has
    lost the format the old one had is refused and the old text stands. A malformed text may still replace a malformed
    one, so the panel never gets stuck on a bad draft, and nothing here judges the values."""
    return well_formed(task, new) or not well_formed(task, old)


def run_panel(req, cfg, api, task=None, prelude="", log=None):
    """cfg keys: seats (list[Seat]), hub (model id or None), rounds, hub_budget, dissenter, tier, catalogue (dict), rng, ctx."""
    seats, N, cat = cfg["seats"], len(cfg["seats"]), cfg["catalogue"]
    rng = cfg.get("rng") or random.Random(0)
    ctx = dict(cfg.get("ctx") or {})
    log = log if log is not None else []
    record = {"accepted": [], "rejected": [], "objections": [], "hub_open": [], "checks": []}

    def touch(s):
        return cat.setdefault(s.key, {"key": s.key, "label": s.label, "runs": 0, "bids": 0, "drafts": 0, "challenged": 0, "corrected": 0, "overruled": 0, "objections": 0, "checksFailed": 0, "recent": []})
    for s in seats:
        touch(s)["runs"] += 1

    # A call that gives up after the backend's retries (its RuntimeError) is a decline: the panel routes around it
    # instead of failing the task. Seats that decline abstain on JSON steps and hand drafts, revisions and replies to
    # another seat; a hub that declines leaves the answer flagged. Configuration errors (ValueError) still propagate.
    declined = []
    declined_letters = set()

    def note_decline(who, step, err):
        declined.append({"who": who, "step": step, "error": str(err)[:160]})
        if who != "hub":
            declined_letters.add(who)

    # A revision or a correction that drops the request's answer format (keeps_format) is refused and recorded here;
    # the text that stood before it stays the answer.
    refused = []

    def note_refusal(who, step, where, text):
        refused.append({"who": who, "step": step, "where": where, "why": "no code block" if task and task.get("answer_type") == "code" else "no FINAL line",
                        "text": (text or "")[:400]})

    def ask(s, user, temp, step, max_tokens=None):
        mt = max_tokens or JSON_TOKENS
        # json_step marks the short JSON-only calls (decompose, bid, compare, critique, vote); the backend may
        # apply a different reasoning setting to them. Answer-writing calls at ANSWER_TOKENS keep the seat's normal one.
        return api.chat(s.model, seat_system(s, N), user, temp, max_tokens=mt, ctx=dict(ctx, step=step), json_step=(mt <= JSON_TOKENS))

    def ask_safe(s, user, temp, step, max_tokens=None):
        """ask, but a decline returns None and is recorded."""
        try:
            return ask(s, user, temp, step, max_tokens)
        except RuntimeError as e:
            note_decline(s.letter, step, e)
            t = touch(s); t["declined"] = t.get("declined", 0) + 1
            return None

    def ask_json(s, user, fb, temp, step, max_tokens=None):
        """JSON step where the fallback is the abstaining answer (no bids, no challenges, keep X, no changes)."""
        return parse_json(ask_safe(s, user, temp, step, max_tokens or JSON_TOKENS), fb)

    def ask_json2(s, user, fb, temp, step, max_tokens=None):
        """JSON step where the caller handles a decline itself: returns None instead of the fallback."""
        raw = ask_safe(s, user, temp, step, max_tokens or JSON_TOKENS)
        return None if raw is None else parse_json(raw, fb)

    def pick(lst):
        return rng.choice(lst) if lst else None

    def willing(lst):
        """The seats in lst that have not declined in this task; all of lst if every one has."""
        w = [s for s in lst if s.letter not in declined_letters]
        return w or list(lst)

    # 1. Decomposition
    proposer = pick(seats)
    comps = norm_comps(ask_json(proposer, P.decompose(req), {}, 0.5, "decompose").get("components"), req)
    reviewer = pick([s for s in seats if s is not proposer]) or proposer
    rv = ask_json(reviewer, P.decompose_review(req, comps), {"changed": "none", "components": comps}, 0.4, "decompose-review")
    if rv.get("changed") and str(rv["changed"]).strip().lower() != "none":
        comps = norm_comps(rv.get("components"), req)
    log.append({"step": 1, "who": proposer.letter, "components": comps})

    # 2. Bidding
    bids = pool([(lambda s=s: (s, ask_json(s, P.bid(req, comps), {"bids": [], "why": ""}, 0.5, "bid"))) for s in seats])
    bidders = {c["id"]: [] for c in comps}
    for s, b in bids:
        ids = [str(x) for x in (b.get("bids") if isinstance(b.get("bids"), list) else []) if str(x) in bidders]
        for i in ids:
            bidders[i].append(s)
        touch(s)["bids"] += len(ids)
    for c in comps:
        if not bidders[c["id"]]:
            load = lambda s: sum(1 for x in comps if s in bidders[x["id"]])
            bidders[c["id"]] = [sorted(willing(seats), key=load)[0]]
        lst = bidders[c["id"]][:]
        rng.shuffle(lst)
        bidders[c["id"]] = lst[:2]
    log.append({"step": 2, "bids": {c["id"]: [s.letter for s in bidders[c["id"]]] for c in comps}})

    # 3. Drafts, comparison of contested drafts, assembly, first critique
    jobs = []
    for c in comps:
        for s in bidders[c["id"]]:
            jobs.append(lambda c=c, s=s: {"c": c, "s": s, "text": ask_safe(s, P.draft(req, c), 0.8, "draft", ANSWER_TOKENS)})
    drafts = [d for d in pool(jobs) if d["text"] is not None]
    for c in comps:  # a component whose every bidder declined goes to another seat; the task fails only if no seat will draft it
        if any(d["c"] is c for d in drafts):
            continue
        tried = {s.letter for s in bidders[c["id"]]}
        for s in sorted(willing(seats), key=lambda s: (s.letter in tried, sum(1 for d in drafts if d["s"] is s))):
            text = ask_safe(s, P.draft(req, c), 0.8, "draft", ANSWER_TOKENS)
            if text is not None:
                drafts.append({"c": c, "s": s, "text": text})
                break
        else:
            raise RuntimeError(f"every seat declined to draft component {c['id']}: " + "; ".join(f"{d['who']} at {d['step']}" for d in declined))
    per = {}
    for d in drafts:
        per.setdefault(d["c"]["id"], []).append(d)
        touch(d["s"])["drafts"] += 1
    chosen = {}
    cmp_jobs = []
    for c in comps:
        ds = per[c["id"]]
        if len(ds) == 1:
            chosen[c["id"]] = ds[0]
            continue

        def judge_job(c=c, ds=ds):
            judge = pick([s for s in seats if not any(d["s"] is s for d in ds)]) or ds[0]["s"]
            r = ask_json(judge, P.compare(req, c, ds[0]["text"], ds[1]["text"]), {"keep": "X"}, 0.3, "compare")
            chosen[c["id"]] = ds[1] if str(r.get("keep", "X")).upper() == "Y" else ds[0]
        cmp_jobs.append(judge_job)
    pool(cmp_jobs)
    loads = sorted(seats, key=lambda s: -sum(1 for c in comps if chosen[c["id"]]["s"] is s))
    assembler = loads[0]
    if len(comps) == 1:
        answer = chosen[comps[0]["id"]]["text"]
    else:
        parts = [{"c": c, "text": chosen[c["id"]]["text"]} for c in comps]
        answer = None
        for s in [assembler] + [x for x in willing(loads) if x is not assembler]:
            answer = ask_safe(s, P.assemble(req, parts), 0.5, "assemble", ANSWER_TOKENS)
            if answer is not None:
                assembler = s
                break
        if answer is None:  # no seat would stitch the parts: ship them in order so the panel still answers
            answer = "\n\n".join(f"{p['c']['title']}\n{p['text']}" for p in parts)
    author = chosen[comps[0]["id"]]["s"] if len(comps) == 1 else assembler
    log.append({"step": 3, "author": author.letter, "draft": answer})

    def critique_round(rnd):
        critics = [s for s in seats if s is not author]
        dissenter = pick(critics) if cfg.get("dissenter") else None
        res = pool([(lambda s=s: (s, ask_json(s, P.dissent(req, answer) if s is dissenter else P.critique(req, answer), {"challenges": [], "verdict": "ready"}, 0.6, "critique"))) for s in critics])
        chs = []
        for s, r in res:
            for x in (r.get("challenges") if isinstance(r.get("challenges"), list) else [])[:4]:
                if isinstance(x, dict) and (x.get("problem") or x.get("claim")):
                    chs.append({"from": s, "claim": str(x.get("claim") or ""), "problem": str(x.get("problem") or ""), "check": str(x.get("check") or "")})
        if chs:
            touch(author)["challenged"] += len(chs)
        log.append({"step": 3 if rnd == 1 else 4, "round": rnd, "challenges": [{"from": c["from"].letter, "problem": c["problem"]} for c in chs]})
        return chs

    challenges = critique_round(1)

    # 4. Molding
    agreed, rounds_used = False, 0
    for rnd in range(1, cfg["rounds"] + 1):
        rounds_used = rnd
        if challenges:
            reviser = pick([s for s in seats if s is not author]) or author
            r = None
            for s in [reviser] + [x for x in willing([x for x in seats if x is not author]) if x is not reviser]:
                r = ask_json2(s, P.revise(req, answer, challenges), {"answer": answer, "accepted": [], "rejected": []}, 0.5, "revise", ANSWER_TOKENS)
                if r is not None:
                    reviser = s
                    break
            if r is None:  # every seat declined to revise: the draft stands and the challenges stay open
                r = {"answer": answer, "accepted": [], "rejected": []}
            replaced, refused_text = False, None
            if isinstance(r.get("answer"), str) and len(r["answer"].strip()) > 20:
                if keeps_format(task, answer, r["answer"].strip()):
                    answer = r["answer"].strip(); replaced = True
                else:  # the revision dropped the answer format: the text that stood before it stays
                    refused_text = r["answer"].strip(); note_refusal(reviser.letter, "revise", f"round {rnd}", refused_text)
            acc = [int(n) for n in (r.get("accepted") or []) if str(n).isdigit() and 1 <= int(n) <= len(challenges)]
            rej = [{"n": int(x.get("n")), "why": str(x.get("why") or "")} for x in (r.get("rejected") or []) if isinstance(x, dict) and str(x.get("n", "")).isdigit() and 1 <= int(x["n"]) <= len(challenges)]
            for n in acc:
                ch = challenges[n - 1]
                if replaced:  # a refused revision corrected nothing
                    t = touch(author); t["corrected"] += 1
                    t["recent"] = ([(ch["problem"] or ch["claim"])[:120]] + t["recent"])[:3]
                record["accepted"].append(ch)
            for x in rej:
                ch = challenges[x["n"] - 1]; touch(ch["from"])["overruled"] += 1
                record["rejected"].append(dict(ch, why=x["why"]))
            if replaced:
                author = reviser
            log.append({"step": 4, "round": rnd, "reviser": reviser.letter, "accepted": len(acc), "rejected": len(rej), "answer": answer,
                        **({"refused": refused_text} if refused_text is not None else {})})
        votes = pool([(lambda s=s: (s, ask_json2(s, P.vote(req, answer), {"ready": False, "objection": "vote could not be read"}, 0.3, "vote"))) for s in seats])
        abstained = [s for s, v in votes if v is None]  # a seat that declined to vote abstains; an unreadable vote still counts as an objection
        votes = [(s, v) for s, v in votes if v is not None]
        voters = [s for s, _ in votes]
        ready_w = sum(s.weight for s, v in votes if v.get("ready") is True)
        total_w = sum(s.weight for s in voters)
        frontier = [s for s in voters if s.tier_class == "frontier"]
        frontier_ok = all(next((v for s2, v in votes if s2 is s), {}).get("ready") is True for s in frontier)
        agreed = bool(votes) and ((frontier_ok and ready_w / total_w >= 0.66) if cfg.get("tier") in ("apex", "god") else all(v.get("ready") is True for _, v in votes))
        record["objections"] = [{"from": s, "objection": str(v.get("objection") or "")} for s, v in votes if v.get("ready") is not True]
        log.append({"step": 4, "round": rnd, "votes": {s.letter: (v.get("ready") is True) for s, v in votes}, "agreed": agreed, **({"abstained": [s.letter for s in abstained]} if abstained else {})})
        if agreed:
            break
        if rnd < cfg["rounds"]:
            challenges = critique_round(rnd + 1)
    for o in record["objections"]:
        touch(o["from"])["objections"] += 1

    pre_hub_answer = answer
    hub_qs, hub_open, checks, hub_corrected, sent_back = 0, [], [], False, False

    # 5. Interrogation (skipped when the hub is removed)
    if cfg.get("hub"):
        hub_sys = P.hub_system(cfg["hub_budget"])
        remaining, qn, qa = cfg["hub_budget"], 0, []
        hub_down = None  # set when a hub call gives up: the interrogation stops and the answer ships flagged, as a deadlock does

        def hub_call(user, step):
            nonlocal hub_down
            try:
                return api.chat(cfg["hub"], hub_sys, user, 0.3, max_tokens=JSON_TOKENS, ctx=dict(ctx, step=step), json_step=True)
            except RuntimeError as e:
                hub_down = f"{step}: {str(e)[:160]}"
                note_decline("hub", step, e)
                return None

        raw = hub_call(P.hub_ask(req, answer, record_text(record), catalogue_digest(seats, cat), min(3, remaining), remaining), "hub-ask")
        hq = parse_json(raw, {"questions": extract_questions(raw), "checks": []}) if raw is not None else {"questions": [], "checks": []}
        for c in (hq.get("checks") if isinstance(hq.get("checks"), list) else [])[:4]:
            if not isinstance(c, dict):
                continue
            value = checkers.safe_eval(c.get("expr"))
            claimed = checkers.parse_number(str(c.get("claimed", "")))
            valid = value is not None and claimed is not None
            ok = valid and abs(value - claimed) <= max(0.01, abs(value) * 0.005)
            checks.append({"kind": "arithmetic", "expr": str(c.get("expr") or ""), "claimed": claimed, "value": value, "valid": valid, "ok": ok, "addressed": False})

        def mechanical():
            """Checks the hub does not need to understand: run the visible examples."""
            if task and task.get("answer_type") == "code":
                ok, detail = checkers.visible_check(task, answer, prelude)
                checks[:] = [c for c in checks if c["kind"] != "code"] + [{"kind": "code", "expr": "run visible examples", "claimed": "pass", "value": detail, "valid": True, "ok": ok, "addressed": False}]
        mechanical()
        for c in checks:
            if c["valid"] and not c["ok"]:
                touch(author)["checksFailed"] += 1
        record["checks"] = checks
        questions = [str(q) for q in (hq.get("questions") if isinstance(hq.get("questions"), list) else []) if q]
        failing0 = [c for c in checks if c["valid"] and not c["ok"]]
        if failing0 and not questions:  # a failed check is itself a question
            questions = ["A check computed outside the panel failed. Which figure or example is wrong, and what is the corrected answer?"]
        sent_back = bool(questions) or bool(failing0)
        while questions and remaining > 0 and not hub_down:
            batch = [{"n": (qn := qn + 1), "q": q} for q in questions[:min(3, remaining)]]
            remaining -= len(batch)
            qa.extend(batch)
            failing = [f"{c['expr']} = {c['value']}, but the answer claims {c['claimed']}" if c["kind"] == "arithmetic" else f"running the visible examples failed: {c['value']}" for c in checks if c["valid"] and not c["ok"] and not c["addressed"]]
            pr = None
            for s in [author] + [x for x in willing(seats) if x is not author]:  # the author answers the hub; if it declines, another seat does
                pr = ask_json2(s, P.panel_reply(req, answer, batch, failing), {"replies": [], "correctedAnswer": None}, 0.4, "panel-reply", ANSWER_TOKENS)
                if pr is not None:
                    break
            if pr is None:
                pr = {"replies": [], "correctedAnswer": None}
            replies = pr.get("replies") if isinstance(pr.get("replies"), list) else []
            for i, b in enumerate(batch):
                r = next((x for x in replies if isinstance(x, dict) and str(x.get("n")) == str(b["n"])), replies[i] if i < len(replies) and isinstance(replies[i], dict) else None)
                b["reply"] = str(r.get("reply") or "") if r else "No reply."
            refused_text = None
            if isinstance(pr.get("correctedAnswer"), str) and len(pr["correctedAnswer"].strip()) > 20:
                if keeps_format(task, answer, pr["correctedAnswer"].strip()):
                    answer = pr["correctedAnswer"].strip(); hub_corrected = True
                    t = touch(author); t["corrected"] += 1; t["recent"] = (["corrected under interrogation"] + t["recent"])[:3]
                    for c in checks:
                        if c["kind"] == "arithmetic":
                            c["addressed"] = True
                    mechanical()  # re-run the visible examples on the corrected code
                else:  # the correction dropped the answer format: the answer under interrogation stays
                    refused_text = pr["correctedAnswer"].strip(); note_refusal(s.letter, "panel-reply", f"questions {batch[0]['n']} to {batch[-1]['n']}", refused_text)
            under_review = [next(b for b in qa if b["n"] == o["n"]) for o in hub_open] + batch
            rv_raw = hub_call(P.hub_review(req, answer, under_review, remaining), "hub-review")
            if rv_raw is None:  # the hub went silent mid-interrogation: everything under review stays open
                hub_open = [{"n": b["n"], "why": "the hub did not answer", "q": b["q"]} for b in under_review]
                questions = []
                log.append({"step": 5, "asked": [b["q"] for b in batch], "replies": [b.get("reply") for b in batch], "open": [o["why"] for o in hub_open], "corrected": hub_corrected, "hub_down": hub_down,
                            **({"refused": refused_text} if refused_text is not None else {})})
                break
            rv = parse_json(rv_raw, {"resolved": [b["n"] for b in under_review], "open": [], "questions": extract_questions(rv_raw)})
            resolved = {int(n) for n in (rv.get("resolved") or []) if str(n).isdigit()}
            hub_open = [{"n": int(o["n"]), "why": str(o.get("why") or ""), "q": next(b["q"] for b in under_review if b["n"] == int(o["n"]))}
                        for o in (rv.get("open") or []) if isinstance(o, dict) and str(o.get("n", "")).isdigit() and any(b["n"] == int(o["n"]) for b in under_review)]
            questions = [str(q) for q in (rv.get("questions") or []) if q] if remaining > 0 else []
            log.append({"step": 5, "asked": [b["q"] for b in batch], "replies": [b.get("reply") for b in batch], "open": [o["why"] for o in hub_open], "corrected": hub_corrected,
                        **({"refused": refused_text} if refused_text is not None else {})})
        hub_qs = qn
        if hub_down and not hub_open:  # the hub never reviewed the answer: it ships with that flag, not as cleared
            hub_open = [{"n": 0, "why": "the hub did not answer (" + hub_down + ")", "q": "hub interrogation"}]
        record["hub_open"] = hub_open
        hub_clear = not hub_open and not questions
    else:
        hub_clear = True

    # 6. Release
    checks_ok = not any(c["valid"] and not c["ok"] and not c["addressed"] and c["kind"] == "arithmetic" for c in checks) and not any(c["kind"] == "code" and not c["ok"] for c in checks)
    gates = {"agreed": agreed, "hub_clear": hub_clear, "checks_ok": checks_ok}
    shipped = agreed and hub_clear and checks_ok
    return {"answer": answer, "pre_hub_answer": pre_hub_answer, "agreed": agreed, "rounds_used": rounds_used, "gates": gates, "shipped": shipped,
            "hub_questions": hub_qs, "hub_open": len(hub_open), "hub_sent_back": sent_back, "hub_corrected": hub_corrected,
            "checks": [{k: v for k, v in c.items() if k != "addressed"} for c in checks], "author": author.letter,
            "seats": {s.letter: s.model for s in seats}, "declined": declined, "refused": refused, "log": log}
