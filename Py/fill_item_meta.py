# -*- coding: utf-8 -*-
"""为 item_codes.json 补充物品元数据字段（需要游戏运行，只读内存）。

- type   : items.txt nType → itemtypes.txt szCode（物品类型，如 axe/amul/scro）
- quality: items.txt level（品质等级 qlvl，如暗金/套装物品的等级门槛）
- invw/h : items.txt nInvwidth/nInvheight（占格宽/高，格数）

链路：pItemTypesTxt = [ [D2Common+0x99E1C] + 0xBF8 ]，行宽 0xE4；
      items.txt 行 nType@+0x11E（1 字节索引）。
已有字段不覆盖。
"""
import ctypes, json, os, sys
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
        dt = mem.read_dword(pid, h, mem.resolve_base(pid, "D2Common.dll+0x99E1C"))
        pit = mem.read_dword(pid, h, dt + 0xBF8)
        base = lt.find_itemtxt_base(pid, h)
        if not pit or not base:
            print("itemtypes/items 表定位失败")
            sys.exit(1)

        raw = open(PATH, "rb").read()
        has_bom = raw[:3] == b"\xef\xbb\xbf"
        ic = json.loads(raw.decode("utf-8-sig"))
        added = 0
        for it in ic["items"]:
            tid = it.get("id")
            if tid is None:
                continue
            row = lt.read_item_row(pid, h, base, tid)
            if not row:
                continue
            ntype = row["ntype"]
            tcode = mem.read(pid, h, pit + ntype * 0xE4, 8).split(b"\x00")[0]
            tcode = tcode[:4].decode("latin-1").strip()
            new = {
                "type": tcode,
                "quality": row["qlvl"],
                "invw": row["xsize"],
                "invh": row["ysize"],
            }
            for k, v in new.items():
                if k not in it:
                    it[k] = v
                    added += 1
        text = json.dumps(ic, ensure_ascii=False)
        with open(PATH, "w", encoding="utf-8") as f:
            if has_bom:
                f.write("\ufeff")
            f.write(text)
        print("补充元数据字段 %d 个（itemtypes 表 %#x, 物品表 %#x）" % (added, pit, base))
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


if __name__ == "__main__":
    main()
