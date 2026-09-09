# -*- coding: utf-8 -*-
"""正确遍历物品链表：node=UnitAny, ItemData=node+0x14, next=ItemData+0x64"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

base = mem.module_base(pid, "D2CLIENT.dll")
p = mem.read_dword(pid, h, base + 0x11B800)
inv = mem.read_dword(pid, h, p + 0x60)
first = mem.read_dword(pid, h, inv + 0xC)
print(f"pInventory={inv:#x} pFirstItem={first:#x}")

node = first
n = 0
seen = set()
while node and node not in seen and n < 30:
    seen.add(node)
    ut = mem.read_dword(pid, h, node)
    tf = mem.read_dword(pid, h, node + 0x4)
    pd = mem.read_dword(pid, h, node + 0x14)
    nx = 0
    if pd:
        nx = mem.read_dword(pid, h, pd + 0x64)
    print(f"节点{n} @{node:#x}: dwUnitType={ut} dwTxtFileNo={tf} pItemData={pd:#x} next={nx:#x}")
    # ItemData 关键字段
    if pd:
        q = mem.read_dword(pid, h, pd)
        fi = mem.read_dword(pid, h, pd + 0x28)
        il = mem.read_dword(pid, h, pd + 0x2C)
        print(f"    ItemData: dwQuality={q} dwFileIndex={fi} ilvl={il}")
    node = nx
    n += 1
print("遍历完成，节点数 =", n)

ctypes.windll.kernel32.CloseHandle(h)
