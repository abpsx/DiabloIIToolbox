# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\global\excel\misc.bin", "rb").read()
ROW = 0x1A8
row = raw[0xFBC0 : 0xFBC0 + ROW]
print("ibg 行（行首 0xFBC0，0x1A8 字节）全部 4 字节列：")
for i in range(0, ROW, 4):
    b = row[i : i + 4]
    d = int.from_bytes(b, "little")
    s = "".join(chr(x) if 32 <= x < 127 else "." for x in b)
    mark = ""
    if b.strip() and s.strip():
        mark = "  <<< 字符串"
    print(f"  +{i:03x}: {b.hex(' ')}  d={d:<10} {s!r}{mark}")
