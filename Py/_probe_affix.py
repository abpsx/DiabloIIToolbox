#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探查：装备戒指的词缀字段（临时脚本）。

物品结构 ItemData：wMagicPrefix[3] @ +0x38、wMagicSuffix[3] @ +0x3E（WORD）。
遍历 pFirstItem 链，筛装备(loc69==3)，打印 code / 词缀 / idat 前 0x50 字节。
"""
import json
import sys

sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

CONFIG_DIR = r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory"


def main() -> None:
    pid = mr.find_process("D2Loader.exe")
    if pid is None:
        print("D2Loader 未运行")
        return
    h = mr.open_process_readonly(pid)
    if not h:
        print("OpenProcess 失败")
        return
    try:
        base = mr.resolve_base(pid, "D2CLIENT.dll+0x11B800")
        unit = mr.read_ptr(pid, h, base)
        pInv = mr.read_ptr(pid, h, unit + 0x60)
        print(f"pInv = 0x{pInv:X}")
        if mr.read_dword(pid, h, pInv) != 0x01020304:
            print("印章校验失败")
            return
        code_map = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json",
                                  encoding="utf-8"))
        # item_codes.json 结构：items? 找 code 索引
        if isinstance(code_map, dict) and "items" in code_map:
            items = code_map["items"]
            by_id = {int(k): v for k, v in code_map.get("by_id", {}).items()}
        else:
            items = code_map
            by_id = {}
        cur = mr.read_ptr(pid, h, pInv + 0x0C)
        seen = set()
        equip = []
        while cur and cur not in seen:
            seen.add(cur)
            txt = mr.read_dword(pid, h, cur + 0x04)
            idat = mr.read_ptr(pid, h, cur + 0x14)
            if idat:
                raw69 = mr.read(pid, h, idat + 0x69, 1)
                loc69 = raw69[0] if raw69 else -1
                if loc69 == 3:  # 装备
                    def w(a):
                        r = mr.read(pid, h, a, 2)
                        return int.from_bytes(r, "little") if r else 0
                    pref = [w(idat + 0x38 + i * 2) for i in range(3)]
                    suff = [w(idat + 0x3E + i * 2) for i in range(3)]
                    code = ""
                    if by_id:
                        code = by_id.get(txt, {}).get("code", "") if isinstance(by_id.get(txt), dict) else ""
                    elif isinstance(items, dict):
                        for k, v in items.items():
                            if isinstance(v, dict) and v.get("id") == txt:
                                code = v.get("code", "")
                                break
                    hex0 = mr.read(pid, h, idat, 0x50)
                    equip.append((code, pref, suff, cur, idat, hex0))
            cur = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
        print(f"装备物品 {len(equip)} 件：")
        for code, pref, suff, cur, idat, hex0 in equip:
            mark = "  <<< 戒指" if code == "rin" else ""
            print(f"  cur=0x{cur:X} idat=0x{idat:X} code={code} prefix={pref} suffix={suff}{mark}")
            if code == "rin":
                print(f"    idat 前0x50: {hex0.hex(' ')}")
    finally:
        mr.ctypes.windll.kernel32.CloseHandle(h)


if __name__ == "__main__":
    main()
