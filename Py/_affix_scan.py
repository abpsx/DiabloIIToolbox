#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描三项链 idat 区域，找 6 个词缀值的真实分布位置"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

def w(a):
    return mr.read_value(pid, h, a, "word")

# 三项链（txt=522 带词缀的）
necks = [
    ("项链1", 0x12d06980, [1119, 1156, 987, 174, 286, 559]),
    ("项链2", 0x12d06a80, [1119, 1159, 1051, 124, 355, 174]),
    ("项链3", 0x12d02000, [1081, 115, 125, 443]),
]
for name, idat, vals in necks:
    print(f"== {name} idat=0x{idat:X} 期望词缀 {vals}")
    # 扫 idat-0x60 到 idat+0x100，找每个值的所有出现位置
    posmap = {}
    for a in range(idat - 0x60, idat + 0x100, 2):
        v = w(a)
        if v in vals:
            posmap.setdefault(v, []).append(a - idat)
    for v in vals:
        print(f"   {v}: 偏移 {posmap.get(v)}")
    # 打印 idat+0x30 到 +0x50 的原始 WORD
    print("   idat+0x30..0x50:", [w(idat + a) for a in range(0x30, 0x52, 2)])
