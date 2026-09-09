#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按钮文本指针字段验证。"""
import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    base = mem.module_base(pid, "D2Win.dll")
    first = mem.read_ptr(pid, h, base + 0x214A0)
    cur, n = first, 0
    while cur and n < 12:
        c = mem.read(pid, h, cur, 0x80)
        t = int.from_bytes(c[0:4], "little")
        x = int.from_bytes(c[0x0C:0x10], "little")
        y = int.from_bytes(c[0x10:0x14], "little")
        if t == 6 and x == 264 and y in (324, 366, 433, 391):
            p5c = int.from_bytes(c[0x5C:0x60], "little")
            p60 = int.from_bytes(c[0x60:0x64], "little")
            p64 = int.from_bytes(c[0x64:0x68], "little")
            print(f"0x{cur:X} pos=({x},{y})")
            print(f"  @0x5C={p5c:X} @0x60={p60:X} @0x64={p64:X} @0x68={int.from_bytes(c[0x68:0x6C],'little'):X}")
            for lbl, p in (("0x5C", p5c), ("0x60", p60), ("0x64", p64)):
                if p and not (0x400000 <= p < 0x500000):
                    s = mem.read(pid, h, p, 64)
                    print(f"  [{lbl}] 0x{p:X} -> {s.split(b'\x00\x00')[0].decode('utf-16-le', errors='replace')!r}" if s else f"  [{lbl}] 0x{p:X} 空")
            print("  @0x40..0x58:", " ".join(f"{int.from_bytes(c[o:o+4],'little'):08X}" for o in range(0x40, 0x58, 4)))
        nxt = int.from_bytes(c[0x3C:0x40], "little")
        cur = nxt
        n += 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
