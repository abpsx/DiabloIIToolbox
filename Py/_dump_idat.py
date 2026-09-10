# -*- coding: utf-8 -*-
"""1) 连续3次读链表确认稳定  2) dump pItemData 完整结构找页号"""
import sys, ctypes, time
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

d2c = mem.module_base(pid, "D2CLIENT.DLL")

def read_bag():
    pPlayer = dword(d2c + 0x11B800)
    pInv = dword(pPlayer + 0x60)
    cur = dword(pInv + 0x0C)
    seen = set()
    out = []
    n = 0
    while cur and cur not in seen and n < 60:
        seen.add(cur)
        txt = dword(cur + 4)
        idat = dword(cur + 0x14)
        r69 = mem.read(pid, h, idat + 0x69, 1) if idat else b""
        r45 = mem.read(pid, h, idat + 0x45, 1) if idat else b""
        if r69 and r45 and r69[0] == 1 and r45[0] == 4:
            name = lt.txt_to_name(pid, h, txt)[0]
            out.append((txt, name, idat, cur))
        cur = dword(idat + 0x64) if idat else 0
        n += 1
    return out

for i in range(3):
    items = read_bag()
    print(f"读{i+1}: {[(t, n) for t, n, _, _ in items]}")
    time.sleep(0.5)

# dump 第一个物品 pItemData 前 0x200 字节，找 ==9/10 的字段
if items:
    idat = items[0][2]
    raw = mem.read(pid, h, idat, 0x200) or b""
    print(f"\n0x{idat:X} pItemData 前 0x200:")
    for i in range(0, 0x200, 16):
        row = raw[i:i+16]
        vals = " ".join(f"{b:02X}" for b in row)
        print(f"  +0x{i:03X}: {vals}")
    print("\n==9/10 的 dword/byte 位置:")
    for i in range(0, 0x200, 4):
        v = int.from_bytes(raw[i:i+4], "little")
        if v in (9, 10):
            print(f"  +0x{i:X} dword = {v}")
    for i in range(0x200):
        if raw[i] in (9, 10):
            print(f"  +0x{i:X} byte = {raw[i]}")
ctypes.windll.kernel32.CloseHandle(h)
