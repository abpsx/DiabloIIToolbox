# -*- coding: utf-8 -*-
"""读页签结构指针目标 + 当前页验证"""
import sys, ctypes, re
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    return mem.read_dword(pid, h, a)

# 页签结构
S = 0x02CBE36C
print(f"页签结构 0x{S:X}:")
print(f"  +0x00 页数dword = {dword(S)} (0x{dword(S):X})")
for off in [0x04, 0x08, 0x0C, 0x10, 0x14]:
    print(f"  +0x{off:02X} = 0x{dword(S+off):X}")

# 指针目标
for off in [0x04, 0x08]:
    p = dword(S + off)
    raw = mem.read(pid, h, p, 80)
    print(f"\n[0x{S+off:X}] -> 0x{p:X}:")
    print("  hex:", raw[:64].hex(" ") if raw else "?")
    s = raw.decode("utf-16-le", errors="replace") if raw else ""
    m = re.search(r"当前页数\s*:\s*(\d+)页", s)
    print("  utf16:", s[:50])
    if m:
        print(f"  >>> 文本页数 = {m.group(1)}")

# 仓库物品
d2c = mem.module_base(pid, "D2CLIENT.DLL")
pPlayer = dword(d2c + 0x11B800)
pInv = dword(pPlayer + 0x60)
cur = dword(pInv + 0x0C)
seen = set(); items = []; n = 0
import locale_text as lt
while cur and cur not in seen and n < 80:
    seen.add(cur)
    txt = dword(cur + 4)
    idat = dword(cur + 0x14)
    r69 = mem.read(pid, h, idat + 0x69, 1) if idat else b""
    r45 = mem.read(pid, h, idat + 0x45, 1) if idat else b""
    if r69 and r45 and r69[0] == 1 and r45[0] == 4:
        items.append(lt.txt_to_name(pid, h, txt)[0])
    cur = dword(idat + 0x64) if idat else 0
    n += 1
print("\n当前仓库物品:", items)
ctypes.windll.kernel32.CloseHandle(h)
