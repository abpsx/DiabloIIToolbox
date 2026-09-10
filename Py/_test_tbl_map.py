# -*- coding: utf-8 -*-
"""验证当前进程物品码表(0x9FF6C) 与候选 ItemTxt 表(flphax) 的关系。

问题: mod(kor) 环境下 ItemTxt 行号 可能 ≠ 物品码表 id(物品 dwTxtFileNo)。
方案: 从物品码表读出城镇卷(529)的 code='tsc '，再在候选 ItemTxt 表里搜该 code 的行号。
"""
from __future__ import annotations
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from locale_text import ROW

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def main():
    pid = mem.find_process("D2Loader.exe")
    h = mem.open_process_readonly(pid)
    try:
        d2c = mem.module_base(pid, "D2Common.dll")
        table = dword(pid, h, d2c + 0x9FF6C)
        table = dword(pid, h, table + 0x8)
        print(f"物品码表 table={table:#x}")
        # 码表条目: 8字节缩写 + 4字节码（早期格式：缩写8字节+码4字节）
        for tid in (529, 530, 587):
            raw = mem.read(pid, h, table + tid * 12, 12)
            abbr = raw[:8].split(b"\x00")[0]
            code = int.from_bytes(raw[8:12], "little")
            print(f"  码表[{tid}] abbr={abbr!r} code={code} (0x{code:X})")

        # 候选 ItemTxt 表
        cands = [0x12a548ec, 0x12a5f384, 0x12af8694, 0x12b0312c, 0x175e44a4]
        print(f"\n候选表扫描 szCode 列（前 {3000} 行）:")
        for base in cands:
            found = {}
            for tid in range(0, 3000):
                raw = mem.read(pid, h, base + tid * ROW + 0x80, 4)
                if not raw:
                    break
                c = raw.split(b"\x00")[0]
                if c in (b"tsc", b"isc", b"r13", b"hp1"):
                    found[c.decode()] = tid
            print(f"  {base:#x}: {found}")
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
