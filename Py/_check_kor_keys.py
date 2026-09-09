# -*- coding: utf-8 -*-
import json
d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_kor_tbl.json", encoding="utf-8"))
print("总条数", len(d))
for k in ["tsc", "isc", "sst", "portal1", "portal11", "portal56", "pr1", "cm1", "vps", "hp1", "679", "713", "key", "pk1"]:
    v = d.get(k, "<无>")
    print(f"  {k!r}: {v!r}")
