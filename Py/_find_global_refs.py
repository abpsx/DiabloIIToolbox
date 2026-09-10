#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 D2Win 代码段中对 0x214A0/0x214B0 等全局的绝对地址引用，
并列出 D2Win 代码引用 0x214xx~0x215xx 范围的所有偏移，找游戏内控件根候选。"""
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
        size = 0x20000  # D2Win 代码+数据约 128KB
        raw = mem.read(pid, h, base, size)
        if not raw:
            print("读取 D2Win 模块失败")
            return 1
        # 统计代码段中对 base+0x21000~0x21800 的绝对引用
        from collections import Counter
        cnt = Counter()
        refs = {}
        for i in range(0, len(raw) - 3):
            v = int.from_bytes(raw[i:i + 4], "little")
            if base + 0x21000 <= v < base + 0x21800:
                off = v - base
                cnt[off] += 1
                refs.setdefault(off, []).append(i)
        print("D2Win 代码引用 0x21000~0x21800 全局偏移：")
        for off, n in sorted(cnt.items()):
            print(f"  +0x{off:05X} 引用 {n} 次")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
