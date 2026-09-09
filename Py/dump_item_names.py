# -*- coding: utf-8 -*-
"""dump 物品全称对照表（内存 0x12A3C0000，UTF-8）→ 合并进 item_codes.json

以物品码表 item_codes.json 为准：对每个 code，在内存块中搜 "code\\0"，
其后第一个 \\0 前的 UTF-8 文本即完整物品名，写入 items[i]["name"]。
"""
import json
import re
import sys

sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

START = 0x12A3A73E   # 用户确认的表起点
END = 0x12A3DB00     # 表尾：CE 块 0x12A3C000 长 0x1B000 → 0x12A3DB00（8 位合法地址）
JSON_PATH = r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json"

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed")
    sys.exit(1)

# 小步长分段读：跳过 guard/不可读页（0x10 粒度尽量吃进页内数据）
raw = bytearray()
ok_pages = 0
for off in range(START, END, 0x10):
    chunk = m.read(pid, h, off, 0x10)
    if chunk:
        raw += chunk
        ok_pages += 1
m.kernel32.CloseHandle(h)
raw = bytes(raw)
if len(raw) < 0x100:
    print("读取失败: 仅", len(raw), "字节")
    sys.exit(1)
print(f"读取 {START:#x}~{END:#x}，成功 {ok_pages} 段 / {len(raw)} 字节")

data = json.load(open(JSON_PATH, encoding="utf-8"))
items = data["items"]
print(f"物品码表共 {len(items)} 条")

# 颜色码清理：ÿcX / ÿc/（ÿ 的 UTF-8 = c3 bf）
CLEAN = re.compile(rb"\xc3\xbfc.", re.DOTALL)

hits = 0
for it in items:
    code = it["code"]
    pat = code.encode("ascii") + b"\x00"
    idx = raw.find(pat)
    if idx < 0:
        continue
    start = idx + len(pat)
    end = raw.find(b"\x00", start)
    if end <= start:
        continue
    val = raw[start:end]
    try:
        name = val.decode("utf-8")
    except Exception:
        continue
    if not name.strip():
        continue
    it["name"] = name
    it["name_clean"] = CLEAN.sub(b"", val).decode("utf-8", errors="replace")
    hits += 1

# 备份后写回
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"命中并写入全称: {hits}/{len(items)}")
print("--- 验证 ---")
for t in ("tsc", "isc", "tbk", "ibk", "sst", "r10", "r20", "gld", "amu", "rin"):
    for it in items:
        if it["code"] == t:
            print(f"{t} (id={it['id']}): name={it.get('name')!r} clean={it.get('name_clean')!r}")
            break
