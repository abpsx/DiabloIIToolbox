#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump 当前界面控件链的 disabled(@0x08) / state(@0x44) 原始值，判断禁用标志字段。"""
import ctypes
import json
import os
import sys

sys.path.insert(0, ".")
import mem_read as mem

py_dir = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    pid = mem.find_process("D2Loader.exe")
    if pid is None:
        print("D2Loader.exe 未运行")
        return 1
    h = mem.open_process_readonly(pid)
    if not h:
        print("OpenProcess 失败")
        return 1
    try:
        items = json.load(open(os.path.join(py_dir, "..", "Setting", "memory", "1.13c.json"), encoding="utf-8"))
        r = mem.read_all(pid, items, py_dir)
        ctrl = r.get("控件链") or r.get("results", {}).get("控件链")
        if not ctrl or not ctrl.get("controls"):
            print("未读取到控件链: ", str(ctrl)[:200])
            return 1
    except Exception as e:
        print(f"read_all 异常: {e}")
        return 1
    finally:
        ctypes.windll.kernel32.CloseHandle(h)

    print(f"state={ctrl['state']} page={ctrl['page']} first=0x{ctrl['first']:X} count={ctrl['count']}")
    for c in ctrl["controls"]:
        t = c["type_name"]
        dis = c["disabled"]
        st = c["state"]
        texts = "/".join(c["texts"]) if c["texts"] else ""
        print(f"  type={c['type']:<3}({t:<6}) dis=0x{dis:08X} state=0x{st:08X} cb={c['cb_off'] or '-':<8} texts={texts!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
