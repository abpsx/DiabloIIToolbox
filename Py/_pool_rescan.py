#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重扫词缀名池（0x12801ACC 起），并反查扩展表是否存在对应行"""
import sys, re, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

def scan_from(beg, size):
    m = {}
    raw = b""
    a = beg
    while a < beg + size:
        chunk = mr.read(pid, h, a, min(0x2000, beg + size - a))
        if not chunk:
            break
        raw += chunk
        a += 0x2000
    pos = 0
    order = []
    while pos < len(raw) - 8:
        i = raw.find(b"\x00", pos)
        if i < 0:
            break
        en = raw[pos:i]
        try:
            en_s = en.decode("utf-8")
        except Exception:
            pos = i + 1
            continue
        if not en_s or len(en_s) > 64 or not re.match(r"^[\x20-\x7e]+$", en_s):
            pos = i + 1
            continue
        j = raw.find(b"\x00", i + 1)
        if j < 0:
            break
        zh = raw[i + 1:j]
        try:
            zh_s = zh.decode("utf-8")
        except Exception:
            pos = i + 1
            continue
        if zh_s and len(zh_s) <= 32 and not re.match(r"^[\x20-\x7e]+$", zh_s):
            if en_s not in m:
                order.append(en_s)
            m[en_s] = zh_s
        pos = j + 1
    return m, order

# 1) 扫词缀名池（0x12801ACC 起，向后 0x8000）
pool, order = scan_from(0x12801ACC, 0x8000)
print(f"词缀名池 0x12801ACC 起共 {len(pool)} 条:")
print("  " + ", ".join(f"{k}→{pool[k]}" for k in order[:60]))

# 2) 反查扩展表（0x1244DFCC 1452 行）是否含这些英文名
sP = 0x1244DFCC
hit = {}
for rid in range(1452):
    raw = mr.read(pid, h, sP + rid * 0x90, 0x90)
    nm = raw.split(b"\x00")[0] if raw else b""
    try:
        nm_s = nm.decode("utf-8")
    except Exception:
        continue
    if nm_s in pool:
        hit.setdefault(nm_s, []).append(rid)

# 3) prefix 原版表（0x124683FC 行 1-669）
pP = 0x124683FC
for rid in range(1, 669):
    raw = mr.read(pid, h, pP + rid * 0x90, 0x90)
    nm = raw.split(b"\x00")[0] if raw else b""
    try:
        nm_s = nm.decode("utf-8")
    except Exception:
        continue
    if nm_s in pool:
        hit.setdefault(nm_s, []).append(("P", rid))

print("\n池中词缀在表的命中:")
for k in order:
    if k in hit:
        print(f"  {k} ({pool[k]}) -> 扩展表行 {hit[k]}")
    else:
        print(f"  {k} ({pool[k]}) -> 表内未找到")
