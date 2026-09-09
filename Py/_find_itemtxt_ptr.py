# -*- coding: utf-8 -*-
"""读物品码表 obj(0x48A2E84) 附近指针，找 ItemTxt 表（行+0x40=code, +0x11E=nType, +0x00=UTF16名）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

OBJ = 0x48A2E84
print("== obj 附近 dword ==")
raw = mem.read(pid, h, OBJ - 0x100, 0x300)
for off in range(0, 0x300, 4):
    v = int.from_bytes(raw[off:off+4], "little")
    if v > 0x10000:  # 像指针
        print(f"  obj{'-' if off<0x100 else '+'}{abs(off-0x100):#x}: {v:#x}")

print("\n== 验证候选指针指向的区域是否 ItemTxt 表 ==")
cands = []
raw = mem.read(pid, h, OBJ - 0x100, 0x300)
for off in range(0, 0x300, 4):
    v = int.from_bytes(raw[off:off+4], "little")
    if 0x10000 < v < 0x7FFFFFFF:
        cands.append(v)

checked = set()
for base in cands:
    if base in checked:
        continue
    checked.add(base)
    # 检查 base 处前几行：+0x40 = ANSI code（4 可打印），+0x11E = type
    codes = []
    types = []
    ok = 0
    for r in range(4):
        code = mem.read(pid, h, base + r * 0x12C + 0x40, 4)
        ntype = mem.read(pid, h, base + r * 0x12C + 0x11E, 1)
        if code and all(32 <= b < 127 for b in code):
            ok += 1
        codes.append(code)
        types.append(ntype[0] if ntype else -1)
    if ok >= 3:
        print(f"  {base:#x}: codes={codes} types={types}  <- 疑似ItemTxt表")

ctypes.windll.kernel32.CloseHandle(h)
