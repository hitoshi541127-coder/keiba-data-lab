import argparse
import csv
import json
import re
from json import JSONDecoder


HEADER = [# race information
          'race_id',
          'date',
          'year',
          'month',
          'day',
          'is_Jan',
          'is_Feb',
          'is_Mar',
          'is_Apr',
          'is_May',
          'is_Jun',
          'is_Jul',
          'is_Aug',
          'is_Sep',
          'is_Oct',
          'is_Nov',
          'is_Dec',
          'is_g1',
          'is_g2',
          'is_g3',
          'is_turf',
          'is_dirt',
          'is_obstacle',
          'is_right',
          'is_left',
          'is_straight',
          'distance',
          'is_sunny',
          'is_cloudy',
          'is_rainy',
          'is_turf_good',
          'is_turf_slightly_heavy',
          'is_turf_heavy',
          'is_turf_bad',
          'is_dirt_good',
          'is_dirt_slightly_heavy',
          'is_dirt_heavy',
          'is_dirt_bad',
          'number_of_horses',
          # horse str information
          'horse_id',
          'name',
          'jocky',
          'trainer',
          'owner',
          # horse information
          'frame',
          'number',
          'is_male',
          'is_female',
          'is_castrated',
          'age',
          'weight',
          'horse_weight',
          'horse_weight_difference',
          # odds information,
          'odds',
          'popularity',
          # horse premium information
          'time_metric',
          'train_time',
          'comments',
          'remarks',
          # result information
          'order',
          'time',
          'difference',
          'passed',
          'last_spurt',
          'prise']


def float_or_none(value):
    if value:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    return None


def int_or_none(value):
    if value:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return None


def parse_title(title):
    if not title:
        return None, None, None, None

    m = re.search(r"([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日", title)

    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        date = f"{year:04d}-{month:02d}-{day:02d}"

        return date, year, month, day

    return None, None, None, None


def parse_class(title):
    if not title:
        return 0, 0, 0

    g1 = 0
    g2 = 0
    g3 = 0

    if re.search(r"G1|GI|GⅠ", title):
        g1 = 1

    if re.search(r"G2|GII|GⅡ", title):
        g2 = 1

    if re.search(r"G3|GIII|GⅢ", title):
        g3 = 1

    return g1, g2, g3


def parse_field(diary):
    if not diary:
        return 0, 0, 0

    turf = 0
    dirt = 0
    obstacle = 0

    if re.search(r"芝", diary):
        turf = 1

    if re.search(r"ダート", diary):
        dirt = 1

    if re.search(r"障害", diary):
        obstacle = 1

    return turf, dirt, obstacle


def parse_rotation(diary):
    if not diary:
        return 0, 0, 0

    right = 0
    left = 0
    straight = 0

    if re.search(r"右", diary):
        right = 1

    if re.search(r"左", diary):
        left = 1

    if re.search(r"直線", diary):
        straight = 1

    return right, left, straight


def parse_distance(diary):
    if not diary:
        return None

    distance = None
    m = re.search(r"([0-9]+)m", diary)

    if m:
        distance = int(m.group(1))

    return distance


def parse_weather(diary):
    if not diary:
        return 0, 0, 0

    sunny = 0
    cloudy = 0
    rainy = 0
    m = re.search(r"天候\s*[:：]\s*(.)", diary)
    weather = None

    if m:
        weather = m.group(1)

    if weather == '晴':
        sunny = 1

    if weather == '曇':
        cloudy = 1

    if weather == '雨':
        rainy = 1

    return sunny, cloudy, rainy


def parse_turf_wetness(diary):
    if not diary:
        return 0, 0, 0, 0

    good = 0
    slightly_heavy = 0
    heavy = 0
    bad = 0

    if re.search(r"芝\s*[:：]\s*良", diary):
        good = 1

    if re.search(r"芝\s*[:：]\s*稍重", diary):
        slightly_heavy = 1

    if re.search(r"芝\s*[:：]\s*重", diary):
        heavy = 1

    if re.search(r"芝\s*[:：]\s*不良", diary):
        bad = 1

    return good, slightly_heavy, heavy, bad


def parse_dirt_wetness(diary):
    if not diary:
        return 0, 0, 0, 0

    good = 0
    slightly_heavy = 0
    heavy = 0
    bad = 0

    if re.search(r"ダート\s*[:：]\s*良", diary):
        good = 1

    if re.search(r"ダート\s*[:：]\s*稍重", diary):
        slightly_heavy = 1

    if re.search(r"ダート\s*[:：]\s*重", diary):
        heavy = 1

    if re.search(r"ダート\s*[:：]\s*不良", diary):
        bad = 1

    return good, slightly_heavy, heavy, bad


def parse_age(age):
    if not age:
        return 0, 0, 0, None

    sex = age[0]
    male = 0
    female = 0
    castrated = 0

    if sex == '牡':
        male = 1

    if sex == '牝':
        female = 1

    if sex == 'セ':
        castrated = 1

    years_old = int_or_none(age[1:])

    return male, female, castrated, years_old


def parse_odds(odds):
    if odds == '---':
        return None

    return float_or_none(odds)


