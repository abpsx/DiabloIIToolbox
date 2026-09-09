# -*- coding: utf-8 -*-
"""搜指向 tsc 行首 0x128E1A1C 的 4 字节指针，找 GetItemText 指针数组"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

TARGET = 0x128E1A1C  # tsc 行首
target_bytes = TARGET.to_bytes(4, "little")

regions = []
addr = 0x10000
while addr < 0x7FFFFFFF:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

hits = []
for lo, size in regions:
    chunk = 0x100000
    for off in range(0, size, chunk):
        buf = mem.read(pid, h, lo + off, min(chunk, size - off))
        if not buf:
            continue
        p = 0
        while True:
            i = buf.find(target_bytes, p)
            if i < 0:
                break
            hits.append(lo + off + i)
            p = i + 1

print("指向 tsc 行首的指针命中:", len(hits))
for hit in hits:
    # 检查是否为数组元素（前/后连续）
    prev_ok = 0
    next_ok = 0
    # 前一个 4 字节
    prev4 = mem.read_dword(pid, h, hit - 4)
    next4 = mem.read_dword(pid, h, hit + 4)
    print(f"  {hit:#x}: prev={prev4:#x} next={next4:#x}")

ctypes.windll.kernel32.CloseHandle(h)
