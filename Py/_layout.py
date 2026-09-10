# -*- coding: utf-8 -*-
"""布局表动态获取模块。
- 扫描 D2CLIENT.DLL 内存中的 InventoryLayout 结构:
    +0x00 SlotWidth(格宽) +0x01 SlotHeight(格高) +0x04 Left +0x08 Right
    +0x0C Top +0x10 Bottom（像素边界, 客户区坐标）
- 识别: 10x10 -> 仓库; 10x4 且 Left 最大 -> 背包; 6x4 -> 盒子。
- 返回每面板: (left, top, cols, rows, pixel_w, pixel_h)
用法: lays = _layout.get(pid, h); base = lays['stash'][:2]
"""
import ctypes, sys
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as _mem

class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD), ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_wchar * 256), ("szExePath", ctypes.c_wchar * 260),
    ]

def _u32(b, o):
    return int.from_bytes(b[o:o + 4], "little")

def _byte(b, o):
    return b[o]

def _module_range(pid, name):
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

def _scan(pid, h):
    mr = _module_range(pid, "D2CLIENT.DLL")
    if not mr:
        return []
    base, size = mr
    buf = _mem.read(pid, h, base, size)
    out = []
    if not buf:
        return out
    for i in range(len(buf) - 0x18):
        sw, sh = _byte(buf, i), _byte(buf, i + 1)
        if not (sw in (10, 6, 4) and sh in (10, 8, 6, 4)):
            continue
        left, right = _u32(buf, i + 4), _u32(buf, i + 8)
        top, bottom = _u32(buf, i + 12), _u32(buf, i + 16)
        if not (0 < left < right < 5000 and 0 < top < bottom < 5000):
            continue
        pw, ph = (right - left + 1) / sw, (bottom - top + 1) / sh
        if 24 < pw < 34 and 24 < ph < 34:
            out.append((sw, sh, left, top, int(pw + 0.5), int(ph + 0.5)))
    return out

def get(pid, h):
    """返回 {'stash': (left,top,cols,rows,pw,ph), 'inventory': (...), 'cube': (...)}"""
    cands = _scan(pid, h)
    stash = [c for c in cands if (c[0], c[1]) == (10, 10)]
    invs = [c for c in cands if (c[0], c[1]) == (10, 4)]
    cubes = [c for c in cands if (c[0], c[1]) == (10, 8)]  # 盒子 10x8 (实测确认)
    r = {}
    if stash:
        c = max(stash, key=lambda x: x[2] * x[3])
        r["stash"] = (c[2], c[3], c[0], c[1], c[4], c[5])
    if invs:
        c = max(invs, key=lambda x: x[2])  # 背包面板 Left 最大
        r["inventory"] = (c[2], c[3], c[0], c[1], c[4], c[5])
    if cubes:
        c = cubes[0]
        r["cube"] = (c[2], c[3], c[0], c[1], c[4], c[5])
    return r
