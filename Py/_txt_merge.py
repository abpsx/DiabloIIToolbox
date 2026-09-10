#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 bin2txt 模板 MagicPrefix/Suffix.txt 补全映射表属性，同名变体按 itype 展开。
结构：id -> {row, name, name_zh, variants: [{level,maxlevel,levelreq,group,itype,etype,mods,spawnable,rare}, ...]}
内存表 id 权威（已锚点+实测验证）；txt 以 name 为键取全部变体。
"""
import sys, json

DP = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_prefix.json"
DS = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_suffix.json"
TP = r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt"
TS = r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt"

TX_COLS = ("name", "comment", "version", "spawnable", "rare", "level", "maxlevel",
           "levelreq", "classspecific", "class", "classlevelreq", "frequency", "group",
           "mod1code", "mod1param", "mod1min", "mod1max",
           "mod2code", "mod2param", "mod2min", "mod2max",
           "mod3code", "mod3param", "mod3min", "mod3max",
           "transform", "transformcolor",
           "itype1", "itype2", "itype3", "itype4", "itype5", "itype6", "itype7",
           "etype1", "etype2", "etype3", "etype4", "etype5",
           "divide", "multiply", "add")

def parse_txt(path):
    """返回 {name: [变体 dict, ...]}（按 txt 出现顺序）"""
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip("\r\n").split("\t")
            if i == 1:
                continue
            name = cols[0].strip()
            if not name or name == "Expansion":
                continue
            rec = {}
            for ci, key in enumerate(TX_COLS):
                if ci < len(cols):
                    v = cols[ci].strip()
                    if v:
                        rec[key] = v
            out.setdefault(name, []).append(rec)
    return out

def intx(v, default=None):
    try:
        return int(v)
    except Exception:
        return default

def to_variant(raw):
    itype = [raw.get(f"itype{i}") for i in range(1, 8)]
    etype = [raw.get(f"etype{i}") for i in range(1, 6)]
    mods = []
    for i in range(1, 4):
        code = raw.get(f"mod{i}code")
        if code:
            mods.append({"code": code,
                         "param": intx(raw.get(f"mod{i}param")),
                         "min": intx(raw.get(f"mod{i}min")),
                         "max": intx(raw.get(f"mod{i}max"))})
    return {
        "level": intx(raw.get("level")),
        "maxlevel": intx(raw.get("maxlevel")),
        "levelreq": intx(raw.get("levelreq")),
        "group": intx(raw.get("group")),
        "spawnable": intx(raw.get("spawnable")),
        "rare": intx(raw.get("rare")),
        "itype": [x for x in itype if x],
        "etype": [x for x in etype if x],
        "mods": mods,
    }

def merge(dict_path, txt_path, out_path):
    d = json.load(open(dict_path, encoding="utf-8"))
    t = parse_txt(txt_path)
    merged = 0
    empty = 0
    for k, v in d.items():
        name = v.get("name", "")
        variants = t.get(name)
        if not variants:
            empty += 1
            v["variants"] = []
            continue
        v["variants"] = [to_variant(r) for r in variants]
        merged += 1
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(f"{out_path}: 共{len(d)}条, 展开变体{merged}条, 无txt记录(anhei段){empty}条")

merge(DP, TP, DP)
merge(DS, TS, DS)

# 抽查：同名多变体按 itype 区分
dp = json.load(open(DP, encoding="utf-8"))
ds = json.load(open(DS, encoding="utf-8"))
for iid in ("401", "1156", "671", "1334"):
    v = dp.get(iid)
    if v:
        print(f"prefix {iid} {v['name']} ({v['name_zh']}) 变体{len(v['variants'])}个:")
        for i, var in enumerate(v["variants"][:8]):
            print(f"   [{i}] lv={var['level']} itype={var['itype']} mods={var['mods']}")
for iid in ("401", "676", "559"):
    v = ds.get(iid)
    if v:
        print(f"suffix {iid} {v['name']} ({v['name_zh']}) 变体{len(v['variants'])}个:")
        for i, var in enumerate(v["variants"][:8]):
            print(f"   [{i}] lv={var['level']} itype={var['itype']} mods={var['mods']}")
