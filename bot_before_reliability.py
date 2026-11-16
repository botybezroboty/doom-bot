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
             (1100, 120), (1380, 120), (1390, -200),
             (1460, -240), (1528, -240), (1592, -240), (1656, -240), (1720, -240),
             (1720, -160), (1536, -160), (1720, -160), (1780, -160),
             (1900, -160), (1950, -400), (1816, -728), (1900, -728),
             (1900, -800), (1850, -850), (1750, -850), (1650, -850), (1600, -800), (1400, -800),
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
    game.set_available_buttons([vzd.Button.MOVE_FORWARD_BACKWARD_DELTA, vzd.Button.TURN_LEFT_RIGHT_DELTA, vzd.Button.SPEED, vzd.Button.USE, vzd.Button.ATTACK, vzd.Button.SELECT_WEAPON3])
    game.set_available_game_variables([vzd.GameVariable.POSITION_X, vzd.GameVariable.POSITION_Y, vzd.GameVariable.ANGLE, vzd.GameVariable.HEALTH, vzd.GameVariable.ARMOR, vzd.GameVariable.SELECTED_WEAPON_AMMO, vzd.GameVariable.KILLCOUNT, vzd.GameVariable.WEAPON3, vzd.GameVariable.AMMO3, vzd.GameVariable.SELECTED_WEAPON])
    game.init()
    game.set_seed(seed)
    video = None
    try:
        game.new_episode(str(path.with_suffix('.lmp')).replace('\\', '/'))
        video = Video(path.with_suffix('.mp4'), 320, 240)
        with path.with_suffix('.jsonl').open('w', encoding='utf-8') as log:
            log.write(json.dumps({'type':'start', 'seed':seed, 'engine_seed':engine_seed, 'skill':3, 'version':version, 'route':route})+'\n')
            waypoint = 0
            med_index = route.index((1816, -728)) if version == 'new' else -1
            shotgun_index = route.index((1536, -160)) if version == 'new' else -1
            stair_start = route.index((1460, -240)) if version == 'new' else -1
            stair_end = route.index((1780, -160)) if version == 'new' else -1
            waypoint_since = 0
            elapsed = 0
            history = deque(maxlen=60)
            escape = 0
            escape_side = 1
            gun_chase = 0
            gun_origin = None
            gun_cooldown = 0
            fixed_shotgun_reached = False
            stair_retries = 0
            abandon_shotgun = False
            with precise_timer():
                while not game.is_episode_finished() and not game.is_player_dead():
                    state = game.get_state()
                    x, y, angle, health, armor, ammo, kills, shotgun, shells, weapon = state.game_variables
                    tick = game.get_episode_time()
                    if version == 'new' and shotgun and math.hypot(x - 1536, y + 160) < 38:
                        fixed_shotgun_reached = True
                    if version == 'new' and waypoint == shotgun_index and (fixed_shotgun_reached or abandon_shotgun):
                        waypoint += 1
                        waypoint_since = elapsed
                    radius = 20 if version == 'new' and stair_start <= waypoint <= stair_end else 35
                    if version == 'new' and waypoint == shotgun_index and shotgun:
                        # The pickup works from about 36 units away.
                        radius = 38
                    if waypoint < len(route)-1 and math.hypot(x-route[waypoint][0], y-route[waypoint][1]) < radius:
                        waypoint += 1
                        waypoint_since = elapsed
                    # The medkit is optional when it cannot be reached.
                    if version == 'new' and waypoint == med_index and elapsed - waypoint_since > 250:
                        waypoint += 1
                        waypoint_since = elapsed
                    # After being pushed north, go back through the known corridor entrance.
                    if version == 'new' and waypoint >= med_index and x < 1820 and y > -320:
                        waypoint = route.index((1390, -200))
                        waypoint_since = elapsed
                    # After being pushed off the steps, try the known way again.
                    if version == 'new' and waypoint == shotgun_index and elapsed - waypoint_since > 180:
                        stair_retries += 1
                        abandon_shotgun = stair_retries >= 3
                        waypoint = stair_start
                        waypoint_since = elapsed
                        history.clear()
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
                    if version == 'new' and waypoint >= len(route) - 2 and -715 <= y <= -642 and (x < 200 or x > 232):
                        target = (216, -705)
                    cmd = action(x,y,angle,target,tick) + [0]
                    if gun_cooldown:
                        gun_cooldown -= 1
                    found = combat(state) if version == 'new' else None
                    if found:
                        cmd = found[0]
                    elif version == 'new' and waypoint >= len(route) - 2 and 200 <= x <= 232 and -690 <= y <= -642:
                        # Do not aim at a point behind: stop and look at the switch.
                        error = (90 - angle + 180) % 360 - 180
                        cmd = [0, max(-15, min(15, -error)), 1,
                               int(abs(error) < 15 and tick % 2 == 0), 0]
                    elif version == 'new' and shotgun_index < waypoint < len(route) - 2 and not shotgun and not gun_cooldown and not escape:
                        # Only objects visible on the screen, no actor positions.
                        guns = [a for a in state.labels if a.object_name == 'Shotgun'
                                and a.width > 0 and (state.labels_buffer == a.value).any()]
                        if guns:
                            gun = min(guns, key=lambda a: abs(a.x + a.width / 2 - 160) / max(1, a.width))
                            error = gun.x + gun.width / 2 - 160
                            if abs(error) < 80 and gun.y + gun.height > 110:
                                if gun_chase == 0:
                                    gun_origin = (x, y)
                                gun_chase += 1
                                if gun_chase >= 70 and math.dist(gun_origin, (x, y)) < 60:
                                    gun_cooldown = 210
                                    gun_chase = 0
                                else:
                                    if gun_chase >= 70:
                                        gun_chase = 0
                                    cmd = [100 if abs(error) < 35 else 0,
                                           max(-12, min(12, error * 0.18)), 1, 0, 0]
                    # Selecting is allowed when the HUD shows the weapon and ammo.
                    cmd.append(int(version == 'new' and shotgun and shells > 0 and weapon != 3))
                    video.write(state.screen_buffer)
                    log.write(json.dumps({'type':'tic','tic':tick,'x':x,'y':y,'angle':angle,'waypoint':waypoint,'health':health,'armor':armor,'ammo':ammo,'kills':kills,'shotgun':shotgun,'shotgun_shells':shells,'weapon':weapon,'target_x':target[0],'target_y':target[1],'action':cmd, 'visible':[{'name':a.object_name,'x':a.x,'width':a.width} for a in state.labels if a.object_name in MONSTERS and (state.labels_buffer == a.value).any()]})+'\n')
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
