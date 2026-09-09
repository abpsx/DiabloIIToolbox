# -*- coding: utf-8 -*-
"""分段 dump kor tbl 明文池（0x12A54000 起），解析 key->value，查 pr/cm/hp/el"""
import sys, ctypes, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

START, END = 0x12A54000, 0x12AA0000
chunks = []
for a in range(START, END, 0x1000):
    raw = mem.read(pid, h, a, 0x1000)
    if not raw:
        chunks.append(b"\x00" * 0x1000)
    else:
        chunks.append(raw)
buf = b"".join(chunks)
print("读取:", len(buf))

segs = []
i = 0
while i < len(buf):
    j = i
    while j < len(buf) and buf[j] != 0:
        j += 1
    seg = buf[i:j]
    if seg:
        try:
            s = seg.decode("utf-8", errors="strict")
            segs.append(s)
        except Exception:
            pass
    i = j + 1
print("分段:", len(segs))

# 找 "Endthispuppy" 起点索引，key/value 交替
if "Endthispuppy" in segs:
    st = segs.index("Endthispuppy")
else:
    st = 0
pairs = []
for k in range(st, len(segs) - 1, 2):
    pairs.append((segs[k], segs[k+1]))
print("配对:", len(pairs))

hits = [p for p in pairs if p[0].startswith(("pr", "cm", "hp", "mp", "el", "key", "pk", "vps", "bpl", "rpl", "bps", "hpo", "hpf", "mpo", "mpf"))]
print("== 药水/护身符/钥匙 相关 ==")
for kk, vv in hits[:60]:
    print(f"  {kk!r} -> {vv!r}")

with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_mem_kor_tbl_pool.json", "w", encoding="utf-8") as f:
    json.dump(dict(pairs), f, ensure_ascii=False)
print("已保存", len(pairs), "条")
ctypes.windll.kernel32.CloseHandle(h)
