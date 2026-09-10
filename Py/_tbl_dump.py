#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dump tbl 描述池（ModStr key -> 中文描述），输出 temp/dict_tbl_modstr.json"""
import sys, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

def read_region(base, size):
    return mr.read(pid, h, base, size) or b""

def parse_pool(raw, base):
    out = {}
    # 格式: key\0描述\0 交替，key 为 ASCII（ModStr/ItemStats 等），描述含 UTF-8 中文
    pos = 0
    n = len(raw)
    while pos < n:
        # 找非零起点
        while pos < n and raw[pos] == 0:
            pos += 1
        if pos >= n:
            break
        end = raw.find(b"\x00", pos)
        if end < 0 or end - pos > 200:
            pos += 1
            continue
        key = raw[pos:end].decode("utf-8", "replace")
        if not key or not key.isprintable():
            pos = end + 1
            continue
        # 描述
        dstart = end + 1
        while dstart < n and raw[dstart] == 0:
            dstart += 1
        dend = raw.find(b"\x00", dstart)
        if dend < 0 or dend - dstart > 500:
            pos = end + 1
            continue
        desc = raw[dstart:dend].decode("utf-8", "replace")
        # 只收 key 像模板名 且 desc 含中文或可打印
        if desc and (any('\u4e00' <= c <= '\u9fff' for c in desc) or desc.isprintable()):
            out[key] = desc
        pos = dend + 1
    return out

pools = {}
# 原版 tbl 区（ModStr 系列）—— 扫描 0x12800000-0x12840000
for base in range(0x12800000, 0x12840000, 0x4000):
    raw = read_region(base, 0x4000)
    if b"ModStr" in raw:
        pools.update(parse_pool(raw, base))
# anhei 扩展区（刺客技能 0x134511d0 附近）
for base in range(0x13440000, 0x13500000, 0x4000):
    raw = read_region(base, 0x4000)
    if b"ModStr" in raw or b"\xe5\x88\xba\xe5\xae\xa2" in raw:
        pools.update(parse_pool(raw, base))

out = {"count": len(pools), "items": pools}
path = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_tbl_modstr.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"描述池 {len(pools)} 条 -> {path}")
# 打印技能相关
for k in sorted(pools):
    if any(w in k.lower() for w in ("modstr3", "skill")) or any(x in pools[k] for x in ("技能", "抗性", "照亮", "准确", "充能", "偷取")):
        print(f"  {k}: {pools[k]}")
