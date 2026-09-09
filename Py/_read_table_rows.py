# -*- coding: utf-8 -*-
"""读 ItemTxt 表（基址 0x128AADF4，行宽 0x1A8）行 0-720，验证 tsc/679"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

ROW = 0x1A8
TABLE = 0x128AAE34

def rowinfo(rowno):
    row = TABLE + rowno * ROW
    code = mem.read(pid, h, row + 0x80, 20)
    ntype = mem.read(pid, h, row + 0x11E, 1)
    loc = mem.read(pid, h, row + 0xF4, 2)
    return (code[:4] if code else b""), (ntype[0] if ntype else -1), (int.from_bytes(loc, "little") if loc else -1)

for rowno in (0, 1, 2, 3, 4, 5, 63, 529, 530, 587, 647, 648, 649, 659, 670, 679, 700, 713, 715, 716):
    c, t, l = rowinfo(rowno)
    print(f"行{rowno}: code={c!r} nType={t} locale={l}")

# 扫 640-716 行找 portal1/pr 相关
print("\n== 扫 670-716 ==")
for rowno in range(670, 717):
    c, t, l = rowinfo(rowno)
    cs = c.decode("latin-1", errors="replace").strip()
    if cs:
        print(f"  行{rowno}: code={cs!r} nType={t} locale={l}")

ctypes.windll.kernel32.CloseHandle(h)
