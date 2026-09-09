# -*- coding: utf-8 -*-
"""大范围 dump 0x12A54000 起明文池，找序号 2200/5391/5425 的 key"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

START = 0x12A54000
SIZE = 0x140000
raw = mem.read(pid, h, START, SIZE)
print(f"读取 {START:#x}+{SIZE:#x} = {len(raw)} 字节")

# 解析 key\0value\0 交替（UTF-8）
pairs = []
pos = 0
while pos < len(raw):
    z = raw.find(b"\x00", pos)
    if z < 0:
        break
    key = raw[pos:z]
    pos = z + 1
    z = raw.find(b"\x00", pos)
    if z < 0:
        break
    val = raw[pos:z]
    pos = z + 1
    if not key:
        break
    try:
        ks = key.decode("utf-8", errors="replace")
    except Exception:
        ks = repr(key)
    pairs.append((ks, val[:40].decode("utf-8", errors="replace")))
    if len(pairs) >= 6000:
        break

print("解析对数:", len(pairs))
for i, (k, v) in enumerate(pairs):
    if i in (0, 1, 2, 3, 1416, 2200, 2202, 4319, 5391, 5392, 5425):
        print(f"  [{i}] {k!r} = {v!r}")
# 找关键 key
for i, (k, v) in enumerate(pairs):
    if k in ("tsc", "isc", "portal1", "pr1", "pr56", "Endthispuppy"):
        print(f"  key[{i}] {k!r} = {v!r}")

ctypes.windll.kernel32.CloseHandle(h)
