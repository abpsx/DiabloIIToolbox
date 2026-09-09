# -*- coding: utf-8 -*-
"""精确反推 ItemTxt 表基（命中点 0x128E1A9C 行首 - 529 行）并验证行号映射"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

ROW = 0x1A8
HIT = 0x128E1A9C        # "tsc " 命中
ROW_TS = 529            # 假设 tsc 行号（=dwTxtFileNo）
rs = HIT - 0x80         # 行首
TABLE = rs - ROW_TS * ROW
print(f"行首 {rs:#x}, 表基 {TABLE:#x}")

# 读行 0,1,2 与 527-533、679 验证
def ri(no):
    row = TABLE + no * ROW
    code = mem.read(pid, h, row + 0x80, 20)
    ntype = mem.read(pid, h, row + 0x11E, 1)
    loc = mem.read(pid, h, row + 0xF4, 2)
    return (code[:4] if code else b""), (ntype[0] if ntype else -1), (int.from_bytes(loc, "little") if loc else -1)

for no in list(range(0, 8)) + [63, 529, 530, 587, 679, 713]:
    c, t, l = ri(no)
    print(f"  行{no}: code={c!r} nType={t} locale={l}")

# 全表扫 0-720 找合法 code 行数
valid = []
for no in range(0, 721):
    row = TABLE + no * ROW
    code = mem.read(pid, h, row + 0x80, 4)
    if code and all(32 <= b < 127 for b in code):
        valid.append((no, code.decode("latin-1")))
print(f"\n合法 code 行: {len(valid)}")
print("前 30:", valid[:30])
print("后 30:", valid[-30:])

ctypes.windll.kernel32.CloseHandle(h)
