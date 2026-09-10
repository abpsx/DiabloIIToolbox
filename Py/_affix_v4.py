#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词缀映射 v4（正确版）：id = 扩展表行号（0x1244DFCC 1452 行），统一 prefix/suffix。
验证锚点：项链1 985=Iron(att) 1312=Monk's(pal) 1051=Snake's(mana) 742=of the Locust(lifesteal)
"""
import sys, json, re
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC
NROWS = 1452

# 读全部行 name
names = []
for rid in range(NROWS):
    raw = mr.read(pid, h, sP + rid * 0x90, 0x90)
    nm = raw.split(b"\x00")[0] if raw else b""
    try:
        names.append(nm.decode("utf-8"))
    except Exception:
        names.append("")

# 名池 en->zh
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

# 生成统一映射：id = 行号
affix = {}
for rid, nm in enumerate(names):
    if not nm:
        continue
    typ = "S" if nm.startswith("of ") else "P"
    affix[str(rid)] = {
        "row": rid,
        "name": nm,
        "type": typ,
        "name_zh": en2zh.get(nm, ""),
    }

with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_affixes.json", "w", encoding="utf-8") as f:
    json.dump(affix, f, ensure_ascii=False, indent=1)
print(f"统一词缀表 {len(affix)} 条 (id 0-{max(map(int, affix))})")

# 三项链词条验证
def w(a):
    return mr.read_value(pid, h, a, "word")

base = mr.read_ptr(pid, h, mr.module_base(pid, "D2Client.dll") + 0x11B800)
inv = mr.read_ptr(pid, h, base + 0x60)
first = mr.read_ptr(pid, h, inv + 0x0C)
cur = first
necks = {}
while cur:
    txt = w(cur + 0x04)
    idat = mr.read_ptr(pid, h, cur + 0x14)
    if idat:
        words = [w(idat + 0x38 + i * 2) for i in range(6)]
        if txt == 520 and any(words):
            necks[hex(cur)] = words
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

for k, v in necks.items():
    print(f"\n项链 {k}: {v}")
    for i, iid in enumerate(v):
        if not iid:
            continue
        e = affix.get(str(iid))
        if e:
            print(f"   槽{i} id{iid} = {e['name']!r} ({e['name_zh'] or '?'}) [{e['type']}]")
        else:
            print(f"   槽{i} id{iid} = ?")
