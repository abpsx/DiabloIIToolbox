#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""游戏内(ESC菜单打开) dump D2Win 高频引用全局偏移的值 + 指向处控件结构检查。"""
import ctypes
import sys

sys.path.insert(0, ".")
import mem_read as mem


def main() -> None:
    pid = mem.find_process("D2Loader.exe")
    if pid is None:
        print("D2Loader.exe 未运行")
        return 1
    h = mem.open_process_readonly(pid)
    if not h:
        print("OpenProcess 失败")
        return 1
    try:
        base = mem.module_base(pid, "D2Win.dll")
        offs = [0x21480, 0x21484, 0x21488, 0x2148C, 0x21490, 0x21494, 0x21498, 0x2149C,
                0x214A0, 0x214A4, 0x214A8, 0x214AC, 0x214B0, 0x214B4, 0x214B8, 0x214BC,
                0x214C0, 0x214C4, 0x214C8, 0x214CC, 0x214D0, 0x214D4, 0x214D8, 0x214DC,
                0x214E0, 0x214E4, 0x214E8, 0x214EC, 0x214F0, 0x214F4, 0x214F8, 0x214FC,
                0x21500, 0x21504, 0x21508, 0x2150C, 0x21510, 0x21514, 0x21518, 0x2151C,
                0x21520, 0x21524, 0x21528, 0x2152C, 0x21530, 0x21534, 0x21538, 0x2153C,
                0x21540]
        for off in offs:
            v = mem.read_dword(pid, h, base + off)
            extra = ""
            if v and not (base <= v < base + 0x20000):
                t = mem.read_dword(pid, h, v)
                if 0 <= t <= 0x10:
                    px = mem.read_dword(pid, h, v + 0x0C)
                    py = mem.read_dword(pid, h, v + 0x10)
                    sx = mem.read_dword(pid, h, v + 0x14)
                    sy = mem.read_dword(pid, h, v + 0x18)
                    if px < 2000 and py < 2000 and sx < 2000 and sy < 2000:
                        nxt = mem.read_dword(pid, h, v + 0x3C)
                        txt = mem.read_dword(pid, h, v + 0x48)
                        extra = (f"  -> type={t} pos=({px},{py}) size=({sx},{sy}) "
                                 f"next=0x{nxt:08X} pFirstText=0x{txt:08X}")
            print(f"  +0x{off:05X} = 0x{v:08X}{extra}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
