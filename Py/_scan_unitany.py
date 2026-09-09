# -*- coding: utf-8 -*-
"""扫 ItemData 前 0x200 字节，找 UnitAny 起始（dwUnitType=2 + dwTxtFileNo 合理）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

base = mem.module_base(pid, "D2CLIENT.dll")
p = mem.read_dword(pid, h, base + 0x11B800)
bag = mem.read_dword(pid, h, p + 0x700)

objs = []
for slot in range(40):
    se = bag + slot * 40
    pos = mem.read_dword(pid, h, se)
    if not pos:
        continue
    codeid = mem.read_dword(pid, h, se + 0x04)
    obj = mem.read_dword(pid, h, se + 0x14)
    objs.append((slot, pos, codeid, obj))
    print(f"slot{slot}: pos={pos} codeid={codeid} obj={obj:#x}")

# 对每个对象，往前扫找 UnitAny
for slot, pos, codeid, obj in objs:
    print(f"== slot{slot} codeid={codeid} obj={obj:#x} ==")
    for delta in range(0x00, 0x140, 0x4):
        cand = obj - delta
        ut = mem.read_dword(pid, h, cand)
        tf = mem.read_dword(pid, h, cand + 0x04)
        if ut == 2 and 0 < tf < 2000:
            print(f"  候选 UnitAny @ {cand:#x} (obj-{delta:#x}): dwUnitType={ut} dwTxtFileNo={tf}")
            uid = mem.read_dword(pid, h, cand + 0x0C)
            mode = mem.read_dword(pid, h, cand + 0x10)
            pd = mem.read_dword(pid, h, cand + 0x14)
            print(f"    dwUnitId={uid} dwMode={mode} pItemData={pd:#x} (pd==obj? {pd==obj})")
            break
    else:
        print("  未找到 UnitAny 起始（dwUnitType=2）")

ctypes.windll.kernel32.CloseHandle(h)
