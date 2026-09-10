#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在游戏进程内存中搜索词条中文描述(UTF-8)，定位 tbl 描述表结构与地址"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr
from ctypes import wintypes

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

MEM_COMMIT = 0x1000
PAGE_READABLE = 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x40 | 0x80

targets = {
    "照亮范围": "照亮范围".encode("utf-8"),
    "圣骑士技能": "圣骑士技能".encode("utf-8"),
    "全抗": "全抗".encode("utf-8"),
    "刺客技能": "刺客技能".encode("utf-8"),
    "准确率": "准确率".encode("utf-8"),
}

found = {k: [] for k in targets}

addr = 0
while addr < 0x7FFFFFFF:
    mbi = MEMORY_BASIC_INFORMATION()
    if not k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        addr += 0x10000
        continue
    size = int(mbi.RegionSize or 0)
    baddr = int(mbi.BaseAddress or 0)
    if not size or not baddr:
        addr += 0x10000
        continue
    if (mbi.State & MEM_COMMIT) and (mbi.Protect & 0xFF) in (0x02, 0x04, 0x20, 0x40, 0x80):
        base = baddr
        if 0x10000000 <= base <= 0x20000000:   # 会话区附近
            raw = mr.read(pid, h, base, min(size, 0x200000))
            if raw:
                for k, pat in targets.items():
                    start = 0
                    while True:
                        i = raw.find(pat, start)
                        if i < 0:
                            break
                        found[k].append(base + i)
                        start = i + 1
        addr = base + size
    else:
        addr = baddr + size

for k, addrs in found.items():
    print(f"{k}: {len(addrs)} 处 -> {[hex(a) for a in addrs[:6]]}")
