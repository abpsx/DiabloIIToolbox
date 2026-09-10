#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 txt mod 词条合并进 dict_magic_affixes.json（id=行号版）"""
import json, re

AFF = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_affixes.json"
TP = r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt"
TS = r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt"

# 解析 txt：name -> [{mod_code, param, min, max, level}]
def parse_txt(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip().split("\t")
            if i == 1 or not cols[0].strip():
                continue
            name = cols[0].strip()
            level = cols[3].strip() if len(cols) > 3 else "?"
            mods = []
            for mi in range(1, 4):
                base = 13 + (mi - 1) * 4
                if len(cols) > base and cols[base].strip():
                    mods.append({
                        "code": cols[base].strip(),
                        "param": cols[base + 1].strip() if len(cols) > base + 1 else "",
                        "min": cols[base + 2].strip() if len(cols) > base + 2 else "",
                        "max": cols[base + 3].strip() if len(cols) > base + 3 else "",
                    })
            if mods:
                out.setdefault(name, []).append({"level": level, "mods": mods})
    return out

tp = parse_txt(TP)
ts = parse_txt(TS)

# mod code -> 中文词条
MOD_ZH = {
    "att": "准确率", "pal": "圣骑士技能", "ama": "亚马逊技能", "nec": "死灵法师技能",
    "sor": "法师技能", "bar": "野蛮人技能", "dru": "德鲁伊技能", "asn": "刺客技能",
    "mana": "法力", "manasteal": "法力偷取", "lifesteal": "生命偷取",
    "light": "照亮范围", "str": "力量", "dex": "敏捷", "vit": "活力", "ene": "能量",
    "res-fire": "火焰抗性", "res-cold": "冰冷抗性", "res-ltng": "闪电抗性",
    "res-pois": "毒素抗性", "red-dmg": "伤害减少", "red-mag": "魔法伤害减少",
    "life": "生命", "thorns": "荆棘伤害", "attack": "攻击",
}

aff = json.load(open(AFF, encoding="utf-8"))
cnt = 0
for iid, e in aff.items():
    nm = e["name"]
    variants = ts.get(nm) or tp.get(nm)
    if not variants:
        e["mod"] = None
        continue
    mods = []
    for v in variants:
        for m in v["mods"]:
            zh = MOD_ZH.get(m["code"], m["code"])
            rng = f"{m['min']}-{m['max']}"
            item = {"zh": zh, "code": m["code"], "range": rng}
            if m["param"]:
                item["param"] = m["param"]
            if item not in mods:
                mods.append(item)
    e["mod"] = mods
    cnt += 1

with open(AFF, "w", encoding="utf-8") as f:
    json.dump(aff, f, ensure_ascii=False, indent=1)

print(f"完成：{cnt}/{len(aff)} 条合并 mod 词条")
# 验证四项链1
for iid in (985, 1312, 1051, 742):
    e = aff[str(iid)]
    print(f"id{iid} {e['name']} ({e['name_zh']}) [{e['type']}] -> {e['mod']}")
