# -*- coding: utf-8 -*-
"""翻页 diff：对比快照，找变化 dword（重点 10→11 的页数变量）"""
import sys, ctypes, json, re
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

old = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_diff_snap.json", encoding="utf-8"))

changed = []  # (addr, old_int, new_int)
for k, hexs in old.items():
    lo = int(k)
    ob = bytes.fromhex(hexs)
    nb = mem.read(pid, h, lo, len(ob))
    if not nb or len(nb) != len(ob):
        continue
    # 按 dword 对比
    n = len(ob) // 4
    for i in range(n):
        o = int.from_bytes(ob[i*4:i*4+4], "little")
        v = int.from_bytes(nb[i*4:i*4+4], "little")
        if o != v:
            changed.append((lo + i*4, o, v))

print(f"变化 dword 共 {len(changed)} 处")
# 重点：值 10→11（页数候选）或 11→10
page_cand = [c for c in changed if c[1] == 10 and c[2] == 11]
print(f"\n10→11 候选 {len(page_cand)} 处:")
for a, o, v in page_cand[:30]:
    print(f"  0x{a:X}: {o} -> {v}")

if not page_cand:
    print("\n全部变化（前 40）:")
    for a, o, v in changed[:40]:
        print(f"  0x{a:X}: {o} -> {v}")
    # 统计变化值范围
    from collections import Counter
    c = Counter(v for _, _, v in changed)
    print("\n新值分布:", c.most_common(15))
ctypes.windll.kernel32.CloseHandle(h)
