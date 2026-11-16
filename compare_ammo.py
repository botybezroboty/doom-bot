"""Compare the current bot with the set from comparison_demons.csv."""

if __name__ == '__main__':
    from hidden_desktop import run_on_hidden_desktop
    run_on_hidden_desktop()
import csv
import json
from pathlib import Path

from defend_the_center import FRAME_WIDTH, REPLAYS, ROOT, TARGET_LABELS, create_game, run_episode


def analyze(path):
    with path.with_suffix('.jsonl').open(encoding='utf-8') as file:
        records = [json.loads(line) for line in file]
    ticks = [row for row in records if row['type'] == 'tic']
    end = records[-1]
    spent = outside = 0
    empty = None
    for current, following in zip(ticks, ticks[1:] + [end]):
        used = max(0, int(current['ammo'] - following['ammo']))
        spent += used
        centered = any(label['name'] in TARGET_LABELS and label['width'] > 0
                       and label['x'] <= FRAME_WIDTH / 2 < label['x'] + label['width']
                       for label in current['labels'])
        if not centered:
            outside += used
        if empty is None and following['ammo'] == 0:
            empty = following['tic']
    return spent, outside, empty


def check_seed(path, expected):
    data = path.read_bytes()
    if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
        raise ValueError(f'Unknown replay format: {path}')
    end = data.index(b'\0', 24) + 1
    if int.from_bytes(data[end:end + 4], 'big') != int(expected):
        raise ValueError(f'Seed does not match: {path}')


def main():
    with (ROOT / 'comparison_demons.csv').open(encoding='utf-8', newline='') as file:
        old = list(csv.DictReader(file))
    if len(old) != 100 or len({row['engine_seed'] for row in old}) != 100:
        raise ValueError('Needs a set of 100 different seeds')
    for row in old:
        path = REPLAYS / row['replay_new']
        check_seed(path, row['engine_seed'])
        analyze(path)
    results = []
    game = create_game()
    deaths = 0
    try:
        for index, previous in enumerate(old, 1):
            (kills, death, reward, ticks), replay, fingerprint = run_episode(
                game, int(previous['seed']), deaths, False)
            deaths += death
            prior = analyze(REPLAYS / previous['replay_new'])
            current = analyze(replay)
            results.append([previous['seed'], previous['engine_seed'], previous['kills_new'],
                            kills, previous['tics_new'], ticks, *prior, *current,
                            previous['replay_new'], replay.name, fingerprint])
            print(f'{index}/100 seed {previous["seed"]}: {previous["kills_new"]} -> {kills}', flush=True)
    finally:
        game.close()
    for row in results:
        check_seed(REPLAYS / row[-2], row[1])
    if len({row[-1] for row in results}) != 100:
        raise ValueError('Repeated frame fingerprints')
    with (ROOT / 'comparison_ammo.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['seed', 'engine_seed', 'kills_old', 'kills_new',
                         'tics_old', 'tics_new', 'spent_old', 'off_target_old',
                         'out_of_ammo_tic_old', 'spent_new', 'off_target_new',
                         'out_of_ammo_tic_new', 'replay_old', 'replay_new', 'frames_sha256_new'])
        writer.writerows(results)


if __name__ == '__main__':
    main()
