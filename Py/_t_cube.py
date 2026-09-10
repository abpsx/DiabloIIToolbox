# -*- coding: utf-8 -*-
"""核查: 盒子是否 10x10。全模块放宽扫描所有 Slot 宽高 + 盒子开关状态。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

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

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

d2c = mem.module_base(pid, "D2CLIENT.DLL")
# 盒子开关 0x50D00+0x64
cube_open = dword(d2c + 0x50D00 + 0x64)
print("盒子开关(0x50D00+0x64):", cube_open)

for mod in ["D2CLIENT.DLL", "D2Common.dll", "D2Win.dll", "D2Gfx.dll", "D2Lang.dll"]:
    mr = module_range(pid, mod)
    if not mr:
        continue
    base, size = mr
    buf = mem.read(pid, h, base, size)
    if not buf:
        continue
    hits = []
    for i in range(len(buf) - 0x18):
        sw, sh = byte(buf, i), byte(buf, i + 1)
        if not (1 <= sw <= 12 and 1 <= sh <= 12):
            continue
        left, right = u32(buf, i + 4), u32(buf, i + 8)
        top, bottom = u32(buf, i + 12), u32(buf, i + 16)
        if not (0 < left < right < 5000 and 0 < top < bottom < 5000):
            continue
        pw, ph = (right - left + 1) / sw, (bottom - top + 1) / sh
        if 15 < pw < 45 and 15 < ph < 45:
            hits.append((base + i, sw, sh, left, top, pw, ph))
    print("----", mod, len(hits), "候选")
    for addr, sw, sh, l, t, pw, ph in hits:
        tag = ""
        if (sw, sh) == (10, 10):
            tag = " <== 10x10"
        print("  %s+%#x: Slot=%dx%d Left=%d Top=%d px=%.1fx%.1f%s"
              % (mod, addr - base, sw, sh, l, t, pw, ph, tag))
ctypes.windll.kernel32.CloseHandle(h)
