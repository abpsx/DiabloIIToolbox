#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜 '人物' UTF-16 全内存 + 反查引用结构。"""
import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    pat = "人物".encode("utf-16-le")  # 4C 4E 09 72
    hits = []
    for lo, hi in [(0x01000000, 0x04000000), (0x0B000000, 0x0C000000),
                   (0x40000000, 0x60000000)]:
        buf = bytearray()
        for p0 in range(lo, hi, 0x10000):
            chunk = mem.read(pid, h, p0, 0x10000)
            buf.extend(chunk if chunk else b"\x00" * 0x10000)
        raw = bytes(buf)
        start = 0
        while True:
            ix = raw.find(pat, start)
            if ix < 0:
                break
            hits.append(lo + ix)
            start = ix + 1
    print(f"'人物' UTF-16 命中 {len(hits)} 处")
    for a in hits[:20]:
        raw = mem.read(pid, h, a - 8, 32)
        ctx = mem._wstr_cut(raw).decode("utf-16-le", errors="replace")
        print(f"  0x{a:08X} ctx={ctx!r}")
        # 反查指向该地址的堆指针
        target = a.to_bytes(4, "little")
        cnt = 0
        for lo2, hi2 in [(0x01000000, 0x04000000), (0x0B000000, 0x0C000000)]:
            buf2 = bytearray()
            for p0 in range(lo2, hi2, 0x10000):
                chunk = mem.read(pid, h, p0, 0x10000)
                buf2.extend(chunk if chunk else b"\x00" * 0x10000)
            raw2 = bytes(buf2)
            st = 0
            while cnt < 8:
                ix2 = raw2.find(target, st)
                if ix2 < 0:
                    break
                ref = lo2 + ix2
                if ref % 4 == 0:
                    print(f"    ref 0x{ref:08X}")
                    cnt += 1
                st = ix2 + 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
