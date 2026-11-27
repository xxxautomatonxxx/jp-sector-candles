"""Market-wide series for the dashboard:
  data/e17.json    TOPIX-17 sector ETFs (1617-1633) + TOPIX ETF 1306, ~3y daily closes
  data/macro.json  WTI, Brent, USD/JPY, US10Y, SOX, Gold, VIX, ~3y daily closes
  data/world.json  major world stock indices, ~2y daily closes
Each series: {"name":..., "d":[dates], "c":[closes]} (own calendar per series).
"""
import json
import os
import time

import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

E17 = [
    ("1306.T", "TOPIX"),
    ("1617.T", "食品"), ("1618.T", "エネルギー資源"), ("1619.T", "建設・資材"), ("1620.T", "素材・化学"),
    ("1621.T", "医薬品"), ("1622.T", "自動車・輸送機"), ("1623.T", "鉄鋼・非鉄"), ("1624.T", "機械"),
    ("1625.T", "電機・精密"), ("1626.T", "情報通信・サービス"), ("1627.T", "電力・ガス"), ("1628.T", "運輸・物流"),
    ("1629.T", "商社・卸売"), ("1630.T", "小売"), ("1631.T", "銀行"), ("1632.T", "金融（除く銀行）"), ("1633.T", "不動産"),
]
MACRO = [
    ("CL=F", "WTI原油"), ("BZ=F", "北海ブレント"), ("JPY=X", "ドル円"), ("^TNX", "米10年金利"),
    ("^SOX", "米半導体指数SOX"), ("GC=F", "金"), ("^VIX", "VIX"),
]
WORLD = [
    ("^N225", "日経平均", "日本"), ("1306.T", "TOPIX（ETF）", "日本"),
    ("^GSPC", "S&P500", "米国"), ("^IXIC", "ナスダック総合", "米国"), ("^DJI", "NYダウ", "米国"), ("^SOX", "SOX", "米国"),
    ("^STOXX50E", "ユーロ・ストックス50", "欧州"), ("^GDAXI", "独DAX", "欧州"), ("^FTSE", "英FTSE100", "欧州"), ("^FCHI", "仏CAC40", "欧州"),
    ("^NSEI", "インドNifty50", "インド"), ("^BSESN", "インドSENSEX", "インド"),
    ("000001.SS", "上海総合", "中国"), ("^HSI", "香港ハンセン", "中国"),
    ("^KS11", "韓国KOSPI", "アジア"), ("^TWII", "台湾加権", "アジア"), ("^AXJO", "豪ASX200", "アジア"), ("^STI", "シンガポールSTI", "アジア"),
    ("^BVSP", "ブラジルBovespa", "新興国"), ("^MXX", "メキシコIPC", "新興国"),
]


def rnd(x):
    x = float(x)
    a = abs(x)
    return round(x, 4) if a < 10 else round(x, 2) if a < 10000 else round(x, 1)


def grab(pairs, period):
    syms = [p[0] for p in pairs]
    df = yf.download(syms, period=period, interval="1d", group_by="ticker",
                     auto_adjust=False, actions=False, threads=True, progress=False)
    out, bad = {}, []
    for p in pairs:
        s = p[0]
        try:
            sub = df[s]["Close"].dropna()
        except KeyError:
            sub = None
        if sub is None or len(sub) < 30:
            time.sleep(1)
            try:
                sub = yf.Ticker(s).history(period=period, interval="1d", auto_adjust=False)["Close"].dropna()
            except Exception:
                sub = None
        if sub is None or len(sub) < 30:
            bad.append(s)
            continue
        rec = {"name": p[1], "d": [i.strftime("%Y-%m-%d") for i in sub.index], "c": [rnd(v) for v in sub]}
        if len(p) > 2:
            rec["region"] = p[2]
        out[s] = rec
    return out, bad


def main():
    os.makedirs(DATA, exist_ok=True)
    meta = {}
    for fn, pairs, period in [("e17", E17, "3y"), ("macro", MACRO, "3y"), ("world", WORLD, "2y")]:
        ser, bad = grab(pairs, period)
        with open(os.path.join(DATA, fn + ".json"), "w", encoding="utf-8") as f:
            json.dump({"order": [p[0] for p in pairs if p[0] in ser], "series": ser}, f,
                      ensure_ascii=False, separators=(",", ":"))
        meta[fn] = {"ok": len(ser), "failed": bad}
    print(json.dumps(meta, ensure_ascii=False))
    with open(os.path.join(DATA, "market_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
