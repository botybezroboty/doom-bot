"""Uruchom ręczną grę Freedoom 2 MAP01 i zmierz czas do wyjścia."""

from datetime import datetime
from pathlib import Path
from time import perf_counter, sleep

import vizdoom as vzd


ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / "powtorki"
RESULTS = ROOT / "wyniki.md"


def main() -> None:
    REPLAYS.mkdir(exist_ok=True)
    started_at = datetime.now()
    replay = REPLAYS / f"recznie_{started_at:%Y%m%d_%H%M%S}.lmp"

    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / "freedoom2.wad"))
    game.set_doom_map("MAP01")
    game.set_doom_config_path(str(ROOT / "recznie.ini"))
    game.set_mode(vzd.Mode.ASYNC_SPECTATOR)
    game.set_window_visible(True)
    game.set_screen_resolution(vzd.ScreenResolution.RES_1280X720)
    game.set_sound_enabled(True)
    game.set_episode_timeout(0)
    game.set_available_game_variables([vzd.GameVariable.DEATHCOUNT])
    game.init()

    try:
        game.new_episode(str(replay))
        start = perf_counter()
        print("Start! Graj klawiaturą i myszą. Czas kończy się po użyciu wyjścia.")

        while not game.is_episode_finished():
            sleep(0.01)

        elapsed = perf_counter() - start
        deaths = game.get_game_variable(vzd.GameVariable.DEATHCOUNT)
        finished_at = datetime.now()
    finally:
        game.close()

    if deaths:
        print(f"Gra zakończona bez wyjścia (zgonów: {int(deaths)}). Powtórka: {replay}")
        return

    RESULTS.touch(exist_ok=True)
    if RESULTS.stat().st_size == 0:
        RESULTS.write_text("# Wyniki gry ręcznej\n\n", encoding="utf-8")
    with RESULTS.open("a", encoding="utf-8") as results:
        results.write(
            f"- {started_at:%Y-%m-%d %H:%M} — MAP01: **{elapsed:.2f} s** "
            f"(ukończono {finished_at:%H:%M}); powtórka: `{replay.name}`\n"
        )

    print(f"Ukończono MAP01 w {elapsed:.2f} s. Wynik: {RESULTS}")
    print(f"Powtórka: {replay}")


if __name__ == "__main__":
    main()
