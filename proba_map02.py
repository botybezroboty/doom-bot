"""Ten sam bot na MAP02: zmiana wyłącznie mapy i nazw artefaktów."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__':
    uruchom_na_ukrytym_pulpicie()

import csv
import hashlib
import json
import types
from pathlib import Path

from sprawdz_wszystko import check_artifacts, fresh_seeds

ROOT = Path(__file__).resolve().parent


def main():
    source = (ROOT/'bot.py').read_bytes()
    fingerprint = hashlib.sha256(source).hexdigest()
    expected = json.loads((ROOT/'zamrozenie_niezawodnosc.json').read_text(encoding='utf-8'))['sha256']['bot.py']
    assert fingerprint == expected, 'Bot zmieniony od porównania MAP01'
    code = source.decode('utf-8')
    changes = {"game.set_doom_map('MAP01')": "game.set_doom_map('MAP02')",
               "f'map01_{version}_": "f'map02_{version}_"}
    for before, after in changes.items():
        assert code.count(before) == 1
        code = code.replace(before, after)
    module = types.ModuleType('eksperyment_map02')
    module.__file__ = str(ROOT/'bot.py')
    exec(compile(code, module.__file__, 'exec'), module.__dict__)
    seed_path = ROOT/'seedy_map02.json'
    if not seed_path.exists():
        seed_path.write_text(json.dumps(fresh_seeds(), indent=2)+'\n', encoding='utf-8')
    seeds = json.loads(seed_path.read_text(encoding='utf-8'))
    assert len(seeds) == len({pair[1] for pair in seeds}) == 20
    manifest = {'mapa':'MAP02', 'trudnosc':3, 'limit':3500, 'start':'nowa gra, bez ekwipunku z MAP01',
                'bot_sha256':fingerprint, 'zmiany_konfiguracji':changes,
                'vizdoom':module.vzd.__version__}
    (ROOT/'manifest_map02.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    rows = []
    with (ROOT/'wyniki_map02.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['mapa','wersja','seed','seed_silnika','wynik','tiki','powtorka'])
        writer.writeheader()
        for seed, engine in seeds:
            assert hashlib.sha256((ROOT/'bot.py').read_bytes()).hexdigest() == fingerprint
            row = module.run(seed)
            assert row['seed_silnika'] == engine
            check_artifacts(ROOT/'powtorki'/(row['powtorka']+'.lmp'), engine)
            row['mapa'] = 'MAP02'
            writer.writerow(row)
            stream.flush()
            rows.append(row)
    assert (ROOT/'bot.py').read_bytes() == source
    print('MAP02:', {outcome:sum(r['wynik']==outcome for r in rows)
                      for outcome in ('wyjscie','zgon','limit')}, flush=True)


if __name__ == '__main__':
    main()
