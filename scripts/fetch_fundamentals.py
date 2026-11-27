"""Valuation and earnings dates per stock -> data/fund.json (best effort; Yahoo data).

Fields: per (trailing PER), fper (forward PER), pbr, dy (dividend yield %, forward rate / price),
mcap (market cap, JPY 100M), ne (next earnings date), le (last quarter end used),
oi_yoy (latest quarter operating income vs same quarter a year earlier, %), oi (latest quarter OI, JPY 100M).
"""
import json
import math
import os
import time

import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def num(x):
    try:
        x = float(x)
        return None if math.isnan(x) or math.isinf(x) else x
    except Exception:
        return None


def main():
    stocks = json.load(open(os.path.join(ROOT, "stocks.json"), encoding="utf-8"))
    wl = os.path.join(ROOT, "watchlist.json")
    if os.path.exists(wl):
        stocks += [s for s in json.load(open(wl, encoding="utf-8")) if s["code"] not in {x["code"] for x in stocks}]
    out, bad = {}, []
    for s in stocks:
        t = yf.Ticker(s["code"] + ".T")
        r = {}
        try:
            info = t.info or {}
            price = num(info.get("currentPrice") or info.get("regularMarketPrice"))
            r["per"] = num(info.get("trailingPE"))
            r["fper"] = num(info.get("forwardPE"))
            r["pbr"] = num(info.get("priceToBook"))
            dr = num(info.get("dividendRate"))
            r["dy"] = round(dr / price * 100, 2) if dr and price else None
            mc = num(info.get("marketCap"))
            r["mcap"] = round(mc / 1e8) if mc else None
        except Exception as e:  # noqa
            bad.append(s["code"])
        try:
            cal = t.calendar or {}
            ed = cal.get("Earnings Date") if isinstance(cal, dict) else None
            if ed:
                r["ne"] = [str(x)[:10] for x in (ed if isinstance(ed, (list, tuple)) else [ed])]
        except Exception:
            pass
        try:
            q = t.quarterly_income_stmt
            if q is not None and "Operating Income" in q.index:
                row = q.loc["Operating Income"].dropna()
                if len(row) >= 1:
                    d0 = row.index[0]
                    r["le"] = str(d0)[:10]
                    r["oi"] = round(float(row.iloc[0]) / 1e8, 1)
                    prev = [k for k in row.index if abs((d0 - k).days - 365) <= 20]
                    if prev and float(row[prev[0]]) > 0:
                        r["oi_yoy"] = round((float(row.iloc[0]) / float(row[prev[0]]) - 1) * 100, 1)
        except Exception:
            pass
        r = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if v is not None}
        out[s["code"]] = r
        time.sleep(0.4)
    with open(os.path.join(ROOT, "data", "fund.json"), "w", encoding="utf-8") as f:
        json.dump({"updated": time.strftime("%Y-%m-%d"), "stocks": out}, f, ensure_ascii=False, separators=(",", ":"))
    print("fund:", len(out), "failed info:", bad)


if __name__ == "__main__":
    main()
