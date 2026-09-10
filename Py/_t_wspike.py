# -*- coding: utf-8 -*-
"""搜 uniqueitems 表: "Wizardspike" ASCII/UTF-16 命中, dump 周围识别记录结构。"""
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
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]

pid = mem.find_process("D2Loader.exe")
h = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
needles = [("Wizardspike", b"Wizardspike"), ("Wizardspike_UTF16", "Wizardspike".encode("utf-16-le"))]
hits = {n: [] for n, _ in needles}
addr = 0
mbi = MEMORY_BASIC_INFORMATION()
while addr < 0x7FFFFFFF:
    if kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
        break
    base = int(mbi.BaseAddress or 0); size = int(mbi.RegionSize)
    if size > 0 and (mbi.State & MEM_COMMIT) and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x08, 0x10, 0x20, 0x40):
        buf = ctypes.create_string_buffer(size)
        n = ctypes.c_size_t(0)
        if kernel32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(n)):
            data = buf.raw[:n.value]
            for name, pat in needles:
                pos = 0
                while True:
                    i = data.find(pat, pos)
                    if i < 0: break
                    hits[name].append(base + i)
                    pos = i + len(pat)
    addr = base + size

for name, lst in hits.items():
    print("%s: %d 处" % (name, len(lst)))
    for a in lst[:15]:
        print("   %#x" % a)

# dump 首个 ASCII 命中周围
if hits["Wizardspike"]:
    a = hits["Wizardspike"][0]
    raw = ctypes.create_string_buffer(0x100)
    n = ctypes.c_size_t(0)
    kernel32.ReadProcessMemory(h, ctypes.c_void_p(a - 0x40), raw, 0x100, ctypes.byref(n))
    b = raw.raw[:n.value]
    for off in range(0, 0x100, 16):
        hexs = " ".join("%02X" % x for x in b[off:off+16])
        asc = "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in b[off:off+16])
        print("   %+03X  %s  |%s|" % (off - 0x40, hexs, asc))
kernel32.CloseHandle(h)
