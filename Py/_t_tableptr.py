# -*- coding: utf-8 -*-
"""分析物品结构到 04BD78F6 / 11E04CB2 对照表的指向。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def byte(pid, h, a):
    raw = mem.read(pid, h, a, 1)
    return raw[0] if raw else 0

def read(pid, h, a, n):
    return mem.read(pid, h, a, n)

def dump(pid, h, addr, n, label):
    buf = read(pid, h, addr, n)
    if not buf:
        print(label, "读失败"); return
    print("== %s %#x ==" % (label, addr))
    for off in range(0, len(buf), 16):
        hexs = " ".join("%02X" % b for b in buf[off:off+16])
        u = buf[off:off+16].decode("utf-16-le", errors="ignore")
        u = "".join(c if c.isprintable() else "." for c in u)
        g = buf[off:off+16].decode("gbk", errors="ignore")
        g = "".join(c if c.isprintable() else "." for c in g)
        print("  %+04X  %s  |%s| |%s|" % (off, hexs, u, g))

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")

dump(pid, h, 0x04BD78F6 - 0x40, 0x100, "T1 04BD78F6")
dump(pid, h, 0x11E04CB2 - 0x40, 0x100, "T2 11E04CB2")

# 找骸骨小刀
pPlayer = dword(pid, h, d2c + 0x11B800)
pInv = dword(pid, h, pPlayer + 0x60)
pFirst = dword(pid, h, pInv + 0x0C)
unit = idat = path = None
p = pFirst; seen = set()
while p and p not in seen:
    seen.add(p)
    txt = dword(pid, h, p + 0x04)
    d = dword(pid, h, p + 0x14)
    loc = byte(pid, h, d + 0x45)
    if loc == 255 and txt == 235:
        unit, idat, path = p, d, dword(pid, h, p + 0x2C)
        break
    p = dword(pid, h, d + 0x64)
print("unit=%#x idat=%#x path=%#x" % (unit, idat, path))

# 扫描结构中的指针, 匹配对照表范围
ranges = [(0x04BD0000, 0x04BE0000, "T1区"), (0x11E00000, 0x11E10000, "T2区")]
def scan(addr, size, label):
    buf = read(pid, h, addr, size)
    if not buf:
        return
    for off in range(0, len(buf) - 3, 4):
        v = int.from_bytes(buf[off:off+4], "little")
        for lo, hi, tag in ranges:
            if lo <= v < hi:
                print("  %s +%#04x = %#x  <- %s内" % (label, off, v, tag))
        # 反向: 值本身是否在结构内? 忽略

scan(unit, 0x400, "UnitAny")
scan(idat, 0x400, "ItemData")
scan(path, 0x400, "Path")
ctypes.windll.kernel32.CloseHandle(h)
