# -*- coding: utf-8 -*-
"""验证: 用布局表 Left/Top 作为基准点击物品是否命中。"""
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import _human

def u32(b, o):
    return int.from_bytes(b[o:o+4], "little")

def byte(b, o):
    return b[o]

class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD), ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_wchar * 256), ("szExePath", ctypes.c_wchar * 260),
    ]

def module_range(pid, name):
    k32 = ctypes.WinDLL("kernel32")
    snap = k32.CreateToolhelp32Snapshot(0x00000008 | 0x00000010, pid)
    if snap == -1:
        return None
    e = MODULEENTRY32W(); e.dwSize = ctypes.sizeof(MODULEENTRY32W)
    if not k32.Module32FirstW(snap, ctypes.byref(e)):
        k32.CloseHandle(snap); return None
    while True:
        if e.szModule.lower() == name.lower():
            base = int(ctypes.addressof(e.modBaseAddr.contents))
            size = int(e.modBaseSize)
            k32.CloseHandle(snap)
            return base, size
        if not k32.Module32NextW(snap, ctypes.byref(e)):
            k32.CloseHandle(snap); return None

def find_layouts(pid, h):
    """扫描 D2CLIENT 找 InventoryLayout 结构, 返回 [(addr, sw, sh, left, top)]"""
    mr = module_range(pid, "D2CLIENT.DLL")
    if not mr:
        return []
    base, size = mr
    buf = mem.read(pid, h, base, size)
    out = []
    for i in range(len(buf) - 0x18):
        sw, sh = byte(buf, i), byte(buf, i + 1)
        if not (sw in (10, 6, 4) and sh in (10, 8, 6, 4)):
            continue
        left, right = u32(buf, i + 4), u32(buf, i + 8)
        top, bottom = u32(buf, i + 12), u32(buf, i + 16)
        if not (0 < left < right < 5000 and 0 < top < bottom < 5000):
            continue
        pw, ph = (right - left + 1) / sw, (bottom - top + 1) / sh
        if 24 < pw < 34 and 24 < ph < 34:
            out.append((base + i, sw, sh, left, top))
    return out

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

# 枚举窗口
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

# 读 pInv
d2c = mem.module_base(pid, "D2CLIENT.DLL")
def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0
pPlayer = dword(d2c + 0x11B800)
pInv = dword(pPlayer + 0x60)

# 找布局
lays = find_layouts(pid, h)
print("候选布局:")
for addr, sw, sh, l, t in lays:
    print("  %#x Slot=%dx%d Left=%d Top=%d" % (addr, sw, sh, l, t))

# 挑 10x10(仓库) 和 10x4(背包) 中与已知基准最接近的
def pick(grid, known):
    cand = [x for x in lays if (x[1], x[2]) == grid]
    if not cand:
        return None
    return min(cand, key=lambda x: abs(x[3]-known[0]) + abs(x[4]-known[1]))

st = pick((10, 10), (538, 370))
bg = pick((10, 4), (857, 541))
print("仓库布局:", st, " 背包布局:", bg)

CELL = 29
for nm, lay, gx, gy in [("仓库", st, 0, 0), ("背包", bg, 0, 0)]:
    if not lay:
        print(nm, "无布局"); continue
    addr, sw, sh, left, top = lay
    x = left + gx * CELL + CELL // 2
    y = top + gy * CELL + CELL // 2
    _human.reset()
    _human.click(hwnd, x, y)
    _human.wait()
    c = dword(pInv + 0x20)
    if c:
        idat = dword(c + 0x14)
        loc = mem.read(pid, h, idat + 0x45, 1)[0]
        txt = dword(c + 0x04)
        print("%s 布局点击(%d,%d) 拿起 txt=%d loc=%d ✓" % (nm, x, y, txt, loc))
        # 放回
        _human.click(hwnd, x, y)
        _human.wait()
    else:
        print("%s 布局点击(%d,%d) 未拿起 ✗" % (nm, x, y))
ctypes.windll.kernel32.CloseHandle(h)
