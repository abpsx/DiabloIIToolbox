# -*- coding: utf-8 -*-
"""读背包物品对象前 0x14（UnitAny 假设）与 ItemData 全结构"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

# 先读背包格子表，拿物品对象
base = mem.module_base(pid, "D2CLIENT.dll")
p = mem.read_dword(pid, h, base + 0x11B800)
bag = mem.read_dword(pid, h, p + 0x700)
print(f"bag = {bag:#x}")
for slot in range(40):
    se = bag + slot * 40
    pos = mem.read_dword(pid, h, se)
    if not pos:
        continue
    codeid = mem.read_dword(pid, h, se + 0x04)
    obj = mem.read_dword(pid, h, se + 0x14)
    if codeid == 529:  # tsc
        print(f"slot{slot}: pos={pos} codeid={codeid} obj={obj:#x}")
        # UnitAny 假设 = obj - 0x14
        ua = obj - 0x14
        print(f"  UnitAny假设 {ua:#x}:")
        for off, name in [(0x0, "dwUnitType"), (0x4, "dwTxtFileNo"), (0x8, "pMemPool"),
                          (0xC, "dwUnitId"), (0x10, "dwMode"), (0x14, "pItemData"),
                          (0x18, "dwAct"), (0x1C, "pDrlgAct"), (0x2C, "pItemPath"),
                          (0x5C, "pStatList"), (0x60, "pInventory")]:
            v = mem.read_dword(pid, h, ua + off)
            print(f"    +{off:#04x} {name} = {v:#x} ({v})")
        # ItemData 关键字段
        print(f"  ItemData {obj:#x}:")
        for off, name in [(0x0, "dwQuality"), (0x28, "dwFileIndex"), (0x2C, "dwItemLevel")]:
            v = mem.read_dword(pid, h, obj + off)
            print(f"    +{off:#04x} {name} = {v:#x} ({v})")
        break

ctypes.windll.kernel32.CloseHandle(h)
