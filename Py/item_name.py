# -*- coding: utf-8 -*-
"""TXT id → 物品名 全自动解析器（1.13c mod，只读内存）

用法:
  python item_name.py 679 713 529 530 63 --json
"""
from __future__ import annotations
import argparse, json, sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from locale_text import (find_itemtxt_base, find_locale_dispatch, get_locale_text,
                         read_utf16, clean_name, read_item_row)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", type=lambda s: int(s, 0), nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print(json.dumps({"ok": False, "error": "D2Loader.exe 未运行"})); return 1
    h = mem.open_process_readonly(pid)
    try:
        base = find_itemtxt_base(pid, h)
        if not base:
            print(json.dumps({"ok": False, "error": "ItemTxt 表基定位失败"})); return 1
        disp = find_locale_dispatch(pid, h)
        rows = []
        for i in args.ids:
            r = read_item_row(pid, h, base, i)
            if not r:
                continue
            raw_name = ""
            if disp:
                ptr = get_locale_text(pid, h, disp, r["locale"])
                if ptr:
                    raw_name = read_utf16(pid, h, ptr)
            r["name"] = raw_name
            r["name_clean"] = clean_name(raw_name)
            rows.append(r)
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)
    out = {"ok": True, "table_base": f"{base:#x}", "rows": rows}
    if args.json:
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(f"ItemTxt 表基: {base:#x}  D2Lang 分派: {disp and 'OK'}\n")
        for r in rows:
            print(f"TXT:{r['txt_id']}  code={r['code']!r}  locale={r['locale']}  nType={r['ntype']}")
            print(f"    name={r['name']!r}")
            print(f"    clean={r['name_clean']!r}")

if __name__ == "__main__":
    sys.exit(main())
