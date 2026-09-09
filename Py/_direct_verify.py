# -*- coding: utf-8 -*-
"""直接读内存码表 obj 的 529/530 条目 + ItemTxt 行 529/530 完整行头"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

# 码表 obj
base = mem.module_base(pid, "D2Common.dll")
obj = mem.read_dword(pid, h, base + 0x9FF6C)
cnt = mem.read_dword(pid, h, obj)
tbl = mem.read_dword(pid, h, obj + 0x8)
print(f"码表 obj={obj:#x} count={cnt} table={tbl:#x}")

# 码表条目 8B: code(4) + id(4)
for i in (528, 529, 530, 531, 92, 587):
    ent = tbl + i * 8
    code = mem.read(pid, h, ent, 4)
    idd = mem.read_dword(pid, h, ent + 4)
    print(f"  码表[{i}]: code={code!r} id={idd}")

print()
# ItemTxt 行 529/530 完整行头
ROW = 0x1A8
for no in (529, 530):
    row = 0x128AADF4 + no * ROW
    head = mem.read(pid, h, row, 0x98)
    print(f"ItemTxt 行{no} @{row:#x} 头0x98:")
    # 分块打印
    for off in (0, 0x20, 0x40, 0x60, 0x80):
        seg = head[off:off+0x18]
        print(f"    +{off:#04x}: {seg!r}")
    # 关键字段
    loc = mem.read(pid, h, row + 0xF4, 2)
    ntype = mem.read(pid, h, row + 0x11E, 1)
    print(f"    locale={int.from_bytes(loc,'little')} nType={ntype[0] if ntype else -1}")

ctypes.windll.kernel32.CloseHandle(h)
