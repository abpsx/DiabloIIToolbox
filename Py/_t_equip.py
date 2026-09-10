# -*- coding: utf-8 -*-
"""枚举身上装备 (loc=255): txt/dwPos/名称, 供定位分析。"""
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
pPlayer = dword(pid, h, d2c + 0x11B800)
pInv = dword(pid, h, pPlayer + 0x60)
print("pPlayer=%#x pInv=%#x" % (pPlayer, pInv))

# 装备/背包/盒子开
def flags(off):
    return dword(pid, h, d2c + 0x50D00 + off)
print("背包开=%d 人物面板开=%d 技能=%d 仓库开=%d 盒子开=%d" %
      (flags(0), flags(4), flags(0xC), flags(0x60), flags(0x64)))

# 码表
try:
    tbl = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json", encoding="utf-8"))
    code2name = {}
    for k, v in tbl.items():
        if isinstance(v, dict):
            code2name[str(k)] = v.get("name") or v.get("full") or ""
        else:
            code2name[str(k)] = str(v)
except Exception as e:
    tbl, code2name = {}, {}
    print("码表读失败:", e)

def name_of(txt):
    n = code2name.get(str(txt))
    if n:
        return n
    # 兼容 {code: "缩写"} 或 {code: "全称"} 结构
    for k, v in tbl.items():
        if isinstance(v, dict) and str(v.get("code")) == str(txt):
            return v.get("name") or v.get("full") or ""
    return "?"

# 遍历物品链表: pInv+0x0C=pFirstItem, ItemData+0x64=pNextItem
pFirst = dword(pid, h, pInv + 0x0C)
print("pFirstItem=%#x" % pFirst)
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

print("共 %d 件" % len(items))
for it, txt, loc, dx, dy, path in items:
    if loc == 255:
        print("  装备: 物品=%#x txt=%d(%s) loc=%d dwPos=(%d,%d) path=%#x" %
              (it, txt, name_of(txt), loc, dx, dy, path))
ctypes.windll.kernel32.CloseHandle(h)
