# -*- coding: utf-8 -*-
"""dump 物品对象 b02EA00 结构，找 txt 行号字段"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

OBJ = 0xb02ea00
raw = mem.read(pid, h, OBJ, 0x200)
print("== 物品对象 b02EA00 ==")
for off in range(0, 0x200, 4):
    v = int.from_bytes(raw[off:off+4], "little")
    mark = ""
    if v == 529 or v == 679:
        mark = "  <<< 529/679!"
    if off % 0x40 == 0:
        print(f"{OBJ+off:#x}:")
    print(f"  +{off:#04x} = {v} (0x{v:X}){mark}")
ctypes.windll.kernel32.CloseHandle(h)
