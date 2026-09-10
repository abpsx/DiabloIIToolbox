# -*- coding: utf-8 -*-
"""生成全部对照字典 json → temp\\（数据源：Setting\\memory\\*.json）。

产物（均为查询友好字典）：
  dict_item_codes.json   物品码表: items(唯一列表{id,code,name,name_raw}) +
                        by_id("330"→items下标) + by_code("lrg"→items下标) 键值对索引
  dict_set_items.json    套装部件: by_index(行号→原样) + by_code(缩写→列表)
  dict_unique_items.json 暗金表:   by_index(行号→原样) + by_code(缩写→列表, 过滤空code占位行)
  dict_set_names.json    套装组名: {英文: 中文}
  dict_notes.json        注释池:   {英文: 中文}
"""
import json, os, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Setting", "memory")
OUT = os.path.join(ROOT, "temp")
os.makedirs(OUT, exist_ok=True)


def load(name: str):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return json.load(f)


def clean(s: str) -> str:
    return (s or "").strip()


def main() -> None:
    # special_names 一次读取共享（dict_set_items / dict_unique_items / dict_set_names / dict_notes）
    sn = load("special_names.json")

    # ---- 1. 物品码表（索引指向 items 下标，键值对瘦身） ----
    ic = load("item_codes.json")
    items, by_id, by_code = [], {}, {}
    type_map: dict[str, str] = {}
    for it in ic["items"]:
        cid, code = it.get("id"), it.get("code")
        if cid is None or not code:
            continue
        idx = len(items)  # 该条在 items 中的位置
        items.append({
            "id": cid, "code": code,
            "name": it.get("name_clean") or it.get("name", ""),
            "name_raw": it.get("name_raw", ""),
            "type": it.get("type"),          # itemtypes 行索引（数字）
            "invw": it.get("invw"), "invh": it.get("invh"),  # 占格宽/高
        })
        by_id[str(cid)] = idx
        by_code.setdefault(code, idx)
        # type → type_code 映射表（itemtypes 行索引 → 类型 code 字符串）
        t = it.get("type")
        tc = (it.get("type_code") or "").strip()
        if t is not None and tc and str(t) not in type_map:
            type_map[str(t)] = tc
    dump("dict_item_codes.json", {"items": items, "by_id": by_id, "by_code": by_code})
    print("dict_item_codes: items=%d by_id=%d by_code=%d" % (len(items), len(by_id), len(by_code)))
    dump("dict_item_types.json", type_map)
    print("dict_item_types: %d" % len(type_map))
    # type → 中文含义（按各 type 实际代表物品归纳；tpot=投掷药剂/gem*=宝石系列）
    dump("dict_item_types_CN.json", TYPE_CN)
    print("dict_item_types_CN: %d" % len(TYPE_CN))

    # ---- 2. 套装部件（顶层 code → 条目列表，无需双索引容器） ----
    si = sn.get("set_items", {})
    set_items: dict[str, list] = {}
    for k, v in si.items():
        c = clean(v.get("code"))
        if c:
            # index=行号(dwIndex, 游戏内 dwFileIndex 直接索引); wloc=名称唯一文本号
            set_items.setdefault(c, []).append(
                {"index": k, "set_idx": v.get("set_idx"), "desc": v.get("desc"),
                 "wloc": v.get("wloc"), "zh": v.get("zh", "")})
    dump("dict_set_items.json", set_items)
    print("dict_set_items: %d code" % len(set_items))

    # ---- 3. 暗金表 ----
    ui = sn.get("unique_items", {})
    ui_idx, ui_code = {}, {}
    for k, v in ui.items():
        ui_idx[k] = v
        c = clean(v.get("code"))
        if c:  # 过滤 "Elite Uniques"/"Rings"/空 等占位行
            ui_code.setdefault(c, []).append(
                {"index": k, "name": v.get("name"), "wloc": v.get("wloc"), "zh": v.get("zh", "")})
    dump("dict_unique_items.json", {"by_index": ui_idx, "by_code": ui_code})
    print("dict_unique_items: by_index=%d by_code=%d(过滤占位行)" % (len(ui_idx), len(ui_code)))

    # ---- 4. 套装组名 ----
    set_names = {en: zh for en, zh in sn.get("set_names", [])}
    dump("dict_set_names.json", set_names)
    print("dict_set_names: %d" % len(set_names))

    # ---- 5. 注释池 ----
    notes = dict(sn.get("notes", {}))
    dump("dict_notes.json", notes)
    print("dict_notes: %d" % len(notes))


# type（itemtypes 行索引）→ 中文含义（按各 type 实际代表物品归纳）
TYPE_CN = {
    "2": "盾", "3": "盔甲", "4": "金币", "5": "箭矢", "6": "弩箭",
    "7": "耳朵", "8": "草药", "10": "戒指", "11": "药剂", "12": "项链",
    "15": "靴子", "16": "手套", "18": "书", "19": "腰带", "21": "火炬",
    "22": "卷轴", "24": "权杖", "25": "法杖", "26": "长杖", "27": "弓",
    "28": "斧", "29": "棍棒", "30": "剑", "31": "锤", "32": "匕首",
    "33": "长矛", "34": "长柄武器", "35": "弩", "36": "钉锤", "37": "头盔",
    "38": "投掷药剂", "39": "任务物品", "40": "器官", "41": "钥匙",
    "42": "投掷匕首", "43": "投掷斧", "44": "标枪", "58": "珠宝",
    "67": "腕刃", "68": "宝珠", "69": "死灵头", "70": "圣骑盾", "71": "蛮人头盔",
    "72": "德鲁伊头", "74": "符文", "75": "头环", "76": "生命药剂",
    "77": "法力药剂", "78": "回复药剂", "79": "体力药剂", "80": "解毒药剂",
    "81": "融解药剂", "82": "小护身符", "83": "中护身符", "84": "大护身符",
    "85": "亚马逊弓", "86": "亚马逊长矛", "87": "亚马逊标枪", "88": "近身刃",
    "96": "紫宝石", "97": "钻石", "98": "绿宝石", "99": "红宝石",
    "100": "蓝宝石", "101": "黄宝石", "102": "骷髅", "103": "符石收纳器",
}


def dump(name: str, obj) -> None:
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("  写出 %s (%.1f KB)" % (name, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
