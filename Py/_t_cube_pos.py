# -*- coding: utf-8 -*-
"""盒子已打开: 移动鼠标到盒子第一格中心(不点击), 请用户确认。"""
import sys, ctypes, time
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
hwnd = 0
def cb(w, l):
    global hwnd
    p = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(w, ctypes.byref(p))
    if p.value == pid and ctypes.windll.user32.IsWindowVisible(w):
        hwnd = w
    return True
PF = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
ctypes.windll.user32.EnumWindows(PF(cb), 0)

# 布局表: 盒子 10x8 @ D2CLIENT+0x10B3C8 (Left=536 Top=298)
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")
def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

layout = d2c + 0x10B3C8
left, top = dword(layout + 0x04), dword(layout + 0x0C)
sw, sh = mem.read(pid, h, layout, 1)[0], mem.read(pid, h, layout + 1, 1)[0]
ctypes.windll.kernel32.CloseHandle(h)
print("盒子布局: Slot=%dx%d  Left=%d Top=%d" % (sw, sh, left, top))

# 第一格中心(客户区)
cx, cy = left + 29 // 2, top + 29 // 2
pt = wintypes.POINT(cx, cy)
ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
print("客户区中心: (%d,%d) -> 屏幕: (%d,%d)" % (cx, cy, pt.x, pt.y))
ctypes.windll.user32.SetCursorPos(pt.x, pt.y)
print("鼠标已移动到盒子第一格中心, 未点击")
