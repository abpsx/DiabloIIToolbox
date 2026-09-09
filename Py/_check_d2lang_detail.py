# -*- coding: utf-8 -*-
"""dump 白羊宫钥匙前后 + 0x153385C2 + 搜 portal1/pr1 UTF-16"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

print("== 白羊宫钥匙前 0x124F59C0~0x124F5AC0 ==")
raw = mem.read(pid, h, 0x124F59C0, 0x100)
for i in range(0, len(raw), 16):
    chunk = raw[i:i+16]
    txt = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
    print(f"  {0x124F59C0+i:#x}: {chunk.hex(' ')}  {txt}")

print("\n== 0x153385C2 ==")
raw2 = mem.read(pid, h, 0x153385C2, 0x80)
print(raw2.hex(" "))
# UTF-16 解码
try:
    s = raw2.decode("utf-16-le", errors="replace")
    print("utf16:", repr(s[:60]))
except Exception as e:
    print("err", e)

print("\n== 搜 portal1/pr1/tsc UTF-16 in 0x124E0000~0x12510000 ==")
for key in ("portal1", "pr1", "tsc", "isc", "hax"):
    needle = key.encode("utf-16-le")
    hits = []
    for base in range(0x124E0000, 0x12510000, 0x10000):
        buf = mem.read(pid, h, base, 0x10000)
        if not buf:
            continue
        p = 0
        while True:
            i = buf.find(needle, p)
            if i < 0:
                break
            hits.append(base + i)
            p = i + 1
    print(f"  {key}: {[f'{x:#x}' for x in hits[:10]]}")

ctypes.windll.kernel32.CloseHandle(h)
