# -*- coding: utf-8 -*-
"""扩大读 0x02C3E370 区域"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
A = 0x02C3E370
raw = mem.read(pid, h, A - 0x100, 0x300) or b""
print("hex (A-0x100 起 0x300):")
for i in range(0, len(raw), 16):
    print(f"  {A-0x100+i:08X}: {raw[i:i+16].hex(' ')}")
print("\nutf16 视图:")
print(raw.decode("utf-16-le", errors="replace"))
ctypes.windll.kernel32.CloseHandle(h)
