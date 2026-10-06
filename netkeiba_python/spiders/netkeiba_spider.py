import os
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import scrapy


DEFAULT_MIN_DATE = "20071231"
DEFAULT_START_URL = "https://db.netkeiba.com/race/list.html"

HORSE_KEYS = [
    "order",
    "frame",
    "number",
    "name",
    "age",
    "weight",
    "jocky",
    "time",
    "difference",
    "time-metric",
    "passed",
    "last-spurt",
    "odds",
    "popularity",
    "horse-weight",
    "train-time",
    "comments",
    "remarks",
    "trainer",
    "owner",
    "prise",
]


class NetkeibaSpider(scrapy.Spider):
    name = "netkeiba"
    custom_settings = {
        "LOG_LEVEL": "INFO",
    }

    def __init__(
        self,
        min_date=None,
        max_pages=None,
        max_races=None,
        start_url=None,
        local_html_dir=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.min_date = self._normalize_date(min_date or os.getenv("MIN_DATE") or DEFAULT_MIN_DATE)
        self.max_pages = self._to_positive_int(max_pages or os.getenv("MAX_PAGES"))
        self.max_races = self._to_positive_int(max_races or os.getenv("MAX_RACES"))
        self.local_html_dir = local_html_dir or os.getenv("LOCAL_HTML_DIR")
        self.calendar_pages_seen = 0
        self.races_seen = 0

        if self.local_html_dir:
            local_dir = Path(self.local_html_dir).expanduser().resolve()
            self.local_html_dir = str(local_dir)
            self.start_urls = [(local_dir / "race_top.html").as_uri()]
        else:
            self.start_urls = [start_url or os.getenv("START_URL") or DEFAULT_START_URL]

    @staticmethod
    def _normalize_date(value):
        value = str(value)
        if not re.fullmatch(r"\d{8}", value):
            raise ValueError("min_date must be YYYYMMDD")
        return value

    @staticmethod
    def _to_positive_int(value):
        if value in (None, ""):
            return None
        parsed = int(value)
        if parsed < 1:
            raise ValueError("limits must be positive integers")
        return parsed

    def _resolve_url(self, response, href):
        if self.local_html_dir and response.url.startswith("file://"):
            parsed = urlparse(href)
            query = parse_qs(parsed.query)
            pid = query.get("pid", [None])[0]
            date = query.get("date", [None])[0]
            candidates = []

            if pid and date:
                candidates.append(f"{pid}_{date}.html")
            if pid:
                candidates.append(f"{pid}.html")

            path_name = Path(parsed.path).name
            if path_name:
                candidates.append(f"{path_name}.html")

            local_dir = Path(self.local_html_dir)
            for filename in candidates:
                path = local_dir / filename
                if path.exists():
                    return path.resolve().as_uri()

        return response.urljoin(href)

    @staticmethod
    def _extract_date(url):
        parsed = urlparse(url)
        query_date = parse_qs(parsed.query).get("date", [None])[0]
        if query_date and re.fullmatch(r"\d{8}", query_date):
            return query_date

        match = re.search(r"(20\d{6}|19\d{6})", url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _extract_race_id(url):
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        for key in ("race_id", "id"):
            value = query.get(key, [None])[0]
            if value:
                return value

        match = re.search(r"/race/([0-9a-zA-Z_]+)/?", parsed.path)
        if match:
            return match.group(1)
        return None

    def _is_race_detail_href(self, href):
        parsed = urlparse(href)
        if self.local_html_dir:
            pid = parse_qs(parsed.query).get("pid", [None])[0]
            if pid == "race_detail":
                return True

        return re.fullmatch(r"/race/\d{12}/?", parsed.path) is not None

    @staticmethod
    def _clean_text(selector_list):
        parts = [part.strip() for part in selector_list.getall()]
        parts = [part for part in parts if part]
        if not parts:
            return None
        return " ".join(parts)

    @staticmethod
    def _normalize_header(header):
        if not header:
            return ""
        return re.sub(r"\s+", "", header)

    def _header_to_key(self, header):
        header = self._normalize_header(header)
        if header == "着順":
            return "order"
        if header == "枠番":
            return "frame"
        if header == "馬番":
            return "number"
        if header == "馬名":
            return "name"
        if header == "性齢":
            return "age"
        if header == "斤量":
            return "weight"
        if header == "騎手":
            return "jocky"
        if header == "タイム":
            return "time"
        if header == "着差":
            return "difference"
        if "タイム指数" in header or "ﾀｲﾑ指数" in header:
            return "time-metric"
        if header == "通過":
            return "passed"
        if header == "上り":
            return "last-spurt"
        if header == "単勝":
            return "odds"
        if header == "人気":
            return "popularity"
        if header == "馬体重":
            return "horse-weight"
        if "調教" in header and ("タイム" in header or "ﾀｲﾑ" in header):
            return "train-time"
        if "コメント" in header or "ｺﾒﾝﾄ" in header:
            return "comments"
        if header == "備考":
            return "remarks"
        if header == "調教師":
            return "trainer"
        if header == "馬主":
            return "owner"
        if "賞金" in header:
            return "prise"
        return None

    def _map_horse(self, headers, values):
        horse = {key: None for key in HORSE_KEYS}
        if len(headers) == len(values):
            for header, value in zip(headers, values):
                key = self._header_to_key(header)
                if key and horse.get(key) is None:
                    horse[key] = value
            return horse

        for key, value in zip(HORSE_KEYS, values):
            horse[key] = value
        return horse

    def parse(self, response):
        self.calendar_pages_seen += 1
        for href in response.css(".race_calendar td a::attr(href)").getall():
            full_url = self._resolve_url(response, href)
            yield scrapy.Request(full_url, callback=self.parse_race_list, errback=self.handle_error)

        if self.max_pages and self.calendar_pages_seen >= self.max_pages:
            self.logger.info("Stopped calendar crawl at max_pages=%s", self.max_pages)
            return

        next_pages = response.css(".race_calendar li.rev a::attr(href)").getall()
        if len(next_pages) <= 1:
            return

        next_page = next_pages[1]
        date = self._extract_date(next_page)
        if not date:
            self.logger.warning("Skip next calendar page without date: %s", next_page)
            return

        if date > self.min_date:
            yield scrapy.Request(
                self._resolve_url(response, next_page),
                callback=self.parse,
                errback=self.handle_error,
            )

    def parse_race_list(self, response):
        selectors = [
            ".race_top_data_info > dd > a::attr(href)",
            ".race_top_data_info a::attr(href)",
            "a[href*='/race/']::attr(href)",
        ]
        race_urls = []
        for selector in selectors:
            race_urls.extend(
                href for href in response.css(selector).getall()
                if self._is_race_detail_href(href)
            )
        self.logger.info("FOUND RACE URLS: %s", len(race_urls))
        for href in dict.fromkeys(race_urls):
            race_id = self._extract_race_id(self._resolve_url(response, href))
            self.races_seen += 1
            yield scrapy.Request(
                self._resolve_url(response, href),
                callback=self.parse_race,
                errback=self.handle_error,
            )

    def parse_race(self, response):
        rows = response.css(".race_table_01 tr")

        result = {
            "race_id": self._extract_race_id(response.url),
            "source_url": response.url,
            "title": response.css("title::text").get() or response.css("h1::text").get(),
            "horses": [],
            "distance": self._clean_text(
                response.css(".racedata.fc span::text")
            ),
            "diary": self._clean_text(response.css(".diary_snap_cut span::text, .diary_snap_cut::text")),
            "smalltxt": self._clean_text(response.css("p.smalltxt::text")),
        }

        headers = [self._clean_text(th.css("::text")) for th in rows[0].css("th")]

        for row in rows[1:]:
            values = [self._clean_text(td.css("::text")) for td in row.css("td")]
            if not values:
                continue
            result["horses"].append(self._map_horse(headers, values))

        if not result["horses"]:
            self.logger.warning("Skip race without horse rows: %s", response.url)
            return

        yield result

    def handle_error(self, failure):
        self.logger.warning("Request failed: %s", failure.request.url)
