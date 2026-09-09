# -*- coding: utf-8 -*-
"""从对齐起点解析 kor tbl 文本区 key\\0value"""
import json

FILES = [
    (r"G:\game\diablo 2\data\local\LNG\kor\String.tbl", 0x3FA94),
    (r"G:\game\diablo 2\data\local\LNG\kor\ExpansionString.tbl", None),
    (r"G:\game\diablo 2\data\local\LNG\kor\PatchString.tbl", None),
]

pairs = {}
for f, start in FILES:
    raw = open(f, "rb").read()
    if start is None:
        # 自动找起点：第一个 >=32 连续文本段（修正 UTF-8 判定）
        def tb(b):
            return (0x20 <= b < 0x7F) or (0x80 <= b < 0xC0) or (0xC0 <= b < 0xF5) or b == 0

        cur = None
        for i in range(len(raw)):
            if tb(raw[i]):
                if cur is None:
                    cur = i
                if i - cur > 64:
                    start = cur
                    break
            else:
                cur = None
    # 起点若落在 \0 则跳过
    while start < len(raw) and raw[start] == 0:
        start += 1
    parts = raw[start:].split(b"\0")
    i = 0
    n = 0
    while i + 1 < len(parts):
        k, v = parts[i], parts[i + 1]
        if k and v:
            ks = k.decode("utf-8", errors="replace")
            vs = v.decode("utf-8", errors="replace")
            pairs.setdefault(ks, vs)
            n += 1
        i += 2
    print(f, "start=", hex(start), "pairs=", n)

print("总 key 数:", len(pairs))

codes = ["qf1", "qf2", "elc", "cap", "hpf", "mpf", "hpo", "mpo", "bpl", "rpl", "bps",
         "qey", "qhr", "qbr", "pr1", "pr2", "cm11", "cm12", "cm16", "tsc", "isc", "amu"]
print("\n--- 查询 ---")
for c in codes:
    print(f"  {c} -> {pairs.get(c, '未找到')!r}")

# pr/cm/qf/elc 前缀
print("\n--- 前缀 key ---")
import re
for k in sorted(pairs.keys()):
    if re.match(r"^(pr\d+|cm\d+|qf\d+|elc)", k, re.I):
        print(f"  {k!r} -> {pairs[k][:44]!r}")

# 保存
json.dump(pairs, open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_kor_tbl.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print("\nsaved _kor_tbl.json")
