#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补词缀中文缺失：全范围扫 en\\0zh\\0"""
import sys, re
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
needles = [b"Lucky", b"Shaman's", b"Captain's", b"Lancer's", b"Rainbow"]
regions = [(0x127E0000, 0x60000), (0x12800000, 0x60000), (0x13440000, 0x50000), (0x12440000, 0x60000)]
found = {}
for beg, size in regions:
    raw = b""
    a = beg
    while a < beg + size:
        chunk = mr.read(pid, h, a, min(0x2000, beg + size - a))
        if not chunk:
            break
        raw += chunk
        a += 0x2000
    for nd in needles:
        pos = 0
        while True:
            i = raw.find(nd, pos)
            if i < 0:
                break
            j = raw.find(b"\x00", i + len(nd))
            if j >= 0:
                zh = raw[j + 1:j + 33].split(b"\x00")[0]
                try:
                    zhs = zh.decode("utf-8")
                except Exception:
                    zhs = None
                if zhs and len(zhs) <= 16 and not re.match(r"^[\x20-\x7e]+$", zhs):
                    found.setdefault(nd.decode("ascii"), zhs)
            pos = i + 1
print(found)
