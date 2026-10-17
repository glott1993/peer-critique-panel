"""Build the pilot 2 task set (harder, larger).

    python make_tasks2.py                      # level 2, 200 tasks -> tasks/pilot2_tasks.json
    python make_tasks2.py --level 3            # harder math/data/logic
    python make_tasks2.py --counts math=60,data=60,code=30,logic=50

Four types:
  math   multi-step exact computations (inventory, payroll, loans, counting, dates)
  data   two tables (customers, orders); the question needs a join
  code   30 harder functions with hidden tests (task_bank2.py, verified on export)
  logic  four-house puzzles with a unique solution, proven by exhaustive search

Every non-code answer is computed by the code that writes the prompt.
"""
import argparse, itertools, json, math, os, random, statistics, subprocess, sys
from datetime import date, timedelta
from fractions import Fraction

import task_bank, task_bank2
from make_tasks import NUMBER_RULE, CODE_RULE, num_task, str_task

FRACTION_RULE = " Give the answer as a fraction in lowest terms, written a/b (or a whole number if the denominator is 1)."


# ---------------------------------------------------------------- math ----
def gen_math(rng, n_target, level):
    tasks = []
    k = 0

    def nid():
        nonlocal k
        k += 1
        return f"math2-{k:02d}"

    def fifo():
        lots = [(rng.randint(40, 160), round(rng.uniform(3.5, 14.0), 2)) for _ in range(2 + level + (3 if level >= 3 else 0))]
        sales = [rng.randint(30, 120) for _ in range(1 + level + (2 if level >= 3 else 0))]
        total_units = sum(q for q, _ in lots)
        while sum(sales) >= total_units - 20:
            sales = [max(20, s - 15) for s in sales]
        inv = [list(l) for l in lots]
        cogs = 0.0
        for s in sales:
            need = s
            while need > 0:
                q, c = inv[0]
                take = min(q, need)
                cogs += take * c; need -= take
                inv[0][0] -= take
                if inv[0][0] == 0:
                    inv.pop(0)
        lot_text = "; ".join(f"lot {i + 1}: {q} units at ${c:.2f}" for i, (q, c) in enumerate(lots))
        sale_text = ", ".join(f"{s} units" for s in sales)
        return num_task(nid(), f"A warehouse receives inventory in this order: {lot_text}. It then sells, in this order: {sale_text}. Using FIFO (first in, first out) costing, what is the total cost of goods sold for these sales? Give the amount in dollars to the nearest cent.", round(cogs, 2), 2, ["fifo", "accounting"])

    def payroll():
        days = 5 + 5 * (level - 1) if level <= 2 else 14
        hours = [rng.choice([0, 6, 7.5, 8, 8, 9, 9.5, 10, 11, 12.5, 13]) for _ in range(days)]
        rate = rng.choice([18.5, 22.0, 24.75, 31.2])
        gross = 0.0
        for h in hours:
            reg = min(h, 8); ot = min(max(h - 8, 0), 4); dt = max(h - 12, 0)
            gross += reg * rate + ot * rate * 1.5 + dt * rate * 2
        hl = ", ".join(f"{h:g}" for h in hours)
        return num_task(nid(), f"An hourly worker is paid ${rate:.2f} per hour. Daily overtime rules: hours over 8 in a day are paid at 1.5 times the rate, and hours over 12 in a day at 2 times the rate; there is no weekly overtime rule. The hours worked on each of {days} days were: {hl}. What is the gross pay for the period, in dollars to the nearest cent?", round(gross, 2), 2, ["payroll"])

    def amortization():
        L = rng.choice([12000, 18500, 24000, 31200]); apr = rng.choice([5.4, 6.0, 6.9, 7.8]); years = rng.choice([3, 4, 5])
        i = apr / 1200; n = years * 12
        M = L * i / (1 - (1 + i) ** (-n))
        months = 4 + 2 * level + (8 if level >= 3 else 0)
        extras = {rng.randint(2, months - 1): rng.choice([500, 750, 1000])}
        if level >= 3:
            extras[rng.randint(2, months - 1)] = rng.choice([300, 600])
        bal = L
        for m in range(1, months + 1):
            interest = bal * i
            bal = bal - (M - interest) - extras.get(m, 0)
        ex_text = " and ".join(f"in month {m} an extra ${e} of principal" for m, e in sorted(extras.items()))
        return num_task(nid(), f"A ${L:,} loan at {apr}% APR is repaid with the standard monthly payment for a {years}-year amortization (interest accrues monthly at one twelfth of the APR; round nothing until the end). On top of the regular payment the borrower pays {ex_text}. What is the remaining balance immediately after the payment in month {months}? Give the amount in dollars to the nearest cent.", round(bal, 2), 2, ["loan", "simulation"])

    def bank_sim():
        months = 3 + 2 * level + (6 if level >= 3 else 0)
        bal = rng.choice([1200.0, 2500.0, 4300.0]); rate = rng.choice([0.25, 0.4, 0.5]); fee = rng.choice([8, 12, 15]); thresh = rng.choice([1000, 1500, 2000])
        moves = [rng.choice([-900, -650, -400, -250, 300, 450, 700, 1100]) for _ in range(months)]
        b = bal
        for mv in moves:
            b += mv
            if b < thresh:
                b -= fee
            b *= 1 + rate / 100
        ml = ", ".join(f"{'deposit' if mv > 0 else 'withdrawal'} of ${abs(mv)}" for mv in moves)
        return num_task(nid(), f"An account starts with ${bal:,.2f}. Each month, in this order: one transaction is applied ({ml}, for months 1 through {months}); then, if the balance is below ${thresh:,}, a ${fee} fee is charged; then interest of {rate}% of the balance is added. What is the balance after month {months}? Give the amount in dollars to the nearest cent.", round(b, 2), 2, ["simulation"])

    def tiered():
        units = rng.randint(180, 900); p1 = rng.choice([4.25, 5.0, 6.4]); p2 = round(p1 * 0.85, 2); p3 = round(p1 * 0.7, 2)
        t1, t2 = 100, 300; disc = rng.choice([3, 5, 8]); disc_over = rng.choice([1500, 2500]); tax = rng.choice([6.5, 7.25, 8.0])
        sub = min(units, t1) * p1 + max(0, min(units, t2) - t1) * p2 + max(0, units - t2) * p3
        if sub > disc_over:
            sub *= 1 - disc / 100
        total = sub * (1 + tax / 100)
        return num_task(nid(), f"A supplier charges ${p1:.2f} per unit for the first {t1} units, ${p2:.2f} per unit for the next {t2 - t1}, and ${p3:.2f} per unit beyond {t2}. If the subtotal exceeds ${disc_over:,}, a {disc}% discount applies to the whole subtotal. Sales tax of {tax}% is then added. What is the total for an order of {units} units, in dollars to the nearest cent?", round(total, 2), 2, ["pricing"])

    def incl_excl():
        N = rng.choice([5000, 8000, 12000, 20000]); a, b, c = rng.choice([(3, 5, 7), (4, 6, 9), (5, 7, 11), (6, 10, 15)])
        if level >= 3:
            d = rng.choice([13, 17, 19])
            cnt = sum(1 for x in range(1, N + 1) if (x % a == 0 or x % b == 0 or x % c == 0) and x % d != 0)
            return num_task(nid(), f"How many integers from 1 to {N:,} inclusive are divisible by at least one of {a}, {b}, or {c}, but not divisible by {d}?", cnt, 0, ["counting", "exact"])
        cnt = sum(1 for x in range(1, N + 1) if x % a == 0 or x % b == 0 or x % c == 0)
        return num_task(nid(), f"How many integers from 1 to {N:,} inclusive are divisible by {a}, {b}, or {c}?", cnt, 0, ["counting", "exact"])

    def crt():
        while True:
            ms = rng.sample([5, 7, 9, 11, 13, 16, 17, 19, 23], 3)
            if all(math.gcd(x, y) == 1 for x, y in itertools.combinations(ms, 2)):
                break
        rs = [rng.randrange(m) for m in ms]
        x = next(v for v in range(1, ms[0] * ms[1] * ms[2] + 1) if all(v % m == r for m, r in zip(ms, rs)))
        return num_task(nid(), f"What is the smallest positive integer that leaves a remainder of {rs[0]} when divided by {ms[0]}, a remainder of {rs[1]} when divided by {ms[1]}, and a remainder of {rs[2]} when divided by {ms[2]}?", x, 0, ["number-theory", "exact"])

    def modpow():
        a = rng.randint(13, 97); b = rng.randint(120, 900); m = rng.choice([101, 131, 151, 163, 191, 211, 233, 257])
        return num_task(nid(), f"What is the remainder when {a}^{b} is divided by {m}?", pow(a, b, m), 0, ["number-theory", "exact"])

    def digit_sum():
        a = rng.randint(21000, 98000); b = rng.randint(1300, 9900); c = rng.randint(101, 997)
        if level >= 3:
            d = rng.randint(1013, 9973)
            return num_task(nid(), f"Compute {a} x {b} x {c} x {d} and give the sum of the decimal digits of the result.", sum(int(x) for x in str(a * b * c * d)), 0, ["arithmetic", "exact"])
        return num_task(nid(), f"Compute {a} x {b} x {c} and give the sum of the decimal digits of the result.", sum(int(d) for d in str(a * b * c)), 0, ["arithmetic", "exact"])

    def business_days_after():
        start = date(2026, rng.randint(1, 10), rng.randint(1, 28)); N = 10 + 10 * level + rng.randint(0, 9) + (40 if level >= 3 else 0)
        hol = sorted({start + timedelta(days=rng.randint(1, N + 40)) for _ in range(2 + 2 * level)})
        hol = [h for h in hol if h.weekday() < 5][:(6 if level >= 3 else 3)]
        d, count = start, 0
        while count < N:
            d += timedelta(days=1)
            if d.weekday() < 5 and d not in hol:
                count += 1
        hl = ", ".join(h.isoformat() for h in hol)
        return str_task(nid(), f"Counting only Mondays through Fridays and skipping these holidays ({hl}), what is the date that is {N} business days after {start.isoformat()}? Give the date as YYYY-MM-DD.", d.isoformat(), ["calendar", "exact"])

    def probability():
        r, g, b = rng.randint(3, 7), rng.randint(2, 6), rng.randint(2, 5); n = r + g + b
        total = math.comb(n, 3)
        same = math.comb(r, 3) + math.comb(g, 3) + math.comb(b, 3)
        all_diff = r * g * b
        p = Fraction(total - all_diff, total)  # at least two share a color
        ans = f"{p.numerator}/{p.denominator}" if p.denominator != 1 else str(p.numerator)
        t = str_task(nid(), f"A bag holds {r} red, {g} green, and {b} blue marbles. Three are drawn at random without replacement. What is the probability that at least two of the three share a color?" + FRACTION_RULE, ans, ["probability", "exact"])
        return t

    def tax_credit():
        b1, b2 = rng.choice([(11000, 45000), (12500, 52000), (14000, 60000)]); r1, r2, r3 = rng.choice([(10, 22, 32), (8, 20, 30), (12, 24, 35)])
        inc = rng.choice([57400, 68250, 81900, 96300]); credit = rng.choice([1200, 1800, 2400]); phase = rng.choice([50000, 60000]); rate = rng.choice([5, 8])
        tax = b1 * r1 / 100 + max(0, min(inc, b2) - b1) * r2 / 100 + max(0, inc - b2) * r3 / 100
        cr = max(0.0, credit - max(0, inc - phase) * rate / 100)
        owed = max(0.0, tax - cr)
        return num_task(nid(), f"In the country of Veld, income tax is {r1}% on the first ${b1:,}, {r2}% from ${b1:,} up to ${b2:,}, and {r3}% above ${b2:,}. A tax credit of ${credit:,} is then subtracted, but the credit is reduced by {rate}% of any income above ${phase:,} (it cannot go below zero, and the tax owed cannot go below zero). How much tax is owed on an income of ${inc:,}? Give the amount in dollars to the nearest cent.", round(owed, 2), 2, ["percent"])

    def series_excl():
        a = rng.randint(200, 900); b = rng.randint(6000, 15000); d = rng.choice([7, 11, 13]); e = rng.choice([4, 6, 9])
        s = sum(x for x in range(a, b + 1) if x % d == 0 and x % e != 0)
        return num_task(nid(), f"What is the sum of all integers from {a} to {b:,} inclusive that are divisible by {d} but not by {e}?", s, 0, ["series", "exact"])

    def reverse_percent():
        final = rng.choice([184.32, 259.7, 412.08, 97.5]); steps = [rng.choice([-15, -10, 12, 18, 20, 25]) for _ in range(2 + level)]
        orig = final
        for s in reversed(steps):
            orig /= (1 + s / 100)
        desc = ", then ".join(f"{'raised' if s > 0 else 'cut'} by {abs(s)}%" for s in steps)
        return num_task(nid(), f"A price was {desc}, ending at ${final:.2f}. What was the original price? Give the amount in dollars to the nearest cent.", round(orig, 2), 2, ["percent"])

    def contributions():
        periods = 4 + level + (5 if level >= 3 else 0); rate = rng.choice([1.5, 2.0, 2.5]); fee = rng.choice([0.5, 0.75]); start = rng.choice([5000, 8000])
        contribs = [rng.choice([0, 250, 400, 600, 900]) for _ in range(periods)]
        b = start
        for c in contribs:
            b = (b + c) * (1 + rate / 100) * (1 - fee / 100)
        cl = ", ".join(f"${c}" for c in contribs)
        return num_task(nid(), f"An investment account starts with ${start:,}. For each of {periods} periods, in this order: a contribution is added ({cl}); the balance then grows by {rate}%; then a fee of {fee}% of the balance is deducted. What is the balance after period {periods}? Give the amount in dollars to the nearest cent.", round(b, 2), 2, ["simulation"])

    gens = [fifo, payroll, amortization, bank_sim, tiered, incl_excl, crt, modpow, digit_sum, business_days_after, probability, tax_credit, series_excl, reverse_percent, contributions]
    if n_target == "generators":
        return gens
    i = 0
    while len(tasks) < n_target:
        tasks.append(gens[i % len(gens)]())
        i += 1
    return tasks


