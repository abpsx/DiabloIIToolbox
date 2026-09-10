# -*- coding: utf-8 -*-
"""页文本快照：记录所有 '当前页数 :' 实例（按 dword 0x524D5F53='当前' 特征定位）"""
import sys, ctypes, json, re
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

# 扫描范围：0x1E850000 大分配（页文本活跃区）+ 全堆低区
ranges = [(0x1E850000, 0x20000000)]
regions = []
for lo0, hi0 in ranges:
    addr = lo0
    while addr < hi0:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
            regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

# 用 dword 特征定位
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
            # 读该处后 40 字节 utf16，解析 '当前页数 : N页'
            s = buf[i:i + 80].decode("utf-16-le", errors="ignore")
            m = re.match(r"当前页数 : (\d+)页", s)
            if m:
                insts.append((a, int(m.group(1))))
            p = i + 1

# 汇总：按数字统计
from collections import Counter
c = Counter(n for _, n in insts)
print(f"实例总数 {len(insts)}，数字分布 {dict(c)}")
# 最新（最大地址）20 个
insts.sort()
print("最大地址 20 个:")
for a, n in insts[-20:]:
    print(f"  0x{a:X} = {n}页")

# 存快照
with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_page_snap.json", "w", encoding="utf-8") as f:
    json.dump({"pid": pid, "insts": [[hex(a), n] for a, n in insts]}, f, ensure_ascii=False, indent=1)
print("快照已存 _page_snap.json")
ctypes.windll.kernel32.CloseHandle(h)
