#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 PrintWindow 截 D2Loader 游戏窗口内容（被遮挡也能截），保存 Py\\_screen_stash.png。"""
import ctypes
import sys
from ctypes import wintypes

sys.path.insert(0, ".")
import mem_read as mem

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def find_hwnd_by_pid(target_pid: int) -> int:
    found = []

    def cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == target_pid:
            found.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found[0] if found else 0


def main() -> None:
    pid = mem.find_process("D2Loader.exe")
    if pid is None:
        print("D2Loader.exe 未运行")
        return 1
    hwnd = find_hwnd_by_pid(pid)
    if not hwnd:
        print("未找到游戏窗口")
        return 1
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    print(f"hwnd=0x{hwnd:X} rect=({rect.left},{rect.top},{w}x{h})")

    hdcWin = user32.GetWindowDC(hwnd)
    memdc = gdi32.CreateCompatibleDC(hdcWin)
    bmp = gdi32.CreateCompatibleBitmap(hdcWin, w, h)
    old = gdi32.SelectObject(memdc, bmp)
    ok = user32.PrintWindow(hwnd, memdc, 2)  # PW_RENDERFULLCONTENT
    print(f"PrintWindow ok={ok}")

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
            ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
            ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # 顶向下
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0  # BI_RGB
    buf = ctypes.create_string_buffer(w * h * 4)
    n = gdi32.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    print(f"GetDIBits n={n}")

    gdi32.SelectObject(memdc, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(hwnd, hdcWin)

    from PIL import Image
    img = Image.frombytes("RGB", (w, h), buf.raw, "raw", "BGRX")
    img.save(r"Py\_screen_stash.png")
    print("已保存 Py\\_screen_stash.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
