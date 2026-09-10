#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩展表全行解析：name/level/min/max/stat枚举/param + txt 交叉标注 stat 枚举中文"""
import sys, json
from collections import Counter
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC

def w(a): return mr.read_value(pid, h, a, "word")

# 1) 读全部行
rows = []
for rid in range(1452):
    b = sP + rid * 0x90
    raw = mr.read(pid, h, b, 0x90)
    nm = raw.split(b"\x00")[0]
    try:
        name = nm.decode("utf-8")
    except Exception:
        name = ""
    if not name:
        continue
    rows.append({
        "row": rid,
        "name": name,
        "level": w(b + 0x24),
        "min": w(b + 0x2C),
        "max": w(b + 0x30),
        "stat": w(b + 0x5C),
        "p58": w(b + 0x58),
    })

# 2) txt 交叉：name -> mod code 集合
def parse_txt_codes(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip().split("\t")
            if i == 1 or not cols[0].strip():
                continue
            codes = set()
            for mi in range(1, 4):
                base = 13 + (mi - 1) * 4
                if len(cols) > base and cols[base].strip():
                    codes.add(cols[base].strip())
            if codes:
                out.setdefault(cols[0].strip(), set()).update(codes)
    return out

tp = parse_txt_codes(r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt")
ts = parse_txt_codes(r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt")
alltxt = {**tp, **ts}
for k, v in tp.items():
    alltxt.setdefault(k, set()).update(v)

# 3) stat 枚举 -> txt mod code 标注（按 name 交叉）
stat_codes = {}
for r in rows:
    codes = alltxt.get(r["name"])
    if codes:
        for c in codes:
            stat_codes.setdefault(r["stat"], Counter())[c] += 1

print("== stat 枚举 -> txt mod code 标注 ==")
stat_zh = {}
for st in sorted(stat_codes):
    top = stat_codes[st].most_common(3)
    print(f"  stat {st:4d} -> {top}")
