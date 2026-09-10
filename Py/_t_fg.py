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
hwnd = 0x30718
fg = ctypes.windll.user32.GetForegroundWindow()
print("前台=0x%X (游戏=0x%X) %s" % (fg, hwnd, "前台" if fg == hwnd else "后台"))
ok = ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(0.8)
fg = ctypes.windll.user32.GetForegroundWindow()
print("SetForegroundWindow=%d 后前台=0x%X" % (ok, fg))
lp = (413 << 16) | 552
ctypes.windll.user32.PostMessageW(hwnd, 0x0201, 0, lp)
ctypes.windll.user32.PostMessageW(hwnd, 0x0202, 0, lp)
for i in range(15):
    time.sleep(0.2)
    c = dword(pid, h, pinv + 0x20)
    if c:
        print("+%.1fs 拿起 %#x" % ((i + 1) * 0.2, c))
        break
else:
    print("3s 未拿起")
ctypes.windll.kernel32.CloseHandle(h)
