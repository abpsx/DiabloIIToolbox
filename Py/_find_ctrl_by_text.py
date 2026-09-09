#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从主菜单按钮文本反查控件结构。
1) 全内存（低堆+D2Win等）搜 "单机模式"（GBK + UTF-16LE）
2) 对文本地址 s：检查 s-0x6C（按钮内联 wText2@+0x6C）是否像 Control(type=6)
   及 s-0x5C（文本框内联）是否像 Control
3) 命中后反查：谁指向该控件（FirstControl/pNext 候选）"""
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
try:
    # ---- 1) 收集要搜索的内存区（D2Win + 低地址堆 0x01xxxxxx~0x30xxxxxx 分段）----
    regions = []
    for mod in ("D2Win.dll", "D2Lang.dll", "Fog.dll", "Anhei2Map.dll"):
        b = mem.module_base(pid, mod)
        if b:
            regions.append((b, 0x30000))
    # 低堆（控件分配区）
    for lo, hi in [(0x01000000, 0x02000000), (0x02000000, 0x04000000),
                   (0x0B000000, 0x0C000000)]:
        regions.append((lo, hi - lo))

    gbk_pat = "单机模式".encode("gbk")
    u16_pat = "单机模式".encode("utf-16-le")
    print(f"GBK 模式: {gbk_pat.hex(' ')}")
    print(f"UTF16 模式: {u16_pat.hex(' ')}")

    text_hits = []
    for base, size in regions:
        buf = bytearray()
        for p0 in range(0, size, 0x1000):
            chunk = mem.read(pid, h, base + p0, 0x1000)
            buf.extend(chunk if chunk else b"\x00" * 0x1000)
        raw = bytes(buf)
        for pat in (gbk_pat, u16_pat):
            start = 0
            while True:
                idx = raw.find(pat, start)
                if idx < 0:
                    break
                text_hits.append((base + idx, "gbk" if pat is gbk_pat else "u16"))
                start = idx + 1
    print(f"文本命中 {len(text_hits)} 处")
    for a, enc in text_hits[:30]:
        print(f"  0x{a:08X} [{enc}]")

    # ---- 2) 检查文本地址附近是否像控件 ----
    def ctrl_at(a):
        c = mem.read(pid, h, a, 0x80)
        if len(c) != 0x80:
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

    print("\n=== 控件反查 ===")
    ctrl_addrs = set()
    for a, enc in text_hits:
        # 按钮内联 wText2 @+0x6C；文本框内联 wText @+0x5C；ControlText 指针 @0x00
        for cand_off, label in ((0x6C, "按钮wText2@+0x6C"), (0x5C, "文本框wText@+0x5C"),
                                (0x00, "文本即+0x0(ControlText?)")):
            caddr = a - cand_off
            r = ctrl_at(caddr)
            if r:
                print(f"  文本0x{a:08X} -0x{cand_off:02X} -> 控件0x{caddr:08X} {r} [{label}]")
                ctrl_addrs.add(caddr)
                break

    # ---- 3) 反查谁指向控件（FirstControl / pNext）----
    print("\n=== 反查指向控件的指针（D2Win 数据段 + 低堆）===")
    for base, size in regions:
        buf = bytearray()
        for p0 in range(0, size, 0x1000):
            chunk = mem.read(pid, h, base + p0, 0x1000)
            buf.extend(chunk if chunk else b"\x00" * 0x1000)
        raw = bytes(buf)
        for caddr in ctrl_addrs:
            target = caddr.to_bytes(4, "little")
            start = 0
            while True:
                idx = raw.find(target, start)
                if idx < 0:
                    break
                ref = base + idx
                # 过滤：4 对齐 + 不在控件自身内部
                if ref % 4 == 0 and not (caddr <= ref < caddr + 0x80):
                    print(f"  0x{ref:08X} (D2Win+0x{ref-base:X}) -> 0x{caddr:08X}")
                start = idx + 1
finally:
    ctypes.windll.kernel32.CloseHandle(h)
