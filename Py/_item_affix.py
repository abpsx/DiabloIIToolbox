#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取仓库物品词条：python _item_affix.py <txt>  (6词缀槽 + 独立词缀位idat+0x36)"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr
import affix_enumerate as ae

TXT = int(sys.argv[1], 0) if len(sys.argv) > 1 else 500

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

def w(a): return mr.read_value(pid, h, a, "word")

aff = ae.enumerate_affixes(pid, h)

base = mr.read_ptr(pid, h, mr.module_base(pid, "D2Client.dll") + 0x11B800)
inv = mr.read_ptr(pid, h, base + 0x60)
first = mr.read_ptr(pid, h, inv + 0x0C)
cur = first
found = []
while cur:
    txt = w(cur + 0x04)
    idat = mr.read_ptr(pid, h, cur + 0x14)
    if idat and txt == TXT:
        found.append((cur, idat))
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

def show(iid, tag):
    if not iid:
        print(f"    {tag}: [空]")
        return
    e = aff.get(str(iid))
    if e:
        print(f"    {tag} id{iid} = {e['name']} ({e['name_zh'] or '?'}) [{e['type']}] "
              f"{e['mod']['zh']} ({e['mod']['code']}) {e['mod']['min']}-{e['mod']['max']}")
    else:
        print(f"    {tag} id{iid} = 未找到")

if not found:
    print(f"未找到 txt={TXT} 的物品")
    sys.exit(0)

print(f"找到 txt={TXT} 物品 {len(found)} 件")
for cur, idat in found:
    extra = w(idat + 0x36)
    words = [w(idat + 0x38 + i * 2) for i in range(6)]
    print(f"\n== 物品 cur={hex(cur)} idat={hex(idat)} 独立词缀位={extra} 槽={words} ==")
    show(extra, "独立")
    for i, iid in enumerate(words):
        show(iid, f"槽{i}")
