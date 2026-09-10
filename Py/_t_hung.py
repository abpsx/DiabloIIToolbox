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

hung = ctypes.windll.user32.IsHungAppWindow(hwnd)
print("IsHungAppWindow=%d" % hung)

# SendMessageTimeout WM_NULL 测响应
WM_NULL = 0x0000
SMTO_ABORTIFHUNG = 0x0002
res = wintypes.DWORD()
r = ctypes.windll.user32.SendMessageTimeoutW(hwnd, WM_NULL, 0, 0, SMTO_ABORTIFHUNG, 3000, ctypes.byref(res))
print("SendMessageTimeout(WM_NULL) rc=%d" % r)

# 物品状态
cur = dword(pid, h, pinv + 0x0C)
seen = set()
while cur and cur not in seen:
    seen.add(cur)
    txt = dword(pid, h, cur + 0x04)
    idat = dword(pid, h, cur + 0x14)
    loc = mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1
    if loc == 4:
        pip = dword(pid, h, cur + 0x2C)
        print("仓库: txt=%d 格(%d,%d)" % (txt, dword(pid, h, pip + 0x0C), dword(pid, h, pip + 0x10)))
    cur = dword(pid, h, idat + 0x64) if idat else 0
print("pCursorItem=%#x" % dword(pid, h, pinv + 0x20))

# SendMessage 同步点击 (0,1)=(552,413) 拿起辨识卷
lp = (413 << 16) | 552
t0 = time.time()
r1 = ctypes.windll.user32.SendMessageW(hwnd, 0x0201, 0, lp)
r2 = ctypes.windll.user32.SendMessageW(hwnd, 0x0202, 0, lp)
print("SendMessage 点击 rc=(%d,%d) 耗时 %.2fs" % (r1, r2, time.time() - t0))
for i in range(15):
    time.sleep(0.2)
    c = dword(pid, h, pinv + 0x20)
    if c:
        print("+%.1fs 拿起 %#x" % ((i + 1) * 0.2, c))
        break
else:
    print("3s 未拿起")
ctypes.windll.kernel32.CloseHandle(h)
