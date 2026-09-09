# -*- coding: utf-8 -*-
import json

d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_tbl_names.json", encoding="utf-8"))
targets = ["城镇卷", "辨视卷", "書尔", "Thul", "项链", "戒指", "美元", "短棍",
           "玉净瓶", "处女宫", "异次元", "体力药", "巨型", "大型", "治疗", "法力",
           "钩镰枪", "巨战斧", "平衡斧", "无指手套", "符石", "怪胎", "投石器", "天堂", "凤凰", "英仙"]
for tag in ("tbl_a", "tbl_b"):
    print(f"===== {tag} =====")
    for t in targets:
        hits = [e["idx"] for e in d[tag] if t in e["text"]]
        if hits:
            for idx in hits[:3]:
                print(f"  [{idx}] {d[tag][idx]['text'][:44]!r}")
