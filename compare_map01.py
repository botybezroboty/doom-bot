"""A comparison of the old and the new version on the same engine seeds."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__':
    run_on_hidden_desktop()
import csv
import argparse
from pathlib import Path
import numpy as np
from bot import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-only", action="store_true")
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
    path = Path(__file__).with_name('comparison_map01.csv')
    old = {}
    if args.new_only:
        with path.open(encoding='utf-8', newline='') as file:
            old = {int(r['seed']): r for r in csv.DictReader(file) if r['version'] == 'old'}
        if set(old) != set(seeds):
            raise ValueError('The old version\'s results are incomplete')
    with path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['version', 'seed', 'engine_seed', 'outcome', 'tics', 'replay'])
        writer.writeheader()
        for seed in seeds:
            for version in ('old', 'new'):
                writer.writerow(old[seed] if args.new_only and version == 'old' else run(seed, version))
                file.flush()


if __name__ == '__main__':
    main()
