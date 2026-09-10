# -*- coding: utf-8 -*-
"""1) 读当前(第10页)仓库物品  2) 页文本实例附近扫 int==10 变量"""
import sys, ctypes, re
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

# 1) 链表仓库物品
d2c = mem.module_base(pid, "D2CLIENT.DLL")
pPlayer = dword(d2c + 0x11B800)
pInv = dword(pPlayer + 0x60)
cur = dword(pInv + 0x0C)
seen = set()
stash_items = []
n = 0
while cur and cur not in seen and n < 60:
    seen.add(cur)
    txt = dword(cur + 4)
    idat = dword(cur + 0x14)
    raw69 = mem.read(pid, h, idat + 0x69, 1) if idat else b""
    raw45 = mem.read(pid, h, idat + 0x45, 1) if idat else b""
    loc69 = raw69[0] if raw69 else -1
    loc45 = raw45[0] if raw45 else -1
    is_stash = loc69 == 1 and loc45 == 4
    name = lt.txt_to_name(pid, h, txt)[0] if is_stash else ""
    if is_stash:
        stash_items.append((txt, name, cur))
    cur = dword(idat + 0x64) if idat else 0
    n += 1
print(f"第10页 仓库物品 {len(stash_items)} 件:")
for txt, name, u in stash_items:
    print(f"  txt={txt} {name} unit={u:#x}")

# 2) 扫 0x1E850000 分配附近：找 10页 文本实例，并检查实例前后 int==10
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

# 扫 alloc=0x1E850000 的所有 region
regions = []
addr = 0x1E850000
while addr < 0x20000000:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if int(mbi.AllocationBase) != 0x1E850000:
        break
    if mbi.State == 0x1000:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

print(f"\n0x1E850000 分配共 {len(regions)} 个 region")
needle = "当前页数 : 10页".encode("utf-16-le")
total = 0
int10_near = []
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
            total += 1
            # 实例前后 0x80 字节内找 int==10
            for dx in range(-0x80, 0x80, 4):
                if dx == 0:
                    continue
                v = dword(a + dx)
                if v == 10:
                    int10_near.append((a, a + dx))
            p = i + 1

print(f"该分配内 10页 实例 {total} 处")
print(f"实例附近 int==10 的变量: {len(int10_near)} 处")
for a, va in int10_near[:15]:
    print(f"  文本@{a:X} 变量@{va:X} ({'+' if va>a else ''}{va-a:#x})")

ctypes.windll.kernel32.CloseHandle(h)
