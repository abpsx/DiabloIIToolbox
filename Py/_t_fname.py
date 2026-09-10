# -*- coding: utf-8 -*-
"""骸骨小刀物品结构全 dump + 指针->名字搜索 + 附近 UTF-16 搜名。"""
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

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")

# 找骸骨小刀
pPlayer = dword(pid, h, d2c + 0x11B800)
pInv = dword(pid, h, pPlayer + 0x60)
pFirst = dword(pid, h, pInv + 0x0C)
target = None
p = pFirst
seen = set()
while p and p not in seen:
    seen.add(p)
    txt = dword(pid, h, p + 0x04)
    idat = dword(pid, h, p + 0x14)
    loc = byte(pid, h, idat + 0x45)
    if loc == 255 and txt == 235:
        target = (p, idat, dword(pid, h, p + 0x2C))
        break
    p = dword(pid, h, idat + 0x64)
if not target:
    print("骸骨小刀未找到"); sys.exit(1)
unit, idat, path = target
print("unit=%#x idat=%#x path=%#x" % (unit, idat, path))

# 1) 读整块并扫描可读指针
def scan_ptrs(addr, size, label):
    buf = read(pid, h, addr, size)
    if not buf:
        print(label, "读失败"); return
    print("== %s (%#x, %d bytes) ==" % (label, addr, size))
    for off in range(0, len(buf) - 3, 4):
        v = int.from_bytes(buf[off:off+4], "little")
        if 0x10000 < v < 0x7FFFFFFF:
            # 试读指针内容
            tb = read(pid, h, v, 0x40)
            if not tb:
                continue
            # 检查是否 UTF-16 可读串
            try:
                s = tb.decode("utf-16-le", errors="ignore")
                chars = [c for c in s if c.isprintable() or c == " "]
                if len(chars) >= 3 and sum(1 for c in s if ord(c) > 0x2E80) >= 2:
                    print("  +%#04x -> %#x: %r" % (off, v, s[:20]))
            except Exception:
                pass

scan_ptrs(unit, 0x100, "UnitAny")
scan_ptrs(idat, 0x90, "ItemData")
scan_ptrs(path, 0x120, "Path")

# 2) 物品附近 ±0x2000 搜 UTF-16 名字
for base, name in [(unit, "unit"), (idat, "idat"), (path, "path")]:
    for needle in ["巫师之刺", "骸骨小刀", "Bone Knife", "Wizardspike"]:
        pat = needle.encode("utf-16-le")
        lo = max(0, base - 0x2000)
        for chunk_off in range(lo, base + 0x2000, 0x1000):
            buf = read(pid, h, chunk_off, 0x1000)
            if not buf:
                continue
            i = buf.find(pat)
            if i >= 0:
                print("附近命中: %s 找 %r @ %#x（相对 %s %+d）" %
                      (name, needle, chunk_off + i, name, chunk_off + i - base))
ctypes.windll.kernel32.CloseHandle(h)
