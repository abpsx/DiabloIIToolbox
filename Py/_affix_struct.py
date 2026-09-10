#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证扩展表行 mod 字段：stat id / min / max / level；收集全部 stat id 分布"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC

def w(a): return mr.read_value(pid, h, a, "word")
def dw(a): return mr.read_value(pid, h, a, "dword")

# 已知词缀验证（stat 期望）
KNOWN = {
    985: ("Iron", "att/tohit"),
    1312: ("Monk's", "pal skill"),
    1051: ("Snake's", "mana"),
    742: ("of the Locust", "lifesteal"),
    744: ("of the Bat", "manasteal"),
    363: ("of the Vampire", "manasteal"),
    118: ("of Life Everlasting", "red-dmg"),
    117: ("of Life", "red-dmg"),
    1121: ("Garnet", "res-fire"),
    374: ("of the Giant", "str"),
    1326: ("Slayer's", "bar skill"),
}
print("== 已知词缀行结构验证 ==")
print("id   name            +24lvl +2Cmin +30max +34   +58   +5Cstat")
for iid, (nm, exp) in KNOWN.items():
    b = sP + iid * 0x90
    raw = mr.read(pid, h, b, 0x90)
    n = raw.split(b"\x00")[0].decode("utf-8", "replace")
    print(f"{iid:4d} {n:16s} {w(b+0x24):5d} {w(b+0x2C):5d} {w(b+0x30):5d} {dw(b+0x34):8x} {w(b+0x58):5d} {w(b+0x5C):5d}  期望:{exp}")

# 收集全部行 stat id 分布
print("\n== 全部行 stat id(+0x5C) 分布 ==")
from collections import Counter
cnt = Counter()
for rid in range(1452):
    st = w(sP + rid * 0x90 + 0x5C)
    if st:
        cnt[st] += 1
for st, c in sorted(cnt.items()):
    print(f"  stat {st:4d} x{c}")
