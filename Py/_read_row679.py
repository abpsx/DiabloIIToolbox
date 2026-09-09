# -*- coding: utf-8 -*-
"""反推 ItemTxt 表基址（tsc 行号=529），读行 679 验证白羊宫钥匙"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

ROW = 0x1A8
TSC_ROW = 529  # 假设 = 码表 id

for base_hit in (0x128e1a9c, 0x4922808):
    rs = base_hit - 0x80
    table = rs - TSC_ROW * ROW
    print(f"== 假设表基 = {rs:#x} - {TSC_ROW}x0x1A8 = {table:#x} ==")
    # 行 0
    c0 = mem.read(pid, h, table + 0x80, 20)
    n0 = mem.read(pid, h, table + 0x12A, 1)
    l0 = mem.read(pid, h, table + 0xF4, 2)
    print(f"  行0: code={c0[:4]!r} nType={n0[0] if n0 else -1} locale={int.from_bytes(l0,'little') if l0 else -1}")
    # 行 1（验证连续性）
    c1 = mem.read(pid, h, table + ROW + 0x80, 20)
    print(f"  行1: code={c1[:4]!r}")
    # 行 529（tsc）
    c529 = mem.read(pid, h, table + 529 * ROW + 0x80, 20)
    print(f"  行529: code={c529[:4]!r}")
    # 行 679（白羊宫钥匙？）
    c679 = mem.read(pid, h, table + 679 * ROW + 0x80, 20)
    n679 = mem.read(pid, h, table + 679 * ROW + 0x12A, 1)
    l679 = mem.read(pid, h, table + 679 * ROW + 0xF4, 2)
    print(f"  行679: code={c679[:4]!r} nType={n679[0] if n679 else -1} locale={int.from_bytes(l679,'little') if l679 else -1}")
    # 行 713
    c713 = mem.read(pid, h, table + 713 * ROW + 0x80, 20)
    n713 = mem.read(pid, h, table + 713 * ROW + 0x12A, 1)
    l713 = mem.read(pid, h, table + 713 * ROW + 0xF4, 2)
    print(f"  行713: code={c713[:4]!r} nType={n713[0] if n713 else -1} locale={int.from_bytes(l713,'little') if l713 else -1}")
    print()

ctypes.windll.kernel32.CloseHandle(h)
