# -*- coding: utf-8 -*-
"""全域扫 '当前页数 : ' 提取页数数字，按数字聚合 + 每数字代表地址"""
import sys, ctypes, re, collections
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

regions = []
addr = 0x10000
while addr < 0x7FFFFFFF:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

needle = "当前页数 : ".encode("utf-16-le")
stats = collections.Counter()
examples = {}
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
            a = lo + off + i
            s = buf[i:i + 30].decode("utf-16-le", errors="ignore")
            m = re.match(r"当前页数 : (\d+)页", s)
            n = int(m.group(1)) if m else -1
            stats[n] += 1
            if n not in examples:
                examples[n] = a
            p = i + 1

print("页数分布:", dict(sorted(stats.items())))
print("各数字代表地址:")
for n in sorted(stats):
    print(f"  {n}页: 0x{examples[n]:X} x{stats[n]}")
ctypes.windll.kernel32.CloseHandle(h)
