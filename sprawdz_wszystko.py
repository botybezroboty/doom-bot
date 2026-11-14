"""Jedno polecenie: testy defend_the_center i niezależna seria MAP01."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__':
    uruchom_na_ukrytym_pulpicie()

import csv
import json
import shutil
import statistics
import unittest
from datetime import datetime
from pathlib import Path

import numpy as np
import vizdoom as vzd
import bot
import defend_the_center as center

ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / 'powtorki'


def recorded_seed(path):
    data = path.read_bytes()
    if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
        raise ValueError(f'Nieznany format powtórki {path}')
    end = data.index(b'\0', 24) + 1
    return int.from_bytes(data[end:end + 4], 'big')


def fresh_seeds():
    """Pomija wszystkie znane seedy silnika i wejściowe ze starych prób."""
    used_engine = set()
    used_input = set()
    for path in REPLAYS.glob('*.lmp'):
        try:
            used_engine.add(recorded_seed(path))
        except (ValueError, IndexError):
            # Starsze nieczytelne powtórki nie pozwalają dowieść świeżości.
            raise ValueError(f'Nie można sprawdzić seeda w {path}')
    for path in REPLAYS.glob('map01*.jsonl'):
        with path.open(encoding='utf-8') as f:
            header = json.loads(f.readline())
        if 'seed' in header:
            used_input.add(int(header['seed']))
        if 'seed_silnika' in header:
            used_engine.add(int(header['seed_silnika']))
    for path in (*ROOT.glob('porownanie_map01*.csv'), *ROOT.glob('dowod_map01*.csv')):
        with path.open(encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                used_input.add(int(row['seed']))
                used_engine.add(int(row['seed_silnika']))
    chosen = []
    for seed in range(1000, 1000000):
        engine = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
        if seed not in used_input and 0 < engine < 2**31 - 1 and engine not in used_engine:
            chosen.append((seed, engine))
            used_engine.add(engine)
            if len(chosen) == 20:
                return chosen
    raise RuntimeError('Nie znaleziono 20 nowych seedów')


def check_artifacts(path, engine):
    if recorded_seed(path) != engine:
        raise RuntimeError(f'Nieprawidłowy seed powtórki {path}')
    for ext in ('.lmp', '.jsonl', '.mp4'):
        if not path.with_suffix(ext).is_file() or not path.with_suffix(ext).stat().st_size:
            raise RuntimeError(f'Brak nagrania {path.with_suffix(ext)}')


def verify_exit(row):
    """Odtwarza przejście i sprawdza użycie przełącznika tuż przed końcem."""
    replay = REPLAYS / (row['powtorka'] + '.lmp')
    entries = [json.loads(line) for line in replay.with_suffix('.jsonl').read_text(encoding='utf-8').splitlines()]
    end = entries[-1]
    if end['wynik'] != 'wyjscie' or end['tik'] != row['tiki']:
        raise RuntimeError(f'Niezgodny dziennik {replay}')
    ticks = [x for x in entries[-6:-1] if x.get('typ') == 'tik']
    # Linia wyjścia MAP01: od (184,-632) do (248,-632).
    if not any(x['akcja'][3] and 130 <= x['x'] <= 302 and -720 <= x['y'] <= -632
               and 25 <= x['kat'] <= 155 for x in ticks):
        raise RuntimeError(f'Brak użycia przy przełączniku wyjścia: {replay}')
    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / 'freedoom2.wad'))
    game.set_doom_map('MAP01')
    game.set_window_visible(False)
    game.init()
    try:
        game.replay_episode(str(replay).replace('\\', '/'))
        count = 0
        with center.dokladny_zegar():
            while not game.is_episode_finished():
                game.advance_action()
                count += 1
                if count > 3500:
                    raise RuntimeError(f'Powtórka przekroczyła limit: {replay}')
        if count != row['tiki'] or game.get_game_variable(vzd.GameVariable.DEATHCOUNT) != 0 or game.get_game_variable(vzd.GameVariable.HEALTH) <= 0:
            raise RuntimeError(f'Powtórka nie potwierdza przejścia: {replay}')
    finally:
        game.close()


def run_center(seeds):
    suite = unittest.defaultTestLoader.loadTestsFromName('test_celowania')
    if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
        raise RuntimeError('Nie przeszły testy celowania defend_the_center')
    rows = []
    for seed, engine in seeds:
        for random_bot in (False, True):
            game = center.create_game()
            try:
                result, replay, fingerprint = center.run_episode(game, seed, 0, random_bot)
            finally:
                game.close()
            check_artifacts(replay, engine)
            kills, deaths, reward, ticks = result
            rows.append({'bot': 'losowy' if random_bot else 'celujacy', 'seed': seed,
                         'seed_silnika': engine, 'zabite': kills, 'zgony': deaths,
                         'tiki': ticks, 'nagroda': reward, 'powtorka': replay.name,
                         'sha256_obrazu': fingerprint})
        print(f'defend_the_center: {len(rows)//2}/20 par', flush=True)
    write_csv(ROOT / 'dowod_center.csv', rows)
    for name in ('celujacy', 'losowy'):
        values = [r['zabite'] for r in rows if r['bot'] == name]
        print(f'defend_the_center {name}: średnio {statistics.mean(values):.2f} zabitych, {len(values)} prób', flush=True)


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    REPLAYS.mkdir(exist_ok=True)
    seeds = fresh_seeds()  # przed rozpoczęciem jakichkolwiek nowych gier
    print('Nowe seedy MAP01:', ', '.join(f'{a}/{b}' for a, b in seeds), flush=True)
    run_center(seeds)
    rows = []
    for i, (seed, engine) in enumerate(seeds, 1):
        row = bot.run(seed)
        check_artifacts(REPLAYS / (row['powtorka'] + '.lmp'), engine)
        if row['wynik'] == 'wyjscie':
            verify_exit(row)
        elif row['wynik'] not in ('zgon', 'limit'):
            raise RuntimeError(f'Nieznany wynik: {row}')
        row['wyjscie_zweryfikowane'] = int(row['wynik'] == 'wyjscie')
        rows.append(row)
        print(f'MAP01: {i}/20 sprawdzonych', flush=True)
    write_csv(ROOT / 'dowod_map01.csv', rows)
    success = [r for r in rows if r['wynik'] == 'wyjscie']
    deaths = sum(r['wynik'] == 'zgon' for r in rows)
    timeout = sum(r['wynik'] == 'limit' for r in rows)
    print(f'MAP01: wyjścia {len(success)}, zgony {deaths}, limit {timeout}', flush=True)
    if success:
        times = [r['tiki'] for r in success]
        best = min(success, key=lambda r: r['tiki'])
        target = REPLAYS / f'najlepsza_map01_{datetime.now():%Y%m%d_%H%M%S_%f}.mp4'
        shutil.copyfile(REPLAYS / (best['powtorka'] + '.mp4'), target)
        print(f'Mediana ukończonych: {statistics.median(times)} tików; poniżej 3027: {sum(t < 3027 for t in times)}/{len(times)}', flush=True)
        print(f'Najlepsza: {best["tiki"]} tików; wideo: {target}', flush=True)
    else:
        print('Mediana ukończonych: brak; nie ma ukończonej próby do pokazania.', flush=True)


if __name__ == '__main__':
    main()
