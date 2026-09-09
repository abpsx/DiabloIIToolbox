# -*- coding: utf-8 -*-
"""检查 0x128E0000~0x12900000 区域可读性，直接读行 679 地址"""
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

# 区域扫描 0x128A0000 - 0x12980000
addr = 0x128A0000
while addr < 0x12980000:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    base = int(mbi.BaseAddress)
    size = int(mbi.RegionSize)
    print(f"  {base:#x} size={size:#x} state={mbi.State:#x} protect={mbi.Protect:#x} type={mbi.Type:#x}")
    addr = base + size

# 直接读关键地址
for a in (0x128AADF4, 0x128E1A1C, 0x128F0000, 0x128F128C, 0x128F119C, 0x1292766C, 0x12927D0C):
    raw = mem.read(pid, h, a, 16)
    print(f"  读 {a:#x}: {raw!r}")

ctypes.windll.kernel32.CloseHandle(h)
