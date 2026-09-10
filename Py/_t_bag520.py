# -*- coding: utf-8 -*-
"""生产链路 read_bag 端到端验证（临时探针）"""
import sys, json, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
cfg_dir = r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory"
cfg = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\1.13c.json", encoding="utf-8"))
bag = next((it for it in cfg if it.get("name") == "背包物品"), None)
rows = mem.read_bag(pid, h, bag, cfg_dir)
print("背包条目数:", len(rows))
for r in rows:
    sp = r.get("special") or ""
    if sp or r.get("quality") in (5, 7):
        print("  code=%s q=%s name=%s special=%r" % (r.get("code"), r.get("quality"), r.get("name"), sp[:44]))
# 找 520
t520 = [r for r in rows if r.get("code") == 520]
for r in t520:
    print("520 显示:", r.get("name"), "|", r.get("special"))
ctypes.windll.kernel32.CloseHandle(h)
