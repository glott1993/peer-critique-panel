"""Build the pilot task set.

Math and data tasks are generated from templates with a fixed seed; the
answer is computed by the same code that writes the prompt, so the key is
right by construction. Code tasks come from task_bank.py and every
reference solution is run against its tests before export.

    python make_tasks.py            # writes tasks/fresh_tasks.json
    python make_tasks.py --seed 7   # a different draw of parameters
"""
import argparse, json, math, os, random, statistics, subprocess, sys
from datetime import date, timedelta

import task_bank

NUMBER_RULE = ("Show brief working, then end your reply with exactly one line of the form "
               "FINAL: <answer>. For a number give digits only (no units, no currency sign, no commas; "
               "use a decimal point). For a date use YYYY-MM-DD. For a time use HH:MM in 24-hour form. "
               "For a weekday or a name give the word only.")
CODE_RULE = ("Reply with the complete function definition in one ```python code block (imports included). "
             "Brief prose around it is fine. The block must pass the visible examples and will be run "
             "against additional hidden tests.")


def num_task(tid, prompt, expected, precision, tags):
    return {"id": tid, "type": "math", "prompt": prompt + "\n\n" + NUMBER_RULE,
            "answer_type": "number", "expected": round(expected, precision), "precision": precision, "tags": tags}


def str_task(tid, prompt, expected, tags, ttype="math"):
    return {"id": tid, "type": ttype, "prompt": prompt + "\n\n" + NUMBER_RULE,
            "answer_type": "string", "expected": expected, "tags": tags}


