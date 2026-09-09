# -*- coding: utf-8 -*-
"""搜 '白羊宫钥匙' UTF-16-LE，找 D2Lang 表值 + 指向它的指针"""
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

regions = []
addr = 0x10000
while addr < 0x7FFFFFFF:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

for needle, nm in [("白羊宫钥匙".encode("utf-16-le"), "utf16 白羊宫钥匙"),
                   ("城镇卷".encode("utf-16-le"), "utf16 城镇卷")]:
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
    print(f"\n{nm}: {len(hits)} 处")
    for hit in hits[:20]:
        # 搜指向它的指针
        tb = hit.to_bytes(4, "little")
        cnt = 0
        for lo2, size2 in regions:
            chunk = 0x100000
            for off in range(0, size2, chunk):
                buf = mem.read(pid, h, lo2 + off, min(chunk, size2 - off))
                if not buf:
                    continue
                p = 0
                while True:
                    i = buf.find(tb, p)
                    if i < 0:
                        break
                    cnt += 1
                    if cnt <= 3:
                        print(f"  {hit:#x} <- 指针 {lo2+off+i:#x}")
                    p = i + 1
        print(f"  {hit:#x}: 指入 {cnt} 处")

ctypes.windll.kernel32.CloseHandle(h)
