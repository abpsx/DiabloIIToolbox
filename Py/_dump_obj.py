# -*- coding: utf-8 -*-
"""读码表 obj 0x200 字节，列出指向高址的指针（候选 ItemTxt 表）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

base = mem.module_base(pid, "D2Common.dll")
obj = mem.read_dword(pid, h, base + 0x9FF6C)
print(f"obj = {obj:#x}")
raw = mem.read(pid, h, obj, 0x200)
for off in range(0, 0x200, 4):
    v = int.from_bytes(raw[off:off+4], "little")
    if v > 0x10000000:  # 高址指针
        print(f"  +{off:#04x}: {v:#x}")

# 也检查 obj-0x100 到 obj+0x100 的低址区域
print("\n== obj 前 0x40 与后 0x40 原始 ==")
for off in range(0, 0x40, 4):
    v = int.from_bytes(raw[off:off+4], "little")
    print(f"  +{off:#04x}: {v:#x}")

ctypes.windll.kernel32.CloseHandle(h)
