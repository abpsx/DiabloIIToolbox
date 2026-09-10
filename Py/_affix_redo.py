#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重做词缀分析：读背包全部物品 0x38 起 6 个 WORD，按扩展表映射，识别项链"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
dp = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_prefix.json", encoding="utf-8"))
ds = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_suffix.json", encoding="utf-8"))
# 合并 id -> (name, 中文, 前缀/后缀)
dall = {}
for iid, v in dp.items():
    dall[int(iid)] = (v["name"], v["name_zh"], "P")
for iid, v in ds.items():
    dall.setdefault(int(iid), (v["name"], v["name_zh"], "S"))

def w(a):
    return mr.read_value(pid, h, a, "word")

base = mr.read_ptr(pid, h, mr.module_base(pid, "D2Client.dll") + 0x11B800)
inv = mr.read_ptr(pid, h, base + 0x60)
first = mr.read_ptr(pid, h, inv + 0x0C)
cur = first
items = []
while cur:
    txt = w(cur + 0x04)
    idat = mr.read_ptr(pid, h, cur + 0x14)
    if idat:
        words = [w(idat + 0x38 + i * 2) for i in range(6)]
        # 品质在 idat 何处？试 +0x00 附近几个位置
        items.append({"cur": hex(cur), "txt": txt, "idat": hex(idat), "words": words})
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

print(f"背包物品 {len(items)} 件:")
for it in items:
    ws = it["words"]
    nz = [i for i, v in enumerate(ws) if v]
    desc = []
    for i, v in enumerate(ws):
        if not v:
            desc.append(f"[{i}]=0")
        else:
            e = dall.get(v)
            if e:
                desc.append(f"[{i}]=id{v} {e[1] or e[0]} ({'前缀' if e[2]=='P' else '后缀'})")
            else:
                desc.append(f"[{i}]=id{v} ?")
    print(f"\n物品 cur={it['cur']} txt={it['txt']} idat={it['idat']} 非零槽{len(nz)}: {nz}")
    print("   " + " | ".join(desc))
