# -*- coding: utf-8 -*-
"""前台化 + SendMessage 点击，验证是否立即生效。"""
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")
pp = dword(pid, h, d2c + 0x11B800)
pinv = dword(pid, h, pp + 0x60)
hwnd = 0x30718

def click(x, y):
    lp = (y << 16) | (x & 0xFFFF)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0201, 0, lp)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0202, 0, lp)

def cursor():
    return dword(pid, h, pinv + 0x20)

fg = ctypes.windll.user32.GetForegroundWindow()
print("前台=0x%X (游戏=0x%X)" % (fg, hwnd))
if fg != hwnd:
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    time.sleep(1.0)
fg = ctypes.windll.user32.GetForegroundWindow()
print("前台化后=0x%X %s" % (fg, "OK" if fg == hwnd else "失败"))

print("光标=%#x" % cursor())
# 点 (0,1)=(552,413)：若光标有辨识卷则放回，否则拿起
click(552, 413)
for i in range(10):
    time.sleep(0.2)
    c = cursor()
    if i in (0, 1, 4, 9):
        print("+%.1fs 光标=%#x" % ((i + 1) * 0.2, c))
    if i == 9:
        print("最终光标=%#x" % c)
ctypes.windll.kernel32.CloseHandle(h)
