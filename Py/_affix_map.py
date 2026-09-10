#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""词缀映射表生成 v3（最终版）：
- suffix/扩展表  [D2Common+0x9FBBC]=0x1244DFCC 1452行（行0-1451），id = 行号+2
    * name 以 "of " 开头 -> suffix 词缀
    * name 非 "of " 开头 -> prefix 词缀（anhei 把 prefix 追加到扩展表后部，行 892+）
- prefix 原版表 [D2Common+0x9FBC0]=0x124683FC 行1-669有效，id = 行号+2
- automagic 表  [D2Common+0x9FBC4]=0x1247FC4C 行0-~44有效
- 中文名来自三个名池（anhei前缀池/原版前缀池/后缀池），en->zh
"""
import sys, json, re
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
if not h:
    print(json.dumps({"ok": False, "error": "无法打开进程 D2Loader.exe"}, ensure_ascii=False))
    sys.exit(1)

def read_rows(base, nrows):
    rows = []
    for i in range(nrows):
        raw = mr.read(pid, h, base + i * 0x90, 0x90)
        rows.append(raw.split(b"\x00")[0] if raw else b"")
    return rows

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

# ---- 名池 ----
pool1 = scan_names(0x12804000, 0x9000)   # anhei 前缀池
pool2 = scan_names(0x127FE000, 0x9000)   # 原版前缀池
pool3 = scan_names(0x1344F000, 0x9000)   # 后缀池
en2zh = {}
for p in (pool1, pool2, pool3):
    en2zh.update(p)
# 池未覆盖的补全（全范围扫 en\0zh\0 结果）
en2zh.update({
    "Lucky": "好运之", "Shaman's": "巫师之", "Captain's": "队长之",
    "Lancer's": "长枪兵之", "Rainbow": "彩虹之",
})
print(f"名池 en->zh {len(en2zh)} 条")

def parse_row(nm):
    if not nm:
        return None
    try:
        name = nm.decode("utf-8")
    except Exception:
        return None
    if not re.match(r"^[\x20-\x7e]+$", name):
        return None
    return name

# ---- 扩展表（0x1244DFCC，1452 行）----
sP = 0x1244DFCC
rows = read_rows(sP, 1452)
prefix = {}
suffix = {}
for rid, nm in enumerate(rows):
    name = parse_row(nm)
    if not name:
        continue
    iid = rid + 2
    is_suf = name.startswith("of ")
    entry = {"row": rid, "name": name, "name_zh": en2zh.get(name, "")}
    if is_suf:
        suffix[str(iid)] = entry
    else:
        prefix[str(iid)] = entry

# ---- prefix 原版表（0x124683FC，行1-669）----
pP = 0x124683FC
prows = read_rows(pP, 669)
for rid in range(1, len(prows)):
    name = parse_row(prows[rid])
    if not name:
        continue
    iid = rid + 2
    prefix.setdefault(str(iid), {"row": rid, "name": name, "name_zh": en2zh.get(name, "")})

# ---- automagic 段（0x1247FC4C，行0-44）----
aP = 0x1247FC4C
arows = read_rows(aP, 45)
for rid, nm in enumerate(arows):
    name = parse_row(nm)
    if not name:
        continue
    iid = rid + 669 + 2   # 扩展表行号 = 669 + automagic行号
    prefix.setdefault(str(iid), {"row": 669 + rid, "name": name, "name_zh": en2zh.get(name, "")})

with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_prefix.json", "w", encoding="utf-8") as f:
    json.dump(prefix, f, ensure_ascii=False, indent=1)
with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\temp\dict_magic_suffix.json", "w", encoding="utf-8") as f:
    json.dump(suffix, f, ensure_ascii=False, indent=1)

print(f"prefix {len(prefix)} 条 (id {min(map(int,prefix))}-{max(map(int,prefix))})")
print(f"suffix {len(suffix)} 条 (id {min(map(int,suffix))}-{max(map(int,suffix))})")
for iid in ("401", "671", "894", "987", "1003", "1119", "1155", "1156", "1159", "1334", "20635"):
    if iid in prefix:
        print(f"  prefix id{iid} -> {prefix[iid]}")
for iid in ("401", "676", "1155", "1453"):
    if iid in suffix:
        print(f"  suffix id{iid} -> {suffix[iid]}")
print(json.dumps({"ok": True, "prefix": len(prefix), "suffix": len(suffix)}))
