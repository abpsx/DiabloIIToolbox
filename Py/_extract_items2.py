# -*- coding: utf-8 -*-
"""提取 tbl_a[200:] 和 tbl_b 全部物品名候选"""
import json
import re

d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_tbl_names.json", encoding="utf-8"))

kw_hit = ["钥匙", "座>>", "宫", "玉净", "符石", "怪胎", "投石", "枷锁", "天堂", "木箱", "心脏",
          "【", "※", "巨战斧", "平衡斧", "钩镰枪", "无指手套", "格斗爪", "腕刺", "阔剑", "巨鹰爪",
          "之", "药", "水晶", "珠子", "角", "袋", "柱", "标志", "战斧", "珠宝", "华宁", "恶魔", "巫师", "泰坦"]
skip_words = ["前往", "交谈", "谈话", "谈论", "打败", "寻找", "带回", "摧毁", "说过", "战争", "局势",
              "我说", "你觉得", "这里", "那里", "现在", "已经", "还是", "但是", "因为", "所以"]


def clean(t):
    return (t.replace("[000A]", " ").replace("[FF0C]", ",").replace("[FF0A]", " ")
             .replace("[FF01]", "!").replace("[FF1F]", "?").replace("[FF08]", "(").replace("[FF09]", ")")
             .replace("[FF1A]", ":"))


def is_item(t):
    t = clean(t)
    if not t or len(t) > 55 or len(t) < 2:
        return False
    if re.match(r"^[0-9]", t):
        return False
    if any(w in t for w in skip_words):
        return False
    if re.match(r"^[A-Za-z ]+$", t) and len(t) < 4:
        return False
    return True


for tag, rng in (("tbl_a", range(200, 512)), ("tbl_b", range(0, 464))):
    print(f"===== {tag} {rng.start}~{rng.stop} =====")
    for idx in rng:
        if idx >= len(d[tag]):
            break
        t = d[tag][idx]["text"]
        if is_item(t):
            print(f"  [{idx}] {clean(t)[:50]}")
