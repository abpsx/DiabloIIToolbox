# -*- coding: utf-8 -*-
"""探查 items.txt 行的类型/其他字段"""
import sys, ctypes
from collections import Counter
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    base = lt.find_itemtxt_base(pid, h)
    disp = lt.find_locale_dispatch(pid, h)
    print("表基:", hex(base))
    types, sizes, locs = Counter(), Counter(), Counter()
    samples = {}
    for tid in [0, 1, 2, 529, 520, 605, 679, 661, 509, 545, 330]:
        row = lt.read_item_row(pid, h, base, tid)
        if row:
            types[row["ntype"]] += 1
            sizes[(row["xsize"], row["ysize"])] += 1
            samples[tid] = (row["code"], row["ntype"], row["xsize"], row["ysize"], row["locale"])
    print("样例 (code, ntype, xsize, ysize, wloc):")
    for tid, s in samples.items():
        print("  id=%d %r" % (tid, s))
    # 全表扫描类型分布
    for tid in range(716):
        row = lt.read_item_row(pid, h, base, tid)
        if row:
            types[row["ntype"]] += 1
            locs[row["locale"]] += 1
    print("ntype 分布(值:次数):", dict(sorted(types.items())))
    # 找 itemtypes 表特征: 搜 "weap" / "armo" 字符串?
    print("尝试在 D2Common 找 itemtypes 指针特征…(略)")
finally:
    ctypes.windll.kernel32.CloseHandle(h)
