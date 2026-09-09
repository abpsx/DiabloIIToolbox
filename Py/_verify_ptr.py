# -*- coding: utf-8 -*-
"""核对城镇卷指针 0x12A3C4EE"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed"); sys.exit(1)

USER_PTR = 0x12A3C4EE

base = m.resolve_base(pid, "D2CLIENT.DLL+0x11B800")
P = m.read_dword(pid, h, base)
print(f"P = *(0x11B800) = {P:#x}")

slot0 = m.read_dword(pid, h, P + 0x700)   # 背包第一格物品对象
slot1 = m.read_dword(pid, h, P + 0x704)   # 第二格
print(f"P+0x700 (第一格) = {slot0:#x}  {'== 用户指针!' if slot0 == USER_PTR else '!= 用户指针'}")
print(f"P+0x704 (第二格) = {slot1:#x}")

# 从用户指针读物品码
c0 = m.read_dword(pid, h, USER_PTR + 0x4)
print(f"*(用户指针+0x4) = {c0:#x} ({c0})  -> {'tsc' if c0 == 529 else 'isc' if c0 == 530 else '?'}")

# 从槽 0 指针读物品码
if slot0:
    c1 = m.read_dword(pid, h, slot0 + 0x4)
    print(f"*(slot0+0x4) = {c1:#x} ({c1})  -> {'tsc' if c1 == 529 else 'isc' if c1 == 530 else '?'}")

# 用户指针处内容
print("用户指针前 0x20 dword:", [hex(m.read_dword(pid, h, USER_PTR + o)) for o in range(0, 0x20, 4)])

m.kernel32.CloseHandle(h)
