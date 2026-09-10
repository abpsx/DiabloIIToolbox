# -*- coding: utf-8 -*-
import json
sn = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\special_names.json", encoding="utf-8"))
ui = sn["unique_items"]
codes = [v.get("code") for v in ui.values() if v.get("code")]
print("unique 有code条数:", len(codes), "/", len(ui))
print("示例:", [(v["code"], v["name"], v["zh"]) for v in ui.values() if v.get("code")][:8])
for k, v in ui.items():
    if v.get("name") == "Gheed's Fortune":
        print("605目标:", k, v)
