#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""txt 与内存表交叉验证：
- MagicSuffix.txt 行号 = id（行2 = id2）
- MagicPrefix.txt 行号 = id？（行3 = id3）
用内存表（已生成 dict）反查 txt 行号，报告差异。
"""
import sys, json

DP = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_prefix.json"
DS = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_suffix.json"
TP = r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt"
TS = r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt"

dp = json.load(open(DP, encoding="utf-8"))
ds = json.load(open(DS, encoding="utf-8"))

def parse_txt(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip("\r\n").split("\t")
            rows.append(cols)
    return rows

# ---- suffix：txt 行号 -> name，与内存 id 对照 ----
srows = parse_txt(TS)
mismatch_s = []
hit_s = 0
for ridx, cols in enumerate(srows, 1):
    if ridx < 2:
        continue
    name = cols[0].strip()
    if not name or name == "Expansion":
        continue
    iid = ridx  # txt 行号 = id
    mem = ds.get(str(iid))
    if mem and mem["name"] == name:
        hit_s += 1
    elif mem and mem["name"] != name:
        mismatch_s.append((iid, name, mem["name"]))
    else:
        mismatch_s.append((iid, name, None))
print(f"[suffix] txt id2-{len(srows)} 命中 {hit_s} 条, 差异 {len(mismatch_s)} 条")
for m in mismatch_s[:20]:
    print("  ", m)

# ---- prefix：txt 行号 -> name，与内存 id 对照 ----
prows = parse_txt(TP)
mismatch_p = []
hit_p = 0
name_to_id = {}
for k, v in dp.items():
    name_to_id.setdefault(v["name"], []).append(int(k))
for ridx, cols in enumerate(prows, 1):
    if ridx < 3:
        continue
    name = cols[0].strip()
    if not name or name == "Expansion":
        continue
    iid = ridx  # 假设 txt 行号 = id
    mem = dp.get(str(iid))
    if mem and mem["name"] == name:
        hit_p += 1
    elif mem and mem["name"] != name:
        mismatch_p.append((iid, name, mem["name"]))
    else:
        # 内存无此 id 或不同名：用 name 反查
        ids = name_to_id.get(name, [])
        mismatch_p.append((iid, name, None, ids[:3]))
print(f"[prefix] txt 行3-{len(prows)} 命中 {hit_p} 条, 差异 {len(mismatch_p)} 条")
for m in mismatch_p[:30]:
    print("  ", m)
