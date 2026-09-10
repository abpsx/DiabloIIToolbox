#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词缀数据源内存化：
- 扩展表行（内存）：name/level/min/max/stat枚举 = 数据源
- txt 仅用于 stat 枚举 -> 中文词条 的一次性标签（生成 dict_magic_stat.json）
- 重新生成 dict_magic_affixes.json：mod 字段从内存行读取
"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC

def w(a): return mr.read_value(pid, h, a, "word")

# ---------- stat 枚举 -> 中文词条（txt 交叉标注 + 手工整理） ----------
STAT_ZH = {
    1: "伤害减少", 2: "魔法伤害减少", 3: "元素伤害吸收", 4: "对远程防御", 5: "反伤",
    6: "攻击速度", 7: "攻击/格挡速度", 8: "格挡几率", 9: "冰冷伤害", 10: "冰冷伤害",
    11: "火焰伤害", 12: "火焰伤害", 13: "闪电伤害", 14: "最大伤害", 15: "最小伤害",
    16: "毒素伤害", 17: "敏捷", 18: "打击恢复", 19: "生命回复", 20: "禁止回复",
    21: "金币加成", 22: "魔法装备加成", 23: "能量", 24: "法力", 25: "照亮范围",
    26: "生命", 27: "生命偷取", 28: "法力偷取", 29: "抗毒时长", 30: "抗毒时长",
    31: "力量", 32: "需求降低", 34: "力量", 35: "移动速度", 37: "耐久回复",
    39: "数量回复", 41: "每级生命", 42: "每级属性", 43: "每级抗性", 44: "技能充能",
    45: "防御提升", 101: "防御", 102: "魔法伤害减少", 103: "最小伤害", 104: "最大伤害",
    105: "伤害加成", 106: "伤害加成", 107: "伤害转法力", 108: "耐力回复", 109: "耐力",
    110: "准确率", 111: "准确率", 112: "准确率", 113: "恐吓", 114: "魔法装备加成",
    115: "法力", 116: "全抗", 117: "元素抗性", 118: "火焰抗性", 119: "闪电抗性",
    120: "毒素抗性", 121: "冰冷抗性", 122: "火焰抗性", 123: "对恶魔伤害", 124: "毒素抗性",
    125: "职业技能", 126: "圣骑士技能", 127: "死灵技能", 128: "法师技能", 129: "野蛮人技能",
    132: "击杀回蓝", 137: "冰冷伤害", 138: "火焰伤害", 139: "闪电伤害", 140: "毒素伤害",
    141: "可堆叠", 142: "对不死伤害",
    300: "技能页", 301: "技能页", 302: "技能页", 303: "属性加成", 304: "属性加成", 305: "毒素伤害",
}
STAT_CODE = {  # txt mod code 标签
    1: "red-dmg", 2: "red-mag", 3: "abs", 4: "dmg-ac", 5: "thorns", 6: "swing",
    7: "swing", 8: "block", 9: "cold", 10: "cold", 11: "fire", 12: "fire",
    13: "ltng", 14: "dmg-max", 15: "dmg-min", 16: "dmg-pois", 17: "dex",
    18: "balance", 19: "regen", 20: "noheal", 21: "gold%", 22: "mag%",
    23: "enr", 24: "mana", 25: "light", 26: "hp", 27: "lifesteal", 28: "manasteal",
    29: "res-pois-len", 30: "res-pois-len", 31: "str", 32: "ease", 34: "str",
    35: "move", 37: "rep-dur", 39: "rep-quant", 41: "hp/lvl", 42: "str/lvl",
    43: "res/lvl", 44: "charged", 45: "ac/time", 101: "ac", 102: "red-mag",
    103: "dmg-min", 104: "dmg-max", 105: "dmg%", 106: "dmg%", 107: "dmg-to-mana",
    108: "regen-stam", 109: "stam", 110: "att", 111: "att", 112: "att", 113: "howl",
    114: "mag%", 115: "mana", 116: "res-all", 117: "res-cold", 118: "res-fire",
    119: "res-ltng", 120: "res-pois", 121: "res-cold", 122: "res-fire",
    123: "dmg-demon", 124: "res-pois", 125: "skilltab", 126: "pal", 127: "nec",
    128: "sor", 129: "bar", 132: "mana-kill", 137: "cold", 138: "fire",
    139: "ltng", 140: "dmg-pois", 141: "stack", 142: "dmg-undead",
}

