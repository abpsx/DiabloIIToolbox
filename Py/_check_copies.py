# -*- coding: utf-8 -*-
"""读 3 个 mod 码表副本，查 portal1/portal56/pr1/pr56"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

copies = {"主表(0x1265D434)": 0x1265D434,
          "副本A(0x4922090)": 0x4922090,
          "副本B(0x4923518)": 0x4923518,
          "副本C(0x128526C4)": 0x128526C4}
want = {"portal1", "portal56", "pr1", "pr56", "pk1", "key"}

for name, table in copies.items():
    # 先读 1000 条（副本可能更长），code 合法即可
    found = {}
    for i in range(2000):
        raw = mem.read(pid, h, table + i * 8, 8)
        if len(raw) != 8:
            break
        c4 = raw[:4].decode("latin-1")
        if not (c4[:1].isalpha()):
            # 可能到尾部了
            if i > 800:
                break
            continue
        code = c4.strip()
        cid = int.from_bytes(raw[4:8], "little")
        if code in want or cid in (679, 713):
            found.setdefault(code, cid)
    print(name, "->", found)

ctypes.windll.kernel32.CloseHandle(h)
