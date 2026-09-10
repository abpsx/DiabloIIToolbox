# -*- coding: utf-8 -*-
"""交换可行性检查 v2（按区域聚类）:
1. 扫描 A/B 全部命中，按 0x1000 页聚类
2. 找 A/B 共享页（格子数组区域特征：同一区域存多个物品指针）
3. 取共享页内各自首位，A 的页内偏移集映射到 B，检查全部命中(值∈{B,0})
"""
from __future__ import annotations
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from _scan_grid_ptr import regions_of, scan_ptr

def page_of(a): return a & ~0xFFF

def main():
    pid = mem.find_process("D2Loader.exe")
    h = mem.open_process_readonly(pid)
    try:
        regions = regions_of(pid, h)
        A, B = 0xa7ce100, 0x12671900   # 辨识卷 / 仓库物品47
        hitsA, hitsB = scan_ptr(pid, h, regions, A), scan_ptr(pid, h, regions, B)
        # 按页聚类
        from collections import defaultdict
        pgA, pgB = defaultdict(list), defaultdict(list)
        for a in hitsA: pgA[page_of(a)].append(a)
        for b in hitsB: pgB[page_of(b)].append(b)
        print("A 命中按页:")
        for p, lst in sorted(pgA.items()):
            print(f"  {p:#x}: {len(lst)} {[hex(x) for x in sorted(lst)]}")
        print("B 命中按页:")
        for p, lst in sorted(pgB.items()):
            print(f"  {p:#x}: {len(lst)} {[hex(x) for x in sorted(lst)]}")
        shared = sorted(set(pgA) & set(pgB))
        print(f"\n共享页: {[hex(p) for p in shared]}")
        if not shared:
            print("无共享页 -> 无法定位格子数组"); return 1
        # 取共享页（多页时取 A/B 命中总数最多的页）
        best = max(shared, key=lambda p: len(pgA[p]) + len(pgB[p]))
        print(f"取共享页 {best:#x}")
        la, lb = sorted(pgA[best]), sorted(pgB[best])
        pA, pB = la[0], lb[0]
        DA = [x - pA for x in la]
        print(f"A 页内命中 {la}  首位 {pA:#x} 偏移集 {[hex(d) for d in DA]}")
        print(f"B 页内命中 {lb}  首位 {pB:#x}")
        all_ok = True
        for d in DA:
            v = int.from_bytes(mem.read(pid, h, pB + d, 4) or b"\0\0\0\0", "little")
            ok = v in (0, B)
            all_ok &= ok
            print(f"  {pB+d:#x}: {v:#x} {'B' if v==B else ('空' if v==0 else '冲突!')}")
        print(f"\n=> {'可以替换' if all_ok else '不可替换（存在冲突格）'}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
