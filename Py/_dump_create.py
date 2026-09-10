#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump 创造新按钮完整文本区，找 '人物'。"""
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
            pft = int.from_bytes(c[0x48:0x4C], "little")
            print(f"创造新 BTN 0x{cur:X} pFirstText=0x{pft:X}")
            # @0x5C..0x70 全 dump
            raw = mem.read(pid, h, cur + 0x5C, 48)
            print("  @0x5C:", " ".join(f"{b:02X}" for b in raw))
            # @0x64 起 64 字节
            raw2 = mem.read(pid, h, cur + 0x64, 64)
            print("  @0x64:", " ".join(f"{b:02X}" for b in raw2))
            # pFirstText 链
            if pft:
                ct = mem.read(pid, h, pft, 0x20)
                print("  ControlText@", hex(pft))
                for j in range(5):
                    wp = int.from_bytes(ct[j*4:j*4+4], "little")
                    if wp and wp > 0x10000:
                        s = mem.read(pid, h, wp, 64)
                        s = mem._wstr_cut(s).decode("utf-16-le", errors="replace")
                        print(f"    wText[{j}]=0x{wp:X} -> {s!r}")
                nxt = int.from_bytes(ct[0x1C:0x20], "little")
                print(f"    pNext=0x{nxt:X}")
        nxt = int.from_bytes(c[0x3C:0x40], "little")
        cur = nxt
        n += 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
