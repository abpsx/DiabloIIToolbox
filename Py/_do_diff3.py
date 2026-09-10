# -*- coding: utf-8 -*-
"""相邻翻页 diff：找 |new-old|==1 的变化点（页数候选，byte/word/dword 粒度）"""
import sys, ctypes, json
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

old = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_diff_snap.json", encoding="utf-8"))

byte_c = []   # (addr, old, new) |new-old|==1
word_c = []
dword_c = []
for k, hexs in old.items():
    lo = int(k)
    ob = bytes.fromhex(hexs)
    nb = mem.read(pid, h, lo, len(ob))
    if not nb or len(nb) != len(ob):
        continue
    n = len(ob)
    for i in range(n):
        if ob[i] != nb[i] and abs(nb[i] - ob[i]) == 1:
            byte_c.append((lo + i, ob[i], nb[i]))
    for i in range(n - 1):
        o = int.from_bytes(ob[i:i+2], "little")
        v = int.from_bytes(nb[i:i+2], "little")
        if o != v and 1 <= o <= 200 and 1 <= v <= 200 and abs(v - o) == 1:
            word_c.append((lo + i, o, v))
    for i in range(n - 3):
        o = int.from_bytes(ob[i:i+4], "little")
        v = int.from_bytes(nb[i:i+4], "little")
        if o != v and 1 <= o <= 200 and 1 <= v <= 200 and abs(v - o) == 1:
            dword_c.append((lo + i, o, v))

print(f"byte ±1: {len(byte_c)}")
for a, o, v in byte_c[:25]:
    print(f"  0x{a:X}: {o} -> {v}")
print(f"word ±1: {len(word_c)}")
for a, o, v in word_c[:25]:
    print(f"  0x{a:X}: {o} -> {v}")
print(f"dword ±1: {len(dword_c)}")
for a, o, v in dword_c[:25]:
    print(f"  0x{a:X}: {o} -> {v}")
ctypes.windll.kernel32.CloseHandle(h)
