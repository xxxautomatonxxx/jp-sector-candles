# jp-sector-candles

東証33業種ヒートマップ（Claude artifact）用の、代表銘柄の日足データ置き場です。

- `stocks.json` … 対象銘柄（業種ごとの代表銘柄）
- `scripts/fetch_candles.py` … Yahoo Finance から日足（約15か月分、分割調整済み）を取得
- `.github/workflows/candles.yml` … 平日 15:55 JST に自動実行し、`data/c/<コード>.json` を更新
- `data/meta.json` … 最終更新日時・取得失敗した銘柄

手動で更新したいときは、GitHub の Actions タブ →「Update daily candles」→「Run workflow」。
