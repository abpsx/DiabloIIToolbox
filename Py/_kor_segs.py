# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\local\LNG\kor\String.tbl", "rb").read()


def is_text_byte(b):
    return (0x20 <= b < 0x7F) or (0xC0 <= b < 0xF5) or b == 0x00


# 找 >=100 字节的连续文本段
segments = []
cur = None
for i in range(len(raw)):
    if is_text_byte(raw[i]):
        if cur is None:
            cur = i
    else:
        if cur is not None:
            if i - cur >= 100:
                segments.append((cur, i))
            cur = None
if cur is not None and len(raw) - cur >= 100:
    segments.append((cur, len(raw)))

print("大文本段:")
for s, e in segments[:20]:
    sample = raw[s : s + 60]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in sample)
    print(f"  {s:#08x} ~ {e:#08x} ({e-s} 字节)  {asc[:55]}")

if segments:
    s0 = segments[0][0]
    # 从 s0 分字段
    print("\n起点字段:")
    pos = s0
    for k in range(6):
        e = raw.find(b"\0", pos)
        f = raw[pos:e].decode("utf-8", errors="replace")[:40]
        print(f"  [{k}] @{pos:#x}: {f!r}")
        pos = e + 1
