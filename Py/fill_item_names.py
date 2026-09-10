# -*- coding: utf-8 -*-
"""补齐 item_codes.json 的物品名（GetLocaleText 全链路）。

历史背景：item_codes.json 早期由明文池 dump（搜 "code\\0" → UTF-8 全称），
mod 新增物品（pr 前缀钥匙/星座、cm11+ 圣符、药水系 mod 文本）不在明文池，
name 为空。本脚本对条目逐个走
  ItemTxt[dwTxtFileNo].wLocaleTxtNo → GetLocaleText（扩展表/主表）补齐：
- 空 name 条目：写 name/name_clean（完整多行清洗文本，保留换行/星号）
- 全量条目：补 name_raw（原始 UTF-16 文本，含色码/换行，不覆盖已有）
"""
import json, os, sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

ROOT = r"C:\Users\abps\Desktop\DiabloIIToolbox"
PATH = os.path.join(ROOT, "Setting", "memory", "item_codes.json")


def main() -> None:
    pid = mem.find_process("D2Loader.exe")
    if pid is None:
        print("D2Loader.exe 未运行")
        sys.exit(1)
    h = mem.open_process_readonly(pid)
    if not h:
        print("OpenProcess 失败")
        sys.exit(1)
    try:
        raw = open(PATH, "rb").read()
        has_bom = raw[:3] == b"\xef\xbb\xbf"
        ic = json.loads(raw.decode("utf-8-sig"))
        filled = raw_added = 0
        for it in ic["items"]:
            tid = it.get("id")
            if tid is None:
                continue
            name, raw_txt, row = lt.txt_to_name_full(pid, h, tid)
            if not raw_txt:
                continue
            if "name_raw" not in it:
                it["name_raw"] = raw_txt
                raw_added += 1
            if name and name != it.get("name"):
                it["name"] = name
                it["name_clean"] = name
                filled += 1
        text = json.dumps(ic, ensure_ascii=False)
        with open(PATH, "w", encoding="utf-8") as f:
            if has_bom:
                f.write("\ufeff")
            f.write(text)
        print("补齐 name %d 条，新增 name_raw %d 条（源文件 %sBOM）" %
              (filled, raw_added, "含" if has_bom else "无"))
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)


if __name__ == "__main__":
    main()
