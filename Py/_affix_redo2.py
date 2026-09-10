#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重做词缀分析 v2：txt=520 项链(amu) / 522 戒指(rin)，6槽=6词缀，法力锚点"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
dp = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_prefix.json", encoding="utf-8"))
ds = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_suffix.json", encoding="utf-8"))
dall = {}
for iid, v in dp.items():
    dall[int(iid)] = (v["name"], v["name_zh"], "P")
for iid, v in ds.items():
    if int(iid) not in dall:
        dall[int(iid)] = (v["name"], v["name_zh"], "S")

# 法力词缀：Serpent's/Lizard's 系 = +mana
MANA = {54:"Lizard's",56:"Snake's",57:"Serpent's",58:"Serpent's",59:"Drake's",60:"Dragon's",61:"Dragon's",62:"Wyrm's",286:"Lizard's",287:"Lizard's",288:"Lizard's",289:"Snake's",290:"Snake's",291:"Snake's",292:"Serpent's",293:"Serpent's",294:"Serpent's",295:"Lizard's",296:"Lizard's",297:"Lizard's",298:"Snake's",299:"Snake's",300:"Serpent's",301:"Serpent's",302:"Lizard's",303:"Lizard's",304:"Snake's",305:"Serpent's",306:"Lizard's",307:"Snake's",308:"Serpent's",309:"Serpent's",310:"Drake's",311:"Dragon's",312:"Dragon's",313:"Wyrm's",314:"Great Wyrm's",315:"Bahamut's",665:"Lizard's"}

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
        items.append({"cur": hex(cur), "txt": txt, "idat": hex(idat), "words": words})
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

def fmt(words):
    out = []
    for i, v in enumerate(words):
        if not v:
            continue
        e = dall.get(v)
        nm = e[0] if e else "?"
        zh = e[1] or "" if e else ""
        ty = e[2] if e else "?"
        mana = " [法力]" if (v in MANA) else ""
        out.append(f"{v}={zh or nm}({ty}){mana}")
    return ", ".join(out)

print("== 项链 (txt=520 amu) 带词缀 ==")
for it in items:
    if it["txt"] == 520 and any(it["words"]):
        print(f"  {it['cur']} idat={it['idat']} 槽{sum(1 for x in it['words'] if x)}: {fmt(it['words'])}")
print("\n== 戒指 (txt=522 rin) 带词缀 ==")
for it in items:
    if it["txt"] == 522 and any(it["words"]):
        print(f"  {it['cur']} idat={it['idat']} 槽{sum(1 for x in it['words'] if x)}: {fmt(it['words'])}")
