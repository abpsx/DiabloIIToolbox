#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D2WIN 控件链验证：读 [D2Win.dll+0x8DB34] FirstControl 并遍历。
游戏内期望 first=0/state=game；菜单/大厅时 first 非零且可列出控件。"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem_read as mem

PID = None
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "Py", "_pid.txt")) as f:
        PID = int(f.read().strip())
except Exception:
    pass

pid = mem.find_process("D2Loader.exe")
if pid is None:
    print(json.dumps({"ok": False, "error": "D2Loader.exe 未运行"}, ensure_ascii=False))
    sys.exit(1)
print(f"PID={pid}")

h = mem.open_process_readonly(pid)
if not h:
    print(json.dumps({"ok": False, "error": "OpenProcess 失败（管理员权限？）"}, ensure_ascii=False))
    sys.exit(1)

try:
    base = mem.resolve_base(pid, "D2Win.dll+0x8DB34")
    print(f"D2Win.dll+0x8DB34 = 0x{base:X}")
    first = mem.read_ptr(pid, h, base)
    print(f"FirstControl = 0x{first:X}" if first else "FirstControl = 0 (NULL)")

    # 对照：界面标记 + 玩家指针
    fog = mem.resolve_base(pid, "Fog.dll+0x4AFE0")
    mark = mem.read_dword(pid, h, fog + 0x8)
    print(f"界面标记 = {mark}")
    player = mem.read_ptr(pid, h, mem.resolve_base(pid, "D2CLIENT+0x11B800"))
    print(f"玩家指针 = 0x{player:X}" if player else "玩家指针 = 0 (NULL)")

    item = {"module": "D2Win.dll", "offset": "0x8DB34", "offsets": [],
            "type": "controls", "player_off": "D2CLIENT+0x11B800"}
    r = mem.read_controls(pid, h, item, os.path.dirname(os.path.abspath(__file__)))
    print(json.dumps({
        "ok": True,
        "first": f"0x{r['first']:X}" if r["first"] else 0,
        "count": r["count"],
        "state": r["state"],
        "page": r["page"],
    }, ensure_ascii=False, indent=1))
    if r["controls"]:
        for c in r["controls"]:
            print(f"  0x{c['addr']:X} {c['type_name']:<12} dis={c['disabled']} "
                  f"pos=({c['pos'][0]},{c['pos'][1]}) size=({c['size'][0]}x{c['size'][1]}) "
                  f"texts={c['texts']}")
finally:
    import ctypes
    ctypes.windll.kernel32.CloseHandle(h)
