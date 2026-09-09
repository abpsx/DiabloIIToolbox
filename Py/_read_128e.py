# -*- coding: utf-8 -*-
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
raw = mem.read(pid, h, 0x128E1880, 0x800)
i = 0
while i < len(raw) - 8:
    if 32 <= raw[i] < 127:
        j = i
        while j < len(raw) and raw[j] != 0:
            j += 1
        s = raw[i:j]
        if 3 <= len(s) <= 24 and all(32 <= b < 127 for b in s):
            print(f"{0x128E1880 + i:#x}: {s.decode('latin-1')!r}")
        i = j + 1
    else:
        i += 4
ctypes.windll.kernel32.CloseHandle(h)
