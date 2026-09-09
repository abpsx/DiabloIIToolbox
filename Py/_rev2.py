# -*- coding: utf-8 -*-
import json

pairs = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_kor_tbl.json", encoding="utf-8"))

print("=== 含'药' ===")
for k, v in sorted(pairs.items()):
    if "药" in v and len(v) <= 30:
        print(f"  {k!r} -> {v!r}")

print("\n=== 含'瓶' ===")
for k, v in sorted(pairs.items()):
    if "瓶" in v and len(v) <= 30:
        print(f"  {k!r} -> {v!r}")

print("\n=== 含'灵' ===")
for k, v in sorted(pairs.items()):
    if "灵" in v and len(v) <= 30:
        print(f"  {k!r} -> {v!r}")

print("\n=== 含'完美/碎裂/普通宝石' ===")
for k, v in sorted(pairs.items()):
    if ("完美" in v or "碎裂" in v) and len(v) <= 30:
        print(f"  {k!r} -> {v!r}")
