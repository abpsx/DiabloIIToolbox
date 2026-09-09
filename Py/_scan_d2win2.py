#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩展扫描：D2Win.dll 数据段（含超出 SizeOfImage 的映射区）找 FirstControl。
先验证 D2Win+0xC9E34（用户CT确认有效）可读，再扫描 0x40000~0x110000。
控件强特征：目标 type∈1..12 + 坐标/尺寸合理 + pNext 链 ≥2 节点均像控件。"""
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
    scan_end = 0x120000  # 覆盖 0xC9E34 等映射延伸区
    print(f"D2Win.dll base=0x{base:X}")

    # 0) 验证 CT 已知偏移可读
    for off in (0xC9E34, 0x8DB34, 0x3D55BC):
        raw = mem.read(pid, h, base + off, 16)
        print(f"  D2Win+0x{off:X}: {raw.hex(' ')}")

    # 1) 按页分段读（跳过不可读页）
    raw = bytearray()
    for p0 in range(0, scan_end, 0x1000):
        chunk = mem.read(pid, h, base + p0, 0x1000)
        if chunk:
            raw.extend(chunk)
        else:
            raw.extend(b"\x00" * 0x1000)
    raw = bytes(raw)
    print(f"读入 {len(raw)} 字节 (0x{scan_end:X})")

    def d(addr):
        off = addr - base
        if 0 <= off <= len(raw) - 4:
            return int.from_bytes(raw[off:off+4], "little")
        return None

    def is_ctrl_like(addr):
        """读目标，判定像不像 Control：type∈1..12 + 坐标/尺寸合理。"""
        chunk = mem.read(pid, h, addr, 0x40)
        if len(chunk) != 0x40:
            return None
        t = int.from_bytes(chunk[0:4], "little")
        if not (1 <= t <= 12):
            return None
        x = int.from_bytes(chunk[0x0C:0x10], "little")
        y = int.from_bytes(chunk[0x10:0x14], "little")
        sx = int.from_bytes(chunk[0x14:0x18], "little")
        sy = int.from_bytes(chunk[0x18:0x1C], "little")
        if not (x <= 3000 and y <= 3000 and sx <= 3000 and sy <= 3000):
            return None
        return (t, x, y, sx, sy)

    # 2) 扫描数据段指针 → 目标像控件，且 pNext 链延续
    hits = []
    for off in range(0x40000, min(len(raw) - 4, scan_end), 4):
        p = d(base + off)
        if not p or p == 0:
            continue
        if base <= p < base + scan_end:
            continue  # 控件在堆/其他模块
        r0 = is_ctrl_like(p)
        if not r0:
            continue
        # 链一致性：至少 2 个节点
        nxt = int.from_bytes(mem.read(pid, h, p + 0x3C, 4) or b"\0\0\0\0", "little")
        chain_len = 1
        cur = nxt
        seen = {p}
        while cur and cur not in seen and chain_len < 8:
            seen.add(cur)
            r = is_ctrl_like(cur)
            if not r:
                break
            chain_len += 1
            cur = int.from_bytes(mem.read(pid, h, cur + 0x3C, 4) or b"\0\0\0\0", "little")
        hits.append((base + off, p, r0, chain_len))

    print(f"候选 {len(hits)} 个（链≥1）")
    for addr, p, (t, x, y, sx, sy), n in hits:
        print(f"  D2Win+0x{addr-base:X} -> 0x{p:X} type={t} pos=({x},{y}) "
              f"size=({sx}x{sy}) 链长={n}")
finally:
    ctypes.windll.kernel32.CloseHandle(h)
