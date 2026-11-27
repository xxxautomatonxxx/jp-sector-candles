"""Compute per-stock technical signals from data/c/*.json -> data/signals.json."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDIR = os.path.join(ROOT, "data", "c")


def sma(a, n, i):
    if i + 1 < n:
        return None
    return sum(a[i - n + 1:i + 1]) / n


def main():
    stocks = json.load(open(os.path.join(ROOT, "stocks.json"), encoding="utf-8"))
    wl = os.path.join(ROOT, "watchlist.json")
    if os.path.exists(wl):
        stocks += [s for s in json.load(open(wl, encoding="utf-8")) if s["code"] not in {x["code"] for x in stocks}]
    rows = []
    for s in stocks:
        p = os.path.join(CDIR, s["code"] + ".json")
        if not os.path.exists(p):
            continue
        j = json.load(open(p, encoding="utf-8"))
        c, v, n = j["c"], j["v"], len(j["c"])
        if n < 80:
            continue
        i = n - 1
        m5, m25, m75 = sma(c, 5, i), sma(c, 25, i), sma(c, 75, i)
        ev = []
        # 5/25 cross within the last 3 sessions
        for k in range(i, i - 3, -1):
            a0, b0, a1, b1 = sma(c, 5, k - 1), sma(c, 25, k - 1), sma(c, 5, k), sma(c, 25, k)
            if None in (a0, b0, a1, b1):
                continue
            if a0 <= b0 and a1 > b1:
                ev.append({"t": "gc", "d": j["d"][k]}); break
            if a0 >= b0 and a1 < b1:
                ev.append({"t": "dc", "d": j["d"][k]}); break
        p75 = sma(c, 75, i - 1)
        if p75 is not None and m75 is not None:
            if c[i - 1] <= p75 and c[i] > m75:
                ev.append({"t": "up75", "d": j["d"][i]})
            elif c[i - 1] >= p75 and c[i] < m75:
                ev.append({"t": "dn75", "d": j["d"][i]})
        av20 = sum(v[i - 20:i]) / 20 if i >= 20 else 0
        vr = v[i] / av20 if av20 else None
        if vr and vr >= 2:
            ev.append({"t": "vol", "d": j["d"][i]})
        win = c[max(0, n - 245):]
        if c[i] >= max(win):
            ev.append({"t": "hi52", "d": j["d"][i]})
        elif c[i] <= min(win):
            ev.append({"t": "lo52", "d": j["d"][i]})
        rows.append({
            "code": s["code"], "name": s["name"], "sector": s.get("sector", ""), "d": j["d"][i],
            "c": c[i], "chg": round((c[i] / c[i - 1] - 1) * 100, 2),
            "chg5": round((c[i] / c[i - 5] - 1) * 100, 2), "chg20": round((c[i] / c[i - 20] - 1) * 100, 2),
            "dev5": round((c[i] / m5 - 1) * 100, 2), "dev25": round((c[i] / m25 - 1) * 100, 2),
            "dev75": round((c[i] / m75 - 1) * 100, 2), "vr": round(vr, 2) if vr else None, "ev": ev,
        })
    with open(os.path.join(ROOT, "data", "signals.json"), "w", encoding="utf-8") as f:
        json.dump({"rows": rows}, f, ensure_ascii=False, separators=(",", ":"))
    print("signals:", len(rows), "stocks,", sum(1 for r in rows if r["ev"]), "with events")


if __name__ == "__main__":
    main()
