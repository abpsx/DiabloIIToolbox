# -*- coding: utf-8 -*-
import re

raw = open(r"G:\game\diablo 2\data\global\excel\misc.bin", "rb").read()
off = 72636
seg = raw[off - 64 : off + 64]
print("pr1 行上下文 hex:")
for i in range(0, len(seg), 16):
    chunk = seg[i : i + 16]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"{off-64+i:#x}: {chunk.hex(' ')}  {asc}")

print()
strs = re.findall(rb"[ -~]{4,}", raw)
print("ASCII 串数:", len(strs))
for s in strs[:60]:
    print("  ", s.decode(errors="replace"))