# ---------------------------------------------------------------- math ----
def gen_math(rng):
    tasks = []
    k = 0

    def nid():
        nonlocal k
        k += 1
        return f"math-{k:02d}"

    for _ in range(2):  # compound savings with contributions
        P = rng.choice([2500, 4000, 7500, 12000]); r = rng.choice([3.6, 4.2, 4.8, 5.4]); c = rng.choice([150, 200, 350, 500]); n = rng.choice([36, 48, 60, 84])
        i = r / 1200
        fv = P * (1 + i) ** n + c * ((1 + i) ** n - 1) / i
        tasks.append(num_task(nid(), f"You deposit ${P:,} in an account that earns {r}% per year, compounded monthly, and you add ${c} at the end of every month. What is the balance immediately after the {n}th deposit? Give the amount in dollars to the nearest cent.", fv, 2, ["finance", "exponent"]))

    for _ in range(2):  # loan payment
        L = rng.choice([18500, 24000, 31200, 42750]); a = rng.choice([5.9, 6.75, 7.25, 8.4]); y = rng.choice([4, 5, 6])
        i = a / 1200; n = y * 12
        M = L * i / (1 - (1 + i) ** (-n))
        tasks.append(num_task(nid(), f"A ${L:,} loan is repaid in equal monthly payments over {y} years at {a}% APR, compounded monthly (standard amortization). What is the monthly payment, in dollars to the nearest cent?", M, 2, ["finance", "exponent"]))

    for _ in range(2):  # work rate
        while True:
            a = rng.choice([6, 8, 9, 10, 12]); b = rng.choice([9, 12, 15, 18]); t = rng.choice([2, 3, 4])
            rem = 1 - t * (1 / a + 1 / b)
            if rem > 0.05 and a != b:
                break
        minutes = rem * b * 60
        tasks.append(num_task(nid(), f"Pump A can fill a tank alone in {a} hours and pump B alone in {b} hours. Both run together for {t} hours, then pump A is switched off. How many more minutes does pump B need to finish filling the tank? Give the answer in minutes to one decimal place.", minutes, 1, ["rates"]))

    for _ in range(2):  # mixture
        while True:
            p = rng.choice([40, 50, 60, 70]); q = rng.choice([10, 15, 20, 25]); s = rng.choice([30, 35, 45]); y = rng.choice([12, 18, 20, 30])
            if q < s < p:
                break
        x = y * (s - q) / (p - s)
        tasks.append(num_task(nid(), f"A chemist has {y} liters of a {q}% acid solution. How many liters of a {p}% acid solution must be added to obtain a {s}% solution? Give the answer in liters to two decimal places.", x, 2, ["algebra"]))

    for _ in range(2):  # digit sum of a product
        a = rng.randint(1200, 9800); b = rng.randint(310, 990); c = rng.randint(17, 97)
        prod = a * b * c
        tasks.append(num_task(nid(), f"Compute the product {a} x {b} x {c}, then give the sum of the decimal digits of that product.", sum(int(d) for d in str(prod)), 0, ["arithmetic", "exact"]))

    for _ in range(2):  # modular exponent
        a = rng.randint(11, 97); b = rng.randint(37, 250); m = rng.choice([101, 113, 127, 131, 139, 149, 151, 163, 167, 173])
        tasks.append(num_task(nid(), f"What is the remainder when {a}^{b} is divided by {m}?", pow(a, b, m), 0, ["number-theory", "exact"]))

    for _ in range(2):  # committee counting
        n = rng.choice([11, 12, 13, 14]); g = rng.choice([5, 6, 7]); kk = rng.choice([4, 5]); w = rng.choice([2, 3])
        total = sum(math.comb(g, i) * math.comb(n - g, kk - i) for i in range(w, min(g, kk) + 1))
        tasks.append(num_task(nid(), f"A club has {n} members: {g} women and {n - g} men. How many ways are there to choose a committee of {kk} members that includes at least {w} women?", total, 0, ["combinatorics", "exact"]))

    for _ in range(2):  # weekday arithmetic
        d0 = date(2026, rng.randint(1, 12), rng.randint(1, 28)); N = rng.randint(120, 1900)
        d1 = d0 + timedelta(days=N)
        tasks.append(str_task(nid(), f"{d0.strftime('%B %d, %Y')} is a {d0.strftime('%A')}. What day of the week is it {N} days later?", d1.strftime('%A'), ["calendar", "exact"]))

    for _ in range(1):  # trip fuel cost with unit conversion
        dist = rng.choice([480, 640, 815, 1120]); cons = rng.choice([6.4, 7.1, 8.3, 9.6]); price = rng.choice([3.19, 3.47, 3.89]); toll = rng.choice([12.5, 18.75, 24.0])
        liters = dist * cons / 100; gallons = liters / 3.78541; cost = gallons * price + toll
        tasks.append(num_task(nid(), f"A car uses {cons} liters of fuel per 100 km. You drive {dist} km and pay ${toll:.2f} in tolls. Fuel costs ${price:.2f} per US gallon, and 1 US gallon = 3.78541 liters. What is the total cost of fuel plus tolls, in dollars to the nearest cent?", cost, 2, ["conversion"]))

    for _ in range(1):  # percent chain
        P = rng.choice([64.0, 89.5, 120.0, 245.0]); a = rng.choice([12, 15, 18, 25]); b = rng.choice([8, 10, 20]); c = rng.choice([5, 7, 9])
        final = P * (1 + a / 100) * (1 - b / 100) * (1 + c / 100)
        tasks.append(num_task(nid(), f"A price starts at ${P:.2f}. It is raised by {a}%, then cut by {b}%, then raised by {c}%. What is the final price, in dollars to the nearest cent?", final, 2, ["percent"]))

    for _ in range(1):  # trailing zeros
        n = rng.randint(150, 980)
        z, p = 0, 5
        while p <= n:
            z += n // p; p *= 5
        tasks.append(num_task(nid(), f"How many trailing zeros does {n}! (the factorial of {n}) have when written in decimal?", z, 0, ["number-theory", "exact"]))

    for _ in range(1):  # arithmetic series with divisibility
        a = rng.randint(100, 400); b = rng.randint(2500, 6000); d = rng.choice([7, 11, 13, 17])
        s = sum(x for x in range(a, b + 1) if x % d == 0)
        tasks.append(num_task(nid(), f"What is the sum of all integers from {a} to {b} inclusive that are divisible by {d}?", s, 0, ["series", "exact"]))

    for _ in range(1):  # probability of at least one success
        p = rng.choice([3, 4.5, 7, 12]); n = rng.choice([8, 12, 20, 30])
        prob = (1 - (1 - p / 100) ** n) * 100
        tasks.append(num_task(nid(), f"Each independent attempt succeeds with probability {p}%. In {n} attempts, what is the probability of at least one success? Give the answer as a percentage to two decimal places.", prob, 2, ["probability"]))

    for _ in range(1):  # invented tax brackets
        b1 = rng.choice([9000, 11000, 14000]); b2 = rng.choice([40000, 48000, 55000]); r1 = rng.choice([8, 10]); r2 = rng.choice([18, 22, 24]); r3 = rng.choice([31, 35]); inc = rng.choice([63400, 71250, 88900, 104300])
        tax = b1 * r1 / 100 + (b2 - b1) * r2 / 100 + (inc - b2) * r3 / 100
        tasks.append(num_task(nid(), f"In the country of Veld, income tax is {r1}% on the first ${b1:,} of income, {r2}% on income above ${b1:,} up to ${b2:,}, and {r3}% on income above ${b2:,}. How much tax is owed on an income of ${inc:,}? Give the amount in dollars to the nearest cent.", tax, 2, ["percent"]))

    for _ in range(1):  # average speed with a stop
        d1 = rng.choice([84, 96, 120]); v1 = rng.choice([60, 72, 80]); d2 = rng.choice([45, 63, 75]); v2 = rng.choice([45, 50, 90]); s = rng.choice([15, 20, 25])
        hours = d1 / v1 + d2 / v2 + s / 60
        tasks.append(num_task(nid(), f"A driver covers {d1} km at {v1} km/h, stops for {s} minutes, then covers {d2} km at {v2} km/h. What is the average speed for the whole trip, including the stop, in km/h to one decimal place?", (d1 + d2) / hours, 1, ["rates"]))

    for _ in range(1):  # buses meet again
        a, b, c = rng.choice([(12, 18, 30), (14, 21, 35), (16, 24, 36), (20, 24, 45)])
        l = math.lcm(a, b, c); h, m = divmod(6 * 60 + l, 60)
        tasks.append(str_task(nid(), f"Three bus routes leave the same terminal together at 06:00. Route 1 departs every {a} minutes, route 2 every {b} minutes, and route 3 every {c} minutes. At what time do all three next depart together? Give the time in 24-hour HH:MM form.", f"{h:02d}:{m:02d}", ["number-theory", "exact"]))

    return tasks


