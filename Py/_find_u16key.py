# -*- coding: utf-8 -*-
"""枚举 32 位地址空间可读区域，搜 UTF-16LE key 模式定位 pr/cm/qf/elc 全称表"""
import ctypes
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed"); sys.exit(1)

MEM_COMMIT = 0x1000
PAGE_READABLE = 0x01 | 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x40 | 0x80  # 排除 NOACCESS(1)/GUARD 处理


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_uint32),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_uint32),
        ("Protect", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
    ]


patterns = {
    "pr1": b"\x70\x00\x72\x00\x31\x00\x00\x00",
    "cm11": b"\x63\x00\x6d\x00\x31\x00\x31\x00\x00\x00",
    "qf1": b"\x71\x00\x66\x00\x31\x00\x00\x00",
    "elc": b"\x65\x00\x6c\x00\x63\x00\x00\x00",
}
found = {k: [] for k in patterns}
regions = 0

addr = 0x10000
while addr < 0x7FFE0000:
    mbi = MBI()
    r = m.kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(MBI))
    if not r:
        break
    base = mbi.BaseAddress or 0
    size = int(mbi.RegionSize)
    if not size:
        break
    if mbi.State & MEM_COMMIT and (mbi.Protect & 0xFF) and not (mbi.Protect & 0x100):  # 排除 PAGE_GUARD
        regions += 1
        chunk = m.read(pid, h, base, size)
        if chunk:
            for k, p in patterns.items():
                pos = 0
                while True:
                    i = chunk.find(p, pos)
                    if i < 0:
                        break
                    found[k].append(base + i)
                    pos = i + 1
    addr = base + size

m.kernel32.CloseHandle(h)
print(f"枚举 {regions} 个可读区域")
for k, lst in found.items():
    print(f"{k}: {len(lst)} 处", [hex(x) for x in lst[:8]])
