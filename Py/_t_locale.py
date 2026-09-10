# -*- coding: utf-8 -*-
"""GetLocaleText 补 unique 中文 + 520 端到端验证（临时探针）"""
import sys, json, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from mem_read import read_dword, read
import special_name as sn

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
d2c = mem.module_base(pid, "D2CLIENT.DLL")
d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\special_names.json", encoding="utf-8"))
names = {en: cn for en, cn in d["set_names"]}
print("520 Tancred:", names.get("Tancred's Weird"))

uni = d["unique_items"]
note = d["notes"]
miss = []
for it in uni.values():
    en = it["name"]
    if not names.get(en) and not note.get(en):
        miss.append((it["code"], en))
print("unique 缺中文:", len(miss), miss[:15])
for en in ("Gheed's Fortune", "Tal Rasha's Horadric Crest", "Wizardspike"):
    print("  %s -> 池:%r" % (en, names.get(en, note.get(en, ""))))
ctypes.windll.kernel32.CloseHandle(h)
