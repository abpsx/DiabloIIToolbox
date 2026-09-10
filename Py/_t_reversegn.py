# -*- coding: utf-8 -*-
"""逆向 D2CLIENT+0x958C0 GetItemName: dump 字节, 找表基址立即数。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def read(pid, h, a, n):
    return mem.read(pid, h, a, n)

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")
d2common = mem.module_base(pid, "D2COMMON.DLL")
d2lang = mem.module_base(pid, "D2LANG.DLL")
d2win = mem.module_base(pid, "D2WIN.DLL")
fog = mem.module_base(pid, "Fog.DLL")
print("D2CLIENT=%#x D2COMMON=%#x D2LANG=%#x D2WIN=%#x Fog=%#x" % (d2c, d2common, d2lang, d2win, fog))

fn = d2c + 0x958C0
buf = read(pid, h, fn, 0x300)
print("GetItemName @ %#x, %d bytes" % (fn, len(buf)))
if not buf:
    print("读失败"); sys.exit(1)

# 打印 hex + 找立即数引用（mov reg, imm32: B8/B9/BA/BB/BC/BD/BE/BF xx xx xx xx）
mods = {"D2CLIENT": d2c, "D2COMMON": d2common, "D2LANG": d2lang, "D2WIN": d2win, "Fog": fog}
for i in range(0, min(len(buf) - 4, 0x300), 1):
    op = buf[i]
    if op in (0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF):
        imm = int.from_bytes(buf[i+1:i+5], "little")
        for name, base in mods.items():
            if base <= imm < base + 0x200000:
                print("  %#x: mov %s, imm32=%#x  <- %s 相对偏移 +%#x" %
                      (fn + i, "e" + hex(op - 0xB8)[2], imm, name, imm - base))
# 也找 call 目标
for i in range(0, min(len(buf) - 4, 0x300), 1):
    if buf[i] == 0xE8:
        rel = int.from_bytes(buf[i+1:i+5], "little", signed=True)
        tgt = (fn + i + 5 + rel) & 0xFFFFFFFF
        for name, base in mods.items():
            if base <= tgt < base + 0x200000:
                print("  %#x: call %#x  <- %s +%#x" % (fn + i, tgt, name, tgt - base))

# 函数头 0x40 hex
for off in range(0, 0x80, 16):
    print("  %+04X  %s" % (off, " ".join("%02X" % b for b in buf[off:off+16])))
ctypes.windll.kernel32.CloseHandle(h)
