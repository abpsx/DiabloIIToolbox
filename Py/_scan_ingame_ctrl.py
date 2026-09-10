#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""游戏内控件链根扫描：
全内存搜 @0x34(回调) 落在 D2Win 代码区的 dword，命中位置-0x34 若像控件结构(小type/合理pos/size)即为候选控件，
再沿 pNext@0x3C 前后遍历找链头。
"""
import ctypes
import sys
from ctypes import wintypes

sys.path.insert(0, ".")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
MEM_COMMIT = 0x1000
PAGE_READABLE = 0x02 | 0x04 | 0x08 | 0x10 | 0x40 | 0x80  # RW/R/X/XC/RWX/RWXC


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


def enum_regions(pid: int, h: int):
    """VirtualQueryEx 枚举可读已提交区域。"""
    regions = []
    addr = 0
    while addr < 0x7FFFFFFF:
        mbi = MEMORY_BASIC_INFORMATION()
        sz = kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi),
                                     ctypes.sizeof(mbi))
        if not sz:
            break
        if (mbi.State == MEM_COMMIT) and (mbi.Protect & PAGE_READABLE) and mbi.RegionSize:
            regions.append((int(mbi.BaseAddress or 0), int(mbi.RegionSize), mbi.Protect))
        addr = int(mbi.BaseAddress or 0) + int(mbi.RegionSize)
    return regions


def scan(pid: int, h: int, lo: int, hi: int):
    """搜 dword ∈ [lo,hi) 的位置，返回候选控件基址列表。"""
    cands = []
    for base, size, prot in enum_regions(pid, h):
        if size > 64 * 1024 * 1024:
            continue  # 跳过超大区域(图像/大堆)
        step = 0x1000
        for off in range(0, size, step):
            n = min(step, size - off)
            raw = mem.read(pid, h, base + off, n)
            if not raw:
                continue
            for i in range(0, len(raw) - 3, 1):
                v = int.from_bytes(raw[i:i + 4], "little")
                if lo <= v < hi:
                    cands.append(base + off + i)
    return cands


def looks_ctrl(pid: int, h: int, addr: int, d2base: int) -> bool:
    t = mem.read_dword(pid, h, addr)
    if t > 0x10:
        return False
    px = mem.read_dword(pid, h, addr + 0x0C)
    py = mem.read_dword(pid, h, addr + 0x10)
    sx = mem.read_dword(pid, h, addr + 0x14)
    sy = mem.read_dword(pid, h, addr + 0x18)
    if not (0 <= px < 2000 and 0 <= py < 2000 and 0 < sx < 2000 and 0 < sy < 2000):
        return False
    cb = mem.read_dword(pid, h, addr + 0x34)
    if not (d2base + 0x1000 <= cb < d2base + 0x20000):
        return False
    return True


def main() -> None:
    pid = mem.find_process("D2Loader.exe")
    if pid is None:
        print("D2Loader.exe 未运行")
        return 1
    h = mem.open_process_readonly(pid)
    if not h:
        print("OpenProcess 失败")
        return 1
    try:
        d2base = mem.module_base(pid, "D2Win.dll")
        lo, hi = d2base + 0x1000, d2base + 0x20000
        print(f"D2Win base=0x{d2base:X} 回调区=[0x{lo:X},0x{hi:X})")
        print("扫描中…")
        hits = scan(pid, h, lo, hi)
        print(f"@0x34∈D2Win代码区 命中 {len(hits)} 处")

        ctrls = [a - 0x34 for a in hits if looks_ctrl(pid, h, a - 0x34, d2base)]
        print(f"结构校验后控件候选 {len(ctrls)} 个")
        # 按 addr 排序
        ctrls = sorted(set(ctrls))
        for a in ctrls:
            t = mem.read_dword(pid, h, a)
            px = mem.read_dword(pid, h, a + 0x0C)
            py = mem.read_dword(pid, h, a + 0x10)
            nxt = mem.read_dword(pid, h, a + 0x3C)
            print(f"  ctrl 0x{a:08X} type={t} pos=({px},{py}) next=0x{nxt:08X}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
