# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\local\LNG\kor\ExpansionString.tbl", "rb").read()
for off in (0x31980, 0x31995):
    seg = raw[off : off + 64]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in seg)
    print(f"ExpansionString @{off:#x}: {seg.hex(' ')}")
    print(f"  {asc}")

raw2 = open(r"G:\game\diablo 2\data\local\LNG\kor\String.tbl", "rb").read()
seg = raw2[0x55360:0x553C0]
asc = "".join(chr(b) if 32 <= b < 127 else "." for b in seg)
print(f"String.tbl @0x55360: {seg.hex(' ')}")
print(f"  {asc}")
