"""The same bot on MAP02: only the map and the artifact names change."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__':
    run_on_hidden_desktop()

import csv
import hashlib
import json
import types
from pathlib import Path

from check_all import check_artifacts, fresh_seeds

ROOT = Path(__file__).resolve().parent


def main():
    source = (ROOT/'bot.py').read_bytes()
    fingerprint = hashlib.sha256(source).hexdigest()
    expected = json.loads((ROOT/'reliability_freeze.json').read_text(encoding='utf-8'))['sha256']['bot.py']
    assert fingerprint == expected, 'The bot changed since the MAP01 comparison'
    code = source.decode('utf-8')
    changes = {"game.set_doom_map('MAP01')": "game.set_doom_map('MAP02')",
               "f'map01_{version}_": "f'map02_{version}_"}
    for before, after in changes.items():
        assert code.count(before) == 1
        code = code.replace(before, after)
    module = types.ModuleType('experiment_map02')
    module.__file__ = str(ROOT/'bot.py')
    exec(compile(code, module.__file__, 'exec'), module.__dict__)
    seed_path = ROOT/'seeds_map02.json'
    if not seed_path.exists():
        seed_path.write_text(json.dumps(fresh_seeds(), indent=2)+'\n', encoding='utf-8')
    seeds = json.loads(seed_path.read_text(encoding='utf-8'))
    assert len(seeds) == len({pair[1] for pair in seeds}) == 20
    manifest = {'map':'MAP02', 'skill':3, 'tic_limit':3500, 'start':'new game, no equipment from MAP01',
                'bot_sha256':fingerprint, 'config_changes':changes,
                'vizdoom':module.vzd.__version__}
    (ROOT/'map02_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    rows = []
    with (ROOT/'results_map02.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['map','version','seed','engine_seed','outcome','tics','replay'])
        writer.writeheader()
        for seed, engine in seeds:
            assert hashlib.sha256((ROOT/'bot.py').read_bytes()).hexdigest() == fingerprint
            row = module.run(seed)
            assert row['engine_seed'] == engine
            check_artifacts(ROOT/'replays'/(row['replay']+'.lmp'), engine)
            row['map'] = 'MAP02'
            writer.writerow(row)
            stream.flush()
            rows.append(row)
    assert (ROOT/'bot.py').read_bytes() == source
    print('MAP02:', {outcome:sum(r['outcome']==outcome for r in rows)
                      for outcome in ('exit','death','timeout')}, flush=True)


if __name__ == '__main__':
    main()
