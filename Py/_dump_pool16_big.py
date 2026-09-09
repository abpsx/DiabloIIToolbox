# -*- coding: utf-8 -*-
"""dump 0x124F4000~0x12508000 UTF-16 池，确认结构（key/value?）"""
import sys, ctypes, json
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

START, END = 0x124F4000, 0x12508000
chunks = []
for a in range(START, END, 0x1000):
    raw = mem.read(pid, h, a, 0x1000)
    chunks.append(raw if raw else b"\x00" * 0x1000)
buf = b"".join(chunks)
print("读取:", len(buf))

strs = []
i = 0
while i + 1 < len(buf):
    j = i
    out = []
    while j + 1 < len(buf):
        c = buf[j] | (buf[j+1] << 8)
        if c == 0:
            break
        out.append(chr(c))
        j += 2
    if out:
        s = "".join(out)
        if 1 <= len(s) <= 80 and all(32 <= ord(ch) < 0x9FFF for ch in s):
            strs.append((START + i, s))
    i = j + 2 if j + 1 < len(buf) else i + 2

print("字符串:", len(strs))
# 看关键段
for addr, s in strs:
    if s.startswith("portal") or s == "城镇卷" or s == "白羊宫钥匙" or s == "体力药" or "钥匙" in s[:6]:
        print(f"  {addr:#x}: {s!r}")

# 结构判断：前 40 条
print("== 前 40 ==")
for addr, s in strs[:40]:
    print(f"  {addr:#x}: {s!r}")

with open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_mem_d2lang_pool16.json", "w", encoding="utf-8") as f:
    json.dump([s for _, s in strs], f, ensure_ascii=False)
print("已保存")
ctypes.windll.kernel32.CloseHandle(h)
