#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深挖游戏内 D2Win 高频全局 0x21518/0x21508 等指向的结构。"""
import ctypes
import sys

sys.path.insert(0, ".")
import mem_read as mem


def dump_region(pid, h, addr, n=0x200):
    print(f"--- 0x{addr:08X} 周边 {n} 字节 ---")
    raw = mem.read(pid, h, addr, n)
    if not raw:
        print("  不可读")
        return
    for i in range(0, n, 16):
        chunk = raw[i:i + 16]
        dws = " ".join(f"{int.from_bytes(chunk[j:j+4],'little'):08X}" for j in range(0, len(chunk), 4))
        print(f"  +0x{i:03X}: {dws}")


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
        for off in (0x21508, 0x2150C, 0x21518, 0x2151C, 0x21520, 0x21524, 0x21528, 0x2152C, 0x21530):
            v = mem.read_dword(pid, h, base + off)
            print(f"D2Win+0x{off:05X} = 0x{v:08X}")
        print()
        for target in (0x14900000, 0x1490000C, 0x1282200C, 0x12822018, 0x0CDB0024, 0x13ED0000):
            dump_region(pid, h, target, 0x80)
            print()
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
