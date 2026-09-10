# -*- coding: utf-8 -*-
"""精确搜 '当前页数 : 10页' 实例 + 检查原 2页 地址现状"""
import sys, ctypes, collections
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def read16(a, n):
    raw = mem.read(pid, h, a, n)
    return raw.decode("utf-16-le", errors="replace") if raw else ""

# 1) 原 2页 地址现状
print("原 0x109C0038 现状:", repr(read16(0x109C0038, 60)))

# 2) 精确搜 10页
needle = "当前页数 : 10页".encode("utf-16-le")
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

regions = []
addr = 0x10000
while addr < 0x7FFFFFFF:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

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
            if len(hits) >= 30:
                break
            p = i + 1
        if len(hits) >= 30:
            break
    if len(hits) >= 30:
        break

print(f"\n'当前页数 : 10页' 命中 {len(hits)} 处:")
for a in hits:
    # 所在 region 的 AllocationBase
    mbi = MBI()
    kernel32.VirtualQueryEx(h, ctypes.c_void_p(a), ctypes.byref(mbi), ctypes.sizeof(mbi))
    print(f"  0x{a:X}  (alloc=0x{mbi.AllocationBase:X} base=0x{mbi.BaseAddress:X} size=0x{mbi.RegionSize:X}) {read16(a, 50)!r}")

# 3) 也搜 '当前页数 :' 只列前 20（看数字分布）
print("\n'当前页数 :' 前 20 实例数字:")
needle2 = "当前页数 :".encode("utf-16-le")
n2 = 0
for lo, size in regions:
    chunk = 0x100000
    for off in range(0, size, chunk):
        buf = mem.read(pid, h, lo + off, min(chunk, size - off))
        if not buf:
            continue
        p = 0
        while True:
            i = buf.find(needle2, p)
            if i < 0:
                break
            a = lo + off + i
            s = read16(a, 40)
            print(f"  0x{a:X}: {s!r}")
            n2 += 1
            if n2 >= 20:
                break
            p = i + 1
        if n2 >= 20:
            break
    if n2 >= 20:
        break

ctypes.windll.kernel32.CloseHandle(h)
