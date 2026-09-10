# -*- coding: utf-8 -*-
"""翻页 diff 快照：Anhei2Map.dll 数据段 + 0x1E850000 分配区"""
import sys, ctypes, json
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

def collect_regions(lo0, hi0):
    regions = []
    addr = lo0
    while addr < hi0:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and ((mbi.Protect & 0xFF) in (0x02, 0x04)):  # RW/R
            regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF
    return regions

anhei = mem.module_base(pid, "Anhei2Map.dll")
print(f"Anhei2Map.dll base=0x{anhei:X}")
ranges = [(anhei, anhei + 0x593000), (0x1E850000, 0x20000000)]
snap = {}
total_bytes = 0
for lo0, hi0 in ranges:
    for lo, size in collect_regions(lo0, hi0):
        buf = mem.read(pid, h, lo, min(size, 0x1000000))
        if buf:
            snap[str(lo)] = buf.hex()
            total_bytes += len(buf)
print(f"快照 {len(snap)} 个 region，共 {total_bytes/1024/1024:.1f} MB")
json.dump(snap, open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_diff_snap.json", "w"))
print("已存 _diff_snap.json")
ctypes.windll.kernel32.CloseHandle(h)
