#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词缀映射：运行时内存枚举（无固化对照表）。

数据源全部来自内存：
  1. 扩展表（[D2Common+0x9FBBC]，1452 行，行宽 0x90）——枚举全部词缀行
     name(行首) / level(+0x24) / min(+0x2C) / max(+0x30) / stat枚举(+0x5C)
  2. tbl 名池——词缀中文名（name_zh）
  3. stat 枚举中文标签——内嵌常量（词缀系统自有枚举，无内存名表，一次性提炼）

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

# ============================================================
# stat 枚举 -> 中文词条（词缀系统自有枚举，一次性提炼自 txt 交叉标注，内嵌固化）
# ============================================================
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
# 词缀名特例：技能系/抗性系细分（词缀名 -> 词条中文, mod code）
NAME_ZH_OVERRIDE = {
    "Monk's": ("圣骑士技能", "pal"), "Slayer's": ("野蛮人技能", "bar"),
    "Garnet": ("火焰抗性", "res-fire"), "of Life": ("生命", "hp"),
    "of the Locust": ("生命偷取", "lifesteal"), "of the Bat": ("法力偷取", "manasteal"),
    "of the Vampire": ("法力偷取", "manasteal"),
    "Snake's": ("法力", "mana"), "Serpent's": ("法力", "mana"),
    "Summoner's": ("圣骑士技能", "pal"),  # anhei mod 实测：Summoner's 词条为圣骑士技能
    "Magekiller's": ("刺客技能", "ass"),
    "Prismatic": ("全抗", "res-all"),
}

# 名池扫描区域（会话地址；重启后按 tbl 加载重取，此处为探查确认值）
POOLS = (0x12800000, 0x12804000, 0x127FE000, 0x1344F000)
POOL_SIZE = 0x9000


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


def enumerate_affixes(pid: int, h: int) -> dict:
    """枚举扩展表全部词缀行 → {id: {row,name,name_zh,type,level,stat,mod}}"""
    sP = table_base(pid, h)
    if not sP:
        return {}
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
        # 词条中文：词缀名特例优先，否则 stat 枚举
        ov = NAME_ZH_OVERRIDE.get(name)
        if ov:
            zh, code = ov
        else:
            zh = STAT_ZH.get(stat, "?")
            code = STAT_CODE.get(stat, "?")
        aff[str(rid)] = {
            "row": rid,
            "name": name,
            "name_zh": en2zh.get(name, ""),
            "type": "S" if name.startswith("of ") else "P",
            "level": lvl,
            "stat": stat,
            "mod": {"zh": zh, "code": code, "min": mn, "max": mx},
        }
    return aff


def main() -> None:
    ap = argparse.ArgumentParser(description="词缀映射：运行时内存枚举")
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
