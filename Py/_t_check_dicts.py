# -*- coding: utf-8 -*-
import json, os
T = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp"
def ld(n):
    return json.load(open(os.path.join(T, n), encoding="utf-8"))

ic = ld("dict_item_codes.json")
print("item_codes by_id[529]:", ic["by_id"]["529"])
print("item_codes by_code[tsc]:", ic["by_code"]["tsc"])
print("item_codes by_id[520]:", ic["by_id"]["520"])

ui = ld("dict_unique_items.json")
print("unique by_code[cm3]:", ui["by_code"].get("cm3"))
print("unique by_index[359]:", ui["by_index"].get("359"))

si = ld("dict_set_items.json")
print("set by_code[xsk]:", si["by_code"].get("xsk"))
print("set by_code[amu] 条数:", len(si["by_code"].get("amu", [])))

sn = ld("dict_set_names.json")
for k in sn:
    if "塔-拉夏" in sn[k]:
        print("set_names 塔-拉夏:", k, "=", sn[k])
        break

nt = ld("dict_notes.json")
for k in ("Wizardspike", "Tancred's Weird"):
    print("notes[%s] = %s" % (k, nt.get(k)))

# 完整性: 每个文件可加载且非空
for f in os.listdir(T):
    d = ld(f)
    print("OK", f, len(d) if isinstance(d, (dict, list)) else "?")
