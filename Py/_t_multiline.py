# -*- coding: utf-8 -*-
"""看扩展表/主表文本的原始换行结构"""
import sys, ctypes, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    base = lt.find_itemtxt_base(pid, h)
    disp = lt.find_locale_dispatch(pid, h)
    print("itemtxt base=%s" % (hex(base) if base else None))
    for tid in [679, 691, 694, 695, 661, 715, 509, 511, 520, 529]:
        row = lt.read_item_row(pid, h, base, tid)
        ptr = lt.get_locale_text(pid, h, disp, row["locale"]) if (row and disp) else None
        raw = lt.read_utf16(pid, h, ptr) if ptr else ""
        print("\nid=%d code=%r wloc=%d" % (tid, row["code"] if row else "?", row["locale"] if row else "?"))
        print("  RAW:", repr(raw))
        print("  CLEAN:", repr(lt.clean_name(raw)))
finally:
    ctypes.windll.kernel32.CloseHandle(h)
