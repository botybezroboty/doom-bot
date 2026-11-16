"""Navigation through the known MAP01, steered by the player's position."""

if __name__ == '__main__':
    from hidden_desktop import run_on_hidden_desktop
    run_on_hidden_desktop()
import argparse
import json
import math
import os
from datetime import datetime
from collections import deque
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
import vizdoom as vzd
import numpy as np
from defend_the_center import precise_timer
from video import Video

ROOT = Path(__file__).resolve().parent
ROUTE = [(650, -160), (770, -160), (1100, 120), (1380, 120), (1390, -200), (1780, -160), (1900, -160), (1950, -400), (1850, -800), (1600, -800), (1400, -800), (1100, -1024), (900, -1024),
         (750, -1024), (550, -1024), (400, -1024), (216, -800), (216, -675)]


# Item points from the map: shotgun/ammo, medkits and the green armor.
# The route stays based on position, not on time or recorded moves.
ROUTE_NEW = [(650, -160), (770, -160), (1088, 304), (1088, 368),
             (1100, 120), (1380, 120), (1390, -200), (1780, -160), (1900, -160), (1950, -400),
             (1816, -728), (1900, -728), (1900, -800), (1600, -800), (1400, -800),
             (1100, -1024), (900, -1024), (750, -1024), (550, -1024),
             (400, -1024), (216, -800), (216, -675)]
MONSTERS = {'ZombieMan', 'ShotgunGuy', 'DoomImp', 'Demon', 'Spectre',
            'ChaingunGuy', 'MarineChainsawVzd', 'Zombieman'}


def combat(state):
    # A label must have real pixels in the buffer of visible objects.
    candidates = [a for a in state.labels if a.object_name in MONSTERS
                  and a.width > 0 and (state.labels_buffer == a.value).any()]
    if not candidates:
        return None
    target = min(candidates, key=lambda a: (abs(a.x + a.width / 2 - 160) / max(a.width, 1), -a.width))
    err = target.x + target.width / 2 - 160
    turn = max(-12, min(12, err * 0.18))
    fire = int(target.x <= 160 < target.x + target.width)
    return [0 if target.width > 32 else 100, turn, 1, 0, fire], target


def action(x, y, angle, target, tick):
    dx, dy = target[0] - x, target[1] - y
    desired = math.degrees(math.atan2(dy, dx)) % 360
    error = (desired - angle + 180) % 360 - 180
    # Steering relies on the current position, not on an order of moves.
    turn = max(-15, min(15, -error))
    return [100 if abs(error) < 55 else 0, turn, 1, int(tick % 12 == 0)]


def run(seed, version="new"):
    route = ROUTE if version == "old" else ROUTE_NEW
    engine_seed = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
    if not 0 < engine_seed < 2**31 - 1:
        raise ValueError(f'Seed {seed} makes Windows truncate the engine seed')
    folder = ROOT / 'replays'
    folder.mkdir(exist_ok=True)
    path = folder / f'map01_{version}_{seed}_{datetime.now():%Y%m%d_%H%M%S_%f}'
    game = vzd.DoomGame()

    game.set_doom_game_path(str(Path(vzd.install_path) / 'freedoom2.wad'))
    game.set_doom_map('MAP01')
    game.set_doom_skill(3)
    game.set_window_visible(False)
    game.set_sound_enabled(False)
    game.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_render_hud(True)
    game.set_render_minimal_hud(False)
    game.set_labels_buffer_enabled(True)
    game.set_episode_timeout(3500)
    game.set_available_buttons([vzd.Button.MOVE_FORWARD_BACKWARD_DELTA, vzd.Button.TURN_LEFT_RIGHT_DELTA, vzd.Button.SPEED, vzd.Button.USE, vzd.Button.ATTACK])
    game.set_available_game_variables([vzd.GameVariable.POSITION_X, vzd.GameVariable.POSITION_Y, vzd.GameVariable.ANGLE, vzd.GameVariable.HEALTH, vzd.GameVariable.ARMOR, vzd.GameVariable.SELECTED_WEAPON_AMMO, vzd.GameVariable.KILLCOUNT])
    game.init()
    game.set_seed(seed)
    video = None
    try:
        game.new_episode(str(path.with_suffix('.lmp')).replace('\\', '/'))
        video = Video(path.with_suffix('.mp4'), 320, 240)
        with path.with_suffix('.jsonl').open('w', encoding='utf-8') as log:
            log.write(json.dumps({'type':'start', 'seed':seed, 'engine_seed':engine_seed, 'skill':3, 'version':version, 'route':route})+'\n')
            waypoint = 0
            waypoint_since = 0
            elapsed = 0
            history = deque(maxlen=60)
            escape = 0
            escape_side = 1
            with precise_timer():
                while not game.is_episode_finished() and not game.is_player_dead():
                    state = game.get_state()
                    x, y, angle, health, armor, ammo, kills = state.game_variables
                    tick = game.get_episode_time()
                    if waypoint < len(route)-1 and math.hypot(x-route[waypoint][0], y-route[waypoint][1]) < 35:
                        waypoint += 1
                        waypoint_since = elapsed
                    # The medkit is optional when it cannot be reached.
                    if version == 'new' and waypoint == 10 and elapsed - waypoint_since > 250:
                        waypoint += 1
                        waypoint_since = elapsed
                    target = route[waypoint]
                    if version == 'new':
                        history.append((x, y))
                        if not escape and len(history) == history.maxlen and math.dist(history[0], (x, y)) < 12:
                            escape = 40
                            escape_side *= -1
                            history.clear()
                        if escape:
                            dx, dy = target[0] - x, target[1] - y
                            norm = max(math.hypot(dx, dy), 1)
                            target = (x - escape_side * dy / norm * 100,
                                      y + escape_side * dx / norm * 100)
                            escape -= 1
                    cmd = action(x,y,angle,target,tick) + [0]
                    found = combat(state) if version == 'new' else None
                    if found:
                        cmd = found[0]
                    video.write(state.screen_buffer)
                    log.write(json.dumps({'type':'tic','tic':tick,'x':x,'y':y,'angle':angle,'waypoint':waypoint,'health':health,'armor':armor,'ammo':ammo,'kills':kills,'action':cmd, 'visible':[{'name':a.object_name,'x':a.x,'width':a.width} for a in state.labels if a.object_name in MONSTERS and (state.labels_buffer == a.value).any()]})+'\n')
                    game.make_action(cmd, 1)
                    elapsed += 1
            dead = game.is_player_dead() or game.get_game_variable(vzd.GameVariable.HEALTH) <= 0
            outcome = 'death' if dead else 'timeout' if elapsed >= 3499 else 'exit'
            log.write(json.dumps({'type':'end','tic':elapsed,'outcome':outcome,
                                  'health':game.get_game_variable(vzd.GameVariable.HEALTH)})+'\n')
            print(seed, outcome, elapsed, path.name, flush=True)
    finally:
        if video: video.close()
        game.close()
    data = path.with_suffix('.lmp').read_bytes()
    if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
        raise RuntimeError('Unknown replay format')
    offset = data.index(b'\0', 24) + 1
    if int.from_bytes(data[offset:offset + 4], 'big') != engine_seed:
        raise RuntimeError('The replay\'s seed differs from the expected one')
    return {'version': version, 'seed': seed, 'engine_seed': engine_seed,
            'outcome': outcome, 'tics': elapsed, 'replay': path.name}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', choices=['old', 'new'], default='new')
    parser.add_argument('seeds', nargs='+', type=int)
    args = parser.parse_args()
    for seed in args.seeds:
        run(seed, args.version)
