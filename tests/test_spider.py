from scrapy.http import HtmlResponse, Request

from netkeiba_python.spiders.netkeiba_spider import NetkeibaSpider


def make_response(url, body):
    request = Request(url=url)
    return HtmlResponse(url=url, request=request, body=body.encode("utf-8"), encoding="utf-8")


def test_parse_race_extracts_race_metadata_and_horses():
    spider = NetkeibaSpider()
    html = """
    <html>
      <head><title>2020年01月01日 テスト G1</title></head>
      <body>
        <p class="smalltxt">1回 東京 1日目</p>
        <div class="diary_snap_cut">芝 : 良 天候 : 晴 1400m</div>
        <table class="race_table_01">
          <tr>
            <th>着 順</th><th>枠 番</th><th>馬 番</th><th>馬名</th>
            <th>性齢</th><th>斤量</th><th>騎手</th><th>タイム</th>
            <th>着差</th><th>ﾀｲﾑ 指数</th><th>ﾀｲﾑ 指数 M</th>
            <th>ｽﾀｰﾄ指数</th><th>追走指数</th><th>上がり指数</th>
            <th>通過</th><th>上り</th><th>単勝</th><th>人 気</th>
            <th>馬体重</th><th>調教 ﾀｲﾑ</th><th>厩舎 ｺﾒﾝﾄ</th>
            <th>備考</th><th>調教師</th><th>馬主</th><th>賞金 (万円)</th>
          </tr>
          <tr>
            <td>1</td><td>4</td><td>10</td><td>馬名</td><td>牡3</td>
            <td>500</td><td>騎手</td><td>1:35.2</td><td>0.3</td>
            <td>11</td><td></td><td></td><td></td><td></td>
            <td>1-1</td><td>33.1</td><td>1.2</td><td>1</td>
            <td>500(+2)</td><td></td><td></td><td></td>
            <td>調教師</td><td>馬主</td><td>5,000</td>
          </tr>
        </table>
      </body>
    </html>
    """
    response = make_response("https://db.netkeiba.com/race/202001010101/", html)

    item = list(spider.parse_race(response))[0]

    assert item["race_id"] == "202001010101"
    assert item["source_url"] == "https://db.netkeiba.com/race/202001010101/"
    assert item["title"] == "2020年01月01日 テスト G1"
    assert item["diary"] == "芝 : 良 天候 : 晴 1400m"
    assert item["smalltxt"] == "1回 東京 1日目"
    assert item["horses"][0]["name"] == "馬名"
    assert item["horses"][0]["passed"] == "1-1"
    assert item["horses"][0]["last-spurt"] == "33.1"
    assert item["horses"][0]["odds"] == "1.2"
    assert item["horses"][0]["popularity"] == "1"
    assert item["horses"][0]["horse-weight"] == "500(+2)"
    assert item["horses"][0]["trainer"] == "調教師"
    assert item["horses"][0]["owner"] == "馬主"
    assert item["horses"][0]["prise"] == "5,000"


def test_parse_race_list_deduplicates_race_links():
    spider = NetkeibaSpider(max_races=2)
    html = """
    <html><body>
      <div class="race_top_data_info">
        <dd><a href="/race/list/20200101/">list</a></dd>
        <dd><a href="/race/movie/202001010101">movie</a></dd>
        <dd><a href="/race/pay/01/20200101/">pay</a></dd>
        <dd><a href="/race/202001010101/">race</a></dd>
        <dd><a href="/race/202001010101/">race duplicate</a></dd>
        <dd><a href="/race/202001010102/">race2</a></dd>
      </div>
    </body></html>
    """
    response = make_response("https://db.netkeiba.com/?pid=race_list&date=20200101", html)

    requests = list(spider.parse_race_list(response))

    assert [request.url for request in requests] == [
        "https://db.netkeiba.com/race/202001010101/",
        "https://db.netkeiba.com/race/202001010102/",
    ]
