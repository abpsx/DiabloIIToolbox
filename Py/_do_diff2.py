# -*- coding: utf-8 -*-
"""按 byte/word 粒度 diff 找 10→11 页数候选"""
import sys, ctypes, json
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

old = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_diff_snap.json", encoding="utf-8"))

byte_cand = []   # 10->11
word_cand = []   # 10->11
dword_cand = []
for k, hexs in old.items():
    lo = int(k)
    ob = bytes.fromhex(hexs)
    nb = mem.read(pid, h, lo, len(ob))
    if not nb or len(nb) != len(ob):
        continue
    n = len(ob)
    for i in range(n - 1):
        if ob[i] != nb[i]:
            if ob[i] == 10 and nb[i] == 11:
                byte_cand.append(lo + i)
        if i + 1 < n:
            o = int.from_bytes(ob[i:i+2], "little")
            v = int.from_bytes(nb[i:i+2], "little")
            if o == 10 and v == 11:
                word_cand.append(lo + i)

print(f"byte 10→11: {len(byte_cand)} 处")
for a in byte_cand[:20]:
    print(f"  0x{a:X}")
print(f"word 10→11: {len(word_cand)} 处")
for a in word_cand[:20]:
    print(f"  0x{a:X}")

# 也看 0x7A3552E4 / 0x7A3556F8 附近（Anhei2Map 变化区）现状
print("\nAnhei2Map 变化点:")
for a in [0x7A3552E4, 0x7A3556F8]:
    raw = mem.read(pid, h, a, 8)
    print(f"  0x{a:X}: {raw.hex(' ')}")
ctypes.windll.kernel32.CloseHandle(h)
