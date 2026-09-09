# -*- coding: utf-8 -*-
"""从已知起点解析 kor 明文池(0x12A55708) 与全称池(0x12A3C4EE)，找 pr1/portal1/tsc"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def parse_from(start, size, label):
    raw = mem.read(pid, h, start, size)
    if not raw:
        print(f"{label}: 读取失败")
        return []
    pairs = []
    pos = 0
    while pos < len(raw):
        z = raw.find(b"\x00", pos)
        if z < 0:
            break
        key = raw[pos:z]
        pos = z + 1
        z = raw.find(b"\x00", pos)
        if z < 0:
            break
        val = raw[pos:z]
        pos = z + 1
        if not key:
            break
        try:
            ks = key.decode("utf-8", errors="replace")
            vs = val.decode("utf-8", errors="replace")
        except Exception:
            ks, vs = repr(key), repr(val)
        pairs.append((start + pos - len(val) - 1, ks, vs))
    print(f"\n== {label}: {len(pairs)} 对 ==")
    for i, (ad, k, v) in enumerate(pairs):
        if k in ("pr1", "portal1", "tsc", "isc", "Endthispuppy", "pr56") or "白羊" in v or "城镇" in v or "辨视" in v or "钥匙" in v:
            print(f"  [{i}] @{ad:#x}: {k!r} = {v[:60]!r}")
    return pairs

parse_from(0x12A55708, 0x30000, "kor 明文池(Endthispuppy 起)")
parse_from(0x12A3C4EE, 0x10000, "全称池(tsc 起)")

ctypes.windll.kernel32.CloseHandle(h)
