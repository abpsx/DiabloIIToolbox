# -*- coding: utf-8 -*-
"""AOB 搜索: 页签控件结构特征 (hgl/tbt/hbt 字体标记序列)
结构布局(已知):
  +0x00: 页数 dword (0基)
  +0x04: 指针A  +0x08: 指针B
  +0x10: FF 00 00 00 01 01 00 00 'hgl ' FF 00 00 00 01 01 00 01 'tbt ' ...
特征: 0x02CBE36C+0x10 起 16 字节 = FF 00 00 00 01 01 00 00 68 67 6C 20 FF 00 00 00
"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# 特征模式: 11 字节足够独特 (FF 00 00 00 01 01 00 00 68 67 6C 20)
pattern = bytes.fromhex("FF0000000101000068676C20")
print(f"搜索特征: {pattern.hex()}")

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
for lo, size in regions:
    chunk = 0x100000
    for off in range(0, size, chunk):
        buf = mem.read(pid, h, lo + off, min(chunk, size - off))
        if not buf:
            continue
        p = 0
        while True:
            i = buf.find(pattern, p)
            if i < 0:
                break
            hits.append(lo + off + i)
            p = i + 1
            if len(hits) > 50:
                break
        if len(hits) > 50:
            break
    if len(hits) > 50:
        break

print(f"\n命中 {len(hits)} 处:")
# 对每处, 检查 命中-0x10 是否为页数(dword 0-12), 命中-0x14 是否为指针
for a in hits:
    pg = mem.read_dword(pid, h, a - 0x10)
    pA = mem.read_dword(pid, h, a - 0x0C)
    pB = mem.read_dword(pid, h, a - 0x08)
    mark = "  <<< 当前页签" if a - 0x10 == 0x02CBE36C else ""
    print(f"  0x{a:X}  页数@0x{a-0x10:X}={pg}  ptrA=0x{pA:X}  ptrB=0x{pB:X}{mark}")
ctypes.windll.kernel32.CloseHandle(h)
