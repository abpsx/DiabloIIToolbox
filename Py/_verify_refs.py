#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 D2Win 数据段高引用地址：值是否指向像控件的结构。"""
import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    base = mem.module_base(pid, "D2Win.dll")
    cands = [0xC9E20, 0xC9E24, 0xC9E28, 0xC9E30, 0xC9E34, 0xE64B8, 0xE56C0,
             0xE658C, 0xE6580, 0x109C54, 0x109C34, 0xE57BC, 0x10996C,
             0xCAB0C, 0xE65B8, 0xE65D0, 0xE65DC, 0xE65CC, 0xE65BC, 0xC8C68]
    print(f"游戏画面: 界面标记={mem.read_dword(pid, h, mem.resolve_base(pid,'Fog.dll+0x4AFE0')+0x8)} 玩家={hex(mem.read_ptr(pid, h, mem.resolve_base(pid,'D2CLIENT+0x11B800')))}")
    for off in cands:
        v = mem.read_dword(pid, h, base + off)
        if not v or v < 0x10000:
            print(f"  D2Win+0x{off:X} = 0x{v:08X}  (null/小值)")
            continue
        chunk = mem.read(pid, h, v, 0x50)
        if len(chunk) != 0x50:
            print(f"  D2Win+0x{off:X} = 0x{v:08X}  读目标失败")
            continue
        t = int.from_bytes(chunk[0:4], "little")
        x = int.from_bytes(chunk[0x0C:0x10], "little")
        y = int.from_bytes(chunk[0x10:0x14], "little")
        sx = int.from_bytes(chunk[0x14:0x18], "little")
        sy = int.from_bytes(chunk[0x18:0x1C], "little")
        nxt = int.from_bytes(chunk[0x3C:0x40], "little")
        tag = "???"
        if 1 <= t <= 12 and x <= 3000 and y <= 3000 and sx <= 3000 and sy <= 3000:
            tag = "像控件!"
        print(f"  D2Win+0x{off:X} = 0x{v:08X}  type={t} pos=({x},{y}) size=({sx}x{sy}) "
              f"next=0x{nxt:08X}  {tag}")
        if tag == "像控件!":
            # 试读文本
            texts = mem.read_control_texts(pid, h, v)
            print(f"      texts={texts}")
finally:
    ctypes.windll.kernel32.CloseHandle(h)
