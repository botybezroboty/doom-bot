"""Keeps the ViZDoom engine's start-up window off the screen on Windows."""
import ctypes
import os
import subprocess
import sys
import uuid

MARKER = 'DOOM_BOT_HIDDEN_DESKTOP'


def run_on_hidden_desktop():
    if sys.platform != 'win32' or os.environ.get(MARKER) == '1':
        return
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.CreateDesktopW.restype = ctypes.c_void_p
    user.CreateDesktopW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
    user.CloseDesktop.argtypes = [ctypes.c_void_p]
    name = 'DoomBot-' + uuid.uuid4().hex
    desktop = user.CreateDesktopW(name, None, None, 0, 0x01ff, None)
    if not desktop:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        from ctypes import wintypes
        class STARTUPINFO(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('lpReserved', wintypes.LPWSTR), ('lpDesktop', wintypes.LPWSTR), ('lpTitle', wintypes.LPWSTR), ('dwX', wintypes.DWORD), ('dwY', wintypes.DWORD), ('dwXSize', wintypes.DWORD), ('dwYSize', wintypes.DWORD), ('dwXCountChars', wintypes.DWORD), ('dwYCountChars', wintypes.DWORD), ('dwFillAttribute', wintypes.DWORD), ('dwFlags', wintypes.DWORD), ('wShowWindow', wintypes.WORD), ('cbReserved2', wintypes.WORD), ('lpReserved2', ctypes.c_void_p), ('hStdInput', wintypes.HANDLE), ('hStdOutput', wintypes.HANDLE), ('hStdError', wintypes.HANDLE)]
        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE), ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)]
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(STARTUPINFO), ctypes.POINTER(PROCESS_INFORMATION)]
        startup = STARTUPINFO(); startup.cb = ctypes.sizeof(startup); startup.lpDesktop = name
        process = PROCESS_INFORMATION()
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline([sys.executable, *sys.argv]))
        old = os.environ.get(MARKER)
        os.environ[MARKER] = '1'
        try:
            if not kernel.CreateProcessW(None, command, None, None, True, 0, None, None, ctypes.byref(startup), ctypes.byref(process)):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            if old is None: os.environ.pop(MARKER, None)
            else: os.environ[MARKER] = old
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.WaitForSingleObject(process.hProcess, 0xffffffff)
        code = wintypes.DWORD(); kernel.GetExitCodeProcess(process.hProcess, ctypes.byref(code))
        kernel.CloseHandle(process.hThread); kernel.CloseHandle(process.hProcess)
        result = code.value
    finally:
        user.CloseDesktop(desktop)
    raise SystemExit(result)


def show_manual_window():
    if sys.platform != 'win32' or os.environ.get(MARKER) != '1':
        return
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.OpenDesktopW.restype = ctypes.c_void_p
    user.OpenDesktopW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    user.SetThreadDesktop.argtypes = [ctypes.c_void_p]
    desktop = user.OpenDesktopW('Default', 0, False, 0x01ff)
    if not desktop or not user.SetThreadDesktop(desktop):
        raise ctypes.WinError(ctypes.get_last_error())
