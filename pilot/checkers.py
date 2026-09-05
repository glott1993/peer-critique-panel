"""Checkers: turn a model's answer text into pass/fail against the task key.

Number answers: the last line matching 'FINAL: <value>' is parsed; a stored
integer must match exactly, a stored decimal must match to within half a
unit of the requested precision plus 0.01% (so rounding differences pass and
arithmetic slips fail). String answers are compared after normalization.
Code answers: the last ```python block is run against the tests in a
separate, resource-limited interpreter with a timeout.
"""
import ast, json, operator, os, re, subprocess, sys, tempfile

FINAL_RE = re.compile(r"^\s*\**\s*FINAL\s*:\s*\**\s*(.+?)\s*\**\s*$", re.I | re.M)
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?|[-+]?\.\d+")
CODE_BLOCK_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def extract_final(text):
    """Return the value after the last FINAL: line, or None."""
    if not text:
        return None
    hits = FINAL_RE.findall(text)
    return hits[-1].strip() if hits else None


def parse_number(s):
    if s is None:
        return None
    s = s.replace("$", "").replace("%", "").replace("\u2212", "-")
    m = NUM_RE.search(s)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def norm_string(s):
    if s is None:
        return None
    s = s.strip().strip("\"'`*").strip().rstrip(".").strip().lower()
    s = re.sub(r"\s+", " ", s)
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", s)
    if m:  # times: pad the hour
        s = f"{int(m.group(1)):02d}:{m.group(2)}"
    return s


def check_number(task, text):
    val = parse_number(extract_final(text))
    if val is None:
        return False, "no FINAL number"
    exp = float(task["expected"]); prec = int(task.get("precision", 0))
    if prec == 0 and float(exp).is_integer():
        ok = abs(val - exp) < 1e-9
    else:
        tol = 0.5 * 10 ** (-prec) + 1e-9 + 1e-4 * abs(exp)
        ok = abs(val - exp) <= tol
    return ok, f"got {val}, expected {exp}"


def check_string(task, text):
    got = norm_string(extract_final(text))
    exp = norm_string(str(task["expected"]))
    if got is None:
        return False, "no FINAL value"
    return got == exp, f"got {got!r}, expected {exp!r}"


def extract_code(text):
    if not text:
        return None
    blocks = CODE_BLOCK_RE.findall(text)
    if blocks:
        return blocks[-1]
    if "def " in text:  # bare code without fences
        return text
    return None


def run_code(code, tests, prelude, timeout=10):
    """Run candidate code plus test assertions in a separate interpreter.

    Returns (passed, detail). The child runs with -I (isolated), a CPU and
    memory rlimit, and the working directory set to an empty temp folder.
    This is a guard against accidents, not a sandbox against hostile code:
    run the pilot in a disposable environment.
    """
    if code is None:
        return False, "no code block"
    src = code + "\n\n" + prelude + "\n" + "\n".join(tests) + "\nprint('__ALL_TESTS_PASSED__')\n"
    limiter = ("try:\n"
               "    import resource\n"
               "    resource.setrlimit(resource.RLIMIT_CPU, (%d, %d))\n"
               "    resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))\n"
               "except Exception:\n"
               "    pass\n" % (timeout, timeout))
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "candidate.py")
        with open(path, "w") as f:
            f.write(src)
        runner = limiter + f"exec(compile(open({path!r}).read(), 'candidate', 'exec'), {{'__name__': '__main__'}})\n"
        try:
            r = subprocess.run([sys.executable, "-I", "-c", runner], capture_output=True, text=True, timeout=timeout + 2, cwd=d)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    if r.returncode == 0 and "__ALL_TESTS_PASSED__" in r.stdout:
        return True, "all tests passed"
    err = (r.stderr or r.stdout or "").strip().splitlines()
    return False, (err[-1] if err else f"exit {r.returncode}")[:300]


def score(task, text, prelude=""):
    """Score an answer text against the task. Hidden tests for code."""
    t = task["answer_type"]
    if t == "number":
        return check_number(task, text)
    if t == "string":
        return check_string(task, text)
    if t == "code":
        return run_code(extract_code(text), task["visible_tests"] + task["hidden_tests"], prelude)
    raise ValueError(t)


def visible_check(task, text, prelude=""):
    """The mechanical check the hub can order: run the visible examples only."""
    if task["answer_type"] != "code":
        return None
    return run_code(extract_code(text), task["visible_tests"], prelude)


# --- arithmetic checks the hub can order (numbers and + - * / ( ) ** % only)
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos}


def safe_eval(expr):
    try:
        tree = ast.parse(str(expr).replace(",", "").replace("^", "**"), mode="eval")
    except Exception:
        return None

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 400:
                raise ValueError("exponent too large")
            return _OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("unsupported")
    try:
        v = ev(tree)
        return float(v) if isinstance(v, (int, float)) else None
    except Exception:
        return None


if __name__ == "__main__":
    # tiny self-test
    assert extract_final("blah\nFINAL: 12.5\n") == "12.5"
    assert extract_final("FINAL: 3\nmore\n**FINAL:** $1,234.50") == "$1,234.50"
    assert parse_number("$1,234.50") == 1234.5
    assert check_number({"expected": 1234.5, "precision": 2}, "FINAL: 1234.50")[0]
    assert not check_number({"expected": 35, "precision": 0}, "FINAL: 36")[0]
    assert check_string({"expected": "09:00"}, "FINAL: 9:00")[0]
    assert abs(safe_eval("0.07*1200") - 84.0) < 1e-9 and safe_eval("import os") is None
    ok, det = run_code("def f(x):\n    return x+1\n", ["assert f(1) == 2"], "")
    assert ok, det
    ok, det = run_code("def f(x):\n    return x+2\n", ["assert f(1) == 2"], "")
    assert not ok
    print("checkers ok")
