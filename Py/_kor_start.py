# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\local\LNG\kor\String.tbl", "rb").read()

# 找数据区起点：扫描，找连续的可打印/UTF-8 文本区起点
# 先看前 0x300
for i in range(0, 0x300, 32):
    chunk = raw[i : i + 32]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"{i:#06x}: {chunk.hex(' ')}  {asc}")

# 找 qf1 前一个 \0
qi = raw.find(b"\0qf1\0")
print("\n\\0qf1\\0 at:", hex(qi))
# 数据区可能起点：找第一个字节开始就是文本的地方
# 方法：从头扫描，找到长度>=8 的"可打印+UTF8"窗口
def utf8_ok(b):
    return (b >= 0x20 and b < 0x7F) or (b >= 0xC0 and b < 0xF5) or b in (0x00,)

start = None
for i in range(len(raw) - 8):
    if all(utf8_ok(raw[i + j]) for j in range(8)):
        start = i
        break
print("第一个 UTF-8 文本窗口 @", hex(start), raw[start : start + 40])
