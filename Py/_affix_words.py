#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按用户 3前3后 布局：读扩展表行 name（权威），txt mod 反查词条"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC

def row_name(rid):
    raw = mr.read(pid, h, sP + rid * 0x90, 0x90)
    nm = raw.split(b"\x00")[0] if raw else b""
    try:
        return nm.decode("utf-8")
    except Exception:
        return repr(nm)

# txt mod 索引：name -> mods 描述
def parse_txt(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip("\r\n").split("\t")
            if i == 1 or not cols[0].strip():
                continue
            name = cols[0].strip()
            mods = []
            for mi in range(1, 4):
                code = cols[13 + (mi-1)*4] if len(cols) > 13 + (mi-1)*4 else ""
                pmin = cols[15 + (mi-1)*4] if len(cols) > 15 + (mi-1)*4 else ""
                pmax = cols[16 + (mi-1)*4] if len(cols) > 16 + (mi-1)*4 else ""
                if code:
                    mods.append(f"{code} {pmin}-{pmax}")
            if mods:
                out.setdefault(name, []).append("; ".join(mods))
    return out

tp = parse_txt(r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt")
ts = parse_txt(r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt")

# 项链布局：3前3后
necks = {
    "项链1": (985, 1312, 1051, 742),
    "项链2": (1326, 1055, 1121, 117, 374),
    "项链3": (1055, 0, 0, 744, 118, 363),
}
for nm, ids in necks.items():
    print(f"== {nm} ==")
    for iid in ids:
        if not iid:
            print("   [空]")
            continue
        rid = iid - 2
        name = row_name(rid)
        # mod 从 txt 找
        mods = (tp.get(name) or ts.get(name) or ["?"])[0]
        print(f"   id{iid} 行{rid} name={name!r} | mod: {mods}")
