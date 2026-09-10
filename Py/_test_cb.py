#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证控件 cb_off 输出。"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
item = {"module": "D2Win.dll", "offset": "0x214A0", "type": "controls",
        "player_off": "D2CLIENT+0x11B800"}
r = mem.read_controls(pid, h, item, "Setting/memory")
print("state={} page={} count={}".format(r["state"], r["page"], r["count"]))
for c in r["controls"][:10]:
    print("  #{} ({},{}) cb={} {}".format(
        c["type_name"], c["pos"][0], c["pos"][1], c["cb_off"] or "-", c["texts"][:1]))
