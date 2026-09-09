# -*- coding: utf-8 -*-
import json
import re

pairs = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_kor_tbl.json", encoding="utf-8"))

kws = ["体力", "法力", "藥", "药", "瓶子", "治療", "治疗", "红", "蓝", "钥匙", "玉净",
       "符石", "怪胎", "投石", "枷锁", "星座", "宫", "天堂", "之", "完美", "碎裂"]
# 药水/特殊物品反向匹配（排除 quest/词缀类太长的）
hits = {}
for k, v in pairs.items():
    if any(w in v for w in kws) and len(v) <= 40:
        hits[k] = v
# 排序输出
for k in sorted(hits, key=lambda x: (len(x), x)):
    print(f"  {k!r} -> {hits[k]!r}")
print("总数:", len(hits))
