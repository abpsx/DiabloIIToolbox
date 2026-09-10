#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump 创造新按钮 @0x20~0x70 全字段 + 附近堆，找 '人物' 第二文本。"""
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
    while cur and n < 40:
        c = mem.read(pid, h, cur, 0x80)
        t = int.from_bytes(c[0:4], "little")
        x = int.from_bytes(c[0x0C:0x10], "little")
        y = int.from_bytes(c[0x10:0x14], "little")
        if t == 6 and x == 33 and y == 528:
            print(f"创造新 BTN 0x{cur:X}")
            for o in range(0x20, 0x70, 4):
                v = int.from_bytes(c[o:o+4], "little")
                extra = ""
                if v > 0x10000 and (0x01000000 <= v <= 0x40000000 or 0x0B000000 <= v <= 0x0C000000):
                    s = mem.read(pid, h, v, 32)
                    s = mem._wstr_cut(s).decode("utf-16-le", errors="replace") if s else ""
                    extra = f" -> {s!r}"
                print(f"  +0x{o:02X}: 0x{v:08X}{extra}")
        nxt = int.from_bytes(c[0x3C:0x40], "little")
        cur = nxt
        n += 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
