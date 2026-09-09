# -*- coding: utf-8 -*-
"""定位全称表管理指针：在 D2Common.dll 数据段找指向表起点 0x12A3A73E 的 dword"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed"); sys.exit(1)

TARGET = 0x12A3A73E

# 模块基址 + 大小
snap = m.kernel32.CreateToolhelp32Snapshot(m.TH32CS_SNAPMODULE | m.TH32CS_SNAPMODULE32, pid)
base = None
size = 0
if snap != m.INVALID_HANDLE_VALUE:
    entry = m.MODULEENTRY32W()
    entry.dwSize = m.ctypes.sizeof(m.MODULEENTRY32W)
    if m.kernel32.Module32FirstW(snap, m.ctypes.byref(entry)):
        while True:
            if entry.szModule.lower() == "d2common.dll":
                base = int(m.ctypes.addressof(entry.modBaseAddr.contents))
                size = int(entry.modBaseSize)
                break
            if not m.kernel32.Module32NextW(snap, m.ctypes.byref(entry)):
                break
    m.kernel32.CloseHandle(snap)
print(f"D2Common.dll base={base:#x} size={size:#x} ({size} bytes)")
if not base:
    sys.exit(1)

# 0x10 粒度扫描模块内存找 TARGET
hits = []
raw = m.read(pid, h, base, size)
if raw:
    for off in range(0, len(raw) - 3, 4):
        v = int.from_bytes(raw[off:off + 4], "little")
        if v == TARGET:
            hits.append(off)
else:
    # 分段读
    for off in range(0, size, 0x100):
        chunk = m.read(pid, h, base + off, 0x100)
        if chunk:
            for i in range(0, len(chunk) - 3, 4):
                v = int.from_bytes(chunk[i:i + 4], "little")
                if v == TARGET:
                    hits.append(off + i)

print(f"命中 {len(hits)} 处:")
for off in hits[:20]:
    print(f"  D2Common.dll+{off:#x}")

m.kernel32.CloseHandle(h)
