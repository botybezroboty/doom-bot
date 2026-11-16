"""Development trials on MAP01 that protect the held-out set."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__':
    run_on_hidden_desktop()

import argparse
import csv
import hashlib
import json
from pathlib import Path
import bot

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', type=Path)
    parser.add_argument('--results', type=Path, default=Path('reliability_trials.json'))
    parser.add_argument('seeds', nargs='*', type=int)
    args = parser.parse_args()
    seeds = args.seeds or ([int(pair[0]) for pair in json.loads(args.list.read_text())]
                          if args.list else [int(r['seed']) for r in csv.DictReader(
                              (ROOT/'comparison_navigation.csv').open(encoding='utf-8')) if r['version']=='after'])
    held = json.loads((ROOT/'seeds_reliability_heldout.json').read_text())
    if set(seeds) & {pair[0] for pair in held}:
        raise ValueError('Held-out seeds must not be used for tuning')
    args.results.with_suffix('.sha256').write_text(hashlib.sha256((ROOT/'bot.py').read_bytes()).hexdigest()+'\n')
    rows = []
    for seed in seeds:
        rows.append(bot.run(seed))
        args.results.write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
