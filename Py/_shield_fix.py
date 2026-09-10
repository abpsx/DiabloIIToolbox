#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盾牌词条修正：1) 重读行1014/1316/1441 name与结构 2) 扫物品找1441 3) txt精确mod标注"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC

def w(a): return mr.read_value(pid, h, a, "word")
def dw(a): return mr.read_value(pid, h, a, "dword")

# 1) 行结构
print("== 扩展表行 985/1014/1316/263/434/1441 ==")
for rid in (985, 1014, 1316, 263, 434, 1441):
    b = sP + rid * 0x90
    raw = mr.read(pid, h, b, 0x90)
    nm = raw.split(b"\x00")[0].decode("utf-8", "replace")
    nz = []
    for off in range(0x0C, 0x90, 4):
        v = dw(b + off)
        if v:
            nz.append(f"+{off:02X}={v}")
    print(f"行{rid}: {nm!r} 非零: {', '.join(nz[:14])}")

# 2) 扫盾牌找 1441
base = mr.read_ptr(pid, h, mr.module_base(pid, "D2Client.dll") + 0x11B800)
inv = mr.read_ptr(pid, h, base + 0x60)
first = mr.read_ptr(pid, h, inv + 0x0C)
cur = first
shield = None
while cur:
    txt = w(cur + 0x04)
    idat = mr.read_ptr(pid, h, cur + 0x14)
    if idat and txt == 500:
        shield = (cur, idat)
        break
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

if shield:
    cur, idat = shield
    print(f"\n== 盾牌 cur={hex(cur)} idat={hex(idat)} 扫 1441(0x5A1) ==")
    for off in range(-0x300, 0x400, 2):
        v = w(idat + off)
        if v == 1441:
            print(f"  idat{off:+04X} = 1441")
    for off in range(-0x200, 0x200, 2):
        v = w(cur + off)
        if v == 1441:
            print(f"  cur{off:+04X} = 1441")
    # 也看 idat+0x44 附近（词缀槽后）
    print("  idat+0x44..+0x60:", [w(idat + 0x44 + i*2) for i in range(14)])

# 3) txt 精确 mod 标注
def txt_mods(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip().split("\t")
            if i == 1 or not cols[0].strip():
                continue
            mods = []
            for mi in range(1, 4):
                base = 13 + (mi - 1) * 4
                if len(cols) > base and cols[base].strip():
                    mods.append((cols[base].strip(),
                                 cols[base+2].strip() if len(cols) > base+2 else "",
                                 cols[base+3].strip() if len(cols) > base+3 else ""))
            if mods:
                out.setdefault(cols[0].strip(), []).append(mods)
    return out

tp = txt_mods(r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt")
ts = txt_mods(r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt")
print("\n== txt 精确 mod ==")
for nm in ("Bright", "Summoner's", "of Nova Shield", "of Stability"):
    vs = tp.get(nm) or ts.get(nm)
    print(f"{nm}: {vs[:2] if vs else '未找到'}")
