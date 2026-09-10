# -*- coding: utf-8 -*-
"""测试：两次扫描间新增的页文本实例页数 = 当前页？"""
import sys, ctypes, re, time
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
    out = []
    addr = lo0
    while addr < hi0:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
            out.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF
    return out

ranges = [(0x10000000, 0x11000000), (0x1E850000, 0x20000000)]
regions = []
for lo0, hi0 in ranges:
    regions += collect_regions(lo0, hi0)

dword_feat = (0x524D5F53).to_bytes(4, "little")

def scan():
    insts = {}
    for lo, size in regions:
        chunk = 0x100000
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(dword_feat, p)
                if i < 0:
                    break
                a = lo + off + i
                s = buf[i:i + 60].decode("utf-16-le", errors="ignore")
                m = re.match(r"当前页数 : (\d+)页", s)
                if m:
                    insts[a] = int(m.group(1))
                p = i + 1
    return insts

t0 = time.time()
s1 = scan()
t1 = time.time()
time.sleep(2.0)
s2 = scan()
t2 = time.time()

print(f"扫描1: {len(s1)} 处 ({t1-t0:.2f}s)   扫描2: {len(s2)} 处 ({t2-t1-2:.2f}s)")
from collections import Counter
c1 = Counter(s1.values()); c2 = Counter(s2.values())
print("分布1:", dict(sorted(c1.items())))
print("分布2:", dict(sorted(c2.items())))
new = {a: n for a, n in s2.items() if a not in s1}
gone = {a: n for a, n in s1.items() if a not in s2}
print(f"\n新增 {len(new)} 处（页数: {Counter(new.values()) if new else '无'}）")
print(f"消失 {len(gone)} 处（页数: {Counter(gone.values()) if gone else '无'}）")
# 新实例代表地址
for a, n in list(new.items())[:10]:
    print(f"  新 0x{a:X} = {n}页")
ctypes.windll.kernel32.CloseHandle(h)
