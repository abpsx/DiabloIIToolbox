# -*- coding: utf-8 -*-
"""读内存物品码表：查指定 code 的 id（现取 PID）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
print("PID", pid)
if not pid:
    sys.exit()
h = mem.open_process_readonly(pid)

# 物品码表对象链：D2Common.dll+0x9FF6C -> +0x0 计数 -> +0x8 表
base = mem.resolve_base(pid, "D2Common.dll+0x9FF6C")
obj = mem.read_ptr(pid, h, base)
count = mem.read_dword(pid, h, obj)
table = mem.read_ptr(pid, h, obj + 0x8)
print(f"obj={obj:#x} count={count} table={table:#x}")

want = {"portal1", "portal56", "pr1", "pr56", "tsc", "elc"}


def code_str(b4):
    s = b4.decode("latin-1")
    return s.strip()


found = {}
for i in range(count):
    ent = table + i * 8
    raw = mem.read(pid, h, ent, 8)
    if len(raw) != 8:
        break
    c4 = code_str(raw[:4])
    cid = int.from_bytes(raw[4:8], "little")
    if c4 in want:
        found[c4] = cid
        print(f"  {c4!r} -> id={cid} ({cid:#x})")

ctypes.windll.kernel32.CloseHandle(h)
