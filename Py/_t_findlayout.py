# -*- coding: utf-8 -*-
"""内存搜索 InventoryLayout 结构（宽高+像素边界）。
特征: +0x00 SlotWidth, +0x01 SlotHeight, +0x04 Left, +0x08 Right, +0x0C Top, +0x10 Bottom
筛选: Left<Right<Top? 像素/格≈29; 仓库 Left≈538/Top≈370; 背包 Left≈857/Top≈541
"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def u32(b, o):
    return int.from_bytes(b[o:o+4], "little")

def u16(b, o):
    return int.from_bytes(b[o:o+2], "little")

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

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

hits = []
for mod in ["D2CLIENT.DLL", "D2Common.dll", "D2Win.dll", "D2Gfx.dll"]:
    mr = module_range(pid, mod)
    if not mr:
        print(mod, "无"); continue
    base, size = mr
    buf = mem.read(pid, h, base, size)
    if not buf:
        print(mod, "读失败"); continue
    n = 0
    # 搜 SlotWidth,SlotHeight 开头（0A 0A 或 0A 04 或 04 0A 等常见）
    for i in range(len(buf) - 0x18):
        sw, sh = byte(buf, i), byte(buf, i + 1)
        if not (sw in (10, 8, 6, 4, 3, 2, 1) and sh in (10, 8, 6, 4, 3, 2, 1)):
            continue
        left, right = u32(buf, i + 4), u32(buf, i + 8)
        top, bottom = u32(buf, i + 12), u32(buf, i + 16)
        if not (0 < left < right < 5000 and 0 < top < bottom < 5000):
            continue
        pw, ph = (right - left + 1) / sw, (bottom - top + 1) / sh
        if 24 < pw < 34 and 24 < ph < 34:  # 每格 29px 左右
            hits.append((mod, base + i, sw, sh, left, right, top, bottom, pw, ph))
            n += 1
    print("%s: %d 候选" % (mod, n))

print("---- 候选布局 ----")
for m, addr, sw, sh, l, r, t, b, pw, ph in hits:
    tag = ""
    if abs(l - 538) < 30 and abs(t - 370) < 30:
        tag = " <== 仓库(0,0)基准匹配"
    if abs(l - 857) < 30 and abs(t - 541) < 30:
        tag = " <== 背包(0,0)基准匹配"
    print("  %s+%#x: Slot=%dx%d  Left=%d Right=%d Top=%d Bottom=%d  px/格=%.1fx%.1f%s"
          % (m, addr - mem.module_base(pid, m) if False else addr - 0, sw, sh, l, r, t, b, pw, ph, tag))
ctypes.windll.kernel32.CloseHandle(h)
