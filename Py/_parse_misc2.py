# -*- coding: utf-8 -*-
import struct

raw = open(r"G:\game\diablo 2\data\global\excel\misc.bin", "rb").read()

# 头部：前 4 字节 = 0xD0=208。列名从 4 开始，\0 分隔
pos = 4
cols = []
while pos < 0x4000:
    end = raw.find(b"\0", pos)
    if end < 0 or end - pos > 48:
        break
    seg = raw[pos:end]
    if not all(32 <= b < 127 for b in seg):
        break
    cols.append(seg.decode(errors="replace"))
    pos = end + 1
print("列数:", len(cols), "列名区结束:", hex(pos))
for i, c in enumerate(cols):
    print(f"  [{i}] {c}")

# 找 code / name 列
code_col = cols.index("code") if "code" in cols else -1
name_col = cols.index("name") if "name" in cols else -1
print("code列:", code_col, "name列:", name_col)

# 数据区起点
data_start = pos
# 行宽
print("数据区起点:", hex(data_start))
