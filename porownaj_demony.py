"""Porównaj aktualnego bota z zapisaną serią starego bota na tych samych seedach."""
import csv
from defend_the_center import ROOT, create_game, run_episode


def main():
    with (ROOT / 'porownanie.csv').open(encoding='utf-8', newline='') as f:
        old = [row for row in csv.DictReader(f) if row['bot'] == 'etykiety']
    if len(old) != 100 or len({row['seed_silnika'] for row in old}) != 100:
        raise ValueError('Potrzebna jest dawna seria 100 różnych seedów')
    results = []
    game = create_game()
    deaths = 0
    try:
        for index, previous in enumerate(old, 1):
            (kills, death, reward, ticks), replay, fingerprint = run_episode(
                game, int(previous['seed']), deaths, False)
            deaths += death
            results.append([previous['seed'], previous['seed_silnika'],
                            previous['zabite'], kills, previous['tiki'], ticks,
                            previous['powtorka'], replay.name, fingerprint])
            print(f'{index}/100 seed {previous["seed"]}: {previous["zabite"]} -> {kills}', flush=True)
    finally:
        game.close()
    for row in results:
        for replay_name in (row[6], row[7]):
            data = (ROOT / 'powtorki' / replay_name).read_bytes()
            if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
                raise ValueError(f'Nieznany format powtórki: {replay_name}')
            end = data.index(b'\0', 24) + 1
            if int.from_bytes(data[end:end + 4], 'big') != int(row[1]):
                raise ValueError(f'Niezgodny seed: {replay_name}')
    with (ROOT / 'porownanie_demony.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed', 'seed_silnika', 'zabite_stary', 'zabite_nowy',
                         'tiki_stary', 'tiki_nowy', 'powtorka_stary', 'powtorka_nowy', 'sha256_nowy'])
        writer.writerows(results)


if __name__ == '__main__':
    main()
