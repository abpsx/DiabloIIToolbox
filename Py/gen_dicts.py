# -*- coding: utf-8 -*-
"""生成全部对照字典 json → temp\\（数据源：Setting\\memory\\*.json）。

产物（均为查询友好字典）：
  dict_item_codes.json   物品码表: items(唯一列表{id,code,name,name_raw}) +
                        by_id(物品码→{code}) + by_code(缩写→{id}) 纯索引瘦身
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
    # ---- 1. 物品码表（瘦身索引：数据只存一份 items，by_id/by_code 仅映射） ----
    ic = load("item_codes.json")
    items, by_id, by_code = [], {}, {}
    for it in ic["items"]:
        cid, code = it.get("id"), it.get("code")
        if cid is None or not code:
            continue
        items.append({
            "id": cid, "code": code,
            "name": it.get("name_clean") or it.get("name", ""),
            "name_raw": it.get("name_raw", ""),
        })
        by_id[str(cid)] = {"code": code}
        by_code.setdefault(code, {"id": cid})
    dump("dict_item_codes.json", {"items": items, "by_id": by_id, "by_code": by_code})
    print("dict_item_codes: items=%d by_id=%d by_code=%d" % (len(items), len(by_id), len(by_code)))

    # ---- 2. 套装部件 ----
    sn = load("special_names.json")
    si = sn.get("set_items", {})
    si_idx, si_code = {}, {}
    for k, v in si.items():
        si_idx[k] = v
        c = clean(v.get("code"))
        if c:
            # index=行号(dwIndex, 游戏内 dwFileIndex 直接索引); wloc=名称唯一文本号
            si_code.setdefault(c, []).append(
                {"index": k, "set_idx": v.get("set_idx"), "desc": v.get("desc"),
                 "wloc": v.get("wloc"), "zh": v.get("zh", "")})
    dump("dict_set_items.json", {"by_index": si_idx, "by_code": si_code})
    print("dict_set_items: by_index=%d by_code=%d(去空code后)" % (len(si_idx), len(si_code)))

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


def dump(name: str, obj) -> None:
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("  写出 %s (%.1f KB)" % (name, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()
