"""Download ~15 months of daily OHLCV for each stock in stocks.json from Yahoo Finance
and write one compact JSON file per stock to data/c/<code>.json.

Each file: {"code","name","d":[YYYY-MM-DD...],"o":[],"h":[],"l":[],"c":[],"v":[]}
Prices are split-adjusted (not dividend-adjusted). The extra ~75 days before the
1-year window let the page draw the 75-day moving average across the whole year.
"""
import json
import os
import sys
import time

import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "c")
KEEP = 330  # trading days kept (≈ 1 year + 75-day warm-up)


def rnd(x):
    x = float(x)
    return round(x, 1) if x < 10000 else round(x)


def main():
    stocks = json.load(open(os.path.join(ROOT, "stocks.json"), encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    tickers = [s["code"] + ".T" for s in stocks]
    df = yf.download(tickers, period="2y", interval="1d", group_by="ticker",
                     auto_adjust=False, actions=False, threads=True, progress=False)
    ok, bad = 0, []
    latest = None
    for s in stocks:
        t = s["code"] + ".T"
        try:
            sub = df[t].dropna(subset=["Open", "High", "Low", "Close"]).tail(KEEP)
        except KeyError:
            sub = None
        if sub is None or len(sub) < 30:
            # one retry on its own
            time.sleep(1)
            try:
                sub = yf.Ticker(t).history(period="2y", interval="1d", auto_adjust=False)
                sub = sub.dropna(subset=["Open", "High", "Low", "Close"]).tail(KEEP)
            except Exception:
                sub = None
        if sub is None or len(sub) < 30:
            bad.append(s["code"])
            continue
        rec = {
            "code": s["code"], "name": s["name"],
            "d": [i.strftime("%Y-%m-%d") for i in sub.index],
            "o": [rnd(x) for x in sub["Open"]],
            "h": [rnd(x) for x in sub["High"]],
            "l": [rnd(x) for x in sub["Low"]],
            "c": [rnd(x) for x in sub["Close"]],
            "v": [int(x) if x == x else 0 for x in sub["Volume"]],
        }
        with open(os.path.join(OUT, s["code"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, separators=(",", ":"))
        ok += 1
        latest = max(latest or rec["d"][-1], rec["d"][-1])
    meta = {"updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "latest": latest, "ok": ok, "failed": bad}
    with open(os.path.join(ROOT, "data", "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))
    if ok < len(stocks) * 0.8:
        sys.exit("too many failures")


if __name__ == "__main__":
    main()
