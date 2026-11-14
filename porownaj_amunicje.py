"""Porównaj bieżącego bota z serią z porownanie_demony.csv."""

if __name__ == '__main__':
    from ukryte_okno import uruchom_na_ukrytym_pulpicie
    uruchom_na_ukrytym_pulpicie()
import csv
import json
from pathlib import Path

from defend_the_center import FRAME_WIDTH, REPLAYS, ROOT, TARGET_LABELS, create_game, run_episode


def analiza(path):
    with path.with_suffix('.jsonl').open(encoding='utf-8') as file:
        records = [json.loads(line) for line in file]
    ticks = [row for row in records if row['typ'] == 'tik']
    end = records[-1]
    spent = outside = 0
    empty = None
    for current, following in zip(ticks, ticks[1:] + [end]):
        used = max(0, int(current['amunicja'] - following['amunicja']))
        spent += used
        centered = any(label['nazwa'] in TARGET_LABELS and label['szerokosc'] > 0
                       and label['x'] <= FRAME_WIDTH / 2 < label['x'] + label['szerokosc']
                       for label in current['etykiety'])
        if not centered:
            outside += used
        if empty is None and following['amunicja'] == 0:
            empty = following['tik']
    return spent, outside, empty


def sprawdz_seed(path, expected):
    data = path.read_bytes()
    if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
        raise ValueError(f'Nieznany format powtórki: {path}')
    end = data.index(b'\0', 24) + 1
    if int.from_bytes(data[end:end + 4], 'big') != int(expected):
        raise ValueError(f'Niezgodny seed: {path}')


def main():
    with (ROOT / 'porownanie_demony.csv').open(encoding='utf-8', newline='') as file:
        old = list(csv.DictReader(file))
    if len(old) != 100 or len({row['seed_silnika'] for row in old}) != 100:
        raise ValueError('Potrzebna seria 100 różnych seedów')
    for row in old:
        path = REPLAYS / row['powtorka_nowy']
        sprawdz_seed(path, row['seed_silnika'])
        analiza(path)
    results = []
    game = create_game()
    deaths = 0
    try:
        for index, previous in enumerate(old, 1):
            (kills, death, reward, ticks), replay, fingerprint = run_episode(
                game, int(previous['seed']), deaths, False)
            deaths += death
            prior = analiza(REPLAYS / previous['powtorka_nowy'])
            current = analiza(replay)
            results.append([previous['seed'], previous['seed_silnika'], previous['zabite_nowy'],
                            kills, previous['tiki_nowy'], ticks, *prior, *current,
                            previous['powtorka_nowy'], replay.name, fingerprint])
            print(f'{index}/100 seed {previous["seed"]}: {previous["zabite_nowy"]} -> {kills}', flush=True)
    finally:
        game.close()
    for row in results:
        sprawdz_seed(REPLAYS / row[-2], row[1])
    if len({row[-1] for row in results}) != 100:
        raise ValueError('Powtórzone odciski obrazów')
    with (ROOT / 'porownanie_amunicji.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['seed', 'seed_silnika', 'zabite_stary', 'zabite_nowy',
                         'tiki_stary', 'tiki_nowy', 'zuzyte_stary', 'poza_celem_stary',
                         'brak_amunicji_tik_stary', 'zuzyte_nowy', 'poza_celem_nowy',
                         'brak_amunicji_tik_nowy', 'powtorka_stary', 'powtorka_nowy', 'sha256_nowy'])
        writer.writerows(results)


if __name__ == '__main__':
    main()
