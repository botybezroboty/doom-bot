"""A rule-based bot and a random bot for the ViZDoom scenario defend_the_center."""

from __future__ import annotations

if __name__ == '__main__':
    from hidden_desktop import run_on_hidden_desktop
    run_on_hidden_desktop()

import argparse
import ctypes
import csv
import hashlib
import json
import os
import random
import sys
from contextlib import contextmanager

import numpy as np
from datetime import datetime
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"

import vizdoom as vzd
from video import Video


ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / "replays"
SCENARIO = Path(vzd.scenarios_path) / "defend_the_center.cfg"
FRAME_WIDTH = 320
SEARCH_TICS = 4
TARGET_LABELS = {"MarineChainsawVzd", "Demon"}


@contextmanager
def precise_timer():
    """Limits the delay of ViZDoom's waits on Windows during a game."""
    if sys.platform != "win32":
        yield
        return
    winmm = ctypes.WinDLL("winmm")
    if winmm.timeBeginPeriod(1) != 0:
        raise OSError("Could not set the Windows timer resolution")
    try:
        yield
    finally:
        winmm.timeEndPeriod(1)


def choose_action(
    game: vzd.DoomGame, rng: random.Random, random_bot: bool
) -> tuple[list[int], int]:
    """Chooses the turn only from the on-screen object labels."""
    if random_bot:
        turn = rng.choice((0, 1, 2))  # no turn, left, right
        duration = SEARCH_TICS
        shoot = True
    else:
        state = game.get_state()
        labels = state.labels if state is not None and state.labels else []
        # Demons fight up close, so they must be stopped before the others.
        targets = [
            label
            for label in labels
            if label.object_name in TARGET_LABELS and label.width > 0
        ]
        if targets:
            target = min(targets, key=lambda label: (
                label.object_name != "Demon",
                abs(label.x + label.width / 2 - FRAME_WIDTH / 2),
            ))
            target_x = target.x + target.width / 2
            error = target_x - FRAME_WIDTH / 2
            # Do not stop aiming before reaching the narrow outline.
            turn = 1 if target.x + target.width <= FRAME_WIDTH / 2 else (
                2 if target.x > FRAME_WIDTH / 2 else 0)
            duration = 1 if abs(error) < 40 else (2 if abs(error) < 90 else SEARCH_TICS)
            shoot = target.x <= FRAME_WIDTH / 2 < target.x + target.width
        else:
            turn = 2
            duration = SEARCH_TICS
            shoot = False

    return [int(turn == 1), int(turn == 2), int(shoot)], duration


def create_game() -> vzd.DoomGame:
    game = vzd.DoomGame()
    game.set_window_visible(False)
    game.load_config(str(SCENARIO))
    game.set_mode(vzd.Mode.PLAYER)
    game.set_render_all_frames(False)
    game.set_window_visible(False)
    game.set_labels_buffer_enabled(True)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    # The counters only report the result; the bot decides
    # only from the on-screen labels in choose_action().
    game.add_available_game_variable(vzd.GameVariable.KILLCOUNT)
    game.add_available_game_variable(vzd.GameVariable.DEATHCOUNT)
    game.init()
    return game


