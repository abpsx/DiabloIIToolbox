# -*- coding: utf-8 -*-
"""dump 0x124F4000~0x124F8000 UTF-16 字符串池"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

base = 0x124F4000
size = 0x4000
raw = mem.read(pid, h, base, size)
print(f"读取 {base:#x}+{size:#x} = {len(raw)} 字节")

# UTF-16-LE 解析（跳过控制字符）
i = 0
strings = []
while i + 1 < len(raw):
    ch = raw[i] | (raw[i+1] << 8)
    if ch == 0:
        i += 2
        continue
    # 收集可打印
    j = i
    buf = []
    while j + 1 < len(raw):
        c2 = raw[j] | (raw[j+1] << 8)
        if c2 == 0:
            break
        if 0x20 <= c2 < 0x7F or c2 >= 0x3000:
            buf.append(chr(c2))
            j += 2
        else:
            break
    if len(buf) >= 2:
        s = "".join(buf)
        strings.append((base + i, s))
        i = j
    else:
        i += 2

print("UTF-16 字符串:", len(strings))
for ad, s in strings:
    if any(k in s for k in ("pr1", "portal", "白羊", "城镇", "辨视", "tsc", "isc", "钥匙")):
        print(f"  {ad:#x}: {s[:60]!r}")

# 也打印前 30 个看结构
print("\n前 40 个字符串:")
for ad, s in strings[:40]:
    print(f"  {ad:#x}: {s[:50]!r}")

ctypes.windll.kernel32.CloseHandle(h)
