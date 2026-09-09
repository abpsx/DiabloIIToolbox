# -*- coding: utf-8 -*-
import os

roots = [r"G:\game\diablo 2"]
pats = ["异次元".encode("utf-8"), "灵魂枷锁".encode("utf-8"), "嗜血长老".encode("utf-8"),
        "玉净".encode("utf-8"), "怪胎冰妖".encode("utf-8"), "神石巨蟹".encode("utf-8")]
found = set()
for root in roots:
    for dp, dns, fns in os.walk(root):
        # 跳过巨大目录
        low = dp.lower()
        for fn in fns:
            if not fn.lower().endswith((".tbl", ".bin", ".txt", ".csv")):
                continue
            p = os.path.join(dp, fn)
            try:
                sz = os.path.getsize(p)
                if sz > 50_000_000:
                    continue
                raw = open(p, "rb").read(sz)
            except Exception:
                continue
            for pat in pats:
                if pat in raw:
                    found.add((p, pat.decode(), raw.find(pat)))
                    break
for p, pat, off in sorted(found):
    print(f"{pat} @ {off:#x}  {p}")
