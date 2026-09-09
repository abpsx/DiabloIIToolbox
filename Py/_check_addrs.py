# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit(1)
h = mem.open_process_readonly(pid)
for a in (0x12A3C4EE, 0x12A55700, 0x127A004C, 0x127E64E4, 0x127E65A4):
    raw = mem.read(pid, h, a, 32)
    print(f"{a:#x}: {raw!r}")
    if raw:
        print("   utf8:", raw.split(b"\x00")[0].decode("utf-8", errors="replace"))
ctypes.windll.kernel32.CloseHandle(h) if False else None
import ctypes
ctypes.windll.kernel32.CloseHandle(h)
