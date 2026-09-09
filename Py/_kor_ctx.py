# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\local\LNG\kor\String.tbl", "rb").read()
off = 0x425FD
seg = raw[off - 64 : off + 96]
print(f"qf1@{off:#x} 上下文:")
for i in range(0, len(seg), 16):
    chunk = seg[i : i + 16]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"  {off-64+i:#08x}: {chunk.hex(' ')}  {asc}")

# 看文件里 key 区大体位置：搜连续 \0 边界。找从 0x40000 起可打印区
print("\n--- 0x40000 附近 ---")
seg2 = raw[0x40000 : 0x40100]
for i in range(0, len(seg2), 16):
    chunk = seg2[i : i + 16]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"  {0x40000+i:#08x}: {chunk.hex(' ')}  {asc}")
