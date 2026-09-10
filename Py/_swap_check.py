# -*- coding: utf-8 -*-
"""交换可行性检查（用户算法）:
1. 全内存扫描 A、B 物品 UnitAny 指针的所有命中
2. 取各自首位（最小命中地址）pA/pB，A 的占位偏移集 DA = hitsA - pA
3. 将 DA 映射到 pB：pB + d 处值 ∈ {B_ptr, 0} 全部满足 => 可替换
"""
from __future__ import annotations
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from _scan_grid_ptr import regions_of, scan_ptr

def main():
    pid = mem.find_process("D2Loader.exe")
    h = mem.open_process_readonly(pid)
    try:
        regions = regions_of(pid, h)
        # 仓库两个物品（当前进程实测）
        A = 0xa7ce100   # 辨识卷 530  loc45=4 格(7,7)
        B = 0x12671900  # 仓库物品47  loc45=4 格(4,4)
        hitsA = scan_ptr(pid, h, regions, A)
        hitsB = scan_ptr(pid, h, regions, B)
        pA, pB = min(hitsA), min(hitsB)
        DA = sorted(h - pA for h in hitsA)
        print(f"A(辨识卷) {A:#x} 命中{len(hitsA)} 首位{pA:#x} 偏移集{[hex(d) for d in DA]}")
        print(f"B(物品47)  {B:#x} 命中{len(hitsB)} 首位{pB:#x}")

        # 对照：pB + DA
        print("\n对照 pB+DA:")
        all_ok = True
        for d in DA:
            addr = pB + d
            raw = mem.read(pid, h, addr, 4)
            v = int.from_bytes(raw, "little") if raw else 0
            ok = (v == B) or (v == 0)
            tag = "B" if v == B else ("空" if v == 0 else "冲突!")
            if v not in (0, B):
                all_ok = False
            print(f"  {addr:#x}: {v:#x} {tag}")
        print(f"\n=> {'可以替换' if all_ok else '不可替换（存在冲突格）'}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
