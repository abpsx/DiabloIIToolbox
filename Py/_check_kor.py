# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\local\LNG\kor\String.tbl", "rb").read()
for pat in (b"hpo", b"pr1", b"cm11", b"qf1", b"elc", "体力".encode("utf-16-le"),
            "项链".encode("utf-16-le"), "城镇卷".encode("utf-16-le")):
    hits = []
    pos = 0
    while True:
        i = raw.find(pat, pos)
        if i < 0:
            break
        hits.append(i)
        pos = i + 1
        if len(hits) > 6:
            break
    print(pat[:8], [hex(x) for x in hits] if hits else "无")

printable = sum(1 for b in raw if 32 <= b < 127)
print("ASCII 比例:", printable / len(raw))
