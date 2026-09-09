# -*- coding: utf-8 -*-
"""从 tsc 行往前扫，找行 0（表基址），再读行 679/713"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

ROW = 0x1A8
TSC_RS = 0x128E1A1C  # tsc 行首

# 往前扫 2000 行
found = []
for k in range(0, 1500):
    row = TSC_RS - k * ROW
    code = mem.read(pid, h, row + 0x80, 4)
    if len(code) != 4 or not all(32 <= b < 127 for b in code):
        # 非法——再往前确认是否持续非法
        nxt = mem.read(pid, h, row - ROW + 0x80, 4)
        if len(nxt) != 4 or not all(32 <= b < 127 for b in nxt):
            # 表基 = 这一行（行 k）
            print(f"表基(行{k}) = {row:#x}")
            found = k
            break
    if k % 100 == 0:
        pass

# 表基 = TSC_RS - found*ROW
table = TSC_RS - found * ROW
print(f"表基址 = {table:#x}, tsc 行号 = {found}")
for rowno in (0, 1, found - 5, found, found + 150, 679, 713, 900):
    if rowno < 0:
        continue
    row = table + rowno * ROW
    code = mem.read(pid, h, row + 0x80, 20)
    ntype = mem.read(pid, h, row + 0x12A, 1)
    loc = mem.read(pid, h, row + 0xF4, 2)
    c4 = code[:4] if code else b""
    print(f"  行{rowno}: code={c4!r} nType={ntype[0] if ntype else -1} locale={int.from_bytes(loc,'little') if loc else -1}")

ctypes.windll.kernel32.CloseHandle(h)
