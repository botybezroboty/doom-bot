"""Regułowy i losowy bot dla scenariusza ViZDoom defend_the_center."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random

import numpy as np
from datetime import datetime
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"

import vizdoom as vzd
from wideo import Video


ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / "powtorki"
SCENARIO = Path(vzd.scenarios_path) / "defend_the_center.cfg"
FRAME_WIDTH = 320
SEARCH_TICS = 4
TARGET_LABEL = "MarineChainsawVzd"


def choose_action(
    game: vzd.DoomGame, rng: random.Random, random_bot: bool
) -> tuple[list[int], int]:
    """Wybiera skręt wyłącznie na podstawie ekranowych etykiet obiektów."""
    if random_bot:
        turn = rng.choice((0, 1, 2))  # bez skrętu, w lewo, w prawo
        duration = SEARCH_TICS
    else:
        state = game.get_state()
        labels = state.labels if state is not None and state.labels else []
        # Celujemy tylko w etykietę przeciwnika, pomijając gracza, krew i efekty.
        targets = [
            label.x + label.width / 2
            for label in labels
            if label.object_name == TARGET_LABEL and label.width > 0
        ]
        if targets:
            # Najpierw śledź najbliższy środkowi cel; obrót o jeden tic ogranicza
            # przeskakiwanie nad nim przy dużej prędkości obrotu Dooma.
            target_x = min(targets, key=lambda x: abs(x - FRAME_WIDTH / 2))
            error = target_x - FRAME_WIDTH / 2
            turn = 1 if error < -9 else (2 if error > 9 else 0)
            duration = 1 if abs(error) < 40 else (2 if abs(error) < 90 else SEARCH_TICS)
        else:
            turn = 2
            duration = SEARCH_TICS

    return [int(turn == 1), int(turn == 2), 1], duration


def create_game() -> vzd.DoomGame:
    game = vzd.DoomGame()
    game.set_window_visible(False)
    game.load_config(str(SCENARIO))
    game.set_mode(vzd.Mode.PLAYER)
    game.set_render_all_frames(False)
    game.set_window_visible(False)
    game.set_labels_buffer_enabled(True)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    # Liczniki służą wyłącznie do raportowania wyniku; bot podejmuje decyzje
    # tylko na podstawie etykiet ekranowych w choose_action().
    game.add_available_game_variable(vzd.GameVariable.KILLCOUNT)
    game.add_available_game_variable(vzd.GameVariable.DEATHCOUNT)
    game.init()
    return game


def run_episode(
    game: vzd.DoomGame, seed: int, deaths_before: int, random_bot: bool
) -> tuple[tuple[int, int, float, int], Path, str]:
    REPLAYS.mkdir(exist_ok=True)
    started = datetime.now()
    kind = "losowy" if random_bot else "etykiety"
    replay = REPLAYS / f"center_{kind}_{seed:03d}_{started:%Y%m%d_%H%M%S_%f}.lmp"
    game.set_seed(seed)
    rng = random.Random(seed)
    game.new_episode(str(replay).replace("\\", "/"))
    fingerprint = hashlib.sha256()
    video = Video(replay.with_suffix('.avi'), game.get_screen_width(), game.get_screen_height())
    try:
        with replay.with_suffix('.jsonl').open('w', encoding='utf-8') as log:
            log.write(json.dumps({'typ': 'start', 'seed': seed, 'bot': kind, 'powtorka': replay.name, 'fps': 35}) + '\n')
            while not game.is_episode_finished():
                state = game.get_state()
                fingerprint.update(state.screen_buffer.tobytes())
                action, duration = choose_action(game, rng, random_bot)
                game.set_action(action)
                for remaining in range(duration, 0, -1):
                    if game.is_episode_finished():
                        break
                    state = game.get_state()
                    labels = [{'nazwa': label.object_name, 'id': label.object_id,
                               'x': label.x, 'y': label.y, 'szerokosc': label.width,
                               'wysokosc': label.height} for label in state.labels]
                    log.write(json.dumps({'typ': 'tik', 'tik': game.get_episode_time(),
                        'zycie': game.get_game_variable(vzd.GameVariable.HEALTH),
                        'amunicja': game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON_AMMO),
                        'zabite': game.get_game_variable(vzd.GameVariable.KILLCOUNT),
                        'etykiety': labels, 'akcja': action, 'pozostale_tiki_akcji': remaining}, ensure_ascii=False) + '\n')
                    video.write(state.screen_buffer)
                    game.advance_action()
            log.write(json.dumps({'typ': 'koniec', 'tik': game.get_episode_time(),
                'zycie': game.get_game_variable(vzd.GameVariable.HEALTH),
                'amunicja': game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON_AMMO),
                'zabite': game.get_game_variable(vzd.GameVariable.KILLCOUNT),
                'nagroda': game.get_total_reward()}) + '\n')
    finally:
        video.close()
    result = (
        int(game.get_game_variable(vzd.GameVariable.KILLCOUNT)),
        int(game.get_game_variable(vzd.GameVariable.DEATHCOUNT)) - deaths_before,
        game.get_total_reward(),
        game.get_episode_time(),
    )
    return result, replay, fingerprint.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=100)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("--trials musi być dodatnie")

    # ViZDoom używa MT19937 do wyznaczenia seeda silnika. W Windows
    # wartości powyżej INT_MAX są obcinane do INT_MAX przez silnik.
    seeds = []
    used_doom_seeds = set()
    candidate = 0
    while len(seeds) < args.trials:
        doom_seed = int(np.random.RandomState(candidate).randint(0, 2**32, dtype=np.uint32))
        if 0 < doom_seed < 2**31 - 1 and doom_seed not in used_doom_seeds:
            seeds.append((candidate, doom_seed))
            used_doom_seeds.add(doom_seed)
        candidate += 1

    rows = []
    for random_bot in (False, True):
        kills: list[int] = []
        deaths: list[int] = []
        rewards: list[float] = []
        times: list[int] = []
        game = create_game()
        pending_replay: Path | None = None
        deaths_before = 0
        try:
            for trial, (seed, doom_seed) in enumerate(seeds, 1):
                (kill_count, death_count, reward, elapsed), replay, fingerprint = run_episode(
                    game, seed, deaths_before, random_bot
                )
                deaths_before += death_count
                if pending_replay is not None:
                    if not pending_replay.exists():
                        raise RuntimeError(f"ViZDoom nie zapisał powtórki: {pending_replay}")
                    print(f"Powtórka zapisana: {pending_replay.name}", flush=True)
                pending_replay = replay
                rows.append(["losowy" if random_bot else "etykiety", seed, doom_seed, kill_count,
                             death_count, reward, elapsed, replay.name, fingerprint])
                kills.append(kill_count)
                deaths.append(death_count)
                rewards.append(reward)
                times.append(elapsed)
                print(f"{'Losowy' if random_bot else 'Etykiety'} {trial}/{args.trials}: "
                      f"zabite {kill_count}, zgony {death_count}, nagroda {reward:.1f}, "
                      f"czas gry {elapsed} tics", flush=True)
        finally:
            game.close()
        if pending_replay is not None:
            if not pending_replay.exists():
                raise RuntimeError(f"ViZDoom nie zapisał powtórki: {pending_replay}")
            print(f"Powtórka zapisana: {pending_replay.name}", flush=True)
        fingerprints = [row[-1] for row in rows if row[0] == ("losowy" if random_bot else "etykiety")]
        if len(set(fingerprints)) != len(fingerprints):
            raise RuntimeError("Wykryto identyczne przebiegi: porównanie przerwane")
        print(f"Podsumowanie {'losowy' if random_bot else 'etykiety'}: "
              f"średnio zabite {sum(kills) / len(kills):.2f}, "
              f"średnio zgony {sum(deaths) / len(deaths):.2f}, "
              f"średnia nagroda {sum(rewards) / len(rewards):.2f}, "
              f"średni czas {sum(times) / len(times):.1f} tics", flush=True)

    for row in rows:
        replay_path = REPLAYS / row[-2]
        data = replay_path.read_bytes()
        if data[:4] != b"FORM" or data[8:16] != b"ZDEMZDHD":
            raise RuntimeError(f"Nieznany format powtórki: {replay_path}")
        map_end = data.index(b"\0", 24) + 1
        recorded_seed = int.from_bytes(data[map_end:map_end + 4], "big")
        if recorded_seed != row[2]:
            raise RuntimeError(f"Nieprawidłowy seed w powtórce: {replay_path}")
    with (ROOT / "porownanie.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["bot", "seed", "seed_silnika", "zabite", "zgony", "nagroda", "tiki", "powtorka", "sha256_obrazow"])
        writer.writerows(rows)


if __name__ == "__main__":
    main()
