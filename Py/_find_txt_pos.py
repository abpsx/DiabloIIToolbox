#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜 '等级' '资料片人物' UTF-16 位置，确认 TEXTBOX 文本存储结构。"""
import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    pats = {
        "等级": "等级".encode("utf-16-le"),
        "资料片人物": "资料片人物".encode("utf-16-le"),
    }
    regions = [(0x01000000, 0x04000000), (0x0B000000, 0x0C000000)]
    for b0, m in mem.module_base and []:
        pass
    hits = {}
    for lo, hi in regions:
        buf = bytearray()
        for p0 in range(lo, hi, 0x10000):
            chunk = mem.read(pid, h, p0, 0x10000)
            buf.extend(chunk if chunk else b"\x00" * 0x10000)
        raw = bytes(buf)
        for name, pat in pats.items():
            start = 0
            while True:
                idx = raw.find(pat, start)
                if idx < 0:
                    break
                hits.setdefault(name, []).append(lo + idx)
                start = idx + 1
    for name, lst in hits.items():
        print(f"{name}: {len(lst)} 处")
        for a in lst[:8]:
            # 读文本区前后 16 字节上下文
            raw = mem.read(pid, h, a - 4, 96)
            print(f"  0x{a:08X}  ctx: {raw.split(b'\x00\x00')[0][:60]!r}")
            # 反查：谁指向这个地址（0x02xxxxxx / 0x03xxxxxx 堆）
            target = a.to_bytes(4, "little")
            cnt = 0
            for lo2, hi2 in [(0x01000000, 0x04000000), (0x0B000000, 0x0C000000)]:
                buf2 = bytearray()
                for p0 in range(lo2, hi2, 0x10000):
                    chunk = mem.read(pid, h, p0, 0x10000)
                    buf2.extend(chunk if chunk else b"\x00" * 0x10000)
                raw2 = bytes(buf2)
                st = 0
                while cnt < 6:
                    ix = raw2.find(target, st)
                    if ix < 0:
                        break
                    ref = lo2 + ix
                    if ref % 4 == 0:
                        print(f"    ref 0x{ref:08X} (heap) -> 0x{a:08X}")
                        cnt += 1
                    st = ix + 1
            break  # 只反查第一处
finally:
    ctypes.windll.kernel32.CloseHandle(h)