# ---------------------------------------------------------------- data ----
REGIONS = ["North", "South", "East", "West"]
PRODUCTS = ["Anvil", "Bolt", "Crate", "Dowel", "Easel"]
STATUSES = ["shipped", "shipped", "shipped", "pending", "cancelled"]


def make_table(rng, n):
    rows = []
    base = date(2026, 4, 1)
    for i in range(n):
        rows.append({"id": f"ORD-{1000 + rng.randint(1, 900)}", "region": rng.choice(REGIONS), "product": rng.choice(PRODUCTS),
                     "units": rng.randint(1, 40), "unit_price": round(rng.uniform(4, 120), 2),
                     "date": (base + timedelta(days=rng.randint(0, 89))).isoformat(), "status": rng.choice(STATUSES)})
    ids = set()
    for r in rows:  # unique ids
        while r["id"] in ids:
            r["id"] = f"ORD-{1000 + rng.randint(1, 900)}"
        ids.add(r["id"])
    return rows


def table_text(rows):
    lines = ["order_id,region,product,units,unit_price,order_date,status"]
    for r in rows:
        lines.append(f"{r['id']},{r['region']},{r['product']},{r['units']},{r['unit_price']:.2f},{r['date']},{r['status']}")
    return "\n".join(lines)


def rev(r):
    return round(r["units"] * r["unit_price"], 2)


def gen_data(rng):
    tasks = []
    qtypes = ["region_revenue", "top_product_units", "weekend_orders", "avg_price_shipped_region", "best_day",
              "median_units_shipped", "top_two_region_gap", "distinct_products_region", "largest_order", "region_share"]
    k = 0
    for qt in qtypes:
        for _ in range(2):
            while True:
                rows = make_table(rng, rng.randint(14, 20))
                built = build_question(rng, qt, rows)
                if built:
                    break
            k += 1
            prompt, expected, atype, prec = built
            full = ("Here is a table of orders (CSV). Revenue of an order is units x unit_price.\n\n" + table_text(rows) + "\n\n" + prompt)
            t = {"id": f"data-{k:02d}", "type": "data", "prompt": full + "\n\n" + NUMBER_RULE, "answer_type": atype, "expected": expected, "tags": [qt]}
            if atype == "number":
                t["precision"] = prec
            tasks.append(t)
    return tasks