# --------------------------------------------------------------- multi ----
WORDS = {3: "three", 4: "four", 5: "five"}


def multi_rule(n):
    letters = "; ".join(f"<{'ABCDE'[i]}>" for i in range(n))
    return (f"Answer all {WORDS[n]} parts. Show brief working, then end your reply with exactly one line of the form FINAL: {letters} "
            f"with the {WORDS[n]} answers in order separated by semicolons. For a number give digits only (no units, no currency sign, no commas; use a decimal point). "
            "For a date use YYYY-MM-DD. For a fraction use a/b in lowest terms.")


def gen_multi(rng, n_target, level, parts_n=3, prefix="multi2", ttype="multi"):
    gens = gen_math(rng, "generators", level)
    tasks = []
    for k in range(n_target):
        picks = rng.sample(gens, parts_n)
        parts = [g() for g in picks]
        body = "\n\n".join(f"Part {'ABCDE'[i]}: " + p["prompt"].split("\n\n")[0] for i, p in enumerate(parts))
        exp = [{"answer_type": p["answer_type"], "expected": p["expected"], "precision": p.get("precision", 0)} for p in parts]
        tasks.append({"id": f"{prefix}-{k + 1:02d}", "type": ttype, "prompt": f"This task has {WORDS[parts_n]} independent parts.\n\n" + body + "\n\n" + multi_rule(parts_n),
                      "answer_type": "multi", "expected": exp, "tags": [ttype] + [t for p in parts for t in p["tags"]]})
    return tasks


