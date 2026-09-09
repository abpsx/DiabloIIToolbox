# -*- coding: utf-8 -*-
"""读 GetLocaleText 各表指针，验证表[2200]/[5391]/[5425]"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

PTRS = [0x2510A64, 0x2510A6C, 0x2510A70, 0x2510A80, 0x2510A84]
for p in PTRS:
    t = mem.read_dword(pid, h, p)
    print(f"表指针 [{p:#x}] = {t:#x}")

# 对每个表指针，读 [idx] 并读字符串
def read_str(addr, maxlen=80):
    if not addr:
        return None
    raw = mem.read(pid, h, addr, maxlen)
    if not raw:
        return None
    # 尝试 UTF-16
    try:
        s = raw.decode("utf-16-le", errors="ignore").split("\x00")[0]
        if s and any(ord(c) > 0x2E00 for c in s[:5]):
            return s
    except Exception:
        pass
    # UTF-8
    try:
        s = raw.split(b"\x00")[0].decode("utf-8", errors="ignore")
        if s:
            return s
    except Exception:
        pass
    return None

for p in PTRS:
    t = mem.read_dword(pid, h, p)
    if not t or t > 0x80000000:
        continue
    print(f"\n== 表 [{p:#x}] -> {t:#x} ==")
    # 读表头结构（前 8 字节可能是 count/unknown）
    hdr = mem.read(pid, h, t, 16)
    print(f"  表头: {hdr!r}")
    for idx in (0, 1, 5, 2200, 2202, 4319, 5391, 5392, 5425):
        ent = mem.read_dword(pid, h, t + idx * 4)
        s = read_str(ent) if ent else None
        print(f"  [{idx}] -> {ent:#x} {s!r}")

ctypes.windll.kernel32.CloseHandle(h)
