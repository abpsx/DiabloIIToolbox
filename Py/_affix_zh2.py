#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并名池中文(name_zh)到 dict_magic_affixes.json（内存源版）"""
import sys, json, re
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)

def scan_names(beg, size):
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
            m.setdefault(en_s, zh_s)
        pos = j + 1
    return m

en2zh = {}
for beg in (0x12800000, 0x12804000, 0x127FE000, 0x1344F000):
    en2zh.update(scan_names(beg, 0x9000))

AFF = r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_affixes.json"
aff = json.load(open(AFF, encoding="utf-8"))
hit = 0
for e in aff.values():
    zh = en2zh.get(e["name"], "")
    if zh:
        e["name_zh"] = zh
        hit += 1
with open(AFF, "w", encoding="utf-8") as f:
    json.dump(aff, f, ensure_ascii=False, indent=1)
print(f"中文名命中 {hit}/{len(aff)}")
for iid in (985, 1312, 1051, 742):
    e = aff[str(iid)]
    print(f"id{iid} {e['name']} -> {e['name_zh']} | {e['mod']['zh']} {e['mod']['min']}-{e['mod']['max']}")
