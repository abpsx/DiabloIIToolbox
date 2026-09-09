# -*- coding: utf-8 -*-
"""dump kor tbl 明文池 + 0x124F5A6C UTF-16 池，搜 pr/cm/hp key"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

# ---- 1. kor 明文池起点探测：从 0x12A55700 往前找池起点 ----
base = 0x12A55700
# 往前读 0x8000，找 "Endthispuppy" 或池头
pre = mem.read(pid, h, base - 0x8000, 0x8000 + 0x200)
idx = pre.find(b"Endthispuppy")
print("Endthispuppy 在 pre 偏移:", idx, "=> 绝对", hex(base - 0x8000 + idx))
if idx < 0:
    # 找 "名称" GBK
    idx = pre.find("\u540d\u79f0".encode("gbk"))
    print("名称gbk偏移:", idx)
    start = base - 0x8000 + idx if idx >= 0 else base - 0x200
else:
    start = base - 0x8000 + idx
print("池起点约:", hex(start))

# ---- 2. dump 明文池 ----
raw = mem.read(pid, h, start, 0x20000)
print("明文池读取:", len(raw))
segs = []
i = 0
while i < len(raw):
    j = i
    while j < len(raw) and raw[j] != 0:
        j += 1
    seg = raw[i:j]
    if seg:
        try:
            s = seg.decode("utf-8", errors="strict")
            segs.append(s)
        except Exception:
            pass
    i = j + 1
print("分段数:", len(segs))

# key/value 交替：key -> value
pairs = []
k = 0
while k + 1 < len(segs):
    pairs.append((segs[k], segs[k+1]))
    k += 2
print("配对:", len(pairs))
# 找 pr/cm/hp/elx/key
hits = [p for p in pairs if p[0].startswith(("pr", "cm", "hp", "mp", "el", "key", "pk"))]
print("== pr/cm/hp/el 相关 key ==")
for kk, vv in hits[:40]:
    print(f"  {kk!r} -> {vv!r}")

# 保存明文池
import json
with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_mem_kor_tbl_pool.json", "w", encoding="utf-8") as f:
    json.dump(dict(pairs), f, ensure_ascii=False, indent=0)
print("已保存 _mem_kor_tbl_pool.json")

# ---- 3. 0x124F5A6C UTF-16 池 ----
print("\n== UTF-16 池 0x124F5000 ~ 0x124F7000 ==")
raw16 = mem.read(pid, h, 0x124F5000, 0x2000)
s16 = []
i = 0
while i + 1 < len(raw16):
    j = i
    buf = []
    while j + 1 < len(raw16):
        c = raw16[j] | (raw16[j+1] << 8)
        if c == 0:
            break
        buf.append(c)
        j += 2
    if buf:
        try:
            s = "".join(chr(c) for c in buf)
            if 1 <= len(s) <= 60 and all(32 <= ord(ch) < 0x9FFF for ch in s):
                s16.append(s)
        except Exception:
            pass
    i = j + 2 if j + 1 < len(raw16) else i + 2
print("UTF-16 字符串数:", len(s16))
for s in s16[:30]:
    print(f"  {s!r}")

ctypes.windll.kernel32.CloseHandle(h)
