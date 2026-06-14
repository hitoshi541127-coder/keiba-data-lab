import csv
import json

from netkeiba_python.jsontocsv import load_races, main, parse_title


def test_parse_title_accepts_single_digit_month_and_day():
    assert parse_title("2020年1月2日 テスト G1") == ("2020-01-02", 2020, 1, 2)


def test_load_races_accepts_concatenated_scrapy_json_arrays(tmp_path):
    infile = tmp_path / "races.json"
    infile.write_text('[{"race_id": "a", "horses": []}]\n[{"race_id": "b", "horses": []}]', encoding="utf-8")

    races = load_races(infile)

    assert [race["race_id"] for race in races] == ["a", "b"]


def test_main_writes_csv_with_missing_and_non_numeric_values(tmp_path):
    infile = tmp_path / "races.json"
    outfile = tmp_path / "races.csv"
    race = {
        "race_id": "202001010101",
        "title": "2020年01月01日 テスト G1",
        "diary": "芝 : 良 天候 : 晴 1400m",
        "horses": [
            {
                "order": "1",
                "frame": "4",
                "number": "10",
                "name": "馬名",
                "age": "牡3",
                "weight": "500",
                "jocky": "騎手",
                "time": "1:35.2",
                "difference": "0.3",
                "time-metric": "11",
                "passed": "1-1",
                "last-spurt": "33.1",
                "odds": "---",
                "popularity": "bad",
                "horse-weight": "500(+2)",
                "train-time": "",
                "comments": "",
                "remarks": "",
                "trainer": "調教師",
                "owner": "馬主",
                "prise": "5,000",
            }
        ],
    }
    infile.write_text(json.dumps([race], ensure_ascii=False), encoding="utf-8")

    main(infile, outfile)

    rows = list(csv.DictReader(outfile.open(encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["race_id"] == "202001010101"
    assert rows[0]["date"] == "2020-01-01"
    assert rows[0]["is_g1"] == "1"
    assert rows[0]["is_turf"] == "1"
    assert rows[0]["is_sunny"] == "1"
    assert rows[0]["horse_weight"] == "500.0"
    assert rows[0]["horse_weight_difference"] == "2.0"
    assert rows[0]["prise"] == "5000.0"
