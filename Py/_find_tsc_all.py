# -*- coding: utf-8 -*-
"""全内存搜 'tsc ' 4字节，找 misc 数据表位置"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
MEM_COMMIT = 0x1000
PAGE_READABLE = 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x40 | 0x80


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

needle = b"tsc "
addr = 0x10000
regions = []
while addr < 0x7FFFFFFF:
    mbi = MEMORY_BASIC_INFORMATION()
    r = kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi),
                                ctypes.sizeof(mbi))
    if not r:
        break
    size = mbi.RegionSize or 0x1000
    if mbi.State == MEM_COMMIT and (mbi.Protect & 0xFF) & PAGE_READABLE:
        regions.append((int(mbi.BaseAddress), int(size)))
    addr = (int(mbi.BaseAddress) + size + 0xFFFF) & ~0xFFFF

hits = []
for lo, size in regions:
    chunk = 0x100000
    for off in range(0, size, chunk):
        n = min(chunk, size - off)
        buf = mem.read(pid, h, lo + off, n)
        if not buf:
            continue
        p = 0
        while True:
            i = buf.find(needle, p)
            if i < 0:
                break
            hits.append(lo + off + i)
            p = i + 1
            if len(hits) > 60:
                break
        if len(hits) > 60:
            break
    if len(hits) > 60:
        break

print("tsc 命中", len(hits))
for x in sorted(set(hits)):
    print(f"  {x:#x}")
ctypes.windll.kernel32.CloseHandle(h)
