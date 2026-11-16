"""Comparison of three bot versions on the saved set of 100 seeds."""

if __name__ == '__main__':
    from hidden_desktop import run_on_hidden_desktop
    run_on_hidden_desktop()
import csv
import json

from defend_the_center import REPLAYS, ROOT, create_game, run_episode
from compare_ammo import analyze, check_seed


def log_result(path):
    with path.with_suffix('.jsonl').open(encoding='utf-8') as file:
        rows = [json.loads(line) for line in file]
    end = rows[-1]
    if end['type'] != 'end':
        raise ValueError(f'Incomplete log: {path}')
    return int(end['kills']), int(end['tic'])


def main():
    with (ROOT / 'comparison_ammo.csv').open(encoding='utf-8', newline='') as file:
        old = list(csv.DictReader(file))
    if len(old) != 100 or len({row['engine_seed'] for row in old}) != 100:
        raise ValueError('Needs a set of 100 different seeds')
    for row in old:
        for suffix in ('old', 'new'):
            path = REPLAYS / row['replay_' + suffix]
            check_seed(path, row['engine_seed'])
            if log_result(path) != (int(row['kills_' + suffix]), int(row['tics_' + suffix])):
                raise ValueError(f'Log result does not match: {path}')
            analyze(path)
    results = []
    game = create_game()
    deaths = 0
    try:
        for index, row in enumerate(old, 1):
            (kills, death, reward, ticks), replay, fingerprint = run_episode(
                game, int(row['seed']), deaths, False)
            deaths += death
            metrics = []
            for suffix in ('old', 'new'):
                path = REPLAYS / row['replay_' + suffix]
                metrics.extend([row['kills_' + suffix], row['tics_' + suffix],
                                *analyze(path), path.name])
            metrics.extend([kills, ticks, *analyze(replay), replay.name])
            results.append([row['seed'], row['engine_seed'], *metrics, fingerprint])
            print(f'{index}/100 seed {row["seed"]}: {row["kills_old"]} / '
                  f'{row["kills_new"]} / {kills}', flush=True)
    finally:
        game.close()
    for row in results:
        check_seed(REPLAYS / row[-2], row[1])
    if len({row[-1] for row in results}) != 100:
        raise ValueError('Repeated frame fingerprints')
    columns = ['seed', 'engine_seed']
    for version in ('continuous', 'outline', 'fixed'):
        columns.extend(f'{field}_{version}' for field in
                       ('kills', 'tics', 'spent', 'off_target', 'out_of_ammo_tic', 'replay'))
    with (ROOT / 'comparison_three.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([*columns, 'frames_sha256_fixed'])
        writer.writerows(results)


if __name__ == '__main__':
    main()
