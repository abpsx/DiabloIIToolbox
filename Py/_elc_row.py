# -*- coding: utf-8 -*-
raw = open(r"G:\game\diablo 2\data\global\excel\misc.bin", "rb").read()

# 各 code 行起始（按出现顺序排列数据区）。hpo 0x22c hpf 0x57c 差 0x350=2*0x1A8
# 验证行宽 = 0x1A8
elc = raw.find(b"elc ")
cm11 = raw.find(b"cm11")
pr1 = raw.find(b"pr1 ")
print("elc@", hex(elc), "cm11@", hex(cm11), "pr1@", hex(pr1))
print("行宽验证: cm11-elc =", hex(cm11 - elc), "= ", (cm11 - elc) // 0x1A8, "行")

# 每行打印所有 dword 值（小整数重点关注）
for name, off in (("elc", elc), ("cm11", cm11), ("pr1", pr1)):
    row = raw[off : off + 0x1A8]
    print(f"===== {name}@{off:#x} 行内 dword =====")
    vals = []
    for i in range(0, len(row), 4):
        d = int.from_bytes(row[i : i + 4], "little")
        if d != 0xFFFFFFFF and d != 0:
            vals.append((i, d, row[i : i + 4]))
    for i, d, by in vals:
        tag = ""
        try:
            s = by.decode("ascii")
            if all(32 <= ord(c) < 127 for c in s):
                tag = f" '{s}'"
        except Exception:
            pass
        print(f"  +{i:#04x}: {d:#010x} ({d}){tag}")
