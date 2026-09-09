#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 D2Win.dll 代码段找引用数据段绝对地址的指令，收集全局变量候选。
模式：A1/8B 0D/8B 15/89 05/89 0D/89 15/FF 35/C7 05 + imm32（目标 ∈ 数据段）。
FirstControl 是全局指针变量，必然被多处代码引用。"""
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
if not h:
    print("OpenProcess 失败")
    sys.exit(1)

try:
    base = mem.module_base(pid, "D2Win.dll")
    size = 0x120000
    # 分段读
    buf = bytearray()
    for p0 in range(0, size, 0x1000):
        chunk = mem.read(pid, h, base + p0, 0x1000)
        buf.extend(chunk if chunk else b"\x00" * 0x1000)
    raw = bytes(buf)
    print(f"D2Win.dll base=0x{base:X} 读入 {len(raw)} 字节")

    # 数据段范围（含延伸映射）
    DATA_LO, DATA_HI = 0x70000, size

    def imm(off):
        return int.from_bytes(raw[off:off+4], "little")

    refs = collections.defaultdict(list)
    i = 0
    n = len(raw) - 8
    while i < n:
        b = raw[i]
        # 各模式：指令字节 + 4 字节绝对地址
        m = None
        if b == 0xA1:                      # MOV EAX, [imm32]
            m = (i, imm(i+1), "mov eax")
        elif b == 0x8B and raw[i+1] == 0x0D:   # MOV ECX, [imm32]
            m = (i, imm(i+2), "mov ecx")
        elif b == 0x8B and raw[i+1] == 0x15:   # MOV EDX, [imm32]
            m = (i, imm(i+2), "mov edx")
        elif b == 0x89 and raw[i+1] in (0x05, 0x0D, 0x15):  # MOV [imm32], reg
            m = (i, imm(i+2), f"mov [{raw[i+1]:02X}]")
        elif b == 0xFF and raw[i+1] == 0x35:   # PUSH [imm32]
            m = (i, imm(i+2), "push")
        elif b == 0xC7 and raw[i+1] == 0x05:   # MOV [imm32], imm32
            m = (i, imm(i+2), "mov dword")
        if m:
            ipos, addr, kind = m
            off = addr - base
            if DATA_LO <= off < DATA_HI:
                refs[off].append((ipos, kind))
            i += (4 if b == 0xA1 else 5 if b == 0xC7 else 6)
            continue
        i += 1

    print(f"数据段被引用地址 {len(refs)} 个")
    # 按引用次数排序输出
    for off, lst in sorted(refs.items(), key=lambda kv: -len(kv[1])):
        kinds = ",".join(sorted(set(k for _, k in lst)))
        # 读当前值
        val = int.from_bytes(raw[off:off+4], "little")
        print(f"  D2Win+0x{off:X}  x{len(lst):2d}  [{kinds}]  val=0x{val:08X}")
finally:
    ctypes.windll.kernel32.CloseHandle(h)
