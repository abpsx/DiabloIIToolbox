# -*- coding: utf-8 -*-
"""dump 0x12A3C0000 起物品全称池 + 全搜 '白羊宫钥匙'"""
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

# 1) 全搜 '白羊宫钥匙'
needle = "白羊宫钥匙".encode("utf-8")
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
print("白羊宫钥匙 UTF-8 命中:", len(hits))
for hit in hits[:20]:
    print(f"  {hit:#x}")

# 2) dump 0x12A3C0000 区（分段）
print("\n== dump 0x12A3C0000~0x12A4F0000 ==")
pairs = []
for base in range(0x12A3C000, 0x12A4F000, 0x10000):
    raw = mem.read(pid, h, base, 0x10000)
    if not raw:
        continue
    pos = 0
    while pos < len(raw):
        z = raw.find(b"\x00", pos)
        if z < 0:
            break
        key = raw[pos:z]
        pos = z + 1
        z = raw.find(b"\x00", pos)
        if z < 0:
            break
        val = raw[pos:z]
        pos = z + 1
        if not key:
            break
        try:
            ks = key.decode("utf-8", errors="replace")
            vs = val.decode("utf-8", errors="replace")
        except Exception:
            ks, vs = repr(key), repr(val)
        pairs.append((base + pos - len(val) - 1, ks, vs))

print("解析对:", len(pairs))
for i, (ad, k, v) in enumerate(pairs):
    if "pr1" in k or "白羊" in v or "portal1" in k or k == "tsc" or "城镇" in v:
        print(f"  [{i}] @{ad:#x}: {k!r} = {v!r}")

ctypes.windll.kernel32.CloseHandle(h)
