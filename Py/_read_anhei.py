# -*- coding: utf-8 -*-
"""读 Anhei2Map.dll+0x556E0 区域 + 找 9页 文本实例"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
base = mem.module_base(pid, "Anhei2Map.dll")
print(f"Anhei2Map.dll base=0x{base:X}")
for off in [0x556E0, 0x556F0, 0x55700, 0x55740, 0x55780, 0x55800]:
    raw = mem.read(pid, h, base + off, 48)
    print(f"0x{base+off:X}: hex={raw.hex(' ')}")
    print(f"           utf16={raw.decode('utf-16-le', errors='replace')!r}")
ctypes.windll.kernel32.CloseHandle(h)
