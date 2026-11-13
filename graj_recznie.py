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
GCLP_HCURSOR = -12
WM_SETCURSOR = 0x0020
USER32.CreateCursor.argtypes = [
    wintypes.HINSTANCE,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.POINTER(ctypes.c_ubyte),
]
USER32.CreateCursor.restype = wintypes.HANDLE
USER32.SetSystemCursor.argtypes = [wintypes.HANDLE, wintypes.DWORD]
USER32.SetSystemCursor.restype = wintypes.BOOL
USER32.DestroyCursor.argtypes = [wintypes.HANDLE]
USER32.DestroyCursor.restype = wintypes.BOOL
USER32.GetClassLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
USER32.GetClassLongPtrW.restype = wintypes.HANDLE
USER32.SetClassLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.HANDLE]
USER32.SetClassLongPtrW.restype = wintypes.HANDLE
USER32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
USER32.SendMessageW.restype = wintypes.LPARAM


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


def _hide_window_cursor(hwnd: int) -> tuple[int | None, int] | None:
    """Ustaw przezroczysty kursor wyłącznie dla klasy okna ViZDoom."""
    and_mask = (ctypes.c_ubyte * 2)(0xFF, 0xFF)
    xor_mask = (ctypes.c_ubyte * 2)(0, 0)
    cursor = USER32.CreateCursor(None, 0, 0, 1, 1, and_mask, xor_mask)
    if not cursor:
        return None
    previous = USER32.GetClassLongPtrW(hwnd, GCLP_HCURSOR)
    USER32.SetClassLongPtrW(hwnd, GCLP_HCURSOR, cursor)
    if USER32.GetClassLongPtrW(hwnd, GCLP_HCURSOR) != cursor:
        USER32.DestroyCursor(cursor)
        return None
    USER32.SendMessageW(hwnd, WM_SETCURSOR, hwnd, 1)
    return previous, cursor


def _restore_window_cursor(hwnd: int, state: tuple[int | None, int]) -> None:
    previous, blank = state
    USER32.SetClassLongPtrW(hwnd, GCLP_HCURSOR, previous)
    USER32.SendMessageW(hwnd, WM_SETCURSOR, hwnd, 1)
    USER32.DestroyCursor(blank)


def _action(dx: int, dy: int) -> list[float]:
    forward = 100 if _is_pressed(0x57) else -100 if _is_pressed(0x53) else 0  # W / S
    strafe = -100 if _is_pressed(0x41) else 100 if _is_pressed(0x44) else 0  # A / D
    turn = max(-30, min(30, dx * 0.25))
    look = max(-30, min(30, -dy * 0.25))
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
    hwnd = None
    window_cursor = None
    try:
        game.new_episode(str(replay))
        hwnd = _find_game_window()
        original_cursor = wintypes.POINT()
        USER32.GetCursorPos(ctypes.byref(original_cursor))
        center = _mouse_center(hwnd)
        USER32.SetForegroundWindow(hwnd)
        USER32.SetCursorPos(*center)
        window_cursor = _hide_window_cursor(hwnd)
        if window_cursor is None:
            print("Nie udało się ukryć kursora tylko w oknie gry; kursor systemowy pozostaje bez zmian.")
        print("Sterowanie: WASD, mysz, LPM — strzał, E/spacja — użyj, Shift — bieg.")

        start = perf_counter()
        last_frame = start
        while not game.is_episode_finished():
            if USER32.GetForegroundWindow() == hwnd:
                cursor = wintypes.POINT()
                USER32.GetCursorPos(ctypes.byref(cursor))
                dx, dy = cursor.x - center[0], cursor.y - center[1]
                USER32.SetCursorPos(*center)
                game.make_action(_action(dx, dy), 1)
            else:
                game.make_action([0, 0, 0, 0, 0, 0, 0], 1)
            last_frame += FRAME_TIME
            sleep(max(0, last_frame - perf_counter()))

        elapsed = perf_counter() - start
        deaths = game.get_game_variable(vzd.GameVariable.DEATHCOUNT)
        finished_at = datetime.now()
    finally:
        if hwnd is not None and window_cursor is not None:
            _restore_window_cursor(hwnd, window_cursor)
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
