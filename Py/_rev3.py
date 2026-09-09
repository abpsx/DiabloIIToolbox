# -*- coding: utf-8 -*-
import json

pairs = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_kor_tbl.json", encoding="utf-8"))

print("=== key 含 portal ===")
for k, v in sorted(pairs.items()):
    if "portal" in k.lower():
        print(f"  {k!r} -> {v[:40]!r}")

print("\n=== value 含'宫' ===")
for k, v in sorted(pairs.items()):
    if "宫" in v and len(v) <= 40:
        print(f"  {k!r} -> {v[:44]!r}")

print("\n=== value 含'钥匙' ===")
for k, v in sorted(pairs.items()):
    if "钥匙" in v and len(v) <= 40:
        print(f"  {k!r} -> {v[:44]!r}")

print("\n=== key 含 ModStr ===")
for k, v in sorted(pairs.items()):
    if "modstr" in k.lower():
        print(f"  {k!r} -> {v[:44]!r}")

print("\n=== value 含'星座'或'座>>' ===")
for k, v in sorted(pairs.items()):
    if ("座" in v and len(v) <= 30):
        print(f"  {k!r} -> {v[:44]!r}")
