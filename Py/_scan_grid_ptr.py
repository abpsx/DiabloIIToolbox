# -*- coding: utf-8 -*-
"""全内存扫描物品 UnitAny 指针值，分析格子指针数组布局。

原理（用户提示）: 背包/仓库格子区是 dword 指针数组，每格存指向物品的指针；
同一物品占多格 -> 连续格子存相同指针值。
用已知物品指针(城镇卷 0x23c6e00 / 辨识卷 0x23c7000)反查其出现的地址簇。
"""
from __future__ import annotations
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

def regions_of(pid, h):
    out = []
    addr = 0x10000
    while addr < 0x7FFFFFFF:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
            out.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF
    return out

def scan_ptr(pid, h, regions, val, chunk=0x20000):
    """全内存扫 dword 值 val，返回命中地址列表。"""
    needle = (val & 0xFFFFFFFF).to_bytes(4, "little")
    hits = []
    for lo, size in regions:
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(needle, p)
                if i < 0:
                    break
                hits.append(lo + off + i)
                p = i + 1
    return hits

def cluster(hits, gap=8):
    """按地址连续性分组（连续格地址差 4 为一簇，容忍 gap）。"""
    hits = sorted(set(hits))
    groups = []
    cur = [hits[0]] if hits else []
    for a in hits[1:]:
        if a - cur[-1] <= gap:
            cur.append(a)
        else:
            groups.append(cur)
            cur = [a]
    if cur:
        groups.append(cur)
    return groups

def main():
    pid = mem.find_process("D2Loader.exe")
    h = mem.open_process_readonly(pid)
    try:
        regions = regions_of(pid, h)
        print(f"可读区 {len(regions)} 个")
        targets = {0x23c6e00: "城镇卷529", 0x23c7000: "辨识卷530"}
        for val, label in targets.items():
            hits = scan_ptr(pid, h, regions, val)
            print(f"\n[{label}] {val:#x} 命中 {len(hits)} 处:")
            for g in cluster(hits, gap=8):
                if len(g) < 2:
                    print(f"  单点 {g[0]:#x}")
                else:
                    print(f"  簇 {g[0]:#x}..{g[-1]:#x} 共 {len(g)} 个 步进={g[1]-g[0]}")
            # 详细打印前几个命中上下文（看是否在格子数组）
            for a in hits[:12]:
                print(f"    @ {a:#x} (+{a % 0x1000:#x})")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
