#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 D2Win.dll 模块内所有 dword，找指向"控件结构"的指针（FirstControl 候选）。

控件特征（D2BS Control 结构）：目标 +0x00 type∈1..12、+0x0C/0x10/0x14/0x18 坐标/尺寸
合理小值、+0x3C pNext 为 0 或有效指针。
"""
import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if pid is None:
    print("D2Loader.exe 未运行")
    sys.exit(1)
h = mem.open_process_readonly(pid)
if not h:
    print("OpenProcess 失败")
    sys.exit(1)

try:
    base = mem.module_base(pid, "D2Win.dll")
    size = 0xCF000
    print(f"D2Win.dll base=0x{base:X} size=0x{size:X}")

    # 1) 批量读整个模块
    raw = mem.read(pid, h, base, size)
    print(f"读入 {len(raw)} 字节")

    def d(off):
        return int.from_bytes(raw[off:off+4], "little")

    # 2) 扫描：数据段 0x30000 起，指向"模块外"的指针，且目标像控件
    cands = []
    for off in range(0x30000, size - 4, 4):
        p = d(off)
        if p == 0:
            continue
        # 目标不能指向 D2Win.dll 内部（控件在堆/其他模块）
        if base <= p < base + size:
            continue
        # 目标可读性 + 结构特征：用 RPM 读 0x40 字节
        chunk = mem.read(pid, h, p, 0x40)
        if len(chunk) != 0x40:
            continue
        t = int.from_bytes(chunk[0:4], "little")
        if not (1 <= t <= 12):
            continue
        x = int.from_bytes(chunk[0x0C:0x10], "little")
        y = int.from_bytes(chunk[0x10:0x14], "little")
        sx = int.from_bytes(chunk[0x14:0x18], "little")
        sy = int.from_bytes(chunk[0x18:0x1C], "little")
        if not (x <= 2000 and y <= 2000 and sx <= 2000 and sy <= 2000):
            continue
        nxt = int.from_bytes(chunk[0x3C:0x40], "little")
        cands.append((base + off, p, t, x, y, sx, sy, nxt))

    print(f"候选 {len(cands)} 个")
    for c in cands[:40]:
        print(f"  D2Win+0x{c[0]-base:X} -> 0x{c[1]:X} type={c[2]} pos=({c[3]},{c[4]}) "
              f"size=({c[5]}x{c[6]}) next=0x{c[7]:X}")
finally:
    ctypes.windll.kernel32.CloseHandle(h)
