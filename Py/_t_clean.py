# -*- coding: utf-8 -*-
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

c = dword(pid, h, pinv + 0x20)
print("光标物品=%#x" % c if c else "光标为空")
if c:
    base = (857, 541); CELL = 29
    x = base[0] + 0 + 14; y = base[1] + 0 + 14
    lp = (y << 16) | x
    ctypes.windll.user32.SendMessageW(hwnd, 0x0200, 0, lp); time.sleep(0.05)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0201, 0, lp)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0202, 0, lp)
    time.sleep(0.6)
    c2 = dword(pid, h, pinv + 0x20)
    print("放回后光标=%#x" % c2 if c2 else "放回完成，光标为空")

for loc, nm in ((0, "背包"), (4, "仓库")):
    cur = dword(pid, h, pinv + 0x0C); seen = set(); out = []
    while cur and cur not in seen:
        seen.add(cur)
        txt = dword(pid, h, cur + 0x04); idat = dword(pid, h, cur + 0x14)
        l45 = mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1
        if l45 == loc:
            pip = dword(pid, h, cur + 0x2C)
            out.append("%d(%d,%d)" % (txt, dword(pid, h, pip + 0x0C), dword(pid, h, pip + 0x10)))
        cur = dword(pid, h, idat + 0x64) if idat else 0
    print(nm + ": " + ", ".join(out))
ctypes.windll.kernel32.CloseHandle(h)
