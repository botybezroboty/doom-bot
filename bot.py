"""Prosty bot do Freedoom 2 MAP01, sterowany ustalonymi regułami."""

from datetime import datetime
from pathlib import Path

import vizdoom as vzd


ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / "powtorki"


def main() -> None:
    REPLAYS.mkdir(exist_ok=True)
    replay = REPLAYS / f"map01_{datetime.now():%Y%m%d_%H%M%S}.lmp"

    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / "freedoom2.wad"))
    game.set_doom_map("MAP01")
    game.set_window_visible(True)
    game.set_sound_enabled(True)
    game.set_episode_timeout(35 * 60)
    game.set_available_buttons(
        [vzd.Button.MOVE_FORWARD, vzd.Button.TURN_LEFT, vzd.Button.TURN_RIGHT, vzd.Button.ATTACK]
    )
    game.set_recording_episode_path(str(replay))
    game.init()

    try:
        game.new_episode()
        tick = 0
        while not game.is_episode_finished():
            # Prosty patrol: strzelaj i zmieniaj kierunek co kilka sekund.
            left = (tick // 140) % 2 == 0
            game.make_action([1, int(left), int(not left), 1], 4)
            tick += 4
    finally:
        game.close()

    print(f"Powtórka zapisana: {replay}")


if __name__ == "__main__":
    main()
