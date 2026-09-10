# -*- coding: utf-8 -*-
"""读装备物品的 quality/dwFileIndex/词缀字段, 定位特殊名索引。"""
import sys, ctypes, json
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def word(pid, h, a):
    raw = mem.read(pid, h, a, 2)
    return int.from_bytes(raw, "little") if raw else 0

def byte(pid, h, a):
    raw = mem.read(pid, h, a, 1)
    return raw[0] if raw else 0

QUAL = {1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique", 8: "crafted"}

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")
tbl = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json", encoding="utf-8"))
id2name = {str(it["id"]): it.get("name_clean") or it.get("name") for it in tbl.get("items", [])}

pPlayer = dword(pid, h, d2c + 0x11B800)
pInv = dword(pid, h, pPlayer + 0x60)
pFirst = dword(pid, h, pInv + 0x0C)
p = pFirst
seen = set()
while p and p not in seen:
    seen.add(p)
    it = p
    txt = dword(pid, h, it + 0x04)
    idat = dword(pid, h, it + 0x14)
    loc = byte(pid, h, idat + 0x45)
    if loc == 255 and txt == 235:  # 骸骨小刀
        q = dword(pid, h, idat + 0x00)
        fi = dword(pid, h, idat + 0x28)
        rp = word(pid, h, idat + 0x32)
        rs = word(pid, h, idat + 0x34)
        mp = [word(pid, h, idat + 0x38 + 2 * i) for i in range(3)]
        ms = [word(pid, h, idat + 0x3E + 2 * i) for i in range(3)]
        print("骸骨小刀 物品=%#x idat=%#x" % (it, idat))
        print("  quality=%d (%s)" % (q, QUAL.get(q, "?")))
        print("  dwFileIndex=%d (0x%X)  <- unique/set 索引" % (fi, fi))
        print("  wRarePrefix=%d wRareSuffix=%d" % (rp, rs))
        print("  wMagicPrefix=%s wMagicSuffix=%s" % (mp, ms))
        print("  base_name=%s" % id2name.get(str(txt), "?"))
        break
    p = dword(pid, h, idat + 0x64)
ctypes.windll.kernel32.CloseHandle(h)
