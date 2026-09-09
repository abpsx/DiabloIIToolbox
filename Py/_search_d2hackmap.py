# -*- coding: utf-8 -*-
import os, re

p = r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_d2hackmap\d2hackmap"
for f in sorted(os.listdir(p)):
    if not f.endswith((".cpp", ".h")):
        continue
    try:
        src = open(os.path.join(p, f), encoding="gbk", errors="replace").read()
    except Exception:
        continue
    if "TXT:" in src or "txtID" in src or "TxtID" in src or "TxtNo" in src or "TxtFileNo" in src or "itemTxt" in src or "ItemTxt" in src:
        print("======", f)
        for m in re.finditer(r'.{70}(TXT:|txtID|TxtID|TxtNo|TxtFileNo|itemTxt|ItemTxt).{70}', src):
            line = m.group(0).replace("\t", " ").replace("\r", " ").replace("\n", " ")
            print("  ", line)
