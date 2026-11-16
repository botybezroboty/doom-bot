"""Comparison of the frozen versions; the held-out seeds serve only for evaluation."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__':
    run_on_hidden_desktop()

import argparse
import csv
import hashlib
import importlib
import json
import statistics
from pathlib import Path

import vizdoom as vzd
from check_all import check_artifacts, verify_exit

ROOT = Path(__file__).resolve().parent
FIELDS = ['set', 'version', 'seed', 'engine_seed', 'outcome', 'tics',
          'exit_verified', 'replay']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seeds(group):
    if group == 'heldout':
        return json.loads((ROOT/'seeds_reliability_heldout.json').read_text())
    return [(int(r['seed']), int(r['engine_seed'])) for r in
            csv.DictReader((ROOT/'comparison_navigation.csv').open(encoding='utf-8'))
            if r['version'] == 'after']


def inspect(row):
    row = dict(row)
    for field in ('seed', 'engine_seed', 'tics'):
        row[field] = int(row[field])
    path = ROOT/'replays'/(row['replay']+'.lmp')
    check_artifacts(path, row['engine_seed'])
    with path.with_suffix('.jsonl').open(encoding='utf-8') as stream:
        header = json.loads(next(stream))
        for line in stream:
            end = json.loads(line)
    if (header['seed'] != row['seed'] or header['engine_seed'] != row['engine_seed']
            or header['skill'] != 3 or end['type'] != 'end'
            or end['tic'] != row['tics'] or end['outcome'] != row['outcome']):
        raise RuntimeError(f'Log does not match: {path}')
    if row['outcome'] == 'exit':
        verify_exit(row)
    elif row['outcome'] not in ('death', 'timeout'):
        raise RuntimeError(f'Unknown outcome: {row}')
    elif row['outcome'] == 'death' and end['health'] > 0:
        raise RuntimeError(f'No death: {path}')
    elif row['outcome'] == 'timeout' and row['tics'] < 3499:
        raise RuntimeError(f'No timeout: {path}')
    row['exit_verified'] = int(row['outcome'] == 'exit')
    return {key: row[key] for key in FIELDS}


def write(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def check_freeze():
    manifest = json.loads((ROOT/'reliability_freeze.json').read_text(encoding='utf-8'))
    for name, expected in manifest['sha256'].items():
        if digest(ROOT/name) != expected:
            raise RuntimeError(f'File changed after the freeze: {name}')
    if manifest['vizdoom'] != vzd.__version__:
        raise RuntimeError('Different ViZDoom version')
    if manifest['freedoom_sha256'] != digest(Path(vzd.install_path)/'freedoom2.wad'):
        raise RuntimeError('Different Freedoom version')


def play(group, version):
    check_freeze()
    module = importlib.import_module('bot' if version == 'after' else 'bot_before_reliability')
    path = ROOT/f'reliability_{group}_{version}.csv'
    rows = list(csv.DictReader(path.open(encoding='utf-8'))) if path.exists() else []
    pairs = seeds(group)
    if [(int(r['seed']), int(r['engine_seed'])) for r in rows] != [tuple(p) for p in pairs[:len(rows)]]:
        raise RuntimeError('Wrong results list to resume')
    for seed, engine in pairs[len(rows):]:
        check_freeze()
        row = module.run(seed)
        if row['engine_seed'] != engine:
            raise RuntimeError('Different engine seed')
        row.update(set=group, version=version)
        rows.append(inspect(row))
        write(path, rows)
        print(group, version, len(rows), '/', len(pairs), flush=True)


def known(selected_version):
    """Check the existing trials of exactly the same frozen versions."""
    check_freeze()
    old = [r for r in csv.DictReader((ROOT/'comparison_navigation.csv').open(encoding='utf-8'))
           if r['version'] == 'after']
    new = json.loads((ROOT/'reliability_trials_stage3.json').read_text(encoding='utf-8'))
    expected = [tuple(p) for p in seeds('known')]
    for version, source in [('before', old), ('after', new)]:
        if version != selected_version:
            continue
        if [(int(r['seed']), int(r['engine_seed'])) for r in source] != expected:
            raise RuntimeError('Incomplete set of 80 seeds')
        rows = []
        for r in source:
            rows.append(inspect({**r, 'set': 'known', 'version': version}))
            print('Verifying known', version, len(rows), '/ 80', flush=True)
        write(ROOT/f'reliability_known_{version}.csv', rows)


def summary():
    check_freeze()
    all_rows = []
    for group in ('known', 'heldout'):
        for version in ('before', 'after'):
            path = ROOT/f'reliability_{group}_{version}.csv'
            rows = list(csv.DictReader(path.open(encoding='utf-8')))
            if [(int(r['seed']), int(r['engine_seed'])) for r in rows] != [tuple(p) for p in seeds(group)]:
                raise RuntimeError(f'Incomplete results: {path}')
            wins = [int(r['tics']) for r in rows if r['outcome'] == 'exit']
            print(group, version, 'exits', len(wins), 'deaths', sum(r['outcome']=='death' for r in rows),
                  'timeouts', sum(r['outcome']=='timeout' for r in rows),
                  'median', statistics.median(wins) if wins else None,
                  'maximum', max(wins) if wins else None,
                  'under 3027', sum(t < 3027 for t in wins), flush=True)
            all_rows.extend(rows)
    write(ROOT/'comparison_reliability.csv', all_rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['known', 'play', 'summarize'])
    parser.add_argument('--set', choices=['known', 'heldout'], default='heldout')
    parser.add_argument('--version', choices=['before', 'after'], default='after')
    args = parser.parse_args()
    if args.mode == 'known':
        known(args.version)
    elif args.mode == 'play':
        play(args.set, args.version)
    else:
        summary()
