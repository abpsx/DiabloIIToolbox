# -*- coding: utf-8 -*-
"""对空 name 的 59 个条目逐个跑 txt_to_name 全链路"""
import sys, ctypes, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_item_codes.json", encoding="utf-8"))
    empty = [(int(k), v["code"]) for k, v in d["by_id"].items() if not (v.get("name") or "").strip()]
    empty.sort()
    got, miss = [], []
    for tid, code in empty:
        name, row = lt.txt_to_name(pid, h, tid)
        wloc = row["locale"] if row else "?"
        if name:
            got.append((tid, code, wloc, name))
            print("OK  id=%d code=%r wloc=%s -> %r" % (tid, code, wloc, name))
        else:
            miss.append((tid, code, wloc))
            print("--  id=%d code=%r wloc=%s (空)" % (tid, code, wloc))
    print("\n查到 %d / %d" % (len(got), len(empty)))
finally:
    ctypes.windll.kernel32.CloseHandle(h)