# ---------------------------------------------------------------- data ----
REGIONS = ["North", "South", "East", "West"]
TIERS = ["Gold", "Silver", "Bronze"]
PRODUCTS = ["Anvil", "Bolt", "Crate", "Dowel", "Easel", "Flange"]
STATUSES = ["shipped", "shipped", "shipped", "pending", "cancelled", "returned"]
NAMES = ["Avery", "Blake", "Casey", "Devon", "Emery", "Finley", "Harper", "Jordan", "Kendall", "Logan", "Morgan", "Parker", "Quinn", "Reese", "Rowan", "Sawyer"]


def make_tables(rng, n_orders, dupes=0):
    n_cust = 8 + rng.randint(0, 4)
    names = rng.sample(NAMES, n_cust)
    customers = [{"id": f"C{100 + i}", "name": nm, "region": rng.choice(REGIONS), "tier": rng.choice(TIERS)} for i, nm in enumerate(names)]
    base = date(2026, 4, 1)
    orders, ids = [], set()
    for _ in range(n_orders):
        oid = f"O{2000 + rng.randint(1, 900)}"
        while oid in ids:
            oid = f"O{2000 + rng.randint(1, 900)}"
        ids.add(oid)
        orders.append({"id": oid, "cust": rng.choice(customers)["id"], "product": rng.choice(PRODUCTS), "units": rng.randint(1, 45),
                       "price": round(rng.uniform(3, 140), 2), "date": (base + timedelta(days=rng.randint(0, 120))).isoformat(), "status": rng.choice(STATUSES)})
    display = list(orders)
    for _ in range(dupes):  # exact repeats of existing rows, shown in the table but counted once
        display.insert(rng.randrange(len(display) + 1), dict(rng.choice(orders)))
    return customers, orders, display


