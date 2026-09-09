# -*- coding: utf-8 -*-
"""读背包40格物品对象，验证 dwTxtFileNo(UnitAny+0x04) 与码表id(格子表项+0x04)"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

P = mem.read_dword(pid, h, mem.resolve_base(pid, "D2CLIENT.dll+0x11B800"))
print(f"人物 P=0x{P:X}")
bag = P + 0x700
print(f"背包指针表=0x{bag:X}")

# 读码表（code->id 映射）
TABLE = 0x1265D434
CODES = {}
for i in range(716):
    raw = mem.read(pid, h, TABLE + i * 8, 8)
    if len(raw) == 8:
        c = raw[:4].decode("latin-1").strip()
        cid = int.from_bytes(raw[4:8], "little")
        CODES[cid] = c

print("slot  | 格子表项  | +0x04(码表id) | code | +0x0C句柄  | +0x14对象    | obj+0x00 | obj+0x04(txtNo) | obj+0x14(ItemData)")
for s in range(40):
    entry = mem.read_dword(pid, h, bag + s * 4)
    if not entry:
        continue
    e04 = mem.read_dword(pid, h, entry + 0x04)
    e0c = mem.read_dword(pid, h, entry + 0x0C)
    e14 = mem.read_dword(pid, h, entry + 0x14)
    code = CODES.get(e04, "?")
    if not e14:
        print(f"{s:4d} | {entry:#x} | {e04} | {code} | {e0c:#x} | 0 | - | - | -")
        continue
    o00 = mem.read_dword(pid, h, e14 + 0x00)
    o04 = mem.read_dword(pid, h, e14 + 0x04)
    o14 = mem.read_dword(pid, h, e14 + 0x14)
    print(f"{s:4d} | {entry:#x} | {e04} | {code} | {e0c:#x} | {e14:#x} | {o00} | {o04} | {o14:#x}")

ctypes.windll.kernel32.CloseHandle(h)
