# -*- coding: utf-8 -*-
"""1.13c ItemTxt 表验证：行宽0x1A8, code@+0x80, nType@+0x12A, wLocaleTxtNo@+0xF4"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

ROW = 0x1A8
hits = [0x28fb407, 0x2ac8ec8, 0x2c3d614, 0x3481c68, 0x4922808,
        0x4953088, 0x4953354, 0x49534d4, 0x127d6cf4, 0x128c49f0,
        0x128e1a9c, 0x1319c2b0, 0x1319c550, 0x13245934, 0x1756de20]

print("命中点 | 行首(hit-0x80) | 模0x1A8 | code@+0x80 | nType@+0x12A | locale@+0xF4")
for hit in hits:
    rs = hit - 0x80
    mod = rs % ROW
    code = mem.read(pid, h, rs + 0x80, 20)  # szCode[20]
    ntype = mem.read(pid, h, rs + 0x12A, 1)
    loc = mem.read(pid, h, rs + 0xF4, 2)
    c4 = code[:4] if code else b""
    print(f"{hit:#x} | {rs:#x} | {mod:#x} | {c4!r} | {ntype[0] if ntype else -1} | {int.from_bytes(loc,'little') if loc else -1}")

ctypes.windll.kernel32.CloseHandle(h)
