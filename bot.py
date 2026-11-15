"""Nawigacja po znanej MAP01 na podstawie pozycji gracza."""

if __name__ == '__main__':
    from ukryte_okno import uruchom_na_ukrytym_pulpicie
    uruchom_na_ukrytym_pulpicie()
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
from defend_the_center import dokladny_zegar
from wideo import Video

ROOT = Path(__file__).resolve().parent
ROUTE = [(650, -160), (770, -160), (1100, 120), (1380, 120), (1390, -200), (1780, -160), (1900, -160), (1950, -400), (1850, -800), (1600, -800), (1400, -800), (1100, -1024), (900, -1024),
         (750, -1024), (550, -1024), (400, -1024), (216, -800), (216, -675)]


# Punkty przedmiotów z mapy: strzelba/amunicja, apteczki i zielony pancerz.
# Trasa pozostaje oparta na położeniu, a nie na czasie lub nagranych ruchach.
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
    # Etykieta musi mieć rzeczywiste piksele w buforze widocznych obiektów.
    candidates = [a for a in state.labels if a.object_name in MONSTERS
                  and a.width > 0 and (state.labels_buffer == a.value).any()]
    if not candidates:
        return None
    target = min(candidates, key=lambda a: (abs(a.x + a.width / 2 - 160) / max(a.width, 1), -a.width))
    err = target.x + target.width / 2 - 160
    turn = max(-12, min(12, err * 0.18))
    fire = int(target.x <= 160 < target.x + target.width)
    return [35 if target.width < 18 else 0, turn, 1, 0, fire], target


def action(x, y, angle, target, tick):
    dx, dy = target[0] - x, target[1] - y
    desired = math.degrees(math.atan2(dy, dx)) % 360
    error = (desired - angle + 180) % 360 - 180
    # Sterowanie opiera się na aktualnym położeniu, nie na kolejności ruchów.
    turn = max(-15, min(15, -error))
    return [100 if abs(error) < 55 else 0, turn, 1, int(tick % 12 == 0)]


