# -*- coding: utf-8 -*-
"""反查 0x02C3E370 的引用指针 + 归属"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

# 0x02C3E370 归属
mbi = MBI()
kernel32.VirtualQueryEx(h, ctypes.c_void_p(0x02C3E370), ctypes.byref(mbi), ctypes.sizeof(mbi))
print(f"0x02C3E370: alloc=0x{mbi.AllocationBase:X} base=0x{mbi.BaseAddress:X} size=0x{mbi.RegionSize:X} protect=0x{mbi.Protect:X} type=0x{mbi.Type:X}")

# 反查 dword == 0x02C3E370
target = (0x02C3E370).to_bytes(4, "little")
regions = []
addr = 0x10000
while addr < 0x7FFFFFFF:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

# 模块表
class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("GlblcntUsage", wintypes.DWORD), ("ProccntUsage", wintypes.DWORD),
                ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)), ("modBaseSize", wintypes.DWORD),
                ("hModule", wintypes.HMODULE), ("szModule", ctypes.c_wchar * 256), ("szExePath", ctypes.c_wchar * 260)]
snap = kernel32.CreateToolhelp32Snapshot(0x8 | 0x10, pid)
mods = []
e = MODULEENTRY32W(); e.dwSize = ctypes.sizeof(MODULEENTRY32W)
if kernel32.Module32FirstW(snap, ctypes.byref(e)):
    while True:
        mods.append((int(ctypes.addressof(e.modBaseAddr.contents)), e.modBaseSize, e.szModule))
        if not kernel32.Module32NextW(snap, ctypes.byref(e)):
            break
kernel32.CloseHandle(snap)

def mod_of(a):
    for b, sz, name in mods:
        if b <= a < b + sz:
            return f"{name}+0x{a-b:X}"
    return "heap"

hits = []
for lo, size in regions:
    chunk = 0x100000
    for off in range(0, size, chunk):
        buf = mem.read(pid, h, lo + off, min(chunk, size - off))
        if not buf:
            continue
        p = 0
        while True:
            i = buf.find(target, p)
            if i < 0:
                break
            a = lo + off + i
            hits.append(a)
            if len(hits) >= 30:
                break
            p = i + 1
        if len(hits) >= 30:
            break
    if len(hits) >= 30:
        break

print(f"\n指向 0x02C3E370 的指针 {len(hits)} 处:")
for a in hits:
    print(f"  0x{a:X} ({mod_of(a)})")
ctypes.windll.kernel32.CloseHandle(h)
