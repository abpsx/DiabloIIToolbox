# -*- coding: utf-8 -*-
"""AHK v2 轻量语法检查: 括号/花括号/方括号/引号平衡。"""
import re

s = open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Func\Launcher.ahk", encoding="utf-8").read()
ok = True
for o, c in [("(", ")"), ("{", "}"), ("[", "]")]:
    n1, n2 = s.count(o), s.count(c)
    print("%s%s %d/%d %s" % (o, c, n1, n2, "OK" if n1 == n2 else "MISMATCH"))
    if n1 != n2:
        ok = False
bad = 0
lines = s.splitlines()
for i, line in enumerate(lines, 1):
    st = line.strip()
    if st.startswith(";") or st.startswith("/*"):
        continue
    q = st.count('"') + st.count("'")
    if q % 2 == 1:
        print("奇数引号 行", i, ":", st[:60])
        bad += 1
        ok = False
print("引号问题行:", bad)
print("RESULT:", "PASS" if ok else "FAIL")