def parse_horse_weight(horse_weight):
    if not horse_weight:
        return None, None

    m = re.search(r"([0-9]+)\(([+/-]?[0-9]+)\)", horse_weight)
    horse_weight_value = None
    horse_weight_difference = None

    if m:
        horse_weight_value = float(m.group(1))
        horse_weight_difference = float(m.group(2))

    return horse_weight_value, horse_weight_difference


def parse_order(order):
    if not order:
        return None

    if order == '取' or order == '中' or order == '除':
        return None

    m = re.match(r"([0-9]+)", order)

    if not m:
        return None

    return int_or_none(m.group(1))


def parse_time(time):
    if not time:
        return None

    m = re.search(r"([0-9]+):([0-9.]+)", time)

    if not m:
        return None

    return 60.0 * float(m.group(1)) + float(m.group(2))


def parse_prise(prise):
    if not prise:
        return None

    try:
        return float_or_none(prise.replace(',', ''))
    except ValueError:
        return None


def parse_race(race_id, race):
    if not isinstance(race, dict):
        return None

    race_id = race.get('race_id') or race_id
    title = race.get('title')
    date, year, month, day = parse_title(title)
    race_info = [race_id, date, year, month, day]
    race_info += [1 if (i + 1) == month else 0 for i in range(12)]

    g1, g2, g3 = parse_class(title)

    diary = race.get('race_data') or race.get('diary', '')
    turf, dirt, obstacle = parse_field(diary)
    right, left, straight = parse_rotation(diary)
    distance = parse_distance(diary)
    sunny, cloudy, rainy = parse_weather(diary)
    t_good, t_slightly_heavy, t_heavy, t_bad = parse_turf_wetness(diary)
    d_good, d_slightly_heavy, d_heavy, d_bad = parse_dirt_wetness(diary)
    horses = race.get('horses', [])
    number_of_horses = len(horses) if isinstance(horses, list) else 0

    race_info += [g1,
                  g2,
                  g3,
                  turf,
                  dirt,
                  obstacle,
                  right,
                  left,
                  straight,
                  distance,
                  sunny,
                  cloudy,
                  rainy,
                  t_good,
                  t_slightly_heavy,
                  t_heavy,
                  t_bad,
                  d_good,
                  d_slightly_heavy,
                  d_heavy,
                  d_bad,
                  number_of_horses]

    return race_info


def parse_horse(horse):
    if not isinstance(horse, dict):
        return None

    name = horse.get('name')
    jocky = horse.get('jocky')
    trainer = horse.get('trainer')
    owner = horse.get('owner')

    frame = int_or_none(horse.get('frame'))
    number = int_or_none(horse.get('number'))
    male, female, castrated, years_old = parse_age(horse.get('age'))
    weight = float_or_none(horse.get('weight'))
    value, weight_difference = parse_horse_weight(
            horse.get('horse-weight'))

    odds = parse_odds(horse.get('odds'))
    popularity = int_or_none(horse.get('popularity'))

    time_metric = horse.get('time-metric')
    train_time = horse.get('train-time')
    comments = horse.get('comments')
    remarks = horse.get('remarks')

    order = parse_order(horse.get('order'))
    time = parse_time(horse.get('time'))
    difference = horse.get('difference')
    passed = horse.get('passed')
    last_spurt = float_or_none(horse.get('last-spurt'))
    prise = parse_prise(horse.get('prise'))

    return [name,
            jocky,
            trainer,
            owner,
            frame,
            number,
            male,
            female,
            castrated,
            years_old,
            weight,
            value,
            weight_difference,
            odds,
            popularity,
            time_metric,
            train_time,
            comments,
            remarks,
            order,
            time,
            difference,
            passed,
            last_spurt,
            prise]


def load_races(infile, encoding='utf-8'):
    with open(infile, encoding=encoding) as f:
        text = f.read().strip()

    if not text:
        raise ValueError('入力ファイルが空です。')

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Scrapy の -o だと出力が配列の連結やJSON Lines形式になることがあるため吸収する
        decoder = JSONDecoder()
        data = []
        idx = 0

        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1

            if idx >= len(text):
                break

            if text[idx] in ',[]':
                idx += 1
                continue

            value, consumed = decoder.raw_decode(text[idx:])
            if isinstance(value, list):
                data.extend(value)
            else:
                data.append(value)
            idx += consumed

    if not isinstance(data, list):
        data = [data]

    return data


def main(infile, outfile, encoding='utf-8'):
    data = load_races(infile, encoding=encoding)

    with open(outfile, 'w', encoding=encoding, newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(HEADER)

        for i, race in enumerate(data):
            race_info = parse_race(i, race)
            if race_info is None:
                continue
            horses = race.get('horses', []) if isinstance(race, dict) else []
            if not isinstance(horses, list):
                continue

            for horse in horses:
                if not isinstance(horse, dict):
                    continue
                horse_info = parse_horse(horse)
                if horse_info is None:
                    continue

                row = race_info + horse_info
                #print(row)
                writer.writerow(row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--infile',
                        help='入力となる JSON ファイル',
                        type=str,
                        required=True)
    parser.add_argument('-o',
                        '--outfile',
                        help='出力となる CSV ファイル',
                        type=str,
                        required=True)
    parser.add_argument('--encoding',
                        help='入出力ファイルの文字コード',
                        type=str,
                        default='utf-8')
    args = parser.parse_args()

    main(args.infile, args.outfile, encoding=args.encoding)
