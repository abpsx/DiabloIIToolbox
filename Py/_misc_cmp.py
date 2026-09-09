# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\global\excel\misc.bin", "rb").read()
ROW = 0x1A8

def find_row(code4):
    code4 = code4.encode() if isinstance(code4, str) else code4
    for i in range(0, len(raw) - ROW, 4):
        if raw[i : i + 4] == code4:
            return i
    return None

for code in ("tsc ", "vps ", "isc ", "elc ", "ibg ", "hpo ", "pr1 "):
    rs = find_row(code)
    if rs is None:
        print(code, "未找到"); continue
    row = raw[rs : rs + ROW]
    # 打印所有 4 字节列（非 0 或字符串）
    cols = []
    for i in range(0, ROW, 4):
        b = row[i : i + 4]
        d = int.from_bytes(b, "little")
        s = "".join(chr(x) if 32 <= x < 127 else "." for x in b)
        if d != 0 or (b.strip() and s.strip()):
            cols.append(f"+{i:03x}={s if b.strip() and s.strip() else d}")
    print(f"{code} @{rs:#x}:", " ".join(cols[:22]))
