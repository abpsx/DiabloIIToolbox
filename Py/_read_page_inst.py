# -*- coding: utf-8 -*-
"""读 '当前页数 : 2页' 活实例详情 + 所属内存区"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

A = 0x109C0038

# 字符串本体（前 200 字节 UTF-16）
raw = mem.read(pid, h, A, 200)
print(f"0x{A:X} 字符串: {raw.decode('utf-16-le', errors='replace')!r}")

# 所在分配信息
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]
mbi = MBI()
kernel32.VirtualQueryEx(h, ctypes.c_void_p(A), ctypes.byref(mbi), ctypes.sizeof(mbi))
print(f"AllocationBase=0x{mbi.AllocationBase:X} RegionSize=0x{mbi.RegionSize:X} Protect=0x{mbi.Protect:X} Type=0x{mbi.Type:X}")

# 字符串前后的结构：往前看 0x80 字节
pre = mem.read(pid, h, A - 0x80, 0x80) or b""
print(f"前方 0x80 字节(utf16): {pre.decode('utf-16-le', errors='replace')!r}")

# 以 4 字节扫描字符串前的 dword（可能页数变量）
for i in range(0, 0x60, 4):
    v = dword(A - 0x60 + i)
    if v and v < 0x10000:
        print(f"  A-0x{0x60-i:02X} dword = {v} (0x{v:X})")

ctypes.windll.kernel32.CloseHandle(h)
