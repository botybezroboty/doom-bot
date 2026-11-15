"""Próby rozwojowe MAP01 z ochroną odłożonego zestawu."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__':
    uruchom_na_ukrytym_pulpicie()

import argparse
import csv
import hashlib
import json
from pathlib import Path
import bot

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lista', type=Path)
    parser.add_argument('--wyniki', type=Path, default=Path('proby_niezawodnosc.json'))
    parser.add_argument('seeds', nargs='*', type=int)
    args = parser.parse_args()
    seeds = args.seeds or ([int(pair[0]) for pair in json.loads(args.lista.read_text())]
                          if args.lista else [int(r['seed']) for r in csv.DictReader(
                              (ROOT/'porownanie_nawigacja.csv').open(encoding='utf-8')) if r['wersja']=='po'])
    held = json.loads((ROOT/'seedy_niezawodnosc_odlozone.json').read_text())
    if set(seeds) & {pair[0] for pair in held}:
        raise ValueError('Odłożonych seedów nie wolno używać do strojenia')
    args.wyniki.with_suffix('.sha256').write_text(hashlib.sha256((ROOT/'bot.py').read_bytes()).hexdigest()+'\n')
    rows = []
    for seed in seeds:
        rows.append(bot.run(seed))
        args.wyniki.write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
