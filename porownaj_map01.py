"""Porównanie starej i nowej wersji na tych samych seedach silnika."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__':
    uruchom_na_ukrytym_pulpicie()
import csv
import argparse
from pathlib import Path
import numpy as np
from bot import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tylko-nowy", action="store_true")
    args = parser.parse_args()
    seeds = []
    used = set()
    for seed in range(10000):
        engine = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
        if 0 < engine < 2**31 - 1 and engine not in used:
            seeds.append(seed)
            used.add(engine)
        if len(seeds) == 20:
            break
    path = Path(__file__).with_name('porownanie_map01.csv')
    old = {}
    if args.tylko_nowy:
        with path.open(encoding='utf-8', newline='') as file:
            old = {int(r['seed']): r for r in csv.DictReader(file) if r['wersja'] == 'stary'}
        if set(old) != set(seeds):
            raise ValueError('Brak pełnych wyników starej wersji')
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['wersja', 'seed', 'seed_silnika', 'wynik', 'tiki', 'powtorka'])
        writer.writeheader()
        for seed in seeds:
            for version in ('stary', 'nowy'):
                writer.writerow(old[seed] if args.tylko_nowy and version == 'stary' else run(seed, version))
                file.flush()


if __name__ == '__main__':
    main()
