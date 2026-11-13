"""Ręczna gra Freedoom 2 MAP01 z pomiarem czasu ukończenia."""

from datetime import datetime
from pathlib import Path
from shutil import copyfile
from time import perf_counter

import pygame
import vizdoom as vzd


ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / "powtorki"
RESULTS = ROOT / "wyniki.md"
WIDTH, HEIGHT = 1280, 720
FPS = 35


def main() -> None:
    REPLAYS.mkdir(exist_ok=True)
    started_at = datetime.now()
    replay = REPLAYS / f"recznie_{started_at:%Y%m%d_%H%M%S}.lmp"
    runtime_config = ROOT / "recznie_runtime.ini"
    copyfile(ROOT / "recznie.ini", runtime_config)

    pygame.init()
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Freedoom 2 — MAP01 — gra ręczna")
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    clock = pygame.time.Clock()

    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / "freedoom2.wad"))
    game.set_doom_map("MAP01")
    game.set_doom_config_path(str(runtime_config))
    game.set_mode(vzd.Mode.PLAYER)
    game.set_window_visible(False)
    game.set_screen_resolution(vzd.ScreenResolution.RES_1280X720)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_sound_enabled(True)
    game.set_episode_timeout(0)
    for button, maximum in (
        (vzd.Button.MOVE_FORWARD_BACKWARD_DELTA, 100),
        (vzd.Button.MOVE_LEFT_RIGHT_DELTA, 100),
        (vzd.Button.TURN_LEFT_RIGHT_DELTA, 30),
        (vzd.Button.LOOK_UP_DOWN_DELTA, 30),
    ):
        game.add_available_button(button, maximum)
    game.add_available_button(vzd.Button.ATTACK)
    game.add_available_button(vzd.Button.USE)
    game.add_available_button(vzd.Button.SPEED)
    game.set_available_game_variables([vzd.GameVariable.DEATHCOUNT])

    try:
        game.init()
        game.new_episode(str(replay))
        start = perf_counter()
        print("WASD: ruch, mysz: obrót, LPM: strzał, E/spacja: użyj, Shift: bieg.")
        running = True
        focused = True
        mouse_dx = 0
        mouse_dy = 0

        while running and not game.is_episode_finished():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.WINDOWFOCUSLOST:
                    focused = False
                    pygame.event.set_grab(False)
                    pygame.mouse.set_visible(True)
                elif event.type == pygame.WINDOWFOCUSGAINED:
                    focused = True
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
                    pygame.mouse.get_rel()
                elif event.type == pygame.MOUSEMOTION and focused:
                    mouse_dx += event.rel[0]
                    mouse_dy += event.rel[1]

            if not running:
                break

            forward = 0
            strafe = 0
            attack = 0
            use = 0
            run = 0
            if focused:
                keys = pygame.key.get_pressed()
                forward = 100 if keys[pygame.K_w] else -100 if keys[pygame.K_s] else 0
                strafe = -100 if keys[pygame.K_a] else 100 if keys[pygame.K_d] else 0
                attack = int(pygame.mouse.get_pressed()[0])
                use = int(keys[pygame.K_e] or keys[pygame.K_SPACE])
                run = int(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

            turn = max(-30, min(30, mouse_dx * 0.25)) if focused else 0
            look = max(-30, min(30, -mouse_dy * 0.25)) if focused else 0
            mouse_dx = mouse_dy = 0

            state = game.get_state()
            if state is None:
                break
            frame = state.screen_buffer.transpose(1, 0, 2)
            pygame.surfarray.blit_array(window, frame)
            pygame.display.flip()

            game.make_action([forward, strafe, turn, look, attack, use, run], 1)
            clock.tick(FPS)

        elapsed = perf_counter() - start
        deaths = game.get_game_variable(vzd.GameVariable.DEATHCOUNT)
        finished_at = datetime.now()
    finally:
        game.close()
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        pygame.quit()

    if not running:
        print(f"Próba przerwana. Powtórka: {replay}")
        return
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
