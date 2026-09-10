# -*- coding: utf-8 -*-
"""x=581 列 y 扫描：找物品47 真实可点击的 y 范围。拿起后点回放回。"""
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

c0 = cursor()
print("初始光标=%#x" % c0)
if c0:
    print("请先手动放回"); sys.exit(1)

x = 581  # (1,*) 列
hits = []
for y in range(376, 418, 3):
    click(x, y)
    time.sleep(0.4)
    c = cursor()
    if c:
        hits.append(y)
        print("y=%d -> 拿起 %#x" % (y, c))
        click(x, y)  # 放回
        time.sleep(0.4)
        if cursor() != 0:
            print("  放回失败")
    else:
        print("y=%d -> 无反应" % y)
print("命中 y: %s" % hits)
ctypes.windll.kernel32.CloseHandle(h)
