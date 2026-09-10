# -*- coding: utf-8 -*-
"""枚举进程所有窗口（含子窗口）找游戏画布"""
import ctypes, sys
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def get_title(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value

def get_rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom

all_wins = []

@EnumWindowsProc
def cb_top(hwnd, lparam):
    pid2 = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid2))
    if pid2.value == target:
        all_wins.append(("top", hwnd))
    return True

pid = mem.find_process("D2Loader.exe")
target = pid
user32.EnumWindows(cb_top, 0)

# 子窗口
EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

@EnumChildProc
def cb_child(hwnd, lparam):
    all_wins.append(("child", hwnd))
    return True

for level, hwnd in list(all_wins):
    if level == "top":
        user32.EnumChildWindows(hwnd, cb_child, 0)

for level, hwnd in all_wins:
    l, t, r, b = get_rect(hwnd)
    w, h = r - l, b - t
    if w > 50 and h > 50:  # 过滤无效尺寸
        print(f"{level} 0x{hwnd:X} {w}x{h} title={get_title(hwnd)!r} cls={user32.GetClassNameW(hwnd)}")
