# -*- coding: utf-8 -*-
import json

pairs = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_kor_tbl.json", encoding="utf-8"))
for kw in ["异次元", "玉净", "怪胎", "诸葛", "凤凰", "天狼", "摄魂", "神石", "雷公", "飞锤",
           "嗜血", "飞天", "天神", "翻地", "钻地", "守护神", "禁卫军", "堕落天使", "穿心咒",
           "钻石星辰", "幽魂幻术", "灵魂枷锁", "西伯利亚", "雅典娜", "哈迪斯", "天堂鸟", "天堂巨兽",
           "投石器", "木箱", "脖子", "霸主", "科力克"]:
    hits = [(k, v) for k, v in pairs.items() if kw in v and len(v) <= 50]
    if hits:
        print(f"[{kw}]")
        for k, v in hits[:6]:
            print(f"    {k!r} -> {v[:44]!r}")
