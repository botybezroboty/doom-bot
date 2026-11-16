"""One command: the defend_the_center tests and an independent MAP01 series."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__':
    run_on_hidden_desktop()

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
REPLAYS = ROOT / 'replays'


def recorded_seed(path):
    data = path.read_bytes()
    if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
        raise ValueError(f'Unknown replay format {path}')
    end = data.index(b'\0', 24) + 1
    return int.from_bytes(data[end:end + 4], 'big')


def fresh_seeds():
    """Skips every engine seed and input seed known from earlier trials."""
    used_engine = set()
    used_input = set()
    for path in REPLAYS.glob('*.lmp'):
        try:
            used_engine.add(recorded_seed(path))
        except (ValueError, IndexError):
            # Older unreadable replays make freshness impossible to prove.
            raise ValueError(f'Cannot check the seed in {path}')
    for path in REPLAYS.glob('map01*.jsonl'):
        with path.open(encoding='utf-8') as f:
            header = json.loads(f.readline())
        if 'seed' in header:
            used_input.add(int(header['seed']))
        if 'engine_seed' in header:
            used_engine.add(int(header['engine_seed']))
    for path in (*ROOT.glob('comparison_map01*.csv'), *ROOT.glob('proof_map01*.csv')):
        with path.open(encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                used_input.add(int(row['seed']))
                used_engine.add(int(row['engine_seed']))
    chosen = []
    for seed in range(1000, 1000000):
        engine = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
        if seed not in used_input and 0 < engine < 2**31 - 1 and engine not in used_engine:
            chosen.append((seed, engine))
            used_engine.add(engine)
            if len(chosen) == 20:
                return chosen
    raise RuntimeError('Could not find 20 new seeds')


def check_artifacts(path, engine):
    if recorded_seed(path) != engine:
        raise RuntimeError(f'Wrong replay seed {path}')
    for ext in ('.lmp', '.jsonl', '.mp4'):
        if not path.with_suffix(ext).is_file() or not path.with_suffix(ext).stat().st_size:
            raise RuntimeError(f'Missing recording {path.with_suffix(ext)}')


def verify_exit(row):
    """Replays the run and checks that the switch was used just before the end."""
    replay = REPLAYS / (row['replay'] + '.lmp')
    entries = [json.loads(line) for line in replay.with_suffix('.jsonl').read_text(encoding='utf-8').splitlines()]
    end = entries[-1]
    if end['outcome'] != 'exit' or end['tic'] != row['tics']:
        raise RuntimeError(f'Log does not match {replay}')
    ticks = [x for x in entries[-6:-1] if x.get('type') == 'tic']
    # The MAP01 exit line: from (184,-632) to (248,-632).
    if not any(x['action'][3] and 130 <= x['x'] <= 302 and -720 <= x['y'] <= -632
               and 25 <= x['angle'] <= 155 for x in ticks):
        raise RuntimeError(f'No use at the exit switch: {replay}')
    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / 'freedoom2.wad'))
    game.set_doom_map('MAP01')
    game.set_window_visible(False)
    game.init()
    try:
        game.replay_episode(str(replay).replace('\\', '/'))
        count = 0
        with center.precise_timer():
            while not game.is_episode_finished():
                game.advance_action()
                count += 1
                if count > 3500:
                    raise RuntimeError(f'The replay went over the limit: {replay}')
        if count != row['tics'] or game.get_game_variable(vzd.GameVariable.DEATHCOUNT) != 0 or game.get_game_variable(vzd.GameVariable.HEALTH) <= 0:
            raise RuntimeError(f'The replay does not confirm the run: {replay}')
    finally:
        game.close()


def run_center(seeds):
    suite = unittest.defaultTestLoader.loadTestsFromName('test_aiming')
    if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
        raise RuntimeError('The defend_the_center aiming tests failed')
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
            rows.append({'bot': 'random' if random_bot else 'aiming', 'seed': seed,
                         'engine_seed': engine, 'kills': kills, 'deaths': deaths,
                         'tics': ticks, 'reward': reward, 'replay': replay.name,
                         'frames_sha256': fingerprint})
        print(f'defend_the_center: {len(rows)//2}/20 pairs', flush=True)
    write_csv(ROOT / 'proof_center.csv', rows)
    for name in ('aiming', 'random'):
        values = [r['kills'] for r in rows if r['bot'] == name]
        print(f'defend_the_center {name}: mean {statistics.mean(values):.2f} kills, {len(values)} trials', flush=True)


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    REPLAYS.mkdir(exist_ok=True)
    seeds = fresh_seeds()  # before any new game starts
    print('New MAP01 seeds:', ', '.join(f'{a}/{b}' for a, b in seeds), flush=True)
    run_center(seeds)
    rows = []
    for i, (seed, engine) in enumerate(seeds, 1):
        row = bot.run(seed)
        check_artifacts(REPLAYS / (row['replay'] + '.lmp'), engine)
        if row['outcome'] == 'exit':
            verify_exit(row)
        elif row['outcome'] not in ('death', 'timeout'):
            raise RuntimeError(f'Unknown outcome: {row}')
        row['exit_verified'] = int(row['outcome'] == 'exit')
        rows.append(row)
        print(f'MAP01: {i}/20 checked', flush=True)
    write_csv(ROOT / 'proof_map01.csv', rows)
    success = [r for r in rows if r['outcome'] == 'exit']
    deaths = sum(r['outcome'] == 'death' for r in rows)
    timeout = sum(r['outcome'] == 'timeout' for r in rows)
    print(f'MAP01: exits {len(success)}, deaths {deaths}, timeouts {timeout}', flush=True)
    if success:
        times = [r['tics'] for r in success]
        best = min(success, key=lambda r: r['tics'])
        target = REPLAYS / f'best_map01_{datetime.now():%Y%m%d_%H%M%S_%f}.mp4'
        shutil.copyfile(REPLAYS / (best['replay'] + '.mp4'), target)
        print(f'Median of completed: {statistics.median(times)} tics; under 3027: {sum(t < 3027 for t in times)}/{len(times)}', flush=True)
        print(f'Best: {best["tics"]} tics; video: {target}', flush=True)
    else:
        print('Median of completed: none; there is no completed trial to show.', flush=True)


if __name__ == '__main__':
    main()