def build_question(rng, qt, rows):
    live = [r for r in rows if r["status"] != "cancelled"]
    if qt == "region_revenue":
        reg = rng.choice(REGIONS)
        sel = [r for r in live if r["region"] == reg]
        if len(sel) < 2:
            return None
        return (f"What is the total revenue of orders in the {reg} region, excluding cancelled orders? Give the answer in dollars to the nearest cent.", round(sum(rev(r) for r in sel), 2), "number", 2)
    if qt == "top_product_units":
        tot = {}
        for r in rows:
            tot[r["product"]] = tot.get(r["product"], 0) + r["units"]
        ranked = sorted(tot.items(), key=lambda kv: -kv[1])
        if len(ranked) < 2 or ranked[0][1] == ranked[1][1]:
            return None
        return ("Counting all orders regardless of status, which product has the largest total number of units? Give the product name only.", ranked[0][0], "string", None)
    if qt == "weekend_orders":
        n = sum(1 for r in rows if date.fromisoformat(r["date"]).weekday() >= 5)
        if n == 0:
            return None
        return ("How many orders (any status) were placed on a Saturday or a Sunday?", n, "number", 0)
    if qt == "avg_price_shipped_region":
        reg = rng.choice(REGIONS)
        sel = [r for r in rows if r["status"] == "shipped" and r["region"] == reg]
        if len(sel) < 2:
            return None
        return (f"What is the average unit_price of shipped orders in the {reg} region? Give the answer to two decimal places.", round(sum(r["unit_price"] for r in sel) / len(sel), 2), "number", 2)
    if qt == "best_day":
        tot = {}
        for r in live:
            tot[r["date"]] = round(tot.get(r["date"], 0) + rev(r), 2)
        ranked = sorted(tot.items(), key=lambda kv: -kv[1])
        if len(ranked) < 2 or ranked[0][1] == ranked[1][1]:
            return None
        return ("Excluding cancelled orders, on which order_date was total revenue highest? Give the date as YYYY-MM-DD.", ranked[0][0], "string", None)
    if qt == "median_units_shipped":
        sel = [r["units"] for r in rows if r["status"] == "shipped"]
        if len(sel) < 3:
            return None
        return ("What is the median of units over the shipped orders?", float(statistics.median(sel)), "number", 1)
    if qt == "top_two_region_gap":
        tot = {}
        for r in live:
            tot[r["region"]] = round(tot.get(r["region"], 0) + rev(r), 2)
        ranked = sorted(tot.values(), reverse=True)
        if len(ranked) < 2 or ranked[0] == ranked[1]:
            return None
        return ("Excluding cancelled orders, compute total revenue per region. How much larger is the highest region's revenue than the second highest? Give the difference in dollars to the nearest cent.", round(ranked[0] - ranked[1], 2), "number", 2)
    if qt == "distinct_products_region":
        reg = rng.choice(REGIONS)
        sel = {r["product"] for r in rows if r["region"] == reg}
        if not sel:
            return None
        return (f"How many distinct products appear in orders from the {reg} region (any status)?", len(sel), "number", 0)
    if qt == "largest_order":
        ranked = sorted(rows, key=lambda r: -rev(r))
        if rev(ranked[0]) == rev(ranked[1]):
            return None
        return ("Which single order (any status) has the largest revenue? Give its order_id only.", ranked[0]["id"], "string", None)
    if qt == "region_share":
        reg = rng.choice(REGIONS)
        total = sum(rev(r) for r in live); part = sum(rev(r) for r in live if r["region"] == reg)
        if total == 0 or part == 0:
            return None
        return (f"Excluding cancelled orders, what percentage of total revenue comes from the {reg} region? Give the answer as a percentage to one decimal place.", round(100 * part / total, 1), "number", 1)
    return None


# ---------------------------------------------------------------- code ----
def gen_code():
    tasks = []
    for t in task_bank.CODE_TASKS:
        src = t["reference"] + "\n" + task_bank.TEST_PRELUDE + "\n" + "\n".join(t["visible"] + t["hidden"]) + "\n"
        r = subprocess.run([sys.executable, "-I", "-"], input=src, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise SystemExit(f"reference for {t['id']} fails its tests:\n{r.stderr}")
        prompt = (t["spec"] + "\n\nVisible examples (your function must pass these):\n" + "\n".join(t["visible"]) + "\n\n" + CODE_RULE)
        tasks.append({"id": t["id"], "type": "code", "prompt": prompt, "answer_type": "code", "function": t["name"],
                      "visible_tests": t["visible"], "hidden_tests": t["hidden"], "tags": ["code"]})
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--out", default="tasks/fresh_tasks.json")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    tasks = gen_math(rng) + gen_data(rng) + gen_code()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"seed": a.seed, "count": len(tasks), "tasks": tasks}, f, indent=1)
    by = {}
    for t in tasks:
        by[t["type"]] = by.get(t["type"], 0) + 1
    print(f"wrote {len(tasks)} tasks to {a.out}: {by}")


if __name__ == "__main__":
    main()