def tables_text(customers, orders):
    c = ["customer_id,name,region,tier"] + [f"{x['id']},{x['name']},{x['region']},{x['tier']}" for x in customers]
    o = ["order_id,customer_id,product,units,unit_price,order_date,status"] + [f"{r['id']},{r['cust']},{r['product']},{r['units']},{r['price']:.2f},{r['date']},{r['status']}" for r in orders]
    return "Customers (CSV):\n" + "\n".join(c) + "\n\nOrders (CSV):\n" + "\n".join(o)


def rev(o):
    return round(o["units"] * o["price"], 2)


def gen_data(rng, n_target, level):
    n_orders = {1: 22, 2: 34, 3: 80}.get(level, 34)
    qtypes = ["tier_region_revenue", "top_customer_revenue", "avg_order_value_gold", "customers_with_cancelled", "top_product_units_tier",
              "median_price_window", "top_customer_share", "orders_in_window_region", "most_orders_customer", "top_two_region_gap",
              "distinct_products_customer", "units_returned", "earliest_order_customer", "q2_gold_minus_silver"]
    tasks, k, i = [], 0, 0
    while len(tasks) < n_target:
        qt = qtypes[i % len(qtypes)]; i += 1
        for _ in range(60):
            customers, orders, display = make_tables(rng, n_orders, dupes=(3 if level >= 3 else 0))
            built = build_q(rng, qt, customers, orders)
            if built:
                break
        else:
            continue
        k += 1
        prompt, expected, atype, prec = built
        dup_note = " The orders table contains a few exact duplicate rows (same order_id and all other fields); these are data-entry repeats and each such order counts once." if level >= 3 else ""
        full = ("Two tables follow. Revenue of an order is units x unit_price. Unless the question says otherwise, revenue counts only orders whose status is shipped or pending (cancelled and returned orders contribute nothing)." + dup_note + "\n\n"
                + tables_text(customers, display) + "\n\n" + prompt)
        t = {"id": f"data2-{k:02d}", "type": "data", "prompt": full + "\n\n" + NUMBER_RULE, "answer_type": atype, "expected": expected, "tags": [qt]}
        if atype == "number":
            t["precision"] = prec
        tasks.append(t)
    return tasks


