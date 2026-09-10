# -*- coding: utf-8 -*-
"""翻页对比：翻页前快照 vs 现在。确认最新实例规律 + 物品变化"""
import sys, ctypes, json, re
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

# 1) 检查旧快照中的高地址实例现状
try:
    snap = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_page_snap.json", encoding="utf-8"))
    old_top = [[int(a, 16), n] for a, n in snap["insts"]]
    old_top.sort()
    print("旧快照最大地址 5 个现状:")
    for a, n in old_top[-5:]:
        s = mem.read(pid, h, a, 40)
        s = s.decode("utf-16-le", errors="ignore") if s else ""
        print(f"  0x{a:X} 旧={n}页 现在={s[:30]!r}")
except Exception as e:
    print("快照读取失败:", e)

# 2) 重新扫 0x1E850000 分配，找最新（最大地址）'当前页数 : N页'
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]
regions = []
addr = 0x1E850000
while addr < 0x20000000:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if int(mbi.AllocationBase) != 0x1E850000:
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF
        continue
    if mbi.State == 0x1000:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

dword_feat = (0x524D5F53).to_bytes(4, "little")
insts = []
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
            s = buf[i:i + 80].decode("utf-16-le", errors="ignore")
            m = re.match(r"当前页数 : (\d+)页", s)
            if m:
                insts.append((a, int(m.group(1))))
            p = i + 1

insts.sort()
from collections import Counter
c = Counter(n for _, n in insts)
print(f"\n当前实例 {len(insts)} 处，数字分布 {dict(c)}")
print("最大地址 8 个:")
for a, n in insts[-8:]:
    print(f"  0x{a:X} = {n}页")

# 3) 当前仓库物品（loc=4）
d2c = mem.module_base(pid, "D2CLIENT.DLL")
pPlayer = dword(d2c + 0x11B800)
pInv = dword(pPlayer + 0x60)
cur = dword(pInv + 0x0C)
seen = set()
items = []
n = 0
while cur and cur not in seen and n < 60:
    seen.add(cur)
    txt = dword(cur + 4)
    idat = dword(cur + 0x14)
    r69 = mem.read(pid, h, idat + 0x69, 1) if idat else b""
    r45 = mem.read(pid, h, idat + 0x45, 1) if idat else b""
    if r69 and r45 and r69[0] == 1 and r45[0] == 4:
        name = lt.txt_to_name(pid, h, txt)[0]
        items.append((txt, name))
    cur = dword(idat + 0x64) if idat else 0
    n += 1
print(f"\n当前仓库物品 {len(items)} 件:")
for txt, name in items:
    print(f"  txt={txt} {name}")

ctypes.windll.kernel32.CloseHandle(h)
