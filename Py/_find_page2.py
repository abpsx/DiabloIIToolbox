# -*- coding: utf-8 -*-
"""受控搜索：聚合命中区间 + 对代表地址反查指针"""
import sys, ctypes, collections
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

needle = "当前页数".encode("utf-16-le")

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

# 第一遍：计数（按 0x10000 区间聚合），收集每区间首个地址
buckets = collections.Counter()
first_in_bucket = {}
total = 0
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
            b = a & ~0xFFFF
            buckets[b] += 1
            if b not in first_in_bucket:
                first_in_bucket[b] = a
            total += 1
            p = i + 1

print(f"总命中 {total} 处，聚合 {len(buckets)} 个 64KB 区间")
for b, c in buckets.most_common(12):
    a = first_in_bucket[b]
    tail = mem.read(pid, h, a, 48).decode("utf-16-le", errors="replace")
    print(f"  0x{b:08X} x{c}  首个 0x{a:X}: {tail!r}")

# 对 top 区间首地址反查指针（限制范围）
print("\n反查指针（每个代表地址最多 8 个）:")
for b, c in buckets.most_common(6):
    a = first_in_bucket[b]
    needle_b = a.to_bytes(4, "little")
    ptrs = []
    for lo, size in regions:
        chunk = 0x100000
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(needle_b, p)
                if i < 0:
                    break
                ptrs.append(lo + off + i)
                if len(ptrs) >= 8:
                    break
                p = i + 1
            if len(ptrs) >= 8:
                break
        if len(ptrs) >= 8:
            break
    # 打印指针所在模块
    mods = {}
    for m in mem._modules if hasattr(mem, "_modules") else []:
        pass
    print(f"  0x{a:X} <- {[hex(x) for x in ptrs]}")

ctypes.windll.kernel32.CloseHandle(h)