@precise_timer()
def run_episode(
    game: vzd.DoomGame, seed: int, deaths_before: int, random_bot: bool
) -> tuple[tuple[int, int, float, int], Path, str]:
    REPLAYS.mkdir(exist_ok=True)
    started = datetime.now()
    kind = "random" if random_bot else "labels"
    replay = REPLAYS / f"center_{kind}_{seed:03d}_{started:%Y%m%d_%H%M%S_%f}.lmp"
    game.set_seed(seed)
    rng = random.Random(seed)
    game.new_episode(str(replay).replace("\\", "/"))
    fingerprint = hashlib.sha256()
    video = Video(replay.with_suffix('.mp4'), game.get_screen_width(), game.get_screen_height())
    try:
        with replay.with_suffix('.jsonl').open('w', encoding='utf-8') as log:
            log.write(json.dumps({'type': 'start', 'seed': seed, 'bot': kind, 'replay': replay.name, 'fps': 35}) + '\n')
            while not game.is_episode_finished():
                state = game.get_state()
                fingerprint.update(state.screen_buffer.tobytes())
                action, duration = choose_action(game, rng, random_bot)
                game.set_action(action)
                for remaining in range(duration, 0, -1):
                    if game.is_episode_finished():
                        break
                    state = game.get_state()
                    labels = [{'name': label.object_name, 'id': label.object_id,
                               'x': label.x, 'y': label.y, 'width': label.width,
                               'height': label.height} for label in state.labels]
                    log.write(json.dumps({'type': 'tic', 'tic': game.get_episode_time(),
                        'health': game.get_game_variable(vzd.GameVariable.HEALTH),
                        'ammo': game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON_AMMO),
                        'kills': game.get_game_variable(vzd.GameVariable.KILLCOUNT),
                        'labels': labels, 'action': action, 'action_tics_left': remaining}, ensure_ascii=False) + '\n')
                    video.write(state.screen_buffer)
                    game.advance_action()
            log.write(json.dumps({'type': 'end', 'tic': game.get_episode_time(),
                'health': game.get_game_variable(vzd.GameVariable.HEALTH),
                'ammo': game.get_game_variable(vzd.GameVariable.SELECTED_WEAPON_AMMO),
                'kills': game.get_game_variable(vzd.GameVariable.KILLCOUNT),
                'reward': game.get_total_reward()}) + '\n')
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
        parser.error("--trials must be positive")

    # ViZDoom uses MT19937 to derive the engine seed. On Windows
    # the engine truncates values above INT_MAX to INT_MAX.
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
                        raise RuntimeError(f"ViZDoom did not write the replay: {pending_replay}")
                    print(f"Replay written: {pending_replay.name}", flush=True)
                pending_replay = replay
                rows.append(["random" if random_bot else "labels", seed, doom_seed, kill_count,
                             death_count, reward, elapsed, replay.name, fingerprint])
                kills.append(kill_count)
                deaths.append(death_count)
                rewards.append(reward)
                times.append(elapsed)
                print(f"{'Random' if random_bot else 'Labels'} {trial}/{args.trials}: "
                      f"kills {kill_count}, deaths {death_count}, reward {reward:.1f}, "
                      f"game time {elapsed} tics", flush=True)
        finally:
            game.close()
        if pending_replay is not None:
            if not pending_replay.exists():
                raise RuntimeError(f"ViZDoom did not write the replay: {pending_replay}")
            print(f"Replay written: {pending_replay.name}", flush=True)
        fingerprints = [row[-1] for row in rows if row[0] == ("random" if random_bot else "labels")]
        if len(set(fingerprints)) != len(fingerprints):
            raise RuntimeError("Identical runs found: comparison stopped")
        print(f"Summary {'random' if random_bot else 'labels'}: "
              f"mean kills {sum(kills) / len(kills):.2f}, "
              f"mean deaths {sum(deaths) / len(deaths):.2f}, "
              f"mean reward {sum(rewards) / len(rewards):.2f}, "
              f"mean time {sum(times) / len(times):.1f} tics", flush=True)

    for row in rows:
        replay_path = REPLAYS / row[-2]
        data = replay_path.read_bytes()
        if data[:4] != b"FORM" or data[8:16] != b"ZDEMZDHD":
            raise RuntimeError(f"Unknown replay format: {replay_path}")
        map_end = data.index(b"\0", 24) + 1
        recorded_seed = int.from_bytes(data[map_end:map_end + 4], "big")
        if recorded_seed != row[2]:
            raise RuntimeError(f"Wrong seed in the replay: {replay_path}")
    with (ROOT / "comparison.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["bot", "seed", "engine_seed", "kills", "deaths", "reward", "tics", "replay", "frames_sha256"])
        writer.writerows(rows)


if __name__ == "__main__":
    main()
