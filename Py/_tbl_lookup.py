# -*- coding: utf-8 -*-
"""解析 kor tbl（key\0value\0 明文对），查询物品码表未命中 code"""
import json

FILES = [
    r"G:\game\diablo 2\data\local\LNG\kor\String.tbl",
    r"G:\game\diablo 2\data\local\LNG\kor\ExpansionString.tbl",
    r"G:\game\diablo 2\data\local\LNG\kor\PatchString.tbl",
]

pairs = {}
for f in FILES:
    raw = open(f, "rb").read()
    parts = raw.split(b"\0")
    # key\0value\0key\0value...  按顺序成对（有些空串跳过对齐）
    i = 0
    while i + 1 < len(parts):
        k = parts[i]
        v = parts[i + 1]
        if k:
            try:
                ks = k.decode("utf-8", errors="replace")
            except Exception:
                ks = str(k)
            try:
                vs = v.decode("utf-8", errors="replace")
            except Exception:
                vs = str(v)
            # 只记录 value 看起来像文本的（含非 ASCII 或 3+ 字符）
            if vs and (any(ord(c) > 127 for c in vs) or len(vs) >= 3):
                pairs.setdefault(ks, vs)
        i += 2
    print(f, len(parts), "segments")

print("总 key 数:", len(pairs))

# 查询未命中 code
codes = ["qf1", "qf2", "elc", "cap", "hpf", "mpf", "hpo", "mpo", "bpl", "rpl", "bps",
         "qey", "qhr", "qbr", "pr1", "pr2", "cm11", "cm12", "cm16"]
print("\n--- 未命中 code 查询 ---")
for c in codes:
    if c in pairs:
        print(f"  {c} -> {pairs[c]!r}")
    else:
        print(f"  {c} -> 未找到")

# 顺便验证已命中的
print("\n--- 已命中抽查 ---")
for c in ["tsc", "isc", "amu", "rin", "r10", "gld", "tbk", "ibk", "hp1", "mp5", "gcv"]:
    print(f"  {c} -> {pairs.get(c, '未找到')!r}")

# 输出所有含 pr/cm/qf 前缀的 key
print("\n--- pr/cm/qf/elc 前缀 key 样本 ---")
import re
keys = sorted(pairs.keys())
for k in keys:
    if re.match(r"^(pr\d+|cm\d+|qf\d+|elc)", k, re.I):
        print(f"  {k!r} -> {pairs[k][:40]!r}")
