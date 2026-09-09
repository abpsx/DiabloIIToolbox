# -*- coding: utf-8 -*-
"""读 0x2510A68 表（idx<10000 分派），验证 [5391]=白羊宫钥匙"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

for p in range(0x2510A64, 0x2510A90, 4):
    v = mem.read_dword(pid, h, p)
    print(f"[{p:#x}] = {v:#x}")

tb = mem.read_dword(pid, h, 0x2510A68)
print(f"\n表基 [0x2510A68] = {tb:#x}")

def read_str(addr, maxlen=128):
    if not addr or addr < 0x10000:
        return None
    raw = mem.read(pid, h, addr, maxlen)
    if not raw:
        return None
    try:
        s = raw.decode("utf-16-le", errors="ignore").split("\x00")[0]
        if s and any(ord(c) > 0x2E80 for c in s):
            return s
    except Exception:
        pass
    try:
        return raw.split(b"\x00")[0].decode("utf-8", errors="ignore")
    except Exception:
        return None

# 表[5391]：entry 结构未知，先按 4 字节指针试
for idx, lbl in [(0, "idx0"), (1, "idx1"), (2200, "tsc"), (2202, "isc"), (5391, "pr1"), (5425, "pr56")]:
    ent = mem.read_dword(pid, h, tb + idx * 4)
    s = read_str(ent)
    print(f"  表[{idx}] ({lbl}): {ent:#x} {s!r}")

# 若失败，试 12 字节 entry（hash/off/len）或 8 字节
for esz in (8, 12):
    ent = mem.read(pid, h, tb + 5391 * esz, esz)
    print(f"\nentry宽{esz} 表[5391]: {ent.hex(' ')}")

ctypes.windll.kernel32.CloseHandle(h)
