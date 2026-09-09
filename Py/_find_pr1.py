# -*- coding: utf-8 -*-
"""搜 'pr1 ' 命中并检查 ItemTxt 行特征"""
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

for needle in (b"pr1 ", b"portal1", b"pr12"):
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
                i = buf.find(needle, p)
                if i < 0:
                    break
                hits.append(lo + off + i)
                p = i + 1
    print(f"\n== 搜 {needle!r}: {len(hits)} 处 ==")
    for hit in hits[:40]:
        # ItemTxt 行检查：行首 = hit-0x80（若 code@+0x80）
        rs = hit - 0x80
        loc = mem.read(pid, h, rs + 0xF4, 2)
        ntype = mem.read(pid, h, rs + 0x11E, 1)
        prev4 = mem.read(pid, h, hit - 4, 4)
        nxt4 = mem.read(pid, h, hit + 8, 4)
        print(f"  {hit:#x}: 行首{rs:#x} locale={int.from_bytes(loc,'little') if loc else -1} nType={ntype[0] if ntype else -1} prev={prev4!r} next8={nxt4!r}")

ctypes.windll.kernel32.CloseHandle(h)
