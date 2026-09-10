#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 @0x04 指向内容 + @0x34 唯一性。"""
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
    print("idx type addr       _04val   _04->[0..3]  _34     _34code?")
    while cur and n < 30:
        c = mem.read(pid, h, cur, 0x5C)
        t = int.from_bytes(c[0:4], "little")
        if t == 6:  # 只看按钮
            v04 = int.from_bytes(c[0x04:0x08], "little")
            v34 = int.from_bytes(c[0x34:0x38], "little")
            d04 = mem.read(pid, h, v04, 4) if v04 > 0x10000 else b""
            b0 = int.from_bytes(d04, "little") if d04 else 0
            # @0x34 指向的内容前 8 字节（若可读）
            d34 = mem.read(pid, h, v34, 8) if v34 > 0x10000 else b""
            # 判断 @0x34 是否为代码地址（D2Win 内）
            inwin = (base <= v34 < base + 0x300000)
            print(f"  {cur:08X} t=6 _04={v04:08X} -> {b0:08X}  _34={v34:08X} inD2Win={inwin}")
        nxt = int.from_bytes(c[0x3C:0x40], "little")
        cur = nxt
        n += 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
