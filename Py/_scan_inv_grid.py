# -*- coding: utf-8 -*-
"""dump 背包 Inventory 结构尾部，搜索格子指针数组。

pInv=0x11697ec0；物品：城镇卷=0x23c6e00 辨识卷=0x23c7000。
查找包含这些指针的连续数组区域（4字节对齐）。
"""
from __future__ import annotations
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def main():
    pid = mem.find_process("D2Loader.exe")
    h = mem.open_process_readonly(pid)
    try:
        d2c = mem.module_base(pid, "D2CLIENT.DLL")
        pPlayer = dword(pid, h, d2c + 0x11B800)
        pInv = dword(pid, h, pPlayer + 0x60)
        print(f"pInv={pInv:#x}")
        targets = {0x23c6e00: "城镇卷", 0x23c7000: "辨识卷"}

        # 1) pInv 前后区域扫描（pInv-0x200 .. pInv+0x1000）
        for lo in (pInv - 0x200, pInv, pInv + 0x400):
            print(f"\n-- 区域 {lo:#x} .. {lo+0x1000:#x} --")
            for off in range(0, 0x1000, 4):
                v = dword(pid, h, lo + off)
                if v in targets:
                    print(f"   {lo+off:#x}: {targets[v]}")

        # 2) 背包链物品的 pNextInvItem 引用区域（物品结构本身）
        print("\n-- 物品结构内引用 --")
        for unit in (0x23c6e00, 0x23c7000):
            for off in range(0, 0x100, 4):
                v = dword(pid, h, unit + off)
                if v in targets:
                    print(f"   {unit+off:#x} (unit+{off:#x}): {targets[v]}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
