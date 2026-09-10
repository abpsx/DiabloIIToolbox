# -*- coding: utf-8 -*-
import re
for f in ("bag.py", "item_name.py", "item_txt_resolver.py", "dump_item_names.py"):
    try:
        src = open(f, encoding="utf-8").read()
    except Exception as e:
        print(f, "ERR", e)
        continue
    m = re.search(r'"""(.*?)"""', src, re.S)
    print("=====", f, "=====")
    if m:
        print(m.group(1)[:900])
    else:
        print("(无docstring, 行数", src.count("\n"), ")")
