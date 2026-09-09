# -*- coding: utf-8 -*-
"""背包物品列表: UnitInventory.pFirstItem -> UnitAny 链表 -> ItemData.pNextInvItem(+0x64)

结构 (d2hackmap d2structs.h):
  pPlayer = [D2CLIENT.DLL+0x11B800]
  pInv    = [pPlayer + 0x60]             UnitInventory: +0C=pFirstItem +10=pLastItem
  物品链表节点 = UnitAny: dwUnitType@+00(=4) dwTxtFileNo@+04 pItemData@+14
  next = [pItemData + 0x64]
  名称 = GetLocaleText(ItemTxt[wTxtFileNo].wLocaleTxtNo)
"""
from __future__ import annotations
import argparse, json, sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from item_name import find_itemtxt_base, find_locale_dispatch, get_locale_text, read_utf16, clean_name, read_item_row

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def iter_inventory_items(pid, h, pInv):
    """遍历背包物品链表, 产出 (unit, type, txt_id, pItemData)。"""
    cur = dword(pid, h, pInv + 0x0C)  # pFirstItem
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        typ = dword(pid, h, cur)
        txt = dword(pid, h, cur + 0x04)
        idat = dword(pid, h, cur + 0x14)
        yield cur, typ, txt, idat
        cur = dword(pid, h, idat + 0x64) if idat else 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print(json.dumps({"ok": False, "error": "D2Loader.exe 未运行"})); return 1
    h = mem.open_process_readonly(pid)
    try:
        d2c = mem.module_base(pid, "D2CLIENT.DLL")
        pPlayer = dword(pid, h, d2c + 0x11B800)
        if not pPlayer:
            print(json.dumps({"ok": False, "error": "人物指针为空"})); return 1
        pInv = dword(pid, h, pPlayer + 0x60)
        stamp = dword(pid, h, pInv)
        if stamp != 0x01020304:
            print(json.dumps({"ok": False, "error": f"背包印章校验失败 stamp={stamp:#x}"})); return 1
        base = find_itemtxt_base(pid, h)
        disp = find_locale_dispatch(pid, h)
        items = []
        for unit, typ, txt, idat in iter_inventory_items(pid, h, pInv):
            name_raw = name_clean = ""
            if base and disp:
                r = read_item_row(pid, h, base, txt)
                if r:
                    ptr = get_locale_text(pid, h, disp, r["locale"])
                    if ptr:
                        name_raw = read_utf16(pid, h, ptr)
                        name_clean = clean_name(name_raw)
            items.append({
                "unit": f"{unit:#x}", "type": typ, "txt_id": txt,
                "code": (read_item_row(pid, h, base, txt) or {}).get("code", "") if base else "",
                "pItemData": f"{idat:#x}", "name": name_raw, "name_clean": name_clean,
            })
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)
    out = {"ok": True, "count": len(items), "items": items}
    if args.json:
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(f"背包物品 {len(items)} 件:")
        for it in items:
            print(f"  txt={it['txt_id']:<4} code={it['code']!r:<28} {it['name_clean']!r}")

if __name__ == "__main__":
    sys.exit(main())
