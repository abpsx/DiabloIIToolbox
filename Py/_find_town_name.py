# -*- coding: utf-8 -*-
"""搜 '城镇卷' UTF-8 明文，反查 GetLocaleText 索引表"""
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

needle = "城镇卷".encode("utf-8")
print("搜", needle)
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

print("城镇卷 UTF-8 命中:", len(hits))
for hit in hits[:20]:
    print(f"  {hit:#x}")

# 对每个命中点，搜指向它的 4 字节指针
for hit in hits[:5]:
    tb = hit.to_bytes(4, "little")
    phits = []
    for lo, size in regions:
        chunk = 0x100000
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(tb, p)
                if i < 0:
                    break
                phits.append(lo + off + i)
                p = i + 1
    print(f"\n指向 {hit:#x} 的指针: {len(phits)} 处")
    for ph in phits[:15]:
        # 看是否在数组里（检查相邻）
        print(f"  {ph:#x}")

ctypes.windll.kernel32.CloseHandle(h)
