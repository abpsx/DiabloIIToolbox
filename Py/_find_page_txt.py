# -*- coding: utf-8 -*-
"""内存全扫 '当前页数'（UTF-8 / UTF-16LE / GBK），并反查指向它的指针"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

# 候选编码
needles = {
    "utf8": "当前页数".encode("utf-8"),
    "utf16le": "当前页数".encode("utf-16-le"),
    "gbk": "当前页数".encode("gbk"),
}

# VirtualQuery 收集可读区
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

hits = []
for enc, needle in needles.items():
    for lo, size in regions:
        chunk = 0x100000  # 1MB
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(needle, p)
                if i < 0:
                    break
                hits.append((enc, lo + off + i))
                p = i + 1

print(f"命中 {len(hits)} 处:")
for enc, a in hits:
    # 打印字符串后 32 字节（可能含页数）
    tail = mem.read(pid, h, a, 40) or b""
    if enc == "utf16le":
        tail_s = tail.decode("utf-16-le", errors="replace")
    elif enc == "gbk":
        tail_s = tail.decode("gbk", errors="replace")
    else:
        tail_s = tail.decode("utf-8", errors="replace")
    print(f"  [{enc}] {a:#x}: {tail_s!r}")

# 反查指针：全扫 dword == hit（限前几个）
print("\n反查指向指针:")
for enc, a in hits[:6]:
    needle = a.to_bytes(4, "little")
    ptrs = []
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
                ptrs.append(lo + off + i)
                if len(ptrs) >= 12:
                    break
                p = i + 1
            if len(ptrs) >= 12:
                break
        if len(ptrs) >= 12:
            break
    print(f"  [{enc}] {a:#x} <- 指针存放于: {[hex(x) for x in ptrs]}")

ctypes.windll.kernel32.CloseHandle(h)
