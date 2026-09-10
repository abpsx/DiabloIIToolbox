#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项链1：1) txt 全变体修正词缀范围 2) 扫描物品结构找具体数值 2/19/2/4"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

# ---------- 1) txt 全变体 ----------
def parse_txt_all(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip().split("\t")
            if i == 1 or not cols[0].strip():
                continue
            name = cols[0].strip()
            mods = []
            for mi in range(1, 4):
                if len(cols) > 13 + (mi - 1) * 4 and cols[13 + (mi - 1) * 4]:
                    mods.append(f"{cols[13+(mi-1)*4]} {cols[15+(mi-1)*4]}-{cols[16+(mi-1)*4]}")
            if mods:
                out.setdefault(name, []).append((cols[3] if len(cols) > 3 else "?", "; ".join(mods)))
    return out

tp = parse_txt_all(r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt")
ts = parse_txt_all(r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt")
print("== txt 全变体（项链1 四词缀）==")
for nm in ("Iron", "Monk's", "Snake's"):
    print(f"{nm} (prefix):")
    for lvl, mod in tp.get(nm, []):
        print(f"   lvl={lvl}: {mod}")
for nm in ("of the Locust",):
    print(f"{nm} (suffix):")
    for lvl, mod in ts.get(nm, []):
        print(f"   lvl={lvl}: {mod}")

# ---------- 2) 物品结构扫描 ----------
def w(a): return mr.read_value(pid, h, a, "word")
def dw(a): return mr.read_value(pid, h, a, "dword")

base = mr.read_ptr(pid, h, mr.module_base(pid, "D2Client.dll") + 0x11B800)
inv = mr.read_ptr(pid, h, base + 0x60)
first = mr.read_ptr(pid, h, inv + 0x0C)
cur = first
target = None
while cur:
    txt = w(cur + 0x04)
    idat = mr.read_ptr(pid, h, cur + 0x14)
    if idat:
        words = [w(idat + 0x38 + i * 2) for i in range(6)]
        if words == [985, 1312, 1051, 742, 0, 0]:
            target = (cur, idat)
            break
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

if target:
    cur, idat = target
    print(f"\n== 项链1 cur={hex(cur)} idat={hex(idat)} ==")
    # 扫描 idat 前后 0x60 的 WORD
    print("WORD dump idat+0x20 .. +0x70:")
    for off in range(0x20, 0x72, 2):
        print(f"   +{off:02X} = {w(idat + off)}")
    print("WORD dump idat-0x30 .. +0x20:")
    for off in range(-0x30, 0x22, 2):
        print(f"   {off:+03X} = {w(idat + off)}")
    # 找 19 (0x13) 附近
    print("\n扫描 idat±0x80 找 0x13(19) / 0x02(2) / 0x04(4):")
    for off in range(-0x80, 0x80, 2):
        v = w(idat + off)
        if v in (19, 2, 4):
            print(f"   {off:+04X} = {v}")
