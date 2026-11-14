"""Porównanie trzech wersji bota na zapisanym zestawie 100 seedów."""
import csv
import json

from defend_the_center import REPLAYS, ROOT, create_game, run_episode
from porownaj_amunicje import analiza, sprawdz_seed


def wynik_z_dziennika(path):
    with path.with_suffix('.jsonl').open(encoding='utf-8') as file:
        rows = [json.loads(line) for line in file]
    end = rows[-1]
    if end['typ'] != 'koniec':
        raise ValueError(f'Niepełny dziennik: {path}')
    return int(end['zabite']), int(end['tik'])


def main():
    with (ROOT / 'porownanie_amunicji.csv').open(encoding='utf-8', newline='') as file:
        old = list(csv.DictReader(file))
    if len(old) != 100 or len({row['seed_silnika'] for row in old}) != 100:
        raise ValueError('Potrzebna seria 100 różnych seedów')
    for row in old:
        for suffix in ('stary', 'nowy'):
            path = REPLAYS / row['powtorka_' + suffix]
            sprawdz_seed(path, row['seed_silnika'])
            if wynik_z_dziennika(path) != (int(row['zabite_' + suffix]), int(row['tiki_' + suffix])):
                raise ValueError(f'Niezgodny wynik dziennika: {path}')
            analiza(path)
    results = []
    game = create_game()
    deaths = 0
    try:
        for index, row in enumerate(old, 1):
            (kills, death, reward, ticks), replay, fingerprint = run_episode(
                game, int(row['seed']), deaths, False)
            deaths += death
            metrics = []
            for suffix in ('stary', 'nowy'):
                path = REPLAYS / row['powtorka_' + suffix]
                metrics.extend([row['zabite_' + suffix], row['tiki_' + suffix],
                                *analiza(path), path.name])
            metrics.extend([kills, ticks, *analiza(replay), replay.name])
            results.append([row['seed'], row['seed_silnika'], *metrics, fingerprint])
            print(f'{index}/100 seed {row["seed"]}: {row["zabite_stary"]} / '
                  f'{row["zabite_nowy"]} / {kills}', flush=True)
    finally:
        game.close()
    for row in results:
        sprawdz_seed(REPLAYS / row[-2], row[1])
    if len({row[-1] for row in results}) != 100:
        raise ValueError('Powtórzone odciski obrazów')
    columns = ['seed', 'seed_silnika']
    for version in ('ciagly', 'obrys', 'poprawiony'):
        columns.extend(f'{field}_{version}' for field in
                       ('zabite', 'tiki', 'zuzyte', 'poza_celem', 'brak_amunicji_tik', 'powtorka'))
    with (ROOT / 'porownanie_trzech.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([*columns, 'sha256_poprawiony'])
        writer.writerows(results)


if __name__ == '__main__':
    main()
