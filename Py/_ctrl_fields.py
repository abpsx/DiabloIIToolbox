#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比控件回调字段，找准唯一值。"""
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
    print("idx type     addr       _04     _1C     _24     _28     _34     _40     selE    selS  pos")
    while cur and n < 30:
        c = mem.read(pid, h, cur, 0x5C)
        t = int.from_bytes(c[0:4], "little")
        x = int.from_bytes(c[0x0C:0x10], "little")
        y = int.from_bytes(c[0x10:0x14], "little")
        vals = []
        for o in (0x04, 0x1C, 0x24, 0x28, 0x34, 0x40, 0x54, 0x58):
            vals.append("{:08X}".format(int.from_bytes(c[o:o+4], "little")))
        print(f"#{n:<3} 0x{t:02X}      {cur:08X} " + " ".join(vals) + f"   ({x},{y})")
        nxt = int.from_bytes(c[0x3C:0x40], "little")
        cur = nxt
        n += 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
