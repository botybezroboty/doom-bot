"""Nawigacja po znanej MAP01 na podstawie pozycji gracza."""

if __name__ == '__main__':
    from ukryte_okno import uruchom_na_ukrytym_pulpicie
    uruchom_na_ukrytym_pulpicie()
import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
import vizdoom as vzd
import numpy as np
from defend_the_center import dokladny_zegar
from wideo import Video

ROOT = Path(__file__).resolve().parent
ROUTE = [(650, -160), (770, -160), (1100, 120), (1380, 120), (1390, -200), (1780, -160), (1900, -160), (1950, -400), (1850, -800), (1600, -800), (1400, -800), (1100, -1024), (900, -1024),
         (750, -1024), (550, -1024), (400, -1024), (216, -800), (216, -675)]


def action(x, y, angle, target, tick):
    dx, dy = target[0] - x, target[1] - y
    desired = math.degrees(math.atan2(dy, dx)) % 360
    error = (desired - angle + 180) % 360 - 180
    # Sterowanie opiera się na aktualnym położeniu, nie na kolejności ruchów.
    turn = max(-15, min(15, -error))
    return [100 if abs(error) < 55 else 0, turn, 1, int(tick % 12 == 0)]


def run(seed):
    engine_seed = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
    if not 0 < engine_seed < 2**31 - 1:
        raise ValueError(f'Seed {seed} powoduje obcięcie seeda silnika w Windows')
    folder = ROOT / 'powtorki'
    folder.mkdir(exist_ok=True)
    path = folder / f'map01_{seed}_{datetime.now():%Y%m%d_%H%M%S_%f}'
    game = vzd.DoomGame()

    game.set_doom_game_path(str(Path(vzd.install_path) / 'freedoom2.wad'))
    game.set_doom_map('MAP01')
    game.set_doom_skill(3)
    game.set_window_visible(False)
    game.set_sound_enabled(False)
    game.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_episode_timeout(3500)
    game.set_available_buttons([vzd.Button.MOVE_FORWARD_BACKWARD_DELTA, vzd.Button.TURN_LEFT_RIGHT_DELTA, vzd.Button.SPEED, vzd.Button.USE])
    game.set_available_game_variables([vzd.GameVariable.POSITION_X, vzd.GameVariable.POSITION_Y, vzd.GameVariable.ANGLE])
    game.init()
    game.set_seed(seed)
    video = None
    try:
        game.new_episode(str(path.with_suffix('.lmp')).replace('\\', '/'))
        video = Video(path.with_suffix('.mp4'), 320, 240)
        with path.with_suffix('.jsonl').open('w', encoding='utf-8') as log:
            log.write(json.dumps({'typ':'start', 'seed':seed, 'seed_silnika':engine_seed, 'trudnosc':3, 'trasa':ROUTE})+'\n')
            waypoint = 0
            elapsed = 0
            with dokladny_zegar():
                while not game.is_episode_finished() and not game.is_player_dead():
                    state = game.get_state()
                    x,y,angle = state.game_variables
                    tick = game.get_episode_time()
                    if waypoint < len(ROUTE)-1 and math.hypot(x-ROUTE[waypoint][0], y-ROUTE[waypoint][1]) < 35:
                        waypoint += 1
                    cmd = action(x,y,angle,ROUTE[waypoint],tick)
                    video.write(state.screen_buffer)
                    log.write(json.dumps({'typ':'tik','tik':tick,'x':x,'y':y,'kat':angle,'cel':waypoint,'akcja':cmd})+'\n')
                    game.make_action(cmd, 1)
                    elapsed += 1
            dead = game.is_player_dead() or game.get_game_variable(vzd.GameVariable.HEALTH) <= 0
            outcome = 'zgon' if dead else 'limit' if elapsed >= 3499 else 'wyjscie'
            log.write(json.dumps({'typ':'koniec','tik':elapsed,'wynik':outcome,
                                  'zycie':game.get_game_variable(vzd.GameVariable.HEALTH)})+'\n')
            print(seed, outcome, elapsed, path.name, flush=True)
    finally:
        if video: video.close()
        game.close()
    data = path.with_suffix('.lmp').read_bytes()
    if data[:4] != b'FORM' or data[8:16] != b'ZDEMZDHD':
        raise RuntimeError('Nieznany format powtórki')
    offset = data.index(b'\0', 24) + 1
    if int.from_bytes(data[offset:offset + 4], 'big') != engine_seed:
        raise RuntimeError('Seed powtórki nie zgadza się z oczekiwanym')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('seeds', nargs='+', type=int)
    for seed in parser.parse_args().seeds:
        run(seed)