def build_q(rng, qt, customers, orders):
    cmap = {c["id"]: c for c in customers}
    live = [o for o in orders if o["status"] in ("shipped", "pending")]
    if qt == "tier_region_revenue":
        tier, reg = rng.choice(TIERS), rng.choice(REGIONS)
        sel = [o for o in live if cmap[o["cust"]]["tier"] == tier and cmap[o["cust"]]["region"] == reg]
        if len(sel) < 2:
            return None
        return (f"What is the total revenue from customers in the {reg} region whose tier is {tier}? Give the amount in dollars to the nearest cent.", round(sum(rev(o) for o in sel), 2), "number", 2)
    if qt == "top_customer_revenue":
        tot = {}
        for o in live:
            tot[o["cust"]] = round(tot.get(o["cust"], 0) + rev(o), 2)
        ranked = sorted(tot.items(), key=lambda kv: -kv[1])
        if len(ranked) < 2 or ranked[0][1] == ranked[1][1]:
            return None
        return ("Which customer has the highest total revenue? Give the customer's name only.", cmap[ranked[0][0]]["name"], "string", None)
    if qt == "avg_order_value_gold":
        sel = [o for o in orders if o["status"] == "shipped" and cmap[o["cust"]]["tier"] == "Gold"]
        if len(sel) < 3:
            return None
        return ("What is the average revenue per shipped order placed by Gold-tier customers? Give the answer in dollars to two decimal places.", round(sum(rev(o) for o in sel) / len(sel), 2), "number", 2)
    if qt == "customers_with_cancelled":
        n = len({o["cust"] for o in orders if o["status"] == "cancelled"})
        if n == 0:
            return None
        return ("How many distinct customers have at least one cancelled order?", n, "number", 0)
    if qt == "top_product_units_tier":
        tier = rng.choice(TIERS)
        tot = {}
        for o in orders:
            if cmap[o["cust"]]["tier"] == tier:
                tot[o["product"]] = tot.get(o["product"], 0) + o["units"]
        ranked = sorted(tot.items(), key=lambda kv: -kv[1])
        if len(ranked) < 2 or ranked[0][1] == ranked[1][1]:
            return None
        return (f"Counting orders of every status, which product has the most total units ordered by {tier}-tier customers? Give the product name only.", ranked[0][0], "string", None)
    if qt == "median_price_window":
        a = date(2026, rng.randint(4, 6), rng.randint(1, 20)); b = a + timedelta(days=rng.randint(20, 40))
        sel = [o["price"] for o in orders if a.isoformat() <= o["date"] <= b.isoformat()]
        if len(sel) < 4:
            return None
        return (f"What is the median unit_price over all orders (any status) dated from {a.isoformat()} to {b.isoformat()} inclusive? Give the answer to two decimal places.", round(float(statistics.median(sel)), 2), "number", 2)
    if qt == "top_customer_share":
        tot = {}
        for o in live:
            tot[o["cust"]] = round(tot.get(o["cust"], 0) + rev(o), 2)
        total = sum(tot.values())
        ranked = sorted(tot.values(), reverse=True)
        if total == 0 or len(ranked) < 2 or ranked[0] == ranked[1]:
            return None
        return ("What percentage of total revenue comes from the single highest-revenue customer? Give the answer as a percentage to one decimal place.", round(100 * ranked[0] / total, 1), "number", 1)
    if qt == "orders_in_window_region":
        reg = rng.choice(REGIONS); a = date(2026, rng.randint(4, 6), rng.randint(1, 15)); b = a + timedelta(days=rng.randint(15, 35))
        n = sum(1 for o in orders if cmap[o["cust"]]["region"] == reg and a.isoformat() <= o["date"] <= b.isoformat())
        if n == 0:
            return None
        return (f"How many orders (any status) were placed by customers in the {reg} region between {a.isoformat()} and {b.isoformat()} inclusive?", n, "number", 0)
    if qt == "most_orders_customer":
        cnt = {}
        for o in orders:
            cnt[o["cust"]] = cnt.get(o["cust"], 0) + 1
        ranked = sorted(cnt.items(), key=lambda kv: -kv[1])
        if len(ranked) < 2 or ranked[0][1] == ranked[1][1]:
            return None
        return ("Which customer placed the most orders (any status)? Give the customer's name only.", cmap[ranked[0][0]]["name"], "string", None)
    if qt == "top_two_region_gap":
        tot = {}
        for o in live:
            r = cmap[o["cust"]]["region"]; tot[r] = round(tot.get(r, 0) + rev(o), 2)
        ranked = sorted(tot.values(), reverse=True)
        if len(ranked) < 2 or ranked[0] == ranked[1]:
            return None
        return ("Compute total revenue per region (using the customers table for each order's region). How much larger is the highest region's revenue than the second highest? Give the difference in dollars to the nearest cent.", round(ranked[0] - ranked[1], 2), "number", 2)
    if qt == "distinct_products_customer":
        c = rng.choice(customers)
        sel = {o["product"] for o in orders if o["cust"] == c["id"]}
        if len(sel) < 2:
            return None
        return (f"How many distinct products has {c['name']} ordered (any status)?", len(sel), "number", 0)
    if qt == "units_returned":
        n = sum(o["units"] for o in orders if o["status"] == "returned")
        if n == 0:
            return None
        return ("What is the total number of units across all orders with status returned?", n, "number", 0)
    if qt == "earliest_order_customer":
        c = rng.choice(customers)
        sel = sorted(o["date"] for o in orders if o["cust"] == c["id"])
        if len(sel) < 2:
            return None
        return (f"What is the date of {c['name']}'s earliest order (any status)? Give the date as YYYY-MM-DD.", sel[0], "string", None)
    if qt == "q2_gold_minus_silver":
        def tot(tier):
            return round(sum(rev(o) for o in live if cmap[o["cust"]]["tier"] == tier and "2026-04-01" <= o["date"] <= "2026-06-30"), 2)
        g, s = tot("Gold"), tot("Silver")
        if g == 0 or s == 0:
            return None
        return ("For orders dated April 1 through June 30, 2026, what is the revenue from Gold-tier customers minus the revenue from Silver-tier customers? Give the difference in dollars to the nearest cent (it may be negative).", round(g - s, 2), "number", 2)
    return None


