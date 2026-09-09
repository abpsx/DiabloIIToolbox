# -*- coding: utf-8 -*-
"""读 ItemTxt 行 679/713/529 完整结构，dump 字符串字段"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

BASE = 0x127A004C
W = 0x1A8
for row, label in [(0, "hax"), (529, "tsc"), (530, "isc"), (679, "pr1"), (713, "pr56")]:
    a = BASE + row * W
    raw = mem.read(pid, h, a, W)
    print(f"\n== 行 {row} ({label}) @ {a:#x} ==")
    # 提取所有可读字符串
    i = 0
    while i < len(raw):
        if 0x20 <= raw[i] < 0x7F:
            j = i
            while j < len(raw) and 0x20 <= raw[j] < 0x7F:
                j += 1
            if j - i >= 2:
                s = raw[i:j].decode("ascii", errors="replace")
                if s not in ("\x00",):
                    print(f"  +{i:#04x}: {s!r}")
            i = j
        else:
            i += 1

ctypes.windll.kernel32.CloseHandle(h)
