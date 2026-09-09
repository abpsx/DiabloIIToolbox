# -*- coding: utf-8 -*-
"""检查 tsc 候选是否为行表（行宽 0x1A8，code 列 +0x84，行首对齐）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

cands = [0x127d6cf4, 0x128c49f0, 0x128e1a9c, 0x1319c2b0, 0x1319c550,
         0x13245934, 0x1756de20, 0x4922808, 0x4953088]

ROW = 0x1A8
OFF_CODE = 0x84

for c in cands:
    rs = c - OFF_CODE
    if rs % ROW != 0:
        # 尝试附近行首（前移 0x84 到对齐点）
        rs = (rs // ROW) * ROW
        if not (0 <= rs < 0x7FFFFFFF):
            print(f"{c:#x}: 无法对齐"); continue
    raw = mem.read(pid, h, rs + OFF_CODE, 4)
    if raw != b"tsc ":
        # 检查 rs 处本身
        raw2 = mem.read(pid, h, rs, 4)
        print(f"{c:#x}: rs={rs:#x}(+0x84={raw!r} 行首={raw2!r})"); continue
    # 对齐成功：验证连续行
    print(f"{c:#x}: 行首={rs:#x} 行号={rs//ROW} tsc确认")
    # 读行 0 的 code
    base = (rs // ROW) * ROW
    code0 = mem.read(pid, h, base + OFF_CODE, 4)
    print(f"   表基址(行0)={base:#x} code0={code0!r}")
    # 读行 679 的 code
    c679 = mem.read(pid, h, base + 679 * ROW + OFF_CODE, 8)
    print(f"   行679 code={c679[:4]!r} +0x04={c679[4:].hex()}")

ctypes.windll.kernel32.CloseHandle(h)
