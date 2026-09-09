# -*- coding: utf-8 -*-
"""从 tbl dump 提取 mod 特有物品名（非 quest 文本/词缀）"""
import json

d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_tbl_names.json", encoding="utf-8"))

# 过滤：短文本 + 含物品名特征（星座/钥匙/【/特殊词）
import re
kw = ["钥匙", "星座", "座>>", "宫", "玉净", "符石", "怪胎", "投石", "枷锁", "天堂", "木箱",
      "之", "【", "※", "药", "宝石", "水晶", "珠子", "心脏", "角", "袋子", "柱子", "标志",
      "巨战斧", "平衡斧", "钩镰枪", "无指手套", "格斗爪", "腕刺", "阔剑", "巨鹰爪", "战斧",
      "珠", "华宁", "恶魔", "巫师", "泰坦"]
skip = ["[000A]", "[FF0C]", "。", "？", "啊", "哈", "我", "你", "那", "这", "了", "的", "吗",
        "34", "25", "30", "42", "48", "49", "52", "59", "60", "63", "65", "71", "72", "74",
        "78", "85", "90", "104", "125", "37", "6", "9"]


def is_item(t):
    if not t or len(t) > 60 or len(t) < 2:
        return False
    if t.isdigit():
        return False
    if re.match(r"^[0-9]+", t):
        return False
    if any(k in t for k in skip) and not any(k in t for k in ["钥匙", "宫", "座>>", "玉净", "符石"]):
        return False
    # 含 quest 对话特征
    if any(w in t for w in ["前往", "交谈", "谈话", "谈论", "打败", "寻找", "带回", "摧毁", "说过"]):
        return False
    return True


for tag in ("tbl_a", "tbl_b"):
    print(f"===== {tag} 物品名候选 =====")
    for e in d[tag]:
        t = e["text"].replace("[000A]", " ").replace("[FF0C]", ",").replace("[FF0A]", " ").replace("[FF01]", "!").replace("[FF1F]", "?").replace("[FF08]", "(").replace("[FF09]", ")")
        if is_item(t):
            print(f"  [{e['idx']}] {t[:50]}")
