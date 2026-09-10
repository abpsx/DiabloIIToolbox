# -*- coding: utf-8 -*-
"""dump 0x02CBE36C 周围 0x500 找结构特征"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

base = 0x02CBE36C - 0x100
raw = mem.read(pid, h, base, 0x500)
print(f"dump 0x{base:X} 起 0x500 字节 (每行16字节):")
for off in range(0, 0x500, 16):
    chunk = raw[off:off+16]
    hexs = " ".join(f"{b:02X}" for b in chunk)
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"0x{base+off:08X}  {hexs}  {asc}")
ctypes.windll.kernel32.CloseHandle(h)
