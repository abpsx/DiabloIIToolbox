#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump 角色选择界面按钮文本区 + TEXTBOX pFirstText 链。"""
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
        pft = int.from_bytes(c[0x48:0x4C], "little")
        if t == 6:
            raw = mem.read(pid, h, cur + 0x64, 96)
            hexs = " ".join(f"{b:02X}" for b in raw[:48])
            # 快速可打印 utf16
            u = raw.split(b"\x00\x00")
            print(f"BTN 0x{cur:X} ({x},{y}) @0x64 [{hexs}]")
            # 全部非零段
            segs, cseg = [], []
            for i in range(0, len(raw) - 1, 2):
                w = raw[i] | (raw[i+1] << 8)
                if w == 0:
                    if cseg: segs.append("".join(chr(w2) for w2 in cseg)); cseg = []
                else:
                    cseg.append(w)
            if cseg: segs.append("".join(chr(w2) for w2 in cseg))
            print(f"    segs={segs}")
        elif t == 4 and y == 178 and x == 37:
            print(f"TXTBOX 0x{cur:X} ({x},{y}) pFirstText=0x{pft:X}")
            if pft:
                ct = mem.read(pid, h, pft, 0x20)
                for j in range(0, 4):
                    w0 = int.from_bytes(ct[j*4:j*4+4], "little")
                    if w0 and w0 > 0x10000:
                        s = mem.read(pid, h, w0, 128)
                        s = s.split(b"\x00\x00")[0].decode("utf-16-le", errors="replace")
                        print(f"    wText[{j}]=0x{w0:X} -> {s!r}")
        nxt = int.from_bytes(c[0x3C:0x40], "little")
        cur = nxt
        n += 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
