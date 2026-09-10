# -*- coding: utf-8 -*-
"""逐个点击测试找物品47 真实占格。拿起后点回放回，光标状态始终干净。"""
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
cx, cy = 840, 524
DX, DY = -157, -9
CELL = 29

def pt(gx, gy):
    return cx + DX + (gx - 5) * CELL + 14, cy + DY + (gy - 5) * CELL + 14

def click(x, y):
    lp = (y << 16) | (x & 0xFFFF)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0201, 0, lp)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0202, 0, lp)

def cursor():
    return dword(pid, h, pinv + 0x20)

# 当前光标必须为空
c0 = cursor()
print("初始光标=%#x" % c0)
if c0:
    print("请先手动放回"); sys.exit(1)

# 物品47 锚点 (1,0)，测试周围 9 格
for gx, gy in [(1, 0), (2, 0), (3, 0), (1, 1), (1, 2), (0, 0), (2, 1), (0, 1), (3, 1)]:
    c = cursor()
    if c:
        # 有物品在光标：点当前格放回
        click(*pt(gx - 1, gy))  # 无意义，只清光标
        time.sleep(0.5)
        c = cursor()
        if c:
            print("光标残留 %#x，中止" % c)
            break
    x, y = pt(gx, gy)
    click(x, y)
    time.sleep(0.5)
    c = cursor()
    if c:
        # 拿起成功：点回放回
        print("格(%d,%d) (%d,%d) -> 拿起 %#x" % (gx, gy, x, y, c))
        click(x, y)
        time.sleep(0.5)
        if cursor() != 0:
            print("放回失败")
    else:
        print("格(%d,%d) (%d,%d) -> 无反应" % (gx, gy, x, y))
ctypes.windll.kernel32.CloseHandle(h)
