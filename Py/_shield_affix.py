#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取仓库中盾牌(txt=500)的词条：枚举词缀表 + 物品词缀槽映射"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr
import affix_enumerate as ae

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

def w(a): return mr.read_value(pid, h, a, "word")
def dw(a): return mr.read_value(pid, h, a, "dword")

# 枚举词缀映射表（内存）
aff = ae.enumerate_affixes(pid, h)
print(f"词缀表枚举 {len(aff)} 条")

# 遍历物品链
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
        items.append({"cur": cur, "txt": txt, "idat": idat, "words": words})
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

shields = [it for it in items if it["txt"] == 500]
print(f"\n找到盾牌(txt=500) {len(shields)} 件")
for it in shields:
    print(f"\n== 盾牌 cur={hex(it['cur'])} idat={hex(it['idat'])} 词缀槽={it['words']} ==")
    for i, iid in enumerate(it["words"]):
        if not iid:
            continue
        e = aff.get(str(iid))
        if e:
            print(f"  槽{i} id{iid} = {e['name']} ({e['name_zh'] or '?'}) [{e['type']}] "
                  f"lvl{e['level']} {e['mod']['zh']} ({e['mod']['code']}) {e['mod']['min']}-{e['mod']['max']}")
        else:
            print(f"  槽{i} id{iid} = 未找到")
