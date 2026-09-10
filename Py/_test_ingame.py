#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""游戏内 dump D2Win+0x21480~0x214C0 区域，寻找控件根指针线索。"""
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
        if not base:
            print("D2Win.dll 未加载")
            return 1
        print(f"D2Win base=0x{base:X}")
        for off in range(0x21460, 0x214D0, 4):
            v = mem.read_dword(pid, h, base + off)
            extra = ""
            if v:
                # 尝试读一下指向处的前几字节，判断是否像控件结构
                t = mem.read_dword(pid, h, v)
                if 0 <= t <= 0x10:
                    posx = mem.read_dword(pid, h, v + 0x0C)
                    posy = mem.read_dword(pid, h, v + 0x10)
                    if posx < 2000 and posy < 2000:
                        nxt = mem.read_dword(pid, h, v + 0x3C)
                        extra = f"  -> type={t} pos=({posx},{posy}) next=0x{nxt:X}"
            print(f"  +0x{off:X} = 0x{v:08X}{extra}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