# --------------------------------------------------------------- logic ----
P_NAMES = ["Ada", "Ben", "Cleo", "Dev", "Eli"]
DRINKS = ["tea", "coffee", "milk", "juice", "water"]
PETS = ["cat", "dog", "fish", "bird", "horse"]
COLORS = ["red", "blue", "green", "white", "yellow"]
HOUSES = 4


def gen_logic(rng, n_target, level):
    global HOUSES
    HOUSES = 5 if level >= 3 else 4
    vals_of = {"name": P_NAMES[:HOUSES], "drink": DRINKS[:HOUSES], "pet": PETS[:HOUSES], "color": COLORS[:HOUSES]}
    attrs = [("name", vals_of["name"]), ("drink", vals_of["drink"]), ("pet", vals_of["pet"])] + ([("color", vals_of["color"])] if level >= 2 else [])
    tasks = []
    k = 0
    while len(tasks) < n_target:
        sol = {a: rng.sample(vals, HOUSES) for a, vals in attrs}  # house index -> value
        clues = all_true_clues(sol, attrs)
        rng.shuffle(clues)
        chosen = []
        for c in clues:
            chosen.append(c)
            if count_solutions(chosen, attrs, limit=2) == 1:
                break
        else:
            continue
        # drop clues that are not needed, in random order
        for c in list(chosen):
            trial = [x for x in chosen if x is not c]
            if count_solutions(trial, attrs, limit=2) == 1:
                chosen = trial
        if len(chosen) < HOUSES:
            continue
        # question
        qattr, qval_attr = rng.choice([("pet", "name"), ("drink", "name"), ("name", "drink"), ("name", "pet")] + ([("color", "name"), ("name", "color")] if level >= 2 else []))
        idx = rng.randrange(HOUSES)
        if qattr == "name":
            q = {"pet": f"Which pet does {sol['name'][idx]} keep?", "drink": f"What does {sol['name'][idx]} drink?", "color": f"What color is {sol['name'][idx]}'s house?"}[qval_attr]
            ans = sol[qval_attr][idx]
        else:
            q = f"Who keeps the {sol[qattr][idx]}?" if qattr == "pet" else (f"Who drinks {sol[qattr][idx]}?" if qattr == "drink" else f"Who lives in the {sol[qattr][idx]} house?")
            ans = sol["name"][idx]
        k += 1
        intro = (f"{'Five' if HOUSES == 5 else 'Four'} houses stand in a row, numbered 1 to {HOUSES} from left to right. Each house has exactly one resident (" + ", ".join(vals_of['name']) + "), one drink ("
                 + ", ".join(vals_of['drink']) + "), and one pet (" + ", ".join(vals_of['pet']) + ")" + (", and one color (" + ", ".join(vals_of['color']) + ")" if level >= 2 else "")
                 + "; no value is shared between houses. Clues:\n" + "\n".join(f"{i + 1}. {c[0]}" for i, c in enumerate(chosen)) + f"\n\n{q} There is exactly one answer.")
        tasks.append(str_task(f"logic2-{k:02d}", intro, ans, ["logic", "exact"], ttype="logic"))
    return tasks


