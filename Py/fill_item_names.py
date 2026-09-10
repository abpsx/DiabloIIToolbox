# -*- coding: utf-8 -*-
"""补齐 item_codes.json 中 name 为空的 mod 物品名（GetLocaleText 全链路）。

历史背景：item_codes.json 早期由明文池 dump（搜 "code\\0" → UTF-8 全称），
mod 新增物品（pr 前缀钥匙/星座、cm11+ 圣符、药水系 mod 文本）不在明文池，
name 为空。本脚本对空 name 条目逐个走
  ItemTxt[dwTxtFileNo].wLocaleTxtNo → GetLocaleText（扩展表/主表）
补齐 name/name_clean。只填空，不覆盖已有。
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
        filled = 0
        for it in ic["items"]:
            if (it.get("name") or "").strip():
                continue
            tid = it.get("id")
            if tid is None:
                continue
            name, row = lt.txt_to_name(pid, h, tid)
            if name:
                it["name"] = name
                it["name_clean"] = name
                filled += 1
        text = json.dumps(ic, ensure_ascii=False)
        with open(PATH, "w", encoding="utf-8") as f:
            if has_bom:
                f.write("\ufeff")
            f.write(text)
        print("已补齐 %d 条（源文件 %sBOM）" % (filled, "含" if has_bom else "无"))
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)


if __name__ == "__main__":
    main()
