# -*- coding: utf-8 -*-
"""搜 '城镇卷' UTF-16/UTF-8，验证 ItemTxt 行首"""
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

needles = {
    "utf16": "城镇卷".encode("utf-16-le"),
    "utf8": "城镇卷".encode("utf-8"),
}

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

found = {k: [] for k in needles}
for lo, size in regions:
    chunk = 0x100000
    for off in range(0, size, chunk):
        n = min(chunk, size - off)
        buf = mem.read(pid, h, lo + off, n)
        if not buf:
            continue
        for k, nd in needles.items():
            if len(found[k]) >= 40:
                continue
            p = 0
            while True:
                i = buf.find(nd, p)
                if i < 0:
                    break
                found[k].append(lo + off + i)
                p = i + 1

for k, v in found.items():
    print("==", k, len(v))
    for x in sorted(set(v)):
        code40 = mem.read(pid, h, x + 0x40, 4)
        code84 = mem.read(pid, h, x + 0x84, 4)
        ntype = mem.read(pid, h, x + 0x11E, 1)
        print(f"  {x:#x}: +0x40={code40!r} +0x84={code84!r} nType={ntype[0] if ntype else -1}")
ctypes.windll.kernel32.CloseHandle(h)
