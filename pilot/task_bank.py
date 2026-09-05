"""Original coding tasks for the pilot.

Each task has a plain-language spec, a few visible example assertions that
are shown to the models (and that the hub runs mechanically), a larger set
of hidden assertions used only for scoring, and a reference solution.
make_tasks.py verifies every reference against every test before export.
"""

TEST_PRELUDE = '''
def _raises(fn, *args, **kw):
    try:
        fn(*args, **kw)
    except ValueError:
        return True
    except Exception:
        return False
    return False
'''

CODE_TASKS = [
    {
        "id": "code-01",
        "name": "parse_duration",
        "spec": "Write a Python function parse_duration(s: str) -> int that converts a duration string into a number of seconds. The string holds one or more parts, each a non-negative integer followed by one unit letter: h (hours), m (minutes) or s (seconds). Parts may appear in any order, separated by any amount of whitespace or none at all, e.g. '1h 30m', '45m', '2h5s', '90s'. Leading and trailing whitespace is allowed. Each unit may appear at most once. For an empty string, an unknown unit, a repeated unit, a number without a unit, a unit without a number, a decimal number, or any other malformed input, raise ValueError.",
        "visible": [
            "assert parse_duration('1h 30m') == 5400",
            "assert parse_duration('45m') == 2700",
            "assert parse_duration('2h5s') == 7205",
        ],
        "hidden": [
            "assert parse_duration('90s') == 90",
            "assert parse_duration('  1h  ') == 3600",
            "assert parse_duration('30m 1h') == 5400",
            "assert parse_duration('0s') == 0",
            "assert parse_duration('1h1m1s') == 3661",
            "assert _raises(parse_duration, '')",
            "assert _raises(parse_duration, '1x')",
            "assert _raises(parse_duration, '1h1h')",
            "assert _raises(parse_duration, 'h')",
            "assert _raises(parse_duration, '1h m')",
            "assert _raises(parse_duration, '1.5h')",
            "assert _raises(parse_duration, '   ')",
        ],
        "reference": '''
import re
def parse_duration(s):
    s = s.strip()
    if not s:
        raise ValueError("empty")
    pat = re.compile(r"\\s*(\\d+)\\s*([hms])\\s*")
    pos, total, seen = 0, 0, set()
    while pos < len(s):
        m = pat.match(s, pos)
        if not m:
            raise ValueError("malformed")
        n, u = int(m.group(1)), m.group(2)
        if u in seen:
            raise ValueError("repeated unit")
        seen.add(u)
        total += n * {"h": 3600, "m": 60, "s": 1}[u]
        pos = m.end()
    return total
''',
    },
    {
        "id": "code-02",
        "name": "merge_intervals",
        "spec": "Write a Python function merge_intervals(intervals) that takes a list of [start, end] integer pairs (start <= end, inclusive) in any order and returns a new list of merged pairs sorted by start. Two intervals merge when they overlap or touch: [1, 4] and [4, 5] merge into [1, 5], but [1, 4] and [5, 6] do not. Return each interval as a two-element list. An empty input returns an empty list. Do not modify the input.",
        "visible": [
            "assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]",
            "assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]",
        ],
        "hidden": [
            "assert merge_intervals([[1, 4], [5, 6]]) == [[1, 4], [5, 6]]",
            "assert merge_intervals([]) == []",
            "assert merge_intervals([[5, 7], [1, 3]]) == [[1, 3], [5, 7]]",
            "assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]",
            "assert merge_intervals([[2, 2]]) == [[2, 2]]",
            "assert merge_intervals([[1, 2], [2, 3], [3, 4]]) == [[1, 4]]",
            "assert merge_intervals([[3, 5], [1, 2], [6, 8], [5, 6]]) == [[1, 2], [3, 8]]",
            "_x = [[3, 4], [1, 2]]; merge_intervals(_x); assert _x == [[3, 4], [1, 2]]",
        ],
        "reference": '''
def merge_intervals(intervals):
    out = []
    for s, e in sorted([list(i) for i in intervals]):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
''',
    },
    {
        "id": "code-03",
        "name": "rle_encode",
        "spec": "Write a Python function rle_encode(s: str) -> str. Scan the string for runs of identical consecutive characters. A run of 4 or more is written as the character followed by '#' and the run length in decimal (so 'aaaaa' becomes 'a#5'). Runs of 1 to 3 characters are written literally. The input never contains '#'. The empty string encodes to the empty string.",
        "visible": [
            "assert rle_encode('aaaaabbbcc') == 'a#5bbbcc'",
            "assert rle_encode('aaaa') == 'a#4'",
        ],
        "hidden": [
            "assert rle_encode('') == ''",
            "assert rle_encode('aaa') == 'aaa'",
            "assert rle_encode('abababab') == 'abababab'",
            "assert rle_encode('x' * 12) == 'x#12'",
            "assert rle_encode('aaaabaaaa') == 'a#4ba#4'",
            "assert rle_encode(' ' * 5) == ' #5'",
            "assert rle_encode('aaaaBBBBBcc') == 'a#4B#5cc'",
            "assert rle_encode('z') == 'z'",
        ],
        "reference": '''
def rle_encode(s):
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        n = j - i
        out.append(s[i] + "#" + str(n) if n >= 4 else s[i] * n)
        i = j
    return "".join(out)
''',
    },
    {
        "id": "code-04",
        "name": "luhn_valid",
        "spec": "Write a Python function luhn_valid(s: str) -> bool that checks a number with the Luhn algorithm. First remove all spaces and hyphens. If the remaining string has fewer than 2 characters or contains anything other than digits, return False. Otherwise, starting from the rightmost digit and moving left, double every second digit (subtracting 9 if the result exceeds 9), sum all digits, and return True exactly when the sum is a multiple of 10.",
        "visible": [
            "assert luhn_valid('4111 1111 1111 1111') is True",
            "assert luhn_valid('4111 1111 1111 1112') is False",
        ],
        "hidden": [
            "assert luhn_valid('79927398713') is True",
            "assert luhn_valid('7992-7398-713') is True",
            "assert luhn_valid('') is False",
            "assert luhn_valid('0') is False",
            "assert luhn_valid('00') is True",
            "assert luhn_valid('4111a1111111111') is False",
            "assert luhn_valid('18') is True",
            "assert luhn_valid('19') is False",
            "assert luhn_valid(' 1 8 ') is True",
        ],
        "reference": '''
def luhn_valid(s):
    d = s.replace(" ", "").replace("-", "")
    if len(d) < 2 or not d.isdigit():
        return False
    total = 0
    for i, ch in enumerate(reversed(d)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0
''',
    },
    {
        "id": "code-05",
        "name": "business_days",
        "spec": "Write a Python function business_days(start: str, end: str, holidays) -> int. start and end are ISO dates 'YYYY-MM-DD'; holidays is an iterable of ISO date strings. Return the number of days from start to end inclusive that are Monday to Friday and are not in holidays. If end is before start, return 0. Holidays that fall on weekends must not be double counted.",
        "visible": [
            "assert business_days('2026-09-07', '2026-09-11', []) == 5",
            "assert business_days('2026-09-07', '2026-09-11', ['2026-09-09']) == 4",
        ],
        "hidden": [
            "assert business_days('2026-09-05', '2026-09-06', []) == 0",
            "assert business_days('2026-09-11', '2026-09-07', []) == 0",
            "assert business_days('2026-09-07', '2026-09-07', []) == 1",
            "assert business_days('2026-09-01', '2026-09-30', ['2026-09-07']) == 21",
            "assert business_days('2026-09-07', '2026-09-11', ['2026-09-12', '2026-09-13']) == 5",
            "assert business_days('2026-12-24', '2027-01-02', ['2026-12-25', '2027-01-01']) == 5",
            "assert business_days('2024-02-26', '2024-03-01', []) == 5",
            "assert business_days('2026-09-07', '2026-09-11', ['2026-09-09', '2026-09-09']) == 4",
        ],
        "reference": '''
from datetime import date, timedelta
def business_days(start, end, holidays):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    if b < a:
        return 0
    hol = {date.fromisoformat(h) for h in holidays}
    n, d = 0, a
    while d <= b:
        if d.weekday() < 5 and d not in hol:
            n += 1
        d += timedelta(days=1)
    return n
''',
    },
    {
        "id": "code-06",
        "name": "top_k_frequent",
        "spec": "Write a Python function top_k_frequent(words, k) that returns a list of the k most frequent strings in the list words, most frequent first. Ties in frequency are broken alphabetically (plain string order, case-sensitive). If k exceeds the number of distinct words, return all distinct words in that order. k is a non-negative integer; k == 0 returns an empty list.",
        "visible": [
            "assert top_k_frequent(['a', 'b', 'a', 'c', 'b', 'a'], 2) == ['a', 'b']",
            "assert top_k_frequent(['x', 'y', 'z'], 2) == ['x', 'y']",
        ],
        "hidden": [
            "assert top_k_frequent([], 3) == []",
            "assert top_k_frequent(['b', 'a'], 5) == ['a', 'b']",
            "assert top_k_frequent(['b', 'b', 'a', 'a', 'c'], 2) == ['a', 'b']",
            "assert top_k_frequent(['B', 'a', 'B', 'a'], 1) == ['B']",
            "assert top_k_frequent(['q'], 0) == []",
            "assert top_k_frequent(['dog', 'cat', 'cat', 'ant', 'ant', 'ant'], 3) == ['ant', 'cat', 'dog']",
        ],
        "reference": '''
from collections import Counter
def top_k_frequent(words, k):
    c = Counter(words)
    return [w for w, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))][:k]
''',
    },
    {
        "id": "code-07",
        "name": "int_to_base",
        "spec": "Write a Python function int_to_base(n: int, base: int) -> str that writes the integer n in the given base, 2 <= base <= 36, using digits 0-9 then lowercase letters a-z. Negative numbers get a leading '-'. Zero is '0' in every base. Raise ValueError for a base outside 2..36.",
        "visible": [
            "assert int_to_base(255, 16) == 'ff'",
            "assert int_to_base(-10, 2) == '-1010'",
        ],
        "hidden": [
            "assert int_to_base(0, 7) == '0'",
            "assert int_to_base(35, 36) == 'z'",
            "assert int_to_base(36, 36) == '10'",
            "assert int_to_base(8, 8) == '10'",
            "assert int_to_base(1295, 36) == 'zz'",
            "assert int_to_base(-1, 3) == '-1'",
            "assert _raises(int_to_base, 5, 1)",
            "assert _raises(int_to_base, 5, 37)",
        ],
        "reference": '''
def int_to_base(n, base):
    if not 2 <= base <= 36:
        raise ValueError("base")
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    neg, n = n < 0, abs(n)
    out = []
    while n:
        n, r = divmod(n, base)
        out.append(digits[r])
    return ("-" if neg else "") + "".join(reversed(out))
''',
    },
    {
        "id": "code-08",
        "name": "flatten_keys",
        "spec": "Write a Python function flatten_keys(d: dict) -> dict that flattens a nested structure of dicts and lists into a single-level dict. Nested dict keys are joined with '.', and list positions are written as '[i]' appended to the key, so {'a': {'b': 1, 'c': [2, {'d': 3}]}} becomes {'a.b': 1, 'a.c[0]': 2, 'a.c[1].d': 3}. All keys are strings. An empty dict or empty list encountered as a value is kept as that value under its key. The top-level input is always a dict.",
        "visible": [
            "assert flatten_keys({'a': {'b': 1, 'c': [2, {'d': 3}]}}) == {'a.b': 1, 'a.c[0]': 2, 'a.c[1].d': 3}",
            "assert flatten_keys({}) == {}",
        ],
        "hidden": [
            "assert flatten_keys({'x': []}) == {'x': []}",
            "assert flatten_keys({'k': {'m': {}}}) == {'k.m': {}}",
            "assert flatten_keys({'a': [[1, 2], [3]]}) == {'a[0][0]': 1, 'a[0][1]': 2, 'a[1][0]': 3}",
            "assert flatten_keys({'a': 1, 'b': 'two'}) == {'a': 1, 'b': 'two'}",
            "assert flatten_keys({'a': {'b': {'c': {'d': 4}}}}) == {'a.b.c.d': 4}",
            "assert flatten_keys({'a': [{'b': []}]}) == {'a[0].b': []}",
            "assert flatten_keys({'n': None}) == {'n': None}",
        ],
        "reference": '''
def flatten_keys(d):
    out = {}
    def walk(v, key):
        if isinstance(v, dict) and v:
            for k, x in v.items():
                walk(x, k if key == "" else key + "." + k)
        elif isinstance(v, list) and v:
            for i, x in enumerate(v):
                walk(x, key + "[" + str(i) + "]")
        else:
            out[key] = v
    for k, v in d.items():
        walk(v, k)
    return out
''',
    },
    {
        "id": "code-09",
        "name": "parse_range_list",
        "spec": "Write a Python function parse_range_list(s: str) -> list that parses strings like '1-3,5,8-10' into a sorted list of unique non-negative integers, here [1, 2, 3, 5, 8, 9, 10]. Items are separated by commas; whitespace around items is allowed. An item is either a single integer or two integers joined by '-' meaning an inclusive range. An empty string (or only whitespace) returns []. Raise ValueError for an empty item (as in '1,,2'), a range whose first number is larger than its second, a negative number, or anything that is not an integer.",
        "visible": [
            "assert parse_range_list('1-3,5,8-10') == [1, 2, 3, 5, 8, 9, 10]",
            "assert parse_range_list(' 4 , 2 ') == [2, 4]",
        ],
        "hidden": [
            "assert parse_range_list('') == []",
            "assert parse_range_list('   ') == []",
            "assert parse_range_list('3,3,1-3') == [1, 2, 3]",
            "assert parse_range_list('7-7') == [7]",
            "assert parse_range_list('0-2') == [0, 1, 2]",
            "assert _raises(parse_range_list, '1,,2')",
            "assert _raises(parse_range_list, '5-3')",
            "assert _raises(parse_range_list, '-1')",
            "assert _raises(parse_range_list, '1-2-3')",
            "assert _raises(parse_range_list, 'a')",
            "assert _raises(parse_range_list, '1,')",
        ],
        "reference": '''
def parse_range_list(s):
    if not s.strip():
        return []
    out = set()
    for item in s.split(","):
        item = item.strip()
        if not item:
            raise ValueError("empty item")
        parts = item.split("-")
        if len(parts) == 1:
            nums = [parts[0]]
        elif len(parts) == 2:
            nums = parts
        else:
            raise ValueError("bad range")
        vals = []
        for p in nums:
            p = p.strip()
            if not p.isdigit():
                raise ValueError("not an integer")
            vals.append(int(p))
        if len(vals) == 1:
            out.add(vals[0])
        else:
            if vals[0] > vals[1]:
                raise ValueError("reversed range")
            out.update(range(vals[0], vals[1] + 1))
    return sorted(out)
''',
    },
    {
        "id": "code-10",
        "name": "csv_split",
        "spec": "Write a Python function csv_split(line: str) -> list that splits one line of CSV into fields. Fields are separated by commas. A field may be enclosed in double quotes; inside a quoted field, commas are literal and a doubled quote \"\" stands for one literal quote. Unquoted fields are returned exactly as written (no trimming). A quoted field must be followed by a comma or the end of the line. The empty line yields one empty field: ['']. Raise ValueError for an unterminated quoted field or for characters after a closing quote.",
        "visible": [
            "assert csv_split('a,b,c') == ['a', 'b', 'c']",
            "assert csv_split('\"a,b\",c') == ['a,b', 'c']",
            "assert csv_split('\"say \"\"hi\"\"\",x') == ['say \"hi\"', 'x']",
        ],
        "hidden": [
            "assert csv_split('') == ['']",
            "assert csv_split('a,,b') == ['a', '', 'b']",
            "assert csv_split('a, b') == ['a', ' b']",
            "assert csv_split(',') == ['', '']",
            "assert csv_split('\"\"') == ['']",
            "assert csv_split('\"\",\"\"') == ['', '']",
            "assert csv_split('x,\"\"\"\"') == ['x', '\"']",
            "assert _raises(csv_split, '\"unterminated')",
            "assert _raises(csv_split, '\"a\"b')",
            "assert csv_split('a,\"b\"') == ['a', 'b']",
        ],
        "reference": '''
def csv_split(line):
    fields, i, n = [], 0, len(line)
    while True:
        if i < n and line[i] == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated quote")
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"'); i += 2; continue
                    i += 1
                    break
                buf.append(line[i]); i += 1
            fields.append("".join(buf))
            if i < n and line[i] != ",":
                raise ValueError("junk after closing quote")
        else:
            j = line.find(",", i)
            if j < 0:
                j = n
            fields.append(line[i:j])
            i = j
        if i >= n:
            return fields
        i += 1
        if i == n:
            fields.append("")
            return fields
''',
    },
    {
        "id": "code-11",
        "name": "moving_average",
        "spec": "Write a Python function moving_average(xs, w) that returns the list of simple moving averages of the numbers xs over windows of exactly w consecutive elements, each rounded to 4 decimal places, as floats. The result has len(xs) - w + 1 elements; if w is larger than len(xs), return []. w must be an integer >= 1, otherwise raise ValueError.",
        "visible": [
            "assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]",
            "assert moving_average([5, 5, 5], 3) == [5.0]",
        ],
        "hidden": [
            "assert moving_average([1, 2], 3) == []",
            "assert moving_average([], 1) == []",
            "assert moving_average([2], 1) == [2.0]",
            "assert moving_average([1, 2, 4], 1) == [1.0, 2.0, 4.0]",
            "assert moving_average([1, 1, 2], 3) == [1.3333]",
            "assert moving_average([0.1, 0.2, 0.3, 0.4], 3) == [0.2, 0.3]",
            "assert _raises(moving_average, [1, 2], 0)",
            "assert _raises(moving_average, [1, 2], 1.5)",
            "assert all(isinstance(v, float) for v in moving_average([1, 2, 3], 2))",
        ],
        "reference": '''
def moving_average(xs, w):
    if not isinstance(w, int) or isinstance(w, bool) or w < 1:
        raise ValueError("window")
    if w > len(xs):
        return []
    out, s = [], sum(xs[:w])
    out.append(round(s / w, 4))
    for i in range(w, len(xs)):
        s += xs[i] - xs[i - w]
        out.append(round(s / w, 4))
    return [float(v) for v in out]
''',
    },
    {
        "id": "code-12",
        "name": "is_balanced",
        "spec": "Write a Python function is_balanced(s: str) -> bool that returns True when every bracket in s is closed by the matching bracket in the correct nesting order, considering only the three pairs (), [] and {}. All other characters are ignored. The empty string is balanced.",
        "visible": [
            "assert is_balanced('([]{})') is True",
            "assert is_balanced('([)]') is False",
        ],
        "hidden": [
            "assert is_balanced('') is True",
            "assert is_balanced('((') is False",
            "assert is_balanced('a(b)c') is True",
            "assert is_balanced(')(') is False",
            "assert is_balanced('{[()()]}') is True",
            "assert is_balanced('{[(])}') is False",
            "assert is_balanced('no brackets here') is True",
            "assert is_balanced('(]') is False",
        ],
        "reference": '''
def is_balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    st = []
    for ch in s:
        if ch in "([{":
            st.append(ch)
        elif ch in pairs:
            if not st or st.pop() != pairs[ch]:
                return False
    return not st
''',
    },
    {
        "id": "code-13",
        "name": "slugify",
        "spec": "Write a Python function slugify(title: str) -> str. Lowercase the text, replace every maximal run of characters that are not ASCII letters or ASCII digits with a single hyphen, then strip hyphens from both ends. Non-ASCII letters count as separators (no transliteration). The result may be empty.",
        "visible": [
            "assert slugify('Hello, World!') == 'hello-world'",
            "assert slugify('  Multiple   spaces ') == 'multiple-spaces'",
        ],
        "hidden": [
            "assert slugify('---') == ''",
            "assert slugify('') == ''",
            "assert slugify('Caf\\u00e9 au lait') == 'caf-au-lait'",
            "assert slugify('A1 b2') == 'a1-b2'",
            "assert slugify('ALREADY-slug') == 'already-slug'",
            "assert slugify('x_y.z') == 'x-y-z'",
            "assert slugify('2026/09/05') == '2026-09-05'",
        ],
        "reference": '''
import re
def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
''',
    },
    {
        "id": "code-14",
        "name": "word_wrap",
        "spec": "Write a Python function word_wrap(text: str, width: int) -> list that splits text into words on whitespace and packs them greedily into lines of at most width characters, words separated by single spaces. A word longer than width goes on a line by itself, unbroken. Return the list of lines. Text that is empty or only whitespace returns []. Raise ValueError if width < 1.",
        "visible": [
            "assert word_wrap('the quick brown fox', 10) == ['the quick', 'brown fox']",
            "assert word_wrap('a bb ccc', 3) == ['a', 'bb', 'ccc']",
        ],
        "hidden": [
            "assert word_wrap('', 5) == []",
            "assert word_wrap('   ', 5) == []",
            "assert word_wrap('abcdefgh ij', 4) == ['abcdefgh', 'ij']",
            "assert word_wrap('a b c d', 3) == ['a b', 'c d']",
            "assert word_wrap('one\\ntwo  three', 9) == ['one two', 'three']",
            "assert word_wrap('exactly ten', 11) == ['exactly ten']",
            "assert word_wrap('exactly ten', 10) == ['exactly', 'ten']",
            "assert _raises(word_wrap, 'x', 0)",
        ],
        "reference": '''
def word_wrap(text, width):
    if width < 1:
        raise ValueError("width")
    lines, cur = [], ""
    for w in text.split():
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur += " " + w
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines
''',
    },
    {
        "id": "code-15",
        "name": "anagram_groups",
        "spec": "Write a Python function anagram_groups(words) that groups the strings in words that are anagrams of each other (same characters with the same counts; case-sensitive). Return a list of groups, keeping only groups with at least two words. Each group is a list sorted alphabetically (duplicates kept), and the groups are ordered by their first word.",
        "visible": [
            "assert anagram_groups(['eat', 'tea', 'tan', 'ate', 'nat', 'bat']) == [['ate', 'eat', 'tea'], ['nat', 'tan']]",
            "assert anagram_groups(['a']) == []",
        ],
        "hidden": [
            "assert anagram_groups([]) == []",
            "assert anagram_groups(['ab', 'ab', 'ba']) == [['ab', 'ab', 'ba']]",
            "assert anagram_groups(['Ab', 'ba']) == []",
            "assert anagram_groups(['listen', 'silent', 'enlist', 'google', 'gogole']) == [['enlist', 'listen', 'silent'], ['gogole', 'google']]",
            "assert anagram_groups(['zz', 'z']) == []",
            "assert anagram_groups(['b', 'a', 'b', 'a']) == [['a', 'a'], ['b', 'b']]",
        ],
        "reference": '''
def anagram_groups(words):
    groups = {}
    for w in words:
        groups.setdefault("".join(sorted(w)), []).append(w)
    out = [sorted(g) for g in groups.values() if len(g) >= 2]
    return sorted(out, key=lambda g: g[0])
''',
    },
    {
        "id": "code-16",
        "name": "next_permutation",
        "spec": "Write a Python function next_permutation(lst) that rearranges the list of integers lst in place into the lexicographically next greater permutation and returns True. If lst is already the last permutation (non-increasing order), rearrange it into the first permutation (sorted ascending) and return False. Duplicates are allowed. An empty list or a single-element list returns False.",
        "visible": [
            "_a = [1, 2, 3]; assert next_permutation(_a) is True and _a == [1, 3, 2]",
            "_b = [3, 2, 1]; assert next_permutation(_b) is False and _b == [1, 2, 3]",
        ],
        "hidden": [
            "_c = [1, 1, 5]; assert next_permutation(_c) is True and _c == [1, 5, 1]",
            "_d = []; assert next_permutation(_d) is False and _d == []",
            "_e = [7]; assert next_permutation(_e) is False and _e == [7]",
            "_f = [1, 3, 2]; assert next_permutation(_f) is True and _f == [2, 1, 3]",
            "_g = [2, 3, 1]; assert next_permutation(_g) is True and _g == [3, 1, 2]",
            "_h = [1, 5, 1]; assert next_permutation(_h) is True and _h == [5, 1, 1]",
            "_i = [2, 2]; assert next_permutation(_i) is False and _i == [2, 2]",
        ],
        "reference": '''
def next_permutation(lst):
    i = len(lst) - 2
    while i >= 0 and lst[i] >= lst[i + 1]:
        i -= 1
    if i < 0:
        lst.sort()
        return False
    j = len(lst) - 1
    while lst[j] <= lst[i]:
        j -= 1
    lst[i], lst[j] = lst[j], lst[i]
    lst[i + 1:] = lst[i + 1:][::-1]
    return True
''',
    },
    {
        "id": "code-17",
        "name": "dedupe_stable",
        "spec": "Write a Python function dedupe_stable(items) that returns a new list with duplicates removed, keeping the first occurrence of each value in its original order. Equality is decided with ==, and the function must work for unhashable items such as lists.",
        "visible": [
            "assert dedupe_stable([1, 2, 1, 3, 2]) == [1, 2, 3]",
            "assert dedupe_stable([[1], [2], [1]]) == [[1], [2]]",
        ],
        "hidden": [
            "assert dedupe_stable([]) == []",
            "assert dedupe_stable(['a', 'A', 'a']) == ['a', 'A']",
            "assert dedupe_stable([1, 1.0, True]) == [1]",
            "assert dedupe_stable([{'k': 1}, {'k': 1}, {'k': 2}]) == [{'k': 1}, {'k': 2}]",
            "assert dedupe_stable([None, None, 0]) == [None, 0]",
            "_z = [3, 3]; _r = dedupe_stable(_z); assert _r == [3] and _z == [3, 3]",
        ],
        "reference": '''
def dedupe_stable(items):
    out = []
    for x in items:
        if not any(x == y for y in out):
            out.append(x)
    return out
''',
    },
    {
        "id": "code-18",
        "name": "compare_versions",
        "spec": "Write a Python function compare_versions(a: str, b: str) -> int that compares two dotted version strings numerically part by part and returns -1, 0 or 1 for a < b, a == b, a > b. Missing trailing parts count as 0, so '1.2' equals '1.2.0'. Leading zeros are allowed ('1.01' equals '1.1'). Raise ValueError if any part is empty or is not a string of decimal digits.",
        "visible": [
            "assert compare_versions('1.2.10', '1.2.9') == 1",
            "assert compare_versions('1.2', '1.2.0') == 0",
        ],
        "hidden": [
            "assert compare_versions('0.9', '1.0') == -1",
            "assert compare_versions('1.01', '1.1') == 0",
            "assert compare_versions('2', '10') == -1",
            "assert compare_versions('1.0.0.1', '1') == 1",
            "assert _raises(compare_versions, '1..2', '1.2')",
            "assert _raises(compare_versions, '1.a', '1.0')",
            "assert _raises(compare_versions, '', '1')",
            "assert _raises(compare_versions, '1.-1', '1')",
        ],
        "reference": '''
def compare_versions(a, b):
    def parts(v):
        ps = v.split(".")
        if any(not p.isdigit() for p in ps):
            raise ValueError("bad version")
        return [int(p) for p in ps]
    x, y = parts(a), parts(b)
    n = max(len(x), len(y))
    x += [0] * (n - len(x)); y += [0] * (n - len(y))
    return (x > y) - (x < y)
''',
    },
    {
        "id": "code-19",
        "name": "spiral_order",
        "spec": "Write a Python function spiral_order(matrix) that returns the elements of a rectangular matrix (a list of equal-length row lists) in clockwise spiral order starting from the top-left element: across the top row, down the right column, back along the bottom row, up the left column, then inward. An empty matrix or a matrix of empty rows returns [].",
        "visible": [
            "assert spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]",
            "assert spiral_order([[1, 2], [3, 4]]) == [1, 2, 4, 3]",
        ],
        "hidden": [
            "assert spiral_order([]) == []",
            "assert spiral_order([[]]) == []",
            "assert spiral_order([[1, 2, 3, 4]]) == [1, 2, 3, 4]",
            "assert spiral_order([[1], [2], [3]]) == [1, 2, 3]",
            "assert spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]",
            "assert spiral_order([[1, 2], [3, 4], [5, 6]]) == [1, 2, 4, 6, 5, 3]",
            "assert spiral_order([[7]]) == [7]",
        ],
        "reference": '''
def spiral_order(matrix):
    if not matrix or not matrix[0]:
        return []
    out = []
    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            out.append(matrix[top][c])
        for r in range(top + 1, bottom + 1):
            out.append(matrix[r][right])
        if top < bottom:
            for c in range(right - 1, left - 1, -1):
                out.append(matrix[bottom][c])
        if left < right:
            for r in range(bottom - 1, top, -1):
                out.append(matrix[r][left])
        top += 1; bottom -= 1; left += 1; right -= 1
    return out
''',
    },
    {
        "id": "code-20",
        "name": "caesar_shift",
        "spec": "Write a Python function caesar_shift(s: str, k: int) -> str that shifts every ASCII letter in s forward by k positions in the alphabet, wrapping around, keeping each letter's case, and leaving every other character unchanged. k may be negative or larger than 26.",
        "visible": [
            "assert caesar_shift('abc', 1) == 'bcd'",
            "assert caesar_shift('XYZ', 3) == 'ABC'",
        ],
        "hidden": [
            "assert caesar_shift('Hello, World!', -1) == 'Gdkkn, Vnqkc!'",
            "assert caesar_shift('abc', 26) == 'abc'",
            "assert caesar_shift('abc', -27) == 'zab'",
            "assert caesar_shift('', 5) == ''",
            "assert caesar_shift('a1B2', 27) == 'b1C2'",
            "assert caesar_shift('\\u00e9a', 1) == '\\u00e9b'",
        ],
        "reference": '''
def caesar_shift(s, k):
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + k) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + k) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)
''',
    },
]
