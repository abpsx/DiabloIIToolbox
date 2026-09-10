# -*- coding: utf-8 -*-
"""综合快照：游戏核心模块数据段 + 补丁堆区"""
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

def collect(lo0, hi0):
    out = []
    addr = lo0
    while addr < hi0:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and ((mbi.Protect & 0xFF) in (0x02, 0x04)):
            out.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF
    return out

mods = {}
for name in ["D2Common.dll", "D2CLIENT.DLL", "Fog.dll", "D2Win.dll",
             "D2MultiRes_113c.dll", "Anhei2Map.dll", "D2MCPClient.dll", "d2launch.dll"]:
    b = mem.module_base(pid, name)
    if b:
        mods[name] = (b, 0x200000)  # 覆盖 2MB（含数据段）
        print(f"{name} base=0x{b:X}")

snap = {}
ranges = [(b, b + sz) for b, sz in mods.values()]
ranges += [(0x10000000, 0x11000000), (0x1E850000, 0x20000000)]
for lo0, hi0 in ranges:
    for lo, size in collect(lo0, hi0):
        buf = mem.read(pid, h, lo, min(size, 0x2000000))
        if buf:
            snap[str(lo)] = buf.hex()
print(f"快照 {len(snap)} region，{sum(len(v)//2 for v in snap.values())/1048576:.1f} MB")
json.dump(snap, open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_diff_snap2.json", "w"))
print("已存 _diff_snap2.json")
ctypes.windll.kernel32.CloseHandle(h)
