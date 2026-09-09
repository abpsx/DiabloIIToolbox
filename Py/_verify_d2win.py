#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用引用扫描候选地址验证 FirstControl（主菜单时命中）。"""
import ctypes
import sys
import os
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if pid is None:
    print("D2Loader.exe 未运行")
    sys.exit(1)
h = mem.open_process_readonly(pid)
try:
    base = mem.module_base(pid, "D2Win.dll")
    size = 0x120000
    buf = bytearray()
    for p0 in range(0, size, 0x1000):
        chunk = mem.read(pid, h, base + p0, 0x1000)
        buf.extend(chunk if chunk else b"\x00" * 0x1000)
    raw = bytes(buf)

    def d32(a):
        o = a - base
        return int.from_bytes(raw[o:o+4], "little") if 0 <= o <= len(raw)-4 else None

    def is_ctrl(a):
        c = mem.read(pid, h, a, 0x40)
        if len(c) != 0x40:
            return None
        t = int.from_bytes(c[0:4], "little")
        if not (1 <= t <= 12):
            return None
        x = int.from_bytes(c[0x0C:0x10], "little")
        y = int.from_bytes(c[0x10:0x14], "little")
        sx = int.from_bytes(c[0x14:0x18], "little")
        sy = int.from_bytes(c[0x18:0x1C], "little")
        if x > 3000 or y > 3000 or sx > 3000 or sy > 3000:
            return None
        return (t, x, y, sx, sy)

    refs = collections.defaultdict(int)
    i, n = 0, len(raw) - 8
    while i < n:
        b = raw[i]
        addr = None
        if b == 0xA1:
            addr = d32(base+i+1); i += 5
        elif b == 0x8B and raw[i+1] == 0x0D:
            addr = d32(base+i+2); i += 6
        elif b == 0x8B and raw[i+1] == 0x15:
            addr = d32(base+i+2); i += 6
        elif b == 0x89 and raw[i+1] in (0x05, 0x0D, 0x15):
            addr = d32(base+i+2); i += 6
        elif b == 0xFF and raw[i+1] == 0x35:
            addr = d32(base+i+2); i += 6
        elif b == 0xC7 and raw[i+1] == 0x05:
            addr = d32(base+i+2); i += 10
        else:
            i += 1
        if addr is not None:
            off = addr - base
            if 0x30000 <= off < size:
                refs[off] += 1

    print("界面标记:", mem.read_dword(pid, h, mem.resolve_base(pid, "Fog.dll+0x4AFE0") + 0x8))
    print("玩家:", hex(mem.read_ptr(pid, h, mem.resolve_base(pid, "D2CLIENT+0x11B800"))))
    print()
    print("=== 候选引用地址 -> 当前值 -> 是否像控件 ===")
    hits = []
    for off, cnt in sorted(refs.items(), key=lambda kv: -kv[1]):
        val = d32(base + off)
        if not val or val == 0:
            continue
        if base <= val < base + size:
            continue
        r = is_ctrl(val)
        if r:
            nxt = int.from_bytes(mem.read(pid, h, val + 0x3C, 4) or b"\0\0\0\0", "little")
            chain = 1
            cur, seen = nxt, {val}
            while cur and cur not in seen and chain < 10:
                seen.add(cur)
                rr = is_ctrl(cur)
                if not rr:
                    break
                chain += 1
                cur = int.from_bytes(mem.read(pid, h, cur + 0x3C, 4) or b"\0\0\0\0", "little")
            hits.append((off, cnt, val, r, chain))
            print(f"  [命中] D2Win+0x{off:X} x{cnt} -> 0x{val:X} {r} 链长={chain}")
    print(f"共 {len(hits)} 个命中")
    print()
    print("=== 高引用非0值（前25）===")
    shown = 0
    for off, cnt in sorted(refs.items(), key=lambda kv: -kv[1]):
        val = d32(base + off)
        if not val or val == 0:
            continue
        print(f"  D2Win+0x{off:X} x{cnt} val=0x{val:08X}")
        shown += 1
        if shown >= 25:
            break
finally:
    ctypes.windll.kernel32.CloseHandle(h)
