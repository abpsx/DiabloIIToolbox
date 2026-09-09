# -*- coding: utf-8 -*-
"""人物 UnitAny -> pInventory -> 物品链表，找 tsc 的 UnitAny 读 dwTxtFileNo"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

base = mem.module_base(pid, "D2CLIENT.dll")
p = mem.read_dword(pid, h, base + 0x11B800)
print(f"人物指针 p = {p:#x}")
for off, nm in [(0x0, "dwUnitType"), (0x4, "dwTxtFileNo"), (0x14, "pPlayerData"),
                (0x60, "pInventory")]:
    print(f"  +{off:#x} {nm} = {mem.read_dword(pid,h,p+off):#x}")

inv = mem.read_dword(pid, h, p + 0x60)
print(f"pInventory = {inv:#x}")
if inv:
    for off, nm in [(0x0, "dwSignature"), (0xC, "pFirstItem"), (0x28, "dwItemCount")]:
        print(f"  +{off:#x} {nm} = {mem.read_dword(pid,h,inv+off):#x}")

    # 遍历物品链表（1.13c ItemData +0x64 pNextInvItem? 或 UnitAny pListNext +0xE8）
    # 先试 d2bs 1.14d：ItemData.pNextInvItem +0x64
    first = mem.read_dword(pid, h, inv + 0xC)
    node = first
    n = 0
    while node and n < 60:
        # node 可能是 ItemData 或 UnitAny —— 打印两种偏移
        ut = mem.read_dword(pid, h, node)
        tf = mem.read_dword(pid, h, node + 0x4)
        pd = mem.read_dword(pid, h, node + 0x14)
        nx1 = mem.read_dword(pid, h, node + 0x64)   # ItemData.pNextInvItem?
        nx2 = mem.read_dword(pid, h, node + 0xE8)   # UnitAny.pListNext?
        print(f"  节点{n} @{node:#x}: u={ut} txt={tf} pData={pd:#x} next64={nx1:#x} nextE8={nx2:#x}")
        if nx1 and (nx1 & 0xFFF00000):
            node = nx1
        elif nx2 and (nx2 & 0xFFF00000):
            node = nx2
        else:
            break
        n += 1

ctypes.windll.kernel32.CloseHandle(h)
