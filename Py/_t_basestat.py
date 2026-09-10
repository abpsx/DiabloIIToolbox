# -*- coding: utf-8 -*-
"""读 D2Common sgptDataTable 表数组, 定位 uniqueitems(#17), 读记录262的name locale。"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from locale_text import get_locale_text, find_locale_dispatch, read_utf16

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def read(pid, h, a, n):
    return mem.read(pid, h, a, n)

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2COMMON.DLL")
base = d2c + 0xA33F0
print("sgptDataTable = %#x" % base)

# dump 表数组 0x100 字节, 每8字节一组 (ptr+count)
for i in range(0, 0x100, 8):
    ptr = dword(pid, h, base + i)
    cnt = dword(pid, h, base + i + 4)
    tag = ""
    if ptr:
        # 读表头判断类型
        head = read(pid, h, ptr, 0x40)
        if head:
            # 找 code 串（4字节 ASCII）
            codes = []
            for off in range(0, len(head) - 3, 4):
                c4 = head[off:off+4]
                if all(0x20 <= b < 0x7F for b in c4):
                    codes.append(c4.decode("ascii", "ignore"))
            tag = "codes=" + ",".join(codes[:3])
    print("  #%02d  ptr=%#x  count=%d  %s" % (i // 8, ptr, cnt, tag))

# 假设每表8字节, #17 = +0x88
for idx in (16, 17, 6, 7, 8, 9):
    ptr = dword(pid, h, base + idx * 8)
    cnt = dword(pid, h, base + idx * 8 + 4)
    print("表#%d ptr=%#x count=%d" % (idx, ptr, cnt))
ctypes.windll.kernel32.CloseHandle(h)
