# -*- coding: utf-8 -*-
"""剩余缺失统计（临时探针）"""
import json
d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\special_names.json", encoding="utf-8"))
names = {en: cn for en, cn in d["set_names"]}
note = d["notes"]
miss = []
for it in d["unique_items"].values():
    en = it["name"]
    if en and not names.get(en) and not note.get(en):
        miss.append((it["code"], en))
print("unique 仍缺中文:", len(miss))
print(miss[:40])
# 套装 zh 缺失
setmiss = [it["desc"] for it in d["set_items"].values() if not it.get("zh")]
print("套装 zh 缺失:", len(setmiss), setmiss)
# 抽样检查中文质量
for en in ("Tancred's Weird", "M'avina's Tenet", "Aldur's Advance", "Natalya's Mark", "Griswold's Valor"):
    print("  %s = %r" % (en, note.get(en) or names.get(en, "")))
