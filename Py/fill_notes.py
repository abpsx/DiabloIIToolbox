# -*- coding: utf-8 -*-
"""补齐 special_names.notes 中的空值（zh 为空/空格）。

空值条目均为暗金物品：按 unique_items 的 name(desc) 找 wloc，
GetLocaleText(wloc) 取中文，只填空不覆盖已有条目。
"""
import ctypes, json, os, sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

ROOT = r"C:\Users\abps\Desktop\DiabloIIToolbox"
SN = os.path.join(ROOT, "Setting", "memory", "special_names.json")


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
        disp = lt.find_locale_dispatch(pid, h)
        if not disp:
            print("locale dispatch 定位失败")
            sys.exit(1)
        sn = json.load(open(SN, encoding="utf-8"))
        notes = sn.get("notes", {})
        uni = sn.get("unique_items", {})
        # name(desc) → wloc
        name_wloc = {v.get("name"): v.get("wloc") for v in uni.values() if v.get("wloc")}
        empty = [k for k, v in notes.items() if not (v or "").strip()]
        filled, still = 0, []
        for k in empty:
            wloc = name_wloc.get(k)
            if wloc is None:
                still.append((k, "无 unique 条目"))
                continue
            ptr = lt.get_locale_text(pid, h, disp, wloc)
            if not ptr:
                still.append((k, "GetLocaleText 失败"))
                continue
            txt = lt.clean_name(lt.read_utf16(pid, h, ptr, 128)).strip()
            if not txt:
                still.append((k, "文本为空"))
                continue
            notes[k] = txt
            filled += 1
        with open(SN, "w", encoding="utf-8") as f:
            json.dump(sn, f, ensure_ascii=False, indent=1)
        print("补齐 %d 条, 仍空 %d 条" % (filled, len(still)))
        for k, why in still[:20]:
            print("  %r: %s" % (k, why))
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


if __name__ == "__main__":
    main()
