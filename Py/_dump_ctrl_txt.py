#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump 按钮/TEXTBOX 文本区真实字节，确认分段/换行结构。"""
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
        if (t == 6 and x == 264 and y in (324, 366, 391, 568)) or (t == 4):
            print(f"--- type={t} pos=({x},{y}) 0x{cur:X} ---")
            for off in (0x5C, 0x64):
                raw = mem.read(pid, h, cur + off, 48)
                if raw:
                    hexs = " ".join(f"{b:02X}" for b in raw[:32])
                    print(f"  @+0x{off:X} [{hexs}]")
        nxt = int.from_bytes(c[0x3C:0x40], "little")
        cur = nxt
        n += 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
