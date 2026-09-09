#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 read_controls 正式实现（主菜单状态）。"""
import ctypes
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if pid is None:
    print("D2Loader.exe 未运行")
    sys.exit(1)
h = mem.open_process_readonly(pid)
try:
    py_dir = os.path.dirname(os.path.abspath(__file__))
    items = json.load(open(os.path.join(py_dir, "..", "Setting", "memory", "1.13c.json"), encoding="utf-8"))
    r = mem.read_all(pid, items, py_dir)
    ct = r.get("控件链")
    print(json.dumps({
        "state": ct["state"], "page": ct["page"],
        "first": hex(ct["first"]) if ct["first"] else 0,
        "count": ct["count"]}, ensure_ascii=False))
    for c in ct["controls"][:12]:
        print(f"  #{c['type_name']:<12} pos={c['pos']} size={c['size']} texts={c['texts']}")
finally:
    ctypes.windll.kernel32.CloseHandle(h)