def all_true_clues(sol, attrs):
    """Every clue template instantiated so that it is true of sol. Each clue is (text, checker) where checker(partial) -> True/False/None."""
    names = dict(attrs)
    clues = []
    A = [a for a, _ in attrs]
    def pos_of(attr, val):
        return sol[attr].index(val)
    def label(attr, val):
        return {"name": val, "drink": f"the person who drinks {val}", "pet": f"the {val} owner", "color": f"the person in the {val} house"}[attr]
    for attr in A:
        for val in names[attr]:
            p = pos_of(attr, val)
            # position clue
            clues.append((f"{label(attr, val)[0].upper() + label(attr, val)[1:]} lives in house {p + 1}.", mk_pos(attr, val, p)))
            # negative position
            q = (p + rng_offset(p)) % HOUSES
            clues.append((f"{label(attr, val)[0].upper() + label(attr, val)[1:]} does not live in house {q + 1}.", mk_notpos(attr, val, q)))
    for a1, a2 in itertools.combinations(A, 2):
        for i in range(HOUSES):
            v1, v2 = sol[a1][i], sol[a2][i]
            clues.append((f"{label(a1, v1)[0].upper() + label(a1, v1)[1:]} is {label(a2, v2)}." if a2 != "name" else f"{label(a2, v2)} is {label(a1, v1)}.", mk_same(a1, v1, a2, v2)))
        for i in range(HOUSES - 1):
            v1, v2 = sol[a1][i], sol[a2][i + 1]
            clues.append((f"{label(a1, v1)[0].upper() + label(a1, v1)[1:]} lives immediately to the left of {label(a2, v2)}.", mk_left(a1, v1, a2, v2)))
            v1b, v2b = sol[a1][i + 1], sol[a2][i]
            clues.append((f"{label(a1, v1b)[0].upper() + label(a1, v1b)[1:]} lives next to {label(a2, v2b)}.", mk_adjacent(a1, v1b, a2, v2b)))
    return clues


