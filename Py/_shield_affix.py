#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取仓库盾牌(txt=500)词条：6词缀槽(idat+0x38) + 独立词缀位(idat+0x36)"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr
import affix_enumerate as ae

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

def w(a): return mr.read_value(pid, h, a, "word")

aff = ae.enumerate_affixes(pid, h)

base = mr.read_ptr(pid, h, mr.module_base(pid, "D2Client.dll") + 0x11B800)
inv = mr.read_ptr(pid, h, base + 0x60)
first = mr.read_ptr(pid, h, inv + 0x0C)
cur = first
while cur:
    txt = w(cur + 0x04)
    idat = mr.read_ptr(pid, h, cur + 0x14)
    if idat and txt == 500:
        break
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

def show(iid, tag):
    if not iid:
        print(f"  {tag}: [空]")
        return
    e = aff.get(str(iid))
    if e:
        print(f"  {tag} id{iid} = {e['name']} ({e['name_zh'] or '?'}) [{e['type']}] "
              f"{e['mod']['zh']} ({e['mod']['code']}) {e['mod']['min']}-{e['mod']['max']}")
    else:
        print(f"  {tag} id{iid} = 未找到")

if cur:
    print(f"盾牌 cur={hex(cur)} idat={hex(idat)}")
    extra = w(idat + 0x36)          # 独立词缀位（不占3前3后）
    words = [w(idat + 0x38 + i * 2) for i in range(6)]
    print(f"独立词缀位(idat+0x36) = {extra}")
    show(extra, "独立")
    print(f"词缀槽(idat+0x38) = {words}")
    for i, iid in enumerate(words):
        show(iid, f"槽{i}")
else:
    print("未找到盾牌(txt=500)")
