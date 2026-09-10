#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词缀映射：运行时内存枚举（纯内存链路，词条中文来自 tbl 描述池）。

数据源全部来自内存：
  1. 扩展表（[D2Common+0x9FBBC]，1452 行，行宽 0x90）——枚举全部词缀行
     name(行首) / level(+0x24) / min(+0x2C) / max(+0x30) / stat枚举(+0x5C)
     / 技能组(+0x64 高16位)
  2. tbl 名池——词缀中文名（name_zh）
  3. tbl 描述池（temp\\dict_tbl_modstr.json，由 _tbl_dump.py 生成）——词条中文描述
     stat → 描述 key 映射见 STAT_KEY；技能组 → 描述 key 见 GROUP_KEY

用法：
  python affix_enumerate.py            # 枚举并打印统计
  python affix_enumerate.py --dump 20  # 打印前 N 行
  python affix_enumerate.py --ids 985,1312,1051,742   # 查指定词缀
"""
from __future__ import annotations

import argparse
import json
import re
import sys

sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

TBL_MODSTR = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_tbl_modstr.json"

# ============================================================
# stat 枚举 -> tbl 描述池 key（词条中文来自 tbl，非 txt）
# ============================================================
STAT_KEY = {
    110: "ModStr1h",       # 攻击准确率 (AR)
    112: "ModStr3f",       # 照亮范围 (Light Radius)
    304: "strModAllResistances",  # 所有抗性+%d
    27: "ModStr2z",        # 生命于击中时偷取 (LL)
    28: "ModStr2y",        # 法力于击中时偷取 (LM)
    18: "ModStr4p",        # 快速打击恢复 (FHR)
    44: "ItemExpansiveChancX",  # 攻击时有 %d%% 机会施展等级 %d %s
}
# 技能组（+0x64 高16位）-> 描述池 key
# 锚点实测：0xFF02(Summoner's) 盾牌=圣骑士技能、0xFF03(Monk's) 项链=圣骑士技能
# 其余组（ama/sor/bar）按原版职业对应；0xFF05/0xFF06(dru/ass) anhei tbl 无描述，待实测
GROUP_KEY = {
    0xFF00: "ModStr3a",  # 亚马逊技能等级
    0xFF01: "ModStr3d",  # 法师技能等级
    0xFF02: "ModStr3b",  # 圣骑士技能等级（anhei 实测）
    0xFF03: "ModStr3b",  # 圣骑士技能等级
    0xFF04: "ModStr3e",  # 野蛮人技能等级
    0xFF05: None,        # anhei tbl 无德鲁伊描述
    0xFF06: None,        # anhei tbl 无刺客描述
}
GROUP_ORIG = {  # 组原版职业（标注用）
    0xFF00: "ama", 0xFF01: "sor", 0xFF02: "nec", 0xFF03: "pal",
    0xFF04: "bar", 0xFF05: "dru", 0xFF06: "ass",
}

# fallback（描述池缺 key 时）：stat 枚举 -> 中文
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
    110: "准确率", 111: "准确率", 112: "照亮范围", 113: "恐吓", 114: "魔法装备加成",
    115: "法力", 116: "全抗", 117: "元素抗性", 118: "火焰抗性", 119: "闪电抗性",
    120: "毒素抗性", 121: "冰冷抗性", 122: "火焰抗性", 123: "对恶魔伤害", 124: "毒素抗性",
    125: "职业技能", 126: "圣骑士技能", 127: "死灵技能", 128: "法师技能", 129: "野蛮人技能",
    132: "击杀回蓝", 137: "冰冷伤害", 138: "火焰伤害", 139: "闪电伤害", 140: "毒素伤害",
    141: "可堆叠", 142: "对不死伤害",
    300: "技能页", 301: "技能页", 302: "技能页", 303: "属性加成", 304: "全抗", 305: "毒素伤害",
}
STAT_CODE = {
    1: "red-dmg", 2: "red-mag", 3: "abs", 4: "dmg-ac", 5: "thorns", 6: "swing",
    7: "swing", 8: "block", 9: "cold", 10: "cold", 11: "fire", 12: "fire",
    13: "ltng", 14: "dmg-max", 15: "dmg-min", 16: "dmg-pois", 17: "dex",
    18: "balance", 19: "regen", 20: "noheal", 21: "gold%", 22: "mag%",
    23: "enr", 24: "mana", 25: "light", 26: "hp", 27: "lifesteal", 28: "manasteal",
    29: "res-pois-len", 30: "res-pois-len", 31: "str", 32: "ease", 34: "str",
    35: "move", 37: "rep-dur", 39: "rep-quant", 41: "hp/lvl", 42: "str/lvl",
    43: "res/lvl", 44: "charged", 45: "ac/time", 101: "ac", 102: "red-mag",
    103: "dmg-min", 104: "dmg-max", 105: "dmg%", 106: "dmg%", 107: "dmg-to-mana",
    108: "regen-stam", 109: "stam", 110: "att", 111: "att", 112: "light", 113: "howl",
    114: "mag%", 115: "mana", 116: "res-all", 117: "res-cold", 118: "res-fire",
    119: "res-ltng", 120: "res-pois", 121: "res-cold", 122: "res-fire",
    123: "dmg-demon", 124: "res-pois", 125: "skilltab", 126: "pal", 127: "nec",
    128: "sor", 129: "bar", 132: "mana-kill", 137: "cold", 138: "fire",
    139: "ltng", 140: "dmg-pois", 141: "stack", 142: "dmg-undead",
}

# 名池扫描区域（会话地址；重启后按 tbl 加载重取，此处为探查确认值）
POOLS = (0x12800000, 0x12804000, 0x127FE000, 0x1344F000)
POOL_SIZE = 0x9000

_COL = re.compile(r"\xffc[0-9a-zA-Z;]")


def clean(s: str) -> str:
    return _COL.sub("", s).strip()


def scan_names(pid: int, h: int, beg: int, size: int) -> dict:
    """扫描 tbl 名池：UTF-8 `英文\0中文\0` 交错 → en->zh"""
    m = {}
    raw = b""
    a = beg
    while a < beg + size:
        chunk = mr.read(pid, h, a, min(0x2000, beg + size - a))
        if not chunk:
            break
        raw += chunk
        a += 0x2000
    pos = 0
    while pos < len(raw) - 8:
        i = raw.find(b"\x00", pos)
        if i < 0:
            break
        en = raw[pos:i]
        try:
            en_s = en.decode("utf-8")
        except Exception:
            pos = i + 1
            continue
        if not en_s or len(en_s) > 64 or not re.match(r"^[\x20-\x7e]+$", en_s):
            pos = i + 1
            continue
        j = raw.find(b"\x00", i + 1)
        if j < 0:
            break
        zh = raw[i + 1:j]
        try:
            zh_s = zh.decode("utf-8")
        except Exception:
            pos = i + 1
            continue
        if zh_s and len(zh_s) <= 32 and not re.match(r"^[\x20-\x7e]+$", zh_s):
            m.setdefault(en_s, zh_s)
        pos = j + 1
    return m


def table_base(pid: int, h: int) -> int | None:
    """扩展表地址：模块偏移现取，不硬编码会话地址。"""
    d2c = mr.module_base(pid, "D2Common.dll")
    if d2c is None:
        return None
    return mr.read_ptr(pid, h, d2c + 0x9FBBC)


def load_desc_pool() -> dict:
    """加载 tbl 描述池（_tbl_dump.py 生成；游戏重启后重跑一次即可）"""
    try:
        with open(TBL_MODSTR, encoding="utf-8") as f:
            return json.load(f).get("items", {})
    except Exception:
        return {}


def enumerate_affixes(pid: int, h: int) -> dict:
    """枚举扩展表全部词缀行 → {id: {row,name,name_zh,type,level,stat,mod}}"""
    sP = table_base(pid, h)
    if not sP:
        return {}
    pool = load_desc_pool()
    en2zh = {}
    for beg in POOLS:
        en2zh.update(scan_names(pid, h, beg, POOL_SIZE))
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
        stat = mr.read_value(pid, h, b + 0x5C, "word")
        lvl = mr.read_value(pid, h, b + 0x24, "word")
        mn = mr.read_value(pid, h, b + 0x2C, "word")
        mx = mr.read_value(pid, h, b + 0x30, "word")
        grp = mr.read_value(pid, h, b + 0x64, "dword") >> 16
        # 词条中文：技能类按组查描述池；否则按 stat 查描述池；fallback STAT_ZH
        code = STAT_CODE.get(stat, "?")
        if stat == 125 and grp in GROUP_KEY:
            key = GROUP_KEY[grp]
            zh = clean(pool.get(key, "")) if key else ""
            if not zh:
                zh = f"技能({GROUP_ORIG.get(grp, '?')}组待确认)"
            code = "skilltab+" + GROUP_ORIG.get(grp, "?")
        else:
            key = STAT_KEY.get(stat)
            zh = clean(pool.get(key, "")) if key else STAT_ZH.get(stat, "?")
            if not zh:
                zh = STAT_ZH.get(stat, "?")
        aff[str(rid)] = {
            "row": rid,
            "name": name,
            "name_zh": en2zh.get(name, ""),
            "type": "S" if name.startswith("of ") else "P",
            "level": lvl,
            "stat": stat,
            "grp": grp,
            "mod": {"zh": zh, "code": code, "min": mn, "max": mx},
        }
    return aff


def main() -> None:
    ap = argparse.ArgumentParser(description="词缀映射：运行时内存枚举（词条来自 tbl 描述池）")
    ap.add_argument("--dump", type=int, default=0, help="打印前 N 行")
    ap.add_argument("--ids", type=str, default="", help="查指定词缀 id，逗号分隔")
    ap.add_argument("--out", type=str, default="", help="写 JSON 文件（可选）")
    args = ap.parse_args()

    pid = mr.find_process("D2Loader.exe")
    if pid is None:
        print(json.dumps({"ok": False, "error": "D2Loader.exe 未运行"}))
        sys.exit(1)
    h = mr.open_process_readonly(pid)
    if not h:
        print(json.dumps({"ok": False, "error": "OpenProcess 失败"}))
        sys.exit(1)
    try:
        aff = enumerate_affixes(pid, h)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(aff, f, ensure_ascii=False, indent=1)
    print(f"枚举 {len(aff)} 条词缀")
    if args.dump:
        for i, (iid, e) in enumerate(aff.items()):
            if i >= args.dump:
                break
            print(f"  id{iid} {e['name']:16s} {e['name_zh']:8s} [{e['type']}] lvl{e['level']:3d} "
                  f"{e['mod']['zh']} {e['mod']['min']}-{e['mod']['max']}")
    if args.ids:
        for iid in [x.strip() for x in args.ids.split(",") if x.strip()]:
            e = aff.get(iid)
            if e:
                print(f"  id{iid} {e['name']} ({e['name_zh']}) [{e['type']}] lvl{e['level']} "
                      f"{e['mod']['zh']} ({e['mod']['code']}) {e['mod']['min']}-{e['mod']['max']}")
            else:
                print(f"  id{iid} 未找到")


if __name__ == "__main__":
    sys.exit(main())
