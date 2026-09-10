# -*- coding: utf-8 -*-
"""细 dump 仓库物品节点原始字段，验证格坐标/wX/wY/绘制坐标读取。"""
from __future__ import annotations
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def main():
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    try:
        d2c = mem.module_base(pid, "D2CLIENT.DLL")
        pPlayer = dword(pid, h, d2c + 0x11B800)
        pInv = dword(pid, h, pPlayer + 0x60)
        print(f"pPlayer={pPlayer:#x} pInv={pInv:#x} stamp={dword(pid,h,pInv):#x}")
        cur = dword(pid, h, pInv + 0x0C)
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            txt = dword(pid, h, cur + 0x04)
            idat = dword(pid, h, cur + 0x14)
            loc45 = mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1
            loc69 = mem.read(pid, h, idat + 0x69, 1)[0] if idat else -1
            pip = dword(pid, h, cur + 0x2C)
            raw8C = dword(pid, h, cur + 0x8C)
            raw90 = dword(pid, h, cur + 0x90)
            print(f"\nunit={cur:#x} txt={txt} loc45={loc45} loc69={loc69}")
            print(f"  pPath(0x2C)={pip:#x}")
            if pip:
                for off in (0x00, 0x04, 0x0C, 0x10, 0x14, 0x18):
                    v = dword(pid, h, pip + off)
                    print(f"    path+{off:#04x} = {v:#x} ({v})")
            print(f"  unit+0x8C dword={raw8C:#x} (低16={raw8C&0xFFFF}, 高16={(raw8C>>16)&0xFFFF})")
            print(f"  unit+0x90 dword={raw90:#x}")
            # ItemData 0x40..0x70 字节扫描，找可能的 x/y
            raw = mem.read(pid, h, idat + 0x40, 0x30) if idat else b""
            if raw:
                print("  ItemData+0x40:", " ".join(f"{b:02X}" for b in raw))
            cur = dword(pid, h, idat + 0x64) if idat else 0
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
