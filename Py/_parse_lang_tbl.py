# -*- coding: utf-8 -*-
"""解析 GetLocaleText 表 0x129F0ECC：12字节 entry {hash, offset, len}"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

TB = 0x129F0ECC
# 读表头 16 字节
hdr = mem.read(pid, h, TB, 16)
print("表头:", hdr.hex(" "))

# 尝试多种 entry 宽度解析
for esz in (8, 12, 16):
    print(f"\n== entry 宽 {esz} ==")
    ok = 0
    for i in range(0, 20):
        ent = mem.read(pid, h, TB + i * esz, esz)
        if not ent:
            break
        if esz == 12:
            hashv, off, ln = int.from_bytes(ent[0:4], "little"), int.from_bytes(ent[4:8], "little"), int.from_bytes(ent[8:12], "little")
            if i < 8:
                print(f"  [{i}] hash={hashv:#x} off={off:#x} len={ln}")
            if ln < 200:
                ok += 1
        elif esz == 8:
            a, b = int.from_bytes(ent[0:4], "little"), int.from_bytes(ent[4:8], "little")
            if i < 8:
                print(f"  [{i}] {a:#x} {b:#x}")
    print(f"  ok={ok}")

ctypes.windll.kernel32.CloseHandle(h)
