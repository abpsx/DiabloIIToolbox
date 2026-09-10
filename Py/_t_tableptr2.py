# -*- coding: utf-8 -*-
"""固定物品 0xabba500, 扫 UnitAny/ItemData/Path 全字段找指向对照表区的指针。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def read(pid, h, a, n):
    return mem.read(pid, h, a, n)

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
unit, idat, path = 0xabba500, dword(pid, h, 0xabba500 + 0x14), dword(pid, h, 0xabba500 + 0x2C)
print("unit=%#x idat=%#x path=%#x" % (unit, idat, path))

ranges = [
    (0x04BD0000, 0x04BE0000, "T1区(04BD)"),
    (0x11E00000, 0x11E10000, "T2区(11E0)"),
    (0x04BD78F6 - 0x10, 0x04BD78F6 + 0x10, "T1精确"),
    (0x11E04CB2 - 0x10, 0x11E04CB2 + 0x10, "T2精确"),
]

def scan(addr, size, label):
    buf = read(pid, h, addr, size)
    if not buf:
        print(label, "读失败"); return
    found = []
    for off in range(0, len(buf) - 3, 4):
        v = int.from_bytes(buf[off:off+4], "little")
        for lo, hi, tag in ranges:
            if lo <= v < hi:
                found.append((off, v, tag))
    # 二级: 字段是表区附近指针的再解引用
    second = []
    for off in range(0, len(buf) - 3, 4):
        v = int.from_bytes(buf[off:off+4], "little")
        if 0x10000 < v < 0x7FFFFFFF:
            v2 = dword(pid, h, v)
            for lo, hi, tag in ranges:
                if lo <= v2 < hi:
                    second.append((off, v, v2, tag))
    if found or second:
        print("== %s (%#x, %d) ==" % (label, addr, size))
        for off, v, tag in found:
            print("  一级 +%#04x -> %#x  %s" % (off, v, tag))
        for off, v, v2, tag in second:
            print("  二级 +%#04x -> %#x -> %#x  %s" % (off, v, v2, tag))

scan(unit, 0x400, "UnitAny")
scan(idat, 0x400, "ItemData")
scan(path, 0x400, "Path")

# 物品所在堆块附近: 找含巫师之刺的引用（在 ±0x4000 内搜 dword 指针指向表文本）
for base, label in [(unit, "unit"), (idat, "idat"), (path, "path")]:
    lo, hi = base - 0x4000, base + 0x4000
    for chunk in range(lo, hi, 0x1000):
        buf = read(pid, h, chunk, 0x1000)
        if not buf:
            continue
        for off in range(0, len(buf) - 3, 4):
            v = int.from_bytes(buf[off:off+4], "little")
            if 0x04BD0000 <= v < 0x04BE0000 or 0x11E00000 <= v < 0x11E10000:
                print("邻近命中: %s 内 %#x 存有表指针 %#x" % (label, chunk + off, v))
ctypes.windll.kernel32.CloseHandle(h)
