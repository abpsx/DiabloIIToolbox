#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实测 D2Loader 窗口/客户区位置，校准控件坐标 → 客户区坐标。"""
import ctypes
from ctypes import wintypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

pid = mem.find_process("D2Loader.exe")
print(f"PID = {pid}")

# 枚举该进程的顶层窗口
results = []


@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def _enum_cb(hwnd, lparam):
    wpid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
    if wpid.value == pid:
        results.append(hwnd)
    return True


user32.EnumWindows(_enum_cb, 0)
print(f"进程窗口数: {len(results)}")
for hwnd in results:
    rect = wintypes.RECT()
    cr = wintypes.RECT()
    pt = wintypes.POINT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    user32.GetClientRect(hwnd, ctypes.byref(cr))
    # 客户区左上角屏幕坐标
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    title = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, title, 256)
    vis = user32.IsWindowVisible(hwnd)
    print(f"  hwnd=0x{hwnd:X} '{title.value}' vis={vis}")
    print(f"    WindowRect: ({rect.left},{rect.top})~({rect.right},{rect.bottom}) "
          f"={rect.right-rect.left}x{rect.bottom-rect.top}")
    print(f"    ClientRect: {cr.right}x{cr.bottom}  ClientToScreen(0,0) = ({pt.x},{pt.y})")
    print(f"    => 客户区起点屏幕坐标 = ({pt.x},{pt.y}), 尺寸 {cr.right}x{cr.bottom}")