def run(seed, version="nowy"):
    route = ROUTE if version == "stary" else ROUTE_NEW
    engine_seed = int(np.random.RandomState(seed).randint(0, 2**32, dtype=np.uint32))
    if not 0 < engine_seed < 2**31 - 1:
        raise ValueError(f'Seed {seed} powoduje obcięcie seeda silnika w Windows')
    folder = ROOT / 'powtorki'
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
            log.write(json.dumps({'typ':'start', 'seed':seed, 'seed_silnika':engine_seed, 'trudnosc':3, 'wersja':version, 'trasa':route})+'\n')
            waypoint = 0
            med_index = route.index((1816, -728)) if version == 'nowy' else -1
            shotgun_index = route.index((1536, -160)) if version == 'nowy' else -1
            stair_start = route.index((1460, -240)) if version == 'nowy' else -1
            stair_end = route.index((1780, -160)) if version == 'nowy' else -1
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
            barrel_attempts = {}
            blast_until = 0
            with dokladny_zegar():
                while not game.is_episode_finished() and not game.is_player_dead():
                    state = game.get_state()
                    x, y, angle, health, armor, ammo, kills, shotgun, shells, weapon = state.game_variables
                    tick = game.get_episode_time()
                    if version == 'nowy' and shotgun and math.hypot(x - 1536, y + 160) < 38:
                        fixed_shotgun_reached = True
                    if version == 'nowy' and waypoint == shotgun_index and (fixed_shotgun_reached or abandon_shotgun):
                        waypoint += 1
                        waypoint_since = elapsed
                    radius = 20 if version == 'nowy' and stair_start <= waypoint <= stair_end else 35
                    if version == 'nowy' and waypoint == shotgun_index and shotgun:
                        # Podniesienie jest możliwe z odległości około 36 jednostek.
                        radius = 38
                    if waypoint < len(route)-1 and math.hypot(x-route[waypoint][0], y-route[waypoint][1]) < radius:
                        waypoint += 1
                        waypoint_since = elapsed
                    # Apteczka jest opcjonalna, gdy nie da się do niej dotrzeć.
                    if version == 'nowy' and waypoint == med_index and elapsed - waypoint_since > 250:
                        waypoint += 1
                        waypoint_since = elapsed
                    # Po wypchnięciu na północ wróć przez znane wejście do korytarza.
                    if version == 'nowy' and waypoint >= med_index and x < 1820 and y > -320:
                        waypoint = route.index((1390, -200))
                        waypoint_since = elapsed
                    # Po zepchnięciu ze stopni spróbuj ponownie znanej drogi.
                    if version == 'nowy' and waypoint == shotgun_index and elapsed - waypoint_since > 180:
                        stair_retries += 1
                        abandon_shotgun = stair_retries >= 3
                        waypoint = stair_start
                        waypoint_since = elapsed
                        history.clear()
                    target = route[waypoint]
                    if version == 'nowy':
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
                    if version == 'nowy' and waypoint >= len(route) - 2 and -715 <= y <= -642 and (x < 200 or x > 232):
                        target = (216, -705)
                    cmd = action(x,y,angle,target,tick) + [0]
                    if gun_cooldown:
                        gun_cooldown -= 1
                    found = combat(state) if version == 'nowy' else None
                    # Beczki na trasie usuwaj z dystansu, zanim walka sprowadzi
                    # gracza w promień wybuchu. Korzystamy tylko z widocznych pikseli.
                    barrels = [a for a in state.labels if a.object_name == 'ExplosiveBarrel'
                               and a.width > 0 and (state.labels_buffer == a.value).any()]
                    # Widoczny fragment może wystawać zza ściany, przez którą
                    # pociski nie przejdą. Po ograniczonej próbie zmień pozycję.
                    safe_barrels = []
                    for barrel in barrels:
                        origin, attempts = barrel_attempts.get(barrel.object_id, ((x, y), 0))
                        if math.dist(origin, (x, y)) > 96:
                            origin, attempts = (x, y), 0
                        barrel_attempts[barrel.object_id] = (origin, attempts)
                        if 6 <= barrel.width <= 18 and attempts < 70:
                            safe_barrels.append(barrel)
                    aiming_barrel = version == 'nowy' and bool(safe_barrels) and ammo > 0
                    if aiming_barrel:
                        barrel = min(safe_barrels, key=lambda a: abs(a.x + a.width / 2 - 160))
                        origin, attempts = barrel_attempts[barrel.object_id]
                        barrel_attempts[barrel.object_id] = (origin, attempts + 1)
                        err = barrel.x + barrel.width / 2 - 160
                        cmd = [0, max(-12, min(12, err * 0.18)), 1, 0,
                               int(barrel.x <= 160 < barrel.x + barrel.width)]
                    elif found and ammo > 0:
                        cmd = found[0]
                    elif version == 'nowy' and waypoint >= len(route) - 2 and 200 <= x <= 232 and -690 <= y <= -642:
                        # Nie celuj w punkt za sobą: zatrzymaj się i patrz na przełącznik.
                        error = (90 - angle + 180) % 360 - 180
                        cmd = [0, max(-15, min(15, -error)), 1,
                               int(abs(error) < 15 and tick % 2 == 0), 0]
                    elif version == 'nowy' and shotgun_index < waypoint < len(route) - 2 and not shotgun and not gun_cooldown and not escape:
                        # Wyłącznie obiekty widoczne na ekranie, bez pozycji aktorów.
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
                    if version == 'nowy':
                        # Wybuch i reakcja łańcuchowa trwają po zniszczeniu beczki;
                        # podmuch może też przemieścić kolejne beczki w stronę gracza.
                        exploding = any(a.object_name == 'DeadExplosiveBarrel'
                                        and (state.labels_buffer == a.value).any()
                                        for a in state.labels)
                        if exploding or (aiming_barrel and cmd[4]):
                            blast_until = tick + 35
                        if tick < blast_until:
                            cmd[0] = 0
                    # Wybór jest dozwolony, gdy HUD pokazuje broń i amunicję.
                    cmd.append(int(version == 'nowy' and shotgun and shells > 0 and weapon != 3))
                    video.write(state.screen_buffer)
                    log.write(json.dumps({'typ':'tik','tik':tick,'x':x,'y':y,'kat':angle,'cel':waypoint,'zycie':health,'pancerz':armor,'amunicja':ammo,'zabite':kills,'strzelba':shotgun,'naboje_strzelby':shells,'bron':weapon,'cel_x':target[0],'cel_y':target[1],'akcja':cmd, 'widoczni':[{'nazwa':a.object_name,'x':a.x,'szerokosc':a.width} for a in state.labels if a.object_name in MONSTERS and (state.labels_buffer == a.value).any()]})+'\n')
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
    return {'wersja': version, 'seed': seed, 'seed_silnika': engine_seed,
            'wynik': outcome, 'tiki': elapsed, 'powtorka': path.name}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wersja', choices=['stary', 'nowy'], default='nowy')
    parser.add_argument('seeds', nargs='+', type=int)
    args = parser.parse_args()
    for seed in args.seeds:
        run(seed, args.wersja)
