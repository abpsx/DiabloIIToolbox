# -*- coding: utf-8 -*-
"""读当前页仓库物品的 pItemData，找页号字段（当前页=8）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

d2c = mem.module_base(pid, "D2CLIENT.DLL")
pPlayer = dword(d2c + 0x11B800)
pInv = dword(pPlayer + 0x60)
cur = dword(pInv + 0x0C)
seen = set()
units = []
n = 0
while cur and cur not in seen and n < 60:
    seen.add(cur)
    txt = dword(cur + 4)
    idat = dword(cur + 0x14)
    r69 = mem.read(pid, h, idat + 0x69, 1) if idat else b""
    r45 = mem.read(pid, h, idat + 0x45, 1) if idat else b""
    if r69 and r45 and r69[0] == 1 and r45[0] == 4:
        name = lt.txt_to_name(pid, h, txt)[0]
        units.append((cur, idat, txt, name))
    cur = dword(idat + 0x64) if idat else 0
    n += 1

print(f"当前页仓库物品 {len(units)} 件:")
for u, idat, txt, name in units:
    print(f"  unit=0x{u:X} idat=0x{idat:X} txt={txt} {name}")

# dump pItemData 前 0x100 字节，标记 ==8 或 ==7 的 dword/byte
for u, idat, txt, name in units:
    raw = mem.read(pid, h, idat, 0x100) or b""
    hits = []
    for i in range(0, 0x100, 4):
        v = int.from_bytes(raw[i:i+4], "little")
        if v in (7, 8):
            hits.append((i, "dword", v))
    for i in range(0x100):
        if raw[i] in (7, 8):
            hits.append((i, "byte", raw[i]))
    print(f"  0x{idat:X} {name}: 页号候选 {hits[:10]}")
ctypes.windll.kernel32.CloseHandle(h)
