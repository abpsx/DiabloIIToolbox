# -*- coding: utf-8 -*-
"""完整 dump kor 明文池(0x12A55000~0x12A90000) 与全称池，找 pr1/portal1/tsc"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def dump_pairs(base, size, label):
    pairs = []
    for b in range(base, base + size, 0x10000):
        raw = mem.read(pid, h, b, 0x10000)
        if not raw:
            continue
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
            pairs.append((b + pos - len(val) - 1, ks, vs))
    print(f"\n== {label}: {len(pairs)} 对 ==")
    for i, (ad, k, v) in enumerate(pairs):
        if k in ("pr1", "pr2", "pr56", "portal1", "tsc", "isc", "Endthispuppy") or "白羊" in v or "城镇" in v or "辨视" in v:
            print(f"  [{i}] @{ad:#x}: {k!r} = {v[:50]!r}")
    return pairs

dump_pairs(0x12A55000, 0x40000, "kor 明文池 0x12A55000")
dump_pairs(0x12A3C000, 0x1D000, "全称池 0x12A3C000")

ctypes.windll.kernel32.CloseHandle(h)