# ---------- txt 特例：name -> mod code（精确标注，仅用于 stat 标签细化） ----------
def parse_txt_codes(path):
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            cols = line.rstrip().split("\t")
            if i == 1 or not cols[0].strip():
                continue
            codes = set()
            for mi in range(1, 4):
                base = 13 + (mi - 1) * 4
                if len(cols) > base and cols[base].strip():
                    codes.add(cols[base].strip())
            if codes:
                out.setdefault(cols[0].strip(), set()).update(codes)
    return out

tp = parse_txt_codes(r"G:\game\diablo 2\tool\bin2txt\template\MagicPrefix.txt")
ts = parse_txt_codes(r"G:\game\diablo 2\tool\bin2txt\template\MagicSuffix.txt")
name_codes = {**tp, **ts}
for k, v in tp.items():
    name_codes.setdefault(k, set()).update(v)

# mod code 细化中文（用于 name 特例）
CODE_ZH = {
    "att": "准确率", "pal": "圣骑士技能", "ama": "亚马逊技能", "nec": "死灵技能",
    "sor": "法师技能", "bar": "野蛮人技能", "dru": "德鲁伊技能", "asn": "刺客技能",
    "mana": "法力", "manasteal": "法力偷取", "lifesteal": "生命偷取",
    "light": "照亮范围", "str": "力量", "dex": "敏捷", "vit": "活力", "ene": "能量",
    "res-fire": "火焰抗性", "res-cold": "冰冷抗性", "res-ltng": "闪电抗性",
    "res-pois": "毒素抗性", "res-all": "全抗", "red-dmg": "伤害减少",
    "red-mag": "魔法伤害减少", "life": "生命", "hp": "生命", "dmg-min": "最小伤害",
    "dmg-max": "最大伤害", "dmg%": "伤害加成", "ac": "防御", "ac%": "防御加成",
    "thorns": "反伤", "skilltab": "技能页", "charged": "技能充能", "swing1": "攻速",
    "swing2": "攻速", "balance1": "打击恢复", "block": "格挡", "cast1": "施法速度",
    "move1": "移动速度", "gold%": "金币加成", "mag%": "魔法装备加成",
    "ease": "需求降低", "stam": "耐力", "regen": "生命回复", "knock": "击退",
    "sock": "凹槽", "cold": "冰冷伤害", "fire": "火焰伤害", "ltng": "闪电伤害",
    "dmg-pois": "毒素伤害", "pois-len": "毒素持续", "dmg-ac": "对远程防御",
}

# ---------- 读全部行，生成 affixes ----------
aff = {}
for rid in range(1452):
    b = sP + rid * 0x90
    raw = mr.read(pid, h, b, 0x90)
    nm = raw.split(b"\x00")[0]
    try:
        name = nm.decode("utf-8")
    except Exception:
        name = ""
    if not name:
        continue
    stat = w(b + 0x5C)
    lvl = w(b + 0x24)
    mn = w(b + 0x2C)
    mx = w(b + 0x30)
    # 词条中文：name 特例优先（技能系/抗性系细化），否则 stat 枚举
    codes = name_codes.get(name)
    zh = STAT_ZH.get(stat, "?")
    code = STAT_CODE.get(stat, "?")
    if codes:
        c0 = sorted(codes)[0]
        if c0 in CODE_ZH:
            zh = CODE_ZH[c0]
            code = c0
    aff[str(rid)] = {
        "row": rid,
        "name": name,
        "name_zh": "",  # 名池中文后续合并
        "type": "S" if name.startswith("of ") else "P",
        "level": lvl,
        "stat": stat,
        "mod": {
            "zh": zh,
            "code": code,
            "min": mn,
            "max": mx,
        },
    }

with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_stat.json", "w", encoding="utf-8") as f:
    json.dump({"stat_zh": {str(k): v for k, v in STAT_ZH.items()},
               "stat_code": {str(k): v for k, v in STAT_CODE.items()},
               "code_zh": CODE_ZH}, f, ensure_ascii=False, indent=1)

with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_affixes.json", "w", encoding="utf-8") as f:
    json.dump(aff, f, ensure_ascii=False, indent=1)

print(f"生成 {len(aff)} 条（内存源）")
for iid in (985, 1312, 1051, 742, 1121, 1326, 744, 363, 118, 374, 117):
    e = aff.get(str(iid))
    if e:
        print(f"id{iid} {e['name']:16s} lvl{e['level']:3d} stat{e['stat']:3d} {e['mod']['zh']} ({e['mod']['code']}) {e['mod']['min']}-{e['mod']['max']}")
