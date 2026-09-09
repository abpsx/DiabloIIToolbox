# -*- coding: utf-8 -*-
"""完整 dump 两张 UTF-16 tbl 字符串数组 → tbl_names.json"""
import json
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed"); sys.exit(1)


def u16str(addr, maxlen=0x400):
    raw = m.read(pid, h, addr, maxlen)
    if not raw:
        return None
    s = ""
    for i in range(0, len(raw) - 2, 2):
        c = int.from_bytes(raw[i:i + 2], "little")
        if c == 0:
            break
        s += chr(c) if 0x20 <= c < 0x7FFF or 0x4E00 <= c <= 0x9FFF else f"[{c:04X}]"
    return s


out = {}
for arr, tag in ((0x489ED00, "tbl_a"), (0x1287E300, "tbl_b")):
    entries = []
    for idx in range(0, 512):
        ptr = m.read_dword(pid, h, arr + idx * 4)
        if not (0x100000 <= ptr < 0x7FF00000):
            break
        s = u16str(ptr)
        if s is None:
            break
        entries.append({"idx": idx, "ptr": hex(ptr), "text": s})
    out[tag] = entries
    print(f"{tag}: {len(entries)} 条")

m.kernel32.CloseHandle(h)
path = r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_tbl_names.json"
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", path)
