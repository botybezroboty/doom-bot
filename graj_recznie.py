"""Ręczna gra Freedoom 2 MAP01 z pomiarem czasu ukończenia."""

import ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from time import perf_counter, sleep

import vizdoom as vzd


ROOT = Path(__file__).resolve().parent
REPLAYS = ROOT / "powtorki"
RESULTS = ROOT / "wyniki.md"
USER32 = ctypes.WinDLL("user32", use_last_error=True)
FRAME_TIME = 1 / 35
CURSOR_SHOWING = 0x00000001


class CursorInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT),
    ]


def _is_pressed(virtual_key: int) -> bool:
    return bool(USER32.GetAsyncKeyState(virtual_key) & 0x8000)


def _find_game_window() -> int:
    windows: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def inspect_window(hwnd: int, _parameter: int) -> bool:
        length = USER32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(length + 1)
        USER32.GetWindowTextW(hwnd, title, length + 1)
        if "VIZDOOM" in title.value.upper():
            windows.append(hwnd)
        return True

    callback = callback_type(inspect_window)
    USER32.EnumWindows(callback, 0)
    if not windows:
        raise RuntimeError("Nie znaleziono okna ViZDoom.")
    return windows[0]


def _mouse_center(hwnd: int) -> tuple[int, int]:
    rect = wintypes.RECT()
    if not USER32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    return (rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2


def _hide_visible_cursor() -> int:
    """Ukryj kursor; zwróć liczbę wywołań do późniejszego przywrócenia."""
    calls = 0
    for _ in range(10):
        info = CursorInfo()
        info.cbSize = ctypes.sizeof(CursorInfo)
        if not USER32.GetCursorInfo(ctypes.byref(info)) or not info.flags & CURSOR_SHOWING:
            break
        USER32.ShowCursor(False)
        calls += 1
    return calls


def _restore_cursor(calls: int) -> None:
    for _ in range(calls):
        USER32.ShowCursor(True)


def _action(dx: int, dy: int) -> list[float]:
    forward = 100 if _is_pressed(0x57) else -100 if _is_pressed(0x53) else 0  # W / S
    strafe = 100 if _is_pressed(0x41) else -100 if _is_pressed(0x44) else 0  # A / D
    turn = max(-30, min(30, dx * 0.25))
    look = max(-30, min(30, dy * 0.25))
    attack = int(_is_pressed(0x01))  # lewy przycisk myszy
    use = int(_is_pressed(0x45) or _is_pressed(0x20))  # E / spacja
    run = int(_is_pressed(0x10))  # Shift
    return [forward, strafe, turn, look, attack, use, run]


def main() -> None:
    REPLAYS.mkdir(exist_ok=True)
    started_at = datetime.now()
    replay = REPLAYS / f"recznie_{started_at:%Y%m%d_%H%M%S}.lmp"
    runtime_config = ROOT / "recznie_runtime.ini"
    copyfile(ROOT / "recznie.ini", runtime_config)

    game = vzd.DoomGame()
    game.set_doom_game_path(str(Path(vzd.install_path) / "freedoom2.wad"))
    game.set_doom_map("MAP01")
    game.set_doom_config_path(str(runtime_config))
    game.set_mode(vzd.Mode.PLAYER)
    game.set_window_visible(True)
    game.set_screen_resolution(vzd.ScreenResolution.RES_1280X720)
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
    game.init()

    original_cursor = None
    cursor_hide_calls = 0
    try:
        game.new_episode(str(replay))
        hwnd = _find_game_window()
        original_cursor = wintypes.POINT()
        USER32.GetCursorPos(ctypes.byref(original_cursor))
        center = _mouse_center(hwnd)
        USER32.SetForegroundWindow(hwnd)
        USER32.SetCursorPos(*center)
        cursor_hide_calls += _hide_visible_cursor()
        print("Sterowanie: WASD, mysz, LPM — strzał, E/spacja — użyj, Shift — bieg.")

        start = perf_counter()
        last_frame = start
        while not game.is_episode_finished():
            if USER32.GetForegroundWindow() == hwnd:
                cursor_hide_calls += _hide_visible_cursor()
                cursor = wintypes.POINT()
                USER32.GetCursorPos(ctypes.byref(cursor))
                dx, dy = cursor.x - center[0], cursor.y - center[1]
                USER32.SetCursorPos(*center)
                game.make_action(_action(dx, dy), 1)
            else:
                _restore_cursor(cursor_hide_calls)
                cursor_hide_calls = 0
                game.make_action([0, 0, 0, 0, 0, 0, 0], 1)
            last_frame += FRAME_TIME
            sleep(max(0, last_frame - perf_counter()))

        elapsed = perf_counter() - start
        deaths = game.get_game_variable(vzd.GameVariable.DEATHCOUNT)
        finished_at = datetime.now()
    finally:
        _restore_cursor(cursor_hide_calls)
        if original_cursor is not None:
            USER32.SetCursorPos(original_cursor.x, original_cursor.y)
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
