# -*- coding: utf-8 -*-
"""测试仓库页读取"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
st = mem.read_stash_state(pid, h)
print("仓库状态:", st)
cfg = {"module": "D2CLIENT.DLL", "offset": "0x11B800", "offsets": ["0x60"], "table": "item_codes.json"}
items = mem.read_bag(pid, h, cfg, r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory")
stash_items = [i for i in items if i["loc"] == 4]
print(f"仓库物品 {len(stash_items)} 件:")
for i in stash_items:
    print(f"  [{i['code']}] {i['name']}")
ctypes.windll.kernel32.CloseHandle(h)
