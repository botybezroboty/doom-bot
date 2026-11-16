"""Comparison of the shotgun and exit fix on two sets of 20 seeds."""
from hidden_desktop import run_on_hidden_desktop
if __name__ == '__main__':
    run_on_hidden_desktop()

import csv
import json
import statistics
from pathlib import Path
import vizdoom as vzd
import bot
import bot_before_fix as old
from defend_the_center import precise_timer
from check_all import fresh_seeds, check_artifacts, verify_exit

ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / 'replays'
FIELDS = ['set', 'version', 'seed', 'engine_seed', 'outcome', 'tics', 'shotgun', 'shotgun_selected', 'tics_at_exit', 'replay']


def inspect(row):
    path = REPLAYS / (row['replay'] + '.lmp')
    check_artifacts(path, int(row['engine_seed']))
    log = [json.loads(s) for s in path.with_suffix('.jsonl').read_text(encoding='utf-8').splitlines()]
    if log[-1]['outcome'] != row['outcome'] or int(log[-1]['tic']) != int(row['tics']):
        raise ValueError(f'Log does not match {path}')
    exit_ticks = ''
    if row['outcome'] == 'exit':
        ticks = [x for x in log[-6:-1] if x.get('type') == 'tic']
        if not any(x['action'][3] and 130 <= x['x'] <= 302 and -720 <= x['y'] <= -632
                   and 25 <= x['angle'] <= 155 for x in ticks):
            raise RuntimeError(f'No use of the switch in {path}')
        arrivals = [q['tic'] for q in log if q.get('type') == 'tic' and q['waypoint'] == 21]
        if arrivals:
            exit_ticks = int(row['tics']) - arrivals[0] + 1
    # The replay also measures the weapon state of the old version, whose log did not record it.
    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / 'freedoom2.wad'))
    game.set_doom_map('MAP01')
    game.set_window_visible(False)
    game.init()
    own = selected = False
    count = 0
    try:
        game.replay_episode(str(path).replace('\\', '/'))
        with precise_timer():
            while not game.is_episode_finished() and count < int(row['tics']):
                own |= bool(game.get_game_variable(vzd.GameVariable.WEAPON3))
                selected |= int(game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON)) == 3
                game.advance_action()
                count += 1
        if row['outcome'] == 'exit' and (not game.is_episode_finished() or
                game.get_game_variable(vzd.GameVariable.DEATHCOUNT) != 0 or
                game.get_game_variable(vzd.GameVariable.HEALTH) <= 0):
            raise RuntimeError(f'The replay does not confirm the exit: {path}')
    finally:
        game.close()
    if count != int(row['tics']):
        raise RuntimeError(f'Replay length does not match {path}: {count} != {row["tics"]}')
    return int(own), int(selected), exit_ticks


def main():
    proof = list(csv.DictReader((ROOT / 'proof_map01.csv').open(encoding='utf-8', newline='')))
    if len(proof) != 20 or len({r['engine_seed'] for r in proof}) != 20:
        raise ValueError('Invalid proof set')
    newseeds = json.loads((ROOT / 'seeds_shotgun.json').read_text(encoding='utf-8'))  # Frozen before the series.
    print('New seeds:', newseeds, flush=True)
    out = ROOT / 'comparison_shotgun.csv'
    rows = []
    with out.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        def save(group, version, row):
            own, selected, exit_ticks = inspect(row)
            result = {'set': group, 'version': version, 'seed': row['seed'],
                      'engine_seed': row['engine_seed'], 'outcome': row['outcome'],
                      'tics': row['tics'], 'shotgun': own, 'shotgun_selected': selected,
                      'tics_at_exit': exit_ticks, 'replay': row['replay']}
            writer.writerow(result)
            f.flush()
            rows.append(result)
            print(group, version, row['seed'], row['outcome'], row['tics'], 'shotgun', own,
                  'selected', selected, 'exit', exit_ticks, flush=True)
        for row in proof:
            save('proof', 'before', row)
            save('proof', 'after', bot.run(int(row['seed'])))
        for seed, engine in newseeds:
            save('new', 'before', old.run(seed))
            save('new', 'after', bot.run(seed))
    for group in ('proof', 'new'):
        for version in ('before', 'after'):
            a = [r for r in rows if r['set'] == group and r['version'] == version]
            wins = [r for r in a if r['outcome'] == 'exit']
            med = statistics.median(int(r['tics']) for r in wins) if wins else None
            exit_med = statistics.median(int(r['tics_at_exit']) for r in wins if r['tics_at_exit'] != '') if wins else None
            print(group, version, 'exits',len(wins),'deaths',sum(r['outcome']=='death' for r in a),
                  'timeouts',sum(r['outcome']=='timeout' for r in a),'median',med,
                  'shotguns',sum(r['shotgun'] for r in a),'selected',sum(r['shotgun_selected'] for r in a),
                  'median at exit',exit_med, flush=True)

if __name__ == '__main__':
    main()
