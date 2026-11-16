"""Compare the current bot with the saved set of the old bot on the same seeds."""

if __name__ == '__main__':
    from hidden_desktop import run_on_hidden_desktop
    run_on_hidden_desktop()
import csv
from defend_the_center import ROOT, create_game, run_episode


def main():
    with (ROOT / 'comparison.csv').open(encoding='utf-8', newline='') as f:
        old = [row for row in csv.DictReader(f) if row['bot'] == 'labels']
    if len(old) != 100 or len({row['engine_seed'] for row in old}) != 100:
        raise ValueError('Needs the earlier set of 100 different seeds')
    results = []
    game = create_game()
    deaths = 0
    try:
        for index, previous in enumerate(old, 1):
            (kills, death, reward, ticks), replay, fingerprint = run_episode(
                game, int(previous['seed']), deaths, False)
            deaths += death
            results.append([previous['seed'], previous['engine_seed'],
                            previous['kills'], kills, previous['tics'], ticks,
                            previous['replay'], replay.name, fingerprint])
            print(f'{index}/100 seed {previous["seed"]}: {previous["kills"]} -> {kills}', flush=True)
    finally:
        game.close()
    for row in results:
        for replay_name in (row[6], row[7]):
            data = (ROOT / 'replays' / replay_name).read_bytes()
            if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
                raise ValueError(f'Unknown replay format: {replay_name}')
            end = data.index(b'\0', 24) + 1
            if int.from_bytes(data[end:end + 4], 'big') != int(row[1]):
                raise ValueError(f'Seed does not match: {replay_name}')
    with (ROOT / 'comparison_demons.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed', 'engine_seed', 'kills_old', 'kills_new',
                         'tics_old', 'tics_new', 'replay_old', 'replay_new', 'frames_sha256_new'])
        writer.writerows(results)


if __name__ == '__main__':
    main()
