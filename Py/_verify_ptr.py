# -*- coding: utf-8 -*-
"""翻页后验证 0x02C3E370 指针"""
import sys, ctypes, re
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

p = dword(0x02C3E370)
raw = mem.read(pid, h, p, 60)
s = raw.decode("utf-16-le", errors="replace") if raw else ""
print(f"[0x02C3E370] = 0x{p:X}")
print(f"  指向内容: {s[:50]!r}")
m = re.match(r"当前页数 : (\d+)页", s)
print("  解析页数:", m.group(1) if m else "非文本")

raw2 = mem.read(pid, h, 0x1AFF7D00, 40)
print("0x1AFF7D00:", raw2.decode("utf-16-le", errors="replace")[:36])

for off in [0x0, 0x4, 0x8, 0xC]:
    print(f"  [0x02C3E370+{off:#x}] = 0x{dword(0x02C3E370+off):X}")

d2c = mem.module_base(pid, "D2CLIENT.DLL")
pPlayer = dword(d2c + 0x11B800)
pInv = dword(pPlayer + 0x60)
cur = dword(pInv + 0x0C)
seen = set()
items = []
n = 0
while cur and cur not in seen and n < 60:
    seen.add(cur)
    txt = dword(cur + 4)
    idat = dword(cur + 0x14)
    r69 = mem.read(pid, h, idat + 0x69, 1) if idat else b""
    r45 = mem.read(pid, h, idat + 0x45, 1) if idat else b""
    if r69 and r45 and r69[0] == 1 and r45[0] == 4:
        items.append(lt.txt_to_name(pid, h, txt)[0])
    cur = dword(idat + 0x64) if idat else 0
    n += 1
print("当前仓库物品:", items)
ctypes.windll.kernel32.CloseHandle(h)
