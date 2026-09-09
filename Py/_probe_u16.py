# -*- coding: utf-8 -*-
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
print("PID", pid)
if not pid:
    sys.exit()
h = mem.open_process_readonly(pid)
for addr in (0x135603CA, 0x124F6882, 0x1287E300, 0x489ED00):
    raw = mem.read(pid, h, addr, 64)
    print(f"{addr:#x}: {raw[:32].hex(' ')}")
    try:
        t16 = raw.decode("utf-16-le", errors="replace").split("\x00")[0]
        print("  utf16:", repr(t16[:30]))
    except Exception as e:
        print("  err", e)
    try:
        t8 = raw.split(b"\x00")[0].decode("utf-8", errors="replace")
        if t8.strip():
            print("  utf8:", repr(t8[:30]))
    except Exception:
        pass
ctypes.windll.kernel32.CloseHandle(h)
