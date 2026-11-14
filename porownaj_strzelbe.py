"""Porównanie poprawki strzelby i wyjścia na dwóch zestawach po 20 seedów."""
from ukryte_okno import uruchom_na_ukrytym_pulpicie
if __name__ == '__main__':
    uruchom_na_ukrytym_pulpicie()

import csv
import json
import statistics
from pathlib import Path
import vizdoom as vzd
import bot
import bot_przed_poprawka as old
from defend_the_center import dokladny_zegar
from sprawdz_wszystko import fresh_seeds, check_artifacts, verify_exit

ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / 'powtorki'
FIELDS = ['seria', 'wersja', 'seed', 'seed_silnika', 'wynik', 'tiki', 'strzelba', 'wybrana_strzelba', 'tiki_przy_wyjsciu', 'powtorka']


def inspect(row):
    path = REPLAYS / (row['powtorka'] + '.lmp')
    check_artifacts(path, int(row['seed_silnika']))
    log = [json.loads(s) for s in path.with_suffix('.jsonl').read_text(encoding='utf-8').splitlines()]
    if log[-1]['wynik'] != row['wynik'] or int(log[-1]['tik']) != int(row['tiki']):
        raise ValueError(f'Niezgodny dziennik {path}')
    exit_ticks = ''
    if row['wynik'] == 'wyjscie':
        ticks = [x for x in log[-6:-1] if x.get('typ') == 'tik']
        if not any(x['akcja'][3] and 130 <= x['x'] <= 302 and -720 <= x['y'] <= -632
                   and 25 <= x['kat'] <= 155 for x in ticks):
            raise RuntimeError(f'Brak użycia przełącznika w {path}')
        arrivals = [q['tik'] for q in log if q.get('typ') == 'tik' and q['cel'] == 21]
        if arrivals:
            exit_ticks = int(row['tiki']) - arrivals[0] + 1
    # Odtworzenie mierzy również stan broni starej wersji, której dziennik go nie zapisywał.
    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / 'freedoom2.wad'))
    game.set_doom_map('MAP01')
    game.set_window_visible(False)
    game.init()
    own = selected = False
    count = 0
    try:
        game.replay_episode(str(path).replace('\\', '/'))
        with dokladny_zegar():
            while not game.is_episode_finished() and count < int(row['tiki']):
                own |= bool(game.get_game_variable(vzd.GameVariable.WEAPON3))
                selected |= int(game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON)) == 3
                game.advance_action()
                count += 1
        if row['wynik'] == 'wyjscie' and (not game.is_episode_finished() or
                game.get_game_variable(vzd.GameVariable.DEATHCOUNT) != 0 or
                game.get_game_variable(vzd.GameVariable.HEALTH) <= 0):
            raise RuntimeError(f'Powtórka nie potwierdza wyjścia: {path}')
    finally:
        game.close()
    if count != int(row['tiki']):
        raise RuntimeError(f'Niezgodny czas powtórki {path}: {count} != {row["tiki"]}')
    return int(own), int(selected), exit_ticks


def main():
    proof = list(csv.DictReader((ROOT / 'dowod_map01.csv').open(encoding='utf-8', newline='')))
    if len(proof) != 20 or len({r['seed_silnika'] for r in proof}) != 20:
        raise ValueError('Nieprawidłowa seria dowodowa')
    newseeds = json.loads((ROOT / 'seedy_strzelba.json').read_text(encoding='utf-8'))  # Zamrożone przed seriami.
    print('Nowe seedy:', newseeds, flush=True)
    out = ROOT / 'porownanie_strzelba.csv'
    rows = []
    with out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        def save(group, version, row):
            own, selected, exit_ticks = inspect(row)
            result = {'seria': group, 'wersja': version, 'seed': row['seed'],
                      'seed_silnika': row['seed_silnika'], 'wynik': row['wynik'],
                      'tiki': row['tiki'], 'strzelba': own, 'wybrana_strzelba': selected,
                      'tiki_przy_wyjsciu': exit_ticks, 'powtorka': row['powtorka']}
            writer.writerow(result)
            f.flush()
            rows.append(result)
            print(group, version, row['seed'], row['wynik'], row['tiki'], 'strzelba', own,
                  'wybrana', selected, 'wyjście', exit_ticks, flush=True)
        for row in proof:
            save('dowod', 'przed', row)
            save('dowod', 'po', bot.run(int(row['seed'])))
        for seed, engine in newseeds:
            save('nowe', 'przed', old.run(seed))
            save('nowe', 'po', bot.run(seed))
    for group in ('dowod', 'nowe'):
        for version in ('przed', 'po'):
            a = [r for r in rows if r['seria'] == group and r['wersja'] == version]
            wins = [r for r in a if r['wynik'] == 'wyjscie']
            med = statistics.median(int(r['tiki']) for r in wins) if wins else None
            exit_med = statistics.median(int(r['tiki_przy_wyjsciu']) for r in wins if r['tiki_przy_wyjsciu'] != '') if wins else None
            print(group, version, 'wyjścia',len(wins),'zgony',sum(r['wynik']=='zgon' for r in a),
                  'limity',sum(r['wynik']=='limit' for r in a),'mediana',med,
                  'strzelby',sum(r['strzelba'] for r in a),'wybrane',sum(r['wybrana_strzelba'] for r in a),
                  'mediana przy wyjściu',exit_med, flush=True)

if __name__ == '__main__':
    main()
