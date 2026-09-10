# -*- coding: utf-8 -*-
"""读 InventoryLayout/StashLayout 布局表（面板打开时）。"""
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

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")
print("D2CLIENT=%#x" % d2c)

for name, off in [("Inventory", 0x1016F0), ("Stash", 0x1015E0),
                  ("Cube", 0x1016D8), ("Store", 0x1016C0),
                  ("Trade", 0x101598), ("Merc", 0x11CC84)]:
    p = dword(pid, h, d2c + off)
    print("%s layout@%#x: ptr=%#x" % (name, off, p))
    if p:
        sw = byte(pid, h, p + 0x00)
        sh = byte(pid, h, p + 0x01)
        left = dword(pid, h, p + 0x04)
        right = dword(pid, h, p + 0x08)
        top = dword(pid, h, p + 0x0C)
        bottom = dword(pid, h, p + 0x10)
        spw = byte(pid, h, p + 0x14)
        sph = byte(pid, h, p + 0x15)
        print("    Slot=%dx%d PixelSlot=%dx%d  Left=%d Right=%d Top=%d Bottom=%d" %
              (sw, sh, spw, sph, left, right, top, bottom))
ctypes.windll.kernel32.CloseHandle(h)
