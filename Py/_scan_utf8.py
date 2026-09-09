# -*- coding: utf-8 -*-
"""扫描内存 UTF-8 全称表扩展区，找未命中 code 的 key"""
import json
import sys

sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed")
    sys.exit(1)

START = 0x12A3A73E
END = 0x12A4C000  # 扩展扫描范围


def read_region(a, size):
    """0x10 粒度跳过不可读段"""
    out = bytearray()
    pos = 0
    while pos < size:
        chunk = m.read(pid, h, a + pos, 0x10)
        if chunk:
            out += chunk
            pos += 0x10
        else:
            out += b"\x00" * 0x10
            pos += 0x10
    return bytes(out)


blob = read_region(START, END - START)
print("读取", len(blob), "字节")

# 解析 key\0value\0 对（UTF-8，key = 4 字节 code 形式）
codes = ["hpo", "hpf", "mpo", "mpf", "bpl", "rpl", "bps", "elc", "elx",
         "pr1", "pr2", "pr3", "cm11", "cm12", "cm16", "cap", "qey", "qhr", "qbr"]
found = {}
pos = 0
n = len(blob)
while pos < n:
    e = blob.find(b"\0", pos)
    if e < 0:
        break
    k = blob[pos:e]
    pos = e + 1
    if len(k) == 4:
        ks = k.decode("latin-1")
        if ks.strip() in codes:
            e2 = blob.find(b"\0", pos)
            if e2 < 0:
                break
            v = blob[pos:e2]
            found[ks] = v.decode("utf-8", errors="replace")
            pos = e2 + 1
            continue
    # 快速前进：跳过过长
    pos = pos if e - pos < 200 else pos
m.kernel32.CloseHandle(h)

for c in codes:
    print(f"  {c} -> {found.get(c, '未找到')!r}")

json.dump({k: v for k, v in found.items() if v},
          open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_utf8_ext.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved")
