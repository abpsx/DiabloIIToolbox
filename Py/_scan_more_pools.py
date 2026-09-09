# -*- coding: utf-8 -*-
"""分段读 0x12A4C000~0x12A5F000 与 0x12A55000~0x12A60000，找 pr1/portal1"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def scan_pairs(base, end, label):
    pairs = []
    buf_all = bytearray()
    addr_map = {}
    for b in range(base, end, 0x1000):
        raw = mem.read(pid, h, b, 0x1000)
        if raw:
            addr_map[len(buf_all)] = b
            buf_all.extend(raw)
    raw = bytes(buf_all)
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
        # 绝对地址
        off = pos - len(val) - 1
        abs_addr = None
        for koff, abase in addr_map.items():
            if koff <= off < koff + 0x1000:
                abs_addr = abase + (off - koff)
                break
        pairs.append((abs_addr, ks, vs))
    print(f"\n== {label}: {len(pairs)} 对 ==")
    for i, (ad, k, v) in enumerate(pairs):
        if "pr" in k or "portal" in k or "白羊" in v or "钥匙" in v:
            print(f"  [{i}] @{ad:#x}: {k!r} = {v[:60]!r}")
    return pairs

scan_pairs(0x12A4C000, 0x12A5E000, "池1延续 0x12A4C000")
scan_pairs(0x12A55000, 0x12A60000, "池2 0x12A55000")

ctypes.windll.kernel32.CloseHandle(h)
