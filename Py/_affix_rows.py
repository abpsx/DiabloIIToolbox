#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全表搜词缀 name 找真实行号，验证 id=行号+2"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC

targets = [b"of the Locust", b"of Light", b"of the Bat", b"Serpent", b"Steel",
           b"Monk's", b"of Absorption", b"of Protection", b"of Might", b"Garnet",
           b"Slayer's", b"of Energy", b"of the Mind", b"of Brilliance"]
found = {t: [] for t in targets}
for rid in range(1452):
    raw = mr.read(pid, h, sP + rid * 0x90, 0x90)
    nm = raw.split(b"\x00")[0] if raw else b""
    for t in targets:
        if nm == t or nm.startswith(t):
            found[t].append(rid)
for t in targets:
    print(f"{t.decode()} -> 行 {found[t][:10]}")
