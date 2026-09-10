# -*- coding: utf-8 -*-
"""读 GetItemName 引用的 7 个模板地址 + 全局指针, 找 unique 名来源。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def read(pid, h, a, n):
    return mem.read(pid, h, a, n)

def dump(pid, h, addr, n, label):
    buf = read(pid, h, addr, n)
    if not buf:
        print(label, "%#x 读失败" % addr); return
    print("== %s %#x ==" % (label, addr))
    for off in range(0, len(buf), 16):
        hexs = " ".join("%02X" % b for b in buf[off:off+16])
        u = "".join(c if c.isprintable() else "." for c in buf[off:off+16].decode("utf-16-le", errors="ignore"))
        g = "".join(c if c.isprintable() else "." for c in buf[off:off+16].decode("gbk", errors="ignore"))
        print("  %+04X  %s  |%s| |%s|" % (off, hexs, u, g))

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")

# 7 个模板地址（quality 0-6 分支的 esi）
for q, a in [(0, 0x6fbbb3b0), (1, 0x6fbbb370), (2, 0x6fbbb288), (3, 0x6fbbb2d0),
             (4, 0x6fbbb398), (5, 0x6fbbb3c8), (6, 0x6fbbb3e0)]:
    v = dword(pid, h, a)
    print("q=%d 模板地址 %#x 首dword=%#x" % (q, a, v))
    dump(pid, h, a, 0x30, "q=%d" % q)

# 全局指针
for off, label in [(0x119854, "g1 0x6fbc9854"), (0x11bc48, "g2 0x6fbcbc48")]:
    v = dword(pid, h, d2c + off)
    print("全局 %s = %#x" % (label, v))
    if 0x10000 < v < 0x7FFFFFFF:
        dump(pid, h, v, 0x40, label + " 指向")
ctypes.windll.kernel32.CloseHandle(h)
