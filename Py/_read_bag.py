# -*- coding: utf-8 -*-
"""读背包 40 槽格子表项 +0x04 id"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行")
    sys.exit()
h = mem.open_process_readonly(pid)

base = mem.resolve_base(pid, "D2CLIENT.dll+0x11B800")
p = mem.read_ptr(pid, h, base)
bag = p + 0x700
print(f"P={p:#x} bag={bag:#x}")

# 读物品码表 name 映射（code -> id）
obj = mem.read_ptr(pid, h, mem.resolve_base(pid, "D2Common.dll+0x9FF6C"))
count = mem.read_dword(pid, h, obj)
table = mem.read_ptr(pid, h, obj + 0x8)
id2code = {}
for i in range(count):
    raw = mem.read(pid, h, table + i * 8, 8)
    if len(raw) != 8:
        break
    c4 = raw[:4].decode("latin-1").strip()
    cid = int.from_bytes(raw[4:8], "little")
    id2code[cid] = c4

for slot in range(40):
    cellp = mem.read_ptr(pid, h, bag + slot * 4)
    if not cellp:
        continue
    pos = mem.read_dword(pid, h, cellp)
    iid = mem.read_dword(pid, h, cellp + 0x04)
    handle = mem.read_dword(pid, h, cellp + 0x0C)
    code = id2code.get(iid, f"?{iid}")
    if iid:
        print(f"槽{slot}: cell={cellp:#x} 位置码={pos} id={iid} 句柄={handle} code={code}")
ctypes.windll.kernel32.CloseHandle(h)
