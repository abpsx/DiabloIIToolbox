# -*- coding: utf-8 -*-
"""扫描全部 items.txt 行的原始 locale 文本，统计含 \n 的条目"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    base = lt.find_itemtxt_base(pid, h)
    disp = lt.find_locale_dispatch(pid, h)
    print("items 表基:", hex(base) if base else None)
    cnt = 0
    for tid in range(716):
        row = lt.read_item_row(pid, h, base, tid)
        if not row:
            continue
        ptr = lt.get_locale_text(pid, h, disp, row["locale"])
        if not ptr:
            continue
        raw = lt.read_utf16(pid, h, ptr)
        if "\n" in raw:
            cnt += 1
            if cnt <= 80:
                print("id=%d code=%r wloc=%d RAW=%r" % (tid, row["code"], row["locale"], raw))
    print("\n含换行条目总数:", cnt)
finally:
    ctypes.windll.kernel32.CloseHandle(h)
