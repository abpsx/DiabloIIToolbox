# -*- coding: utf-8 -*-
"""验证 0x02CBE36C + 归属 + 一级/多级反查静态指针"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

TARGET = 0x02CBE36C

# 1) 验证值
p = mem.read_ptr(pid, h, TARGET)
inner = mem.read_dword(pid, h, p) if p else 0
print(f"[0x{TARGET:X}] = 0x{p:X}  ->  [内] dword = {inner} (0x{inner:X})")
print(f"页数(1基) = {inner + 1 if inner else '?'}")

# 2) 归属
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]
mbi = MBI()
kernel32.VirtualQueryEx(h, ctypes.c_void_p(TARGET), ctypes.byref(mbi), ctypes.sizeof(mbi))
print(f"\n归属: alloc=0x{mbi.AllocationBase:X} base=0x{mbi.BaseAddress:X} size=0x{mbi.RegionSize:X} type=0x{mbi.Type:X}")

# 3) 模块表
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
print("\n模块表:")
for b, sz, name in mods:
    print(f"  {name}: 0x{b:X} size=0x{sz:X}")

def mod_of(a):
    for b, sz, name in mods:
        if b <= a < b + sz:
            return f"{name}+0x{a-b:X}"
    return "heap"

# 4) 全内存扫描：一级反查（谁的值==TARGET）
target_bytes = TARGET.to_bytes(4, "little")
print(f"\n=== 一级反查: dword == 0x{TARGET:X} ===")
regions = []
addr = 0x10000
while addr < 0x7FFFFFFF:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

def scan_for(needle, maxhits=40):
    hits = []
    for lo, size in regions:
        chunk = 0x100000
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(needle, p)
                if i < 0:
                    break
                a = lo + off + i
                hits.append(a)
                if len(hits) >= maxhits:
                    return hits
                p = i + 1
            if len(hits) >= maxhits:
                return hits
        if len(hits) >= maxhits:
            return hits
    return hits

hits1 = scan_for(target_bytes)
print(f"命中 {len(hits1)} 处:")
for a in hits1[:40]:
    print(f"  0x{a:X} ({mod_of(a)})")

# 5) 若一级命中在堆，二级反查（谁指向这些堆地址）
print(f"\n=== 二级反查 ===")
heap_hits = [a for a in hits1 if mod_of(a) == "heap"]
if heap_hits and len(heap_hits) <= 10:
    for hh in heap_hits:
        hits2 = scan_for(hh.to_bytes(4, "little"), 10)
        if hits2:
            print(f"  指向 0x{hh:X} 的指针:")
            for a in hits2:
                print(f"    0x{a:X} ({mod_of(a)})")
ctypes.windll.kernel32.CloseHandle(h)
