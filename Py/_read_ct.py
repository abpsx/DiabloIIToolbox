# -*- coding: utf-8 -*-
import re

p = r"C:\Users\abps\Desktop\新建文件夹\a.CT"
s = open(p, encoding="utf-8", errors="ignore").read()

for kw in ["仓库开", "人物仓库1", "12仓库 14盒子", "盒子开", "背包开"]:
    i = s.find('"' + kw + '"')
    if i < 0:
        print("=== %s: 未找到 ===" % kw)
        continue
    print("=== %s ===" % kw)
    print(s[max(0, i - 500):i + 150].replace("\n", " "))
    print()
