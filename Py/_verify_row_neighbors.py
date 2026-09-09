# -*- coding: utf-8 -*-
"""验证 0x128E1A9C / 0x4922808 是否为 ItemTxt 行（行宽 0x1A8）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

ROW = 0x1A8
for hit in (0x128e1a9c, 0x4922808):
    rs = hit - 0x80
    print(f"== 行首 {rs:#x} ==")
    # 检查前后 6 行
    for k in range(-6, 7):
        row = rs + k * ROW
        code = mem.read(pid, h, row + 0x80, 20)
        ntype = mem.read(pid, h, row + 0x12A, 1)
        loc = mem.read(pid, h, row + 0xF4, 2)
        c4 = code[:4] if code else b""
        printable = all(32 <= b < 127 for b in c4) and c4[:1].isalpha()
        if printable or k == 0:
            print(f"  行{k:+d} @{row:#x}: code={c4!r} nType={ntype[0] if ntype else -1} locale={int.from_bytes(loc,'little') if loc else -1}")
    print()

ctypes.windll.kernel32.CloseHandle(h)
