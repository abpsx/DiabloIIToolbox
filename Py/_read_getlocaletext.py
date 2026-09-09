# -*- coding: utf-8 -*-
"""读 D2Lang+0x9450 GetLocaleText 机器码，找表基址"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

lang_base = mem.module_base(pid, "D2Lang.dll")
print(f"D2Lang 基址: {lang_base:#x}")
faddr = lang_base + 0x9450
code = mem.read(pid, h, faddr, 96)
print(f"GetLocaleText @ {faddr:#x}:")
print(code.hex(" "))

# 简单找 mov eax,[addr] (A1 xx xx xx xx) / mov ecx,[addr] (8B 0D) / mov edx,[addr] (8B 15)
import re
for i in range(len(code) - 4):
    b = code[i]
    if b in (0xA1,):
        addr = int.from_bytes(code[i+1:i+5], "little")
        print(f"  +{i:#x}: mov eax, [{addr:#x}]")
    elif code[i:i+2] == b"\x8B\x0D":
        addr = int.from_bytes(code[i+2:i+6], "little")
        print(f"  +{i:#x}: mov ecx, [{addr:#x}]")
    elif code[i:i+2] == b"\x8B\x15":
        addr = int.from_bytes(code[i+2:i+6], "little")
        print(f"  +{i:#x}: mov edx, [{addr:#x}]")

ctypes.windll.kernel32.CloseHandle(h)
