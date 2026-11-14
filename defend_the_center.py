"""Regułowy i losowy bot dla scenariusza ViZDoom defend_the_center."""

from __future__ import annotations

import argparse
import random
from datetime import datetime
from pathlib import Path

import vizdoom as vzd


ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / "powtorki"
SCENARIO = Path(vzd.scenarios_path) / "defend_the_center.cfg"
FRAME_WIDTH = 320
ACTION_TICS = 4


def choose_action(game: vzd.DoomGame, rng: random.Random, random_bot: bool) -> list[int]:
    """Wybiera skręt wyłącznie na podstawie ekranowych etykiet obiektów."""
    if random_bot:
        turn = rng.choice((0, 1, 2))  # bez skrętu, w lewo, w prawo
    else:
        state = game.get_state()
        labels = state.labels if state is not None and state.labels else []
        # Środek widocznego prostokąta etykiety to jedyna informacja o celu.
        targets = [label.x + label.width / 2 for label in labels if label.width > 0]
        if targets:
            target_x = sum(targets) / len(targets)
            margin = 5
            turn = 1 if target_x < FRAME_WIDTH / 2 - margin else (
                2 if target_x > FRAME_WIDTH / 2 + margin else 0
            )
        else:
            turn = rng.choice((1, 2))

    return [int(turn == 1), int(turn == 2), 1]


def run_episode(seed: int, random_bot: bool) -> tuple[float, int]:
    REPLAYS.mkdir(exist_ok=True)
    started = datetime.now()
    kind = "losowy" if random_bot else "etykiety"
    replay = REPLAYS / f"center_{kind}_{seed:03d}_{started:%Y%m%d_%H%M%S_%f}.lmp"
    game = vzd.DoomGame()
    game.load_config(str(SCENARIO))
    game.set_window_visible(False)
    game.set_labels_buffer_enabled(True)
    game.set_seed(seed)
    game.init()
    rng = random.Random(seed)
    try:
        game.new_episode(str(replay).replace("\\", "/"))
        while not game.is_episode_finished():
            game.make_action(choose_action(game, rng, random_bot), ACTION_TICS)
        result = game.get_total_reward(), game.get_episode_time()
    finally:
        game.close()
    if not replay.exists():
        raise RuntimeError(f"ViZDoom nie zapisał powtórki: {replay}")
    print(f"Powtórka zapisana: {replay.name}", flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=100)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("--trials musi być dodatnie")

    for random_bot in (False, True):
        rewards: list[float] = []
        times: list[int] = []
        for seed in range(args.trials):
            reward, elapsed = run_episode(seed, random_bot)
            rewards.append(reward)
            times.append(elapsed)
            print(f"{'Losowy' if random_bot else 'Etykiety'} {seed + 1}/{args.trials}: "
                  f"nagroda {reward:.1f}, czas gry {elapsed} tics", flush=True)
        print(f"Podsumowanie {'losowy' if random_bot else 'etykiety'}: "
              f"średnia nagroda {sum(rewards) / len(rewards):.2f}, "
              f"średni czas {sum(times) / len(times):.1f} tics", flush=True)


if __name__ == "__main__":
    main()
