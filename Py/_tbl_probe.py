# -*- coding: utf-8 -*-
"""解析 D2 .tbl（TS 格式）文本表，验证物品码 = 字符串索引"""
import struct
import sys

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]

def parse_tbl(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:2] == b"TS", f"不是 TS 格式: {data[:4]!r}"
    version = u32(data, 2)
    count = u32(data, 6)
    typ = u32(data, 10)
    print(f"{path}\n  version=0x{version:x} count={count} type=0x{typ:x} size={len(data)}")
    pos = 14
    entries = []
    for _ in range(count):
        h = u32(data, pos)
        idx = u16(data, pos + 4)
        slen = u16(data, pos + 6)
        s = data[pos + 8: pos + 8 + slen]
        # 去掉结尾 \0（如有）
        if s.endswith(b"\x00"):
            s = s[:-1]
        entries.append((h, idx, s))
        pos += 8 + slen
    # index 区：count 个 (u16 index, u32 offset)
    index_map = {}
    if pos + count * 6 <= len(data):
        for _ in range(count):
            idx = u16(data, pos)
            off = u32(data, pos + 2)
            index_map[idx] = off
            pos += 6
    return version, count, typ, entries, index_map

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else r"G:\game\diablo 2\data\local\LNG\ENG--\easy\string.tbl"
    version, count, typ, entries, index_map = parse_tbl(path)
    print("  entries[0:3]:", [(h, i, s[:40]) for h, i, s in entries[:3]])
    print("  index_map size:", len(index_map))
    # 按 index 查 529/530
    by_index = {i: s for h, i, s in entries}
    for t in (529, 530, 63):
        print(f"  index {t}: {by_index.get(t)!r}")
    # 找含 Scroll of 的
    hits = [(i, s) for h, i, s in entries if b"Scroll of" in s]
    print("  Scroll of 命中:", [(i, s[:50]) for i, s in hits[:10]])
