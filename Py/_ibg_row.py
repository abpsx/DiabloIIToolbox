# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\global\excel\misc.bin", "rb").read()
off = 0xFC44
row = raw[off : off + 0x1A8]
print(f"ibg 行 @{off:#x} ({0x1A8} 字节)")
for i in range(0, len(row), 16):
    chunk = row[i : i + 16]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"  +{i:03x}: {chunk.hex(' ')}  {asc}")

# 同法读 elc 行对比
print("\nelc 行 @0xFA9C")
row = raw[0xFA9C : 0xFA9C + 0x1A8]
for i in range(0, len(row), 16):
    chunk = row[i : i + 16]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"  +{i:03x}: {chunk.hex(' ')}  {asc}")
