# Keiba Data Lab

競馬データを収集・検証・CSV化するための Scrapy ベースのデータパイプラインです。
`db.netkeiba.com` のレース結果ページを安定して収集し、機械学習や分析に使いやすいCSVへ変換します。

This project is based on [Kurorororo/netkeiba_python](https://github.com/Kurorororo/netkeiba_python) and extends it with safer crawling, CSV conversion, tests, and CI.

## 特徴

- 実HTMLのテーブルヘッダを見て列をマッピングするため、列ズレに強い
- `max_pages` / `max_races` / `min_date` で小さく試してから長時間実行できる
- Scrapy の `-O` 出力だけでなく、連結されたJSON配列もCSV変換できる
- DNS制限環境でもローカルHTMLで処理経路を検証できる
- pytest と GitHub Actions で基本動作を検証できる

## 対応環境

- Python 3.8 以上
- Scrapy 2.11 以上

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## クロール

通常の取得:

```bash
scrapy crawl netkeiba -O keiba.json
python netkeiba_python/jsontocsv.py -i keiba.json -o keiba.csv
```

長時間運用では、最初に範囲を絞って確認してください。

```bash
scrapy crawl netkeiba -O sample.json -a max_pages=1 -a max_races=5
python netkeiba_python/jsontocsv.py -i sample.json -o sample.csv
```

指定できる主な引数:

- `min_date`: この日付より古いカレンダーページへ進まない。形式は `YYYYMMDD`。既定値は `20071231`
- `max_pages`: カレンダーページの最大取得数
- `max_races`: レース詳細ページの最大取得数
- `start_url`: 開始URL
- `local_html_dir`: ローカルHTML検証用ディレクトリ

環境変数でも指定できます。

```bash
MIN_DATE=20200101 MAX_RACES=20 scrapy crawl netkeiba -O keiba.json
```

## ローカルHTML検証

DNS や外部ネットワークが使えない環境でも、同じ処理経路を検証できます。

```bash
LOCAL_HTML_DIR=/tmp/race_data scrapy crawl netkeiba -O local.json
python netkeiba_python/jsontocsv.py -i local.json -o local.csv
```

`/tmp/race_data` には次のようなファイルを置きます。

- `race_top.html`
- `race_list.html` または `race_list_YYYYMMDD.html`
- `race_detail.html`

## CSV変換

Scrapy の `-O` 出力だけでなく、複数のJSON配列が連結されたファイルも読み込めます。
欠損値や数値化できない値は空欄として出力します。

```bash
python netkeiba_python/jsontocsv.py -i keiba.json -o keiba.csv
python netkeiba_python/jsontocsv.py -i keiba.json -o keiba.csv --encoding utf-8
```

## テスト

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall netkeiba_python tests
```

## 運用メモ

- `settings.py` では同時接続数、ダウンロード間隔、自動スロットリング、リトライ、HTTPキャッシュを有効化しています。
- 出力ファイルの再実行には Scrapy の `-O` を使います。`-o` は既存ファイルへ追記するため、JSONが連結されることがあります。
- 公開・運用時は対象サイトの利用規約とアクセス頻度を確認してください。
