# -*- coding: utf-8 -*-
"""将 kor tbl 确认的 6 条全称写回 item_codes.json"""
import json
import re
import datetime

PATH = r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json"

# code -> (name, name_clean)
ADD = {
    "qf1": ("克林姆的连枷", "克林姆的连枷"),
    "qf2": ("克林姆的意志", "克林姆的意志"),
    "qey": ("克林姆的眼球", "克林姆的眼球"),
    "qhr": ("克林姆的心脏", "克林姆的心脏"),
    "qbr": ("克林姆的大脑", "克林姆的大脑"),
    "cap": ("帽子【普通】", "帽子【普通】"),
}

d = json.load(open(PATH, encoding="utf-8"))
items = d["items"]
hit = miss = 0
for it in items:
    c = it.get("code", "")
    if c in ADD:
        name, clean = ADD[c]
        if not it.get("name"):
            it["name"] = name
            it["name_clean"] = clean
            hit += 1
        else:
            miss += 1

named = sum(1 for it in items if it.get("name"))
d["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json.dump(d, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"新增 {hit} 条（{miss} 条已有 name 跳过）")
print(f"总数 {len(items)}，已有 name {named}，未命名 {len(items)-named}")
print("剩余未命名:")
for it in items:
    if not it.get("name"):
        print(f"  {it['code']}({it['id']})")
