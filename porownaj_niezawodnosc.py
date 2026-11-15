"""Porównanie zamrożonych wersji; odłożone seedy służą tylko ocenie."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__':
    uruchom_na_ukrytym_pulpicie()

import argparse
import csv
import hashlib
import importlib
import json
import statistics
from pathlib import Path

import vizdoom as vzd
from sprawdz_wszystko import check_artifacts, verify_exit

ROOT = Path(__file__).resolve().parent
FIELDS = ['seria', 'wersja', 'seed', 'seed_silnika', 'wynik', 'tiki',
          'wyjscie_zweryfikowane', 'powtorka']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seeds(group):
    if group == 'odlozone':
        return json.loads((ROOT/'seedy_niezawodnosc_odlozone.json').read_text())
    return [(int(r['seed']), int(r['seed_silnika'])) for r in
            csv.DictReader((ROOT/'porownanie_nawigacja.csv').open(encoding='utf-8'))
            if r['wersja'] == 'po']


def inspect(row):
    row = dict(row)
    for field in ('seed', 'seed_silnika', 'tiki'):
        row[field] = int(row[field])
    path = ROOT/'powtorki'/(row['powtorka']+'.lmp')
    check_artifacts(path, row['seed_silnika'])
    with path.with_suffix('.jsonl').open(encoding='utf-8') as stream:
        header = json.loads(next(stream))
        for line in stream:
            end = json.loads(line)
    if (header['seed'] != row['seed'] or header['seed_silnika'] != row['seed_silnika']
            or header['trudnosc'] != 3 or end['typ'] != 'koniec'
            or end['tik'] != row['tiki'] or end['wynik'] != row['wynik']):
        raise RuntimeError(f'Niezgodny dziennik: {path}')
    if row['wynik'] == 'wyjscie':
        verify_exit(row)
    elif row['wynik'] not in ('zgon', 'limit'):
        raise RuntimeError(f'Nieznany wynik: {row}')
    elif row['wynik'] == 'zgon' and end['zycie'] > 0:
        raise RuntimeError(f'Brak śmierci: {path}')
    elif row['wynik'] == 'limit' and row['tiki'] < 3499:
        raise RuntimeError(f'Brak limitu: {path}')
    row['wyjscie_zweryfikowane'] = int(row['wynik'] == 'wyjscie')
    return {key: row[key] for key in FIELDS}


def write(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def check_freeze():
    manifest = json.loads((ROOT/'zamrozenie_niezawodnosc.json').read_text(encoding='utf-8'))
    for name, expected in manifest['sha256'].items():
        if digest(ROOT/name) != expected:
            raise RuntimeError(f'Plik zmieniony po zamrożeniu: {name}')
    if manifest['vizdoom'] != vzd.__version__:
        raise RuntimeError('Inna wersja ViZDoom')
    if manifest['freedoom_sha256'] != digest(Path(vzd.install_path)/'freedoom2.wad'):
        raise RuntimeError('Inna wersja Freedoom')


def play(group, version):
    check_freeze()
    module = importlib.import_module('bot' if version == 'po' else 'bot_przed_niezawodnoscia')
    path = ROOT/f'niezawodnosc_{group}_{version}.csv'
    rows = list(csv.DictReader(path.open(encoding='utf-8'))) if path.exists() else []
    pairs = seeds(group)
    if [(int(r['seed']), int(r['seed_silnika'])) for r in rows] != [tuple(p) for p in pairs[:len(rows)]]:
        raise RuntimeError('Niewłaściwa lista wyników do wznowienia')
    for seed, engine in pairs[len(rows):]:
        check_freeze()
        row = module.run(seed)
        if row['seed_silnika'] != engine:
            raise RuntimeError('Inny seed silnika')
        row.update(seria=group, wersja=version)
        rows.append(inspect(row))
        write(path, rows)
        print(group, version, len(rows), '/', len(pairs), flush=True)


def known(selected_version):
    """Sprawdź istniejące próby dokładnie tych samych zamrożonych wersji."""
    check_freeze()
    old = [r for r in csv.DictReader((ROOT/'porownanie_nawigacja.csv').open(encoding='utf-8'))
           if r['wersja'] == 'po']
    new = json.loads((ROOT/'proby_niezawodnosc_etap3.json').read_text(encoding='utf-8'))
    expected = [tuple(p) for p in seeds('znane')]
    for version, source in [('przed', old), ('po', new)]:
        if version != selected_version:
            continue
        if [(int(r['seed']), int(r['seed_silnika'])) for r in source] != expected:
            raise RuntimeError('Niekompletny zestaw 80 seedów')
        rows = []
        for r in source:
            rows.append(inspect({**r, 'seria': 'znane', 'wersja': version}))
            print('Weryfikacja znane', version, len(rows), '/ 80', flush=True)
        write(ROOT/f'niezawodnosc_znane_{version}.csv', rows)


def summary():
    check_freeze()
    all_rows = []
    for group in ('znane', 'odlozone'):
        for version in ('przed', 'po'):
            path = ROOT/f'niezawodnosc_{group}_{version}.csv'
            rows = list(csv.DictReader(path.open(encoding='utf-8')))
            if [(int(r['seed']), int(r['seed_silnika'])) for r in rows] != [tuple(p) for p in seeds(group)]:
                raise RuntimeError(f'Niekompletne wyniki: {path}')
            wins = [int(r['tiki']) for r in rows if r['wynik'] == 'wyjscie']
            print(group, version, 'wyjścia', len(wins), 'zgony', sum(r['wynik']=='zgon' for r in rows),
                  'limity', sum(r['wynik']=='limit' for r in rows),
                  'mediana', statistics.median(wins) if wins else None,
                  'maksimum', max(wins) if wins else None,
                  'poniżej 3027', sum(t < 3027 for t in wins), flush=True)
            all_rows.extend(rows)
    write(ROOT/'porownanie_niezawodnosc.csv', all_rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tryb', choices=['znane', 'graj', 'podsumuj'])
    parser.add_argument('--seria', choices=['znane', 'odlozone'], default='odlozone')
    parser.add_argument('--wersja', choices=['przed', 'po'], default='po')
    args = parser.parse_args()
    if args.tryb == 'znane':
        known(args.wersja)
    elif args.tryb == 'graj':
        play(args.seria, args.wersja)
    else:
        summary()
