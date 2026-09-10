# -*- coding: utf-8 -*-
"""搜游戏内存中的 unique 名（UTF-16LE）, 定位 uniqueitems 表。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_READABLE = 0x04 | 0x02 | 0x08 | 0x10 | 0x20 | 0x40 | 0x80  # RWX+copy+guard+noaccess排除

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

pid = mem.find_process("D2Loader.exe")
h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
print("PID", pid, "handle", h)

needle = "巫师之刺".encode("utf-16-le")
hits = []
addr = 0
mbi = MEMORY_BASIC_INFORMATION()
while addr < 0x7FFFFFFF:
    if kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi),
                               ctypes.sizeof(mbi)) == 0:
        break
    base = int(mbi.BaseAddress or 0)
    size = int(mbi.RegionSize)
    if size > 0 and (mbi.State & MEM_COMMIT) and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x08, 0x10, 0x20, 0x40):
        buf = ctypes.create_string_buffer(size)
        n = ctypes.c_size_t(0)
        if kernel32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(n)):
            data = buf.raw[:n.value]
            pos = 0
            while True:
                i = data.find(needle, pos)
                if i < 0:
                    break
                hits.append(base + i)
                pos = i + 2
    addr = base + size
print("命中:", len(hits))
for a in hits[:10]:
    print("  0x%X" % a)

# dump 首个命中周围
if hits:
    a = hits[0]
    buf = ctypes.create_string_buffer(0x100)
    n = ctypes.c_size_t(0)
    if kernel32.ReadProcessMemory(h, ctypes.c_void_p(a - 0x20), buf, 0x100, ctypes.byref(n)):
        raw = buf.raw[:n.value]
        for off in range(0, 0x100, 0x10):
            hexs = " ".join("%02X" % b for b in raw[off:off+16])
            try:
                s = raw[off:off+16].decode("utf-16-le", errors="ignore")
                s = "".join(ch if ch.isprintable() else "." for ch in s)
            except Exception:
                s = ""
            print("  %+03X  %s  |%s|" % (off - 0x20, hexs, s))
kernel32.CloseHandle(h)
