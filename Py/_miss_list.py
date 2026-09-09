# -*- coding: utf-8 -*-
"""输出 item_codes.json 中未命中全称的条目列表"""
import json

d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json", encoding="utf-8"))
items = d["items"]
miss = [it for it in items if "name" not in it]
hit = [it for it in items if "name" in it]
print(f"命中 {len(hit)} / 未命中 {len(miss)} / 总数 {len(items)}")
print("未命中 code(id):")
print(", ".join(f"{it['code']}({it['id']})" for it in miss))
