# -*- coding: utf-8 -*-
"""1) 全内存搜 dword==04BD78F6 / 11E04CB2 的引用者; 2) 扫仓库骸骨小刀结构。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def read(pid, h, a, n):
    return mem.read(pid, h, a, n)

pid = mem.find_process("D2Loader.exe")
h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
mods = {}
for m in ["D2CLIENT.DLL", "D2COMMON.DLL", "D2LANG.DLL", "D2WIN.DLL", "Fog.DLL",
          "D2GFX.DLL", "D2Launch.dll", "D2MCPClient.dll", "d2launch.dll", "Anhei2Map.dll"]:
    b = mem.module_base(pid, m)
    if b:
        mods[m] = b
print("mods:", {k: hex(v) for k, v in mods.items()})

def which_mod(a):
    for name, base in mods.items():
        if base <= a < base + 0x200000:
            return "%s+%#x" % (name, a - base)
    return "heap"

# 1) 全内存搜引用
needles = [0x04BD78F6, 0x11E04CB2]
found = {n: [] for n in needles}
addr = 0
mbi = MEMORY_BASIC_INFORMATION()
while addr < 0x7FFFFFFF:
    if kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
        break
    base = int(mbi.BaseAddress or 0)
    size = int(mbi.RegionSize)
    if size > 0 and (mbi.State & MEM_COMMIT) and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x08, 0x10, 0x20, 0x40):
        buf = ctypes.create_string_buffer(size)
        n = ctypes.c_size_t(0)
        if kernel32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(n)):
            data = buf.raw[:n.value]
            for needle in needles:
                pat = needle.to_bytes(4, "little")
                pos = 0
                while True:
                    i = data.find(pat, pos)
                    if i < 0:
                        break
                    found[needle].append(base + i)
                    pos = i + 4
    addr = base + size
for needle, lst in found.items():
    print("引用 %#x: %d 处" % (needle, len(lst)))
    for a in lst[:25]:
        print("   %#x  <- %s" % (a, which_mod(a)))

# 2) 扫仓库骸骨小刀结构
unit, idat, path = 0xabbbE00, dword(pid, h, 0xabbbE00 + 0x14), dword(pid, h, 0xabbbE00 + 0x2C)
print("仓库骸骨小刀 unit=%#x idat=%#x path=%#x" % (unit, idat, path))
ranges = [(0x04BD0000, 0x04BE0000, "T1区"), (0x11E00000, 0x11E10000, "T2区")]
for base, label, size in [(unit, "UnitAny", 0x400), (idat, "ItemData", 0x400), (path, "Path", 0x400)]:
    buf = read(pid, h, base, size)
    if not buf:
        continue
    for off in range(0, len(buf) - 3, 4):
        v = int.from_bytes(buf[off:off+4], "little")
        for lo, hi, tag in ranges:
            if lo <= v < hi:
                print("  %s +%#04x = %#x %s" % (label, off, v, tag))
kernel32.CloseHandle(h)
