# -*- coding: utf-8 -*-
"""验证 ItemTxt 表基（0x127A004C vs 0x127A008C），读行 0/529/679"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

ROW = 0x1A8
for TABLE in (0x127A004C, 0x127A008C):
    print(f"== 表基 {TABLE:#x} ==")
    for no in (0, 1, 2, 3, 529, 530, 679, 680, 713):
        row = TABLE + no * ROW
        flip = mem.read(pid, h, row, 32)
        code = mem.read(pid, h, row + 0x80, 20)
        loc = mem.read(pid, h, row + 0xF4, 2)
        ntype = mem.read(pid, h, row + 0x11E, 1)
        print(f"  行{no} @{row:#x}: flip={flip[:16]!r} code={code[:4]!r} locale={int.from_bytes(loc,'little') if loc else -1} nType={ntype[0] if ntype else -1}")
    print()

ctypes.windll.kernel32.CloseHandle(h)
