# -*- coding: utf-8 -*-
"""全空间枚举可读区域，搜指向给定地址的 dword 指针"""
import ctypes
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed"); sys.exit(1)

TARGETS = [0x135603C8, 0x135603CA, 0x124F6894, 0x124F6970, 0x124F6882]


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


found = {t: [] for t in TARGETS}
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
    if mbi.State & 0x1000 and (mbi.Protect & 0xFF) and not (mbi.Protect & 0x100):
        regions += 1
        chunk = m.read(pid, h, base, size)
        if chunk:
            for t in TARGETS:
                tb = t.to_bytes(4, "little")
                pos = 0
                while True:
                    i = chunk.find(tb, pos)
                    if i < 0:
                        break
                    found[t].append(base + i)
                    pos = i + 1
    addr = base + size

m.kernel32.CloseHandle(h)
print(f"枚举 {regions} 区域")
for t, lst in found.items():
    print(f"指向 {t:#x}: {len(lst)} 处", [hex(x) for x in lst[:10]])
