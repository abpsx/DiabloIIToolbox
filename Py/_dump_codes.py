# -*- coding: utf-8 -*-
"""dump 物品码表全部条目：索引 + code + id"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

obj = mem.read_ptr(pid, h, mem.resolve_base(pid, "D2Common.dll+0x9FF6C"))
count = mem.read_dword(pid, h, obj)
table = mem.read_ptr(pid, h, obj + 0x8)
print(f"count={count} table={table:#x}")

rows = []
for i in range(count):
    raw = mem.read(pid, h, table + i * 8, 8)
    if len(raw) != 8:
        break
    c4 = raw[:4].decode("latin-1").strip()
    cid = int.from_bytes(raw[4:8], "little")
    rows.append((i, c4, cid))

# 打印索引 670-720 与 id 670-720 附近
print("=== 索引 670~715 (idx, code, id) ===")
for i, c4, cid in rows:
    if 670 <= i <= 715:
        mark = " <<<" if cid in (679, 713) or i in (679, 713) or 'key' in c4 or 'portal' in c4 or 'pr' in c4[:2] else ""
        print(f"  [{i}] {c4!r} id={cid}{mark}")

print("=== 含 key/portal 的 code ===")
for i, c4, cid in rows:
    if 'key' in c4 or 'portal' in c4 or 'k0' in c4 or 'pk' in c4:
        print(f"  [{i}] {c4!r} id={cid}")
ctypes.windll.kernel32.CloseHandle(h)