def rng_offset(p):
    return 1 + (p * 7) % 3


def mk_pos(attr, val, p):
    def chk(part):
        if attr not in part:
            return None
        return part[attr][p] == val
    return chk


def mk_notpos(attr, val, q):
    def chk(part):
        if attr not in part:
            return None
        return part[attr][q] != val
    return chk


def mk_same(a1, v1, a2, v2):
    def chk(part):
        if a1 not in part or a2 not in part:
            return None
        return part[a1].index(v1) == part[a2].index(v2)
    return chk


def mk_left(a1, v1, a2, v2):
    def chk(part):
        if a1 not in part or a2 not in part:
            return None
        return part[a1].index(v1) + 1 == part[a2].index(v2)
    return chk


def mk_adjacent(a1, v1, a2, v2):
    def chk(part):
        if a1 not in part or a2 not in part:
            return None
        return abs(part[a1].index(v1) - part[a2].index(v2)) == 1
    return chk


def count_solutions(clues, attrs, limit=2):
    count = 0
    perms = {a: list(itertools.permutations(vals)) for a, vals in attrs}
    order = [a for a, _ in attrs]

    def rec(i, part):
        nonlocal count
        if count >= limit:
            return
        if i == len(order):
            count += 1
            return
        a = order[i]
        for perm in perms[a]:
            part[a] = perm
            ok = True
            for _, chk in clues:
                r = chk(part)
                if r is False:
                    ok = False
                    break
            if ok:
                rec(i + 1, part)
            del part[a]
            if count >= limit:
                return
    rec(0, {})
    return count


# ---------------------------------------------------------------- code ----
def gen_code(n_target):
    tasks = []
    for t in task_bank2.CODE_TASKS2[:n_target]:
        src = t["reference"] + "\n" + task_bank.TEST_PRELUDE + "\n" + "\n".join(t["visible"] + t["hidden"]) + "\n"
        r = subprocess.run([sys.executable, "-I", "-"], input=src, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise SystemExit(f"reference for {t['id']} fails its tests:\n{r.stderr}")
        prompt = (t["spec"] + "\n\nVisible examples (your function must pass these):\n" + "\n".join(t["visible"]) + "\n\n" + CODE_RULE)
        tasks.append({"id": t["id"], "type": "code", "prompt": prompt, "answer_type": "code", "function": t["name"],
                      "visible_tests": t["visible"], "hidden_tests": t["hidden"], "tags": ["code", "hard"]})
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--level", type=int, default=2, help="1 easier, 2 default, 3 harder (affects math, data, logic)")
    ap.add_argument("--counts", default="math=60,data=60,code=30,logic=50", help="level 3 default: math=40,multi=40,data=50,code=30,logic=40")
    ap.add_argument("--out", default="tasks/pilot2_tasks.json")
    a = ap.parse_args()
    if a.level >= 3 and a.counts == "math=60,data=60,code=30,logic=50":
        a.counts = "math=40,multi=40,data=50,code=30,logic=40,multi4=40"
    counts = {kv.split("=")[0]: int(kv.split("=")[1]) for kv in a.counts.split(",")}
    rng = random.Random(a.seed)
    # generation order is fixed so that adding a type at the end never changes the earlier tasks
    tasks = (gen_math(rng, counts.get("math", 0), a.level) + gen_multi(rng, counts.get("multi", 0), a.level) + gen_data(rng, counts.get("data", 0), a.level)
             + gen_code(counts.get("code", 0)) + gen_logic(rng, counts.get("logic", 0), a.level)
             + gen_multi(rng, counts.get("multi4", 0), a.level, parts_n=4, prefix="multi4", ttype="multi4"))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"seed": a.seed, "level": a.level, "count": len(tasks), "tasks": tasks}, f, indent=1)
    by = {}
    for t in tasks:
        by[t["type"]] = by.get(t["type"], 0) + 1
    print(f"wrote {len(tasks)} tasks to {a.out} (level {a.level}): {by}")


if __name__ == "__main__":
    main()
