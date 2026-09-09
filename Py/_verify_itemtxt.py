# -*- coding: utf-8 -*-
"""验证 tsc 命中点是否为 ItemTxt 表（行首=hit-0x40, +0x11E=nType, +0x00=UTF16名）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

hits = [0x28fb407, 0x2ac8ec8, 0x2c3d614, 0x3481c68, 0x4922808,
        0x4953088, 0x4953354, 0x49534d4, 0x127d6cf4, 0x128c49f0,
        0x128e1a9c, 0x1319c2b0, 0x1319c550, 0x13245934, 0x1756de20]

ROW_CANDS = [0x12C, 0x130, 0x140, 0x150, 0x1A8, 0x200]

for hit in hits:
    rs = hit - 0x40
    code = mem.read(pid, h, rs + 0x40, 4)
    ntype = mem.read(pid, h, rs + 0x11E, 1)
    name = mem.read(pid, h, rs, 32)  # UTF-16 前 16 字符
    # 解码 UTF-16 可打印部分
    nm = ""
    try:
        nm = name.decode("utf-16-le", errors="replace")
        nm = "".join(c if 32 <= ord(c) < 127 or ord(c) > 0x2FFF else "." for c in nm)
    except Exception:
        pass
    # 行首模行宽
    mods = {hex(w): rs % w for w in ROW_CANDS}
    print(f"{hit:#x}: 行首={rs:#x} code@+0x40={code!r} nType@+0x11E={ntype[0] if ntype else -1} name16={nm!r}")
    print(f"       mod={mods}")

ctypes.windll.kernel32.CloseHandle(h)
