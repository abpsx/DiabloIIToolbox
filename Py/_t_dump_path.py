# -*- coding: utf-8 -*-
"""dump 装备物品 pPath/ItemData 全字段, 找屏幕坐标线索。"""
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

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")

tbl = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json", encoding="utf-8"))
id2name = {str(it["id"]): it.get("name_clean") or it.get("name") for it in tbl.get("items", [])}

pPlayer = dword(pid, h, d2c + 0x11B800)
pInv = dword(pid, h, pPlayer + 0x60)
pFirst = dword(pid, h, pInv + 0x0C)
items = []
p = pFirst
seen = set()
while p and p not in seen:
    seen.add(p)
    it = p
    txt = dword(pid, h, it + 0x04)
    idat = dword(pid, h, it + 0x14)
    loc = byte(pid, h, idat + 0x45)
    path = dword(pid, h, it + 0x2C)
    dx, dy = word(pid, h, path + 0x0C), word(pid, h, path + 0x10)
    items.append((it, txt, loc, dx, dy, path))
    p = dword(pid, h, idat + 0x64)

print("== 装备物品 (loc=255) ==")
for it, txt, loc, dx, dy, path in items:
    if loc == 255:
        print("  物品=%#x txt=%d(%s) dwPos=(%d,%d) path=%#x" %
              (it, txt, id2name.get(str(txt), "?"), dx, dy, path))

print("== dump 第1个装备的 pPath (0x00-0x80) ==")
equip = [x for x in items if x[2] == 255]
if equip:
    it, txt, loc, dx, dy, path = equip[0]
    for off in range(0, 0x84, 4):
        v = dword(pid, h, path + off)
        print("  path+%#02x = %#08x (%d)" % (off, v, v))
    print("== ItemData (0x00-0x60) ==")
    idat = dword(pid, h, it + 0x14)
    for off in range(0, 0x64, 4):
        v = dword(pid, h, idat + off)
        print("  idat+%#02x = %#08x (%d)" % (off, v, v))
    print("== Unit (0x00-0x30) ==")
    for off in range(0, 0x34, 4):
        v = dword(pid, h, it + off)
        print("  unit+%#02x = %#08x (%d)" % (off, v, v))
ctypes.windll.kernel32.CloseHandle(h)
