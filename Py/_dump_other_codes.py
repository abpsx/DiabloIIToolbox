# -*- coding: utf-8 -*-
"""dump 0x12677314 码表（另一份），查 679/portal/pr"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

base = 0x12677314
# 向后读 0x8000
raw = mem.read(pid, h, base, 0x8000)

# 解析 8 字节条目 {code4, id4}
items = []
i = 0
while i + 8 <= len(raw):
    c4 = raw[i:i+4]
    cid = int.from_bytes(raw[i+4:i+8], "little")
    if all(32 <= b < 127 for b in c4) and any(chr(b).isalpha() for b in c4) and cid < 100000:
        items.append((c4.decode("latin-1").strip(), cid, base + i))
        i += 8
    else:
        # 尝试找下一个对齐起点
        i += 4

print("条目数:", len(items))
# 去重（可能重叠解析）
seen = {}
for code, cid, addr in items:
    seen.setdefault((code, cid), addr)
print("去重后:", len(seen))

# 查 679/713/portal/pr/pk
for code, cid, addr in items:
    if cid in (679, 713) or code.startswith(("pr", "po", "pk", "key")):
        print(f"  {addr:#x}: {code!r} id={cid}")

# 打印前 30
print("== 前 30 ==")
for code, cid, addr in items[:30]:
    print(f"  {addr:#x}: {code!r} id={cid}")

ctypes.windll.kernel32.CloseHandle(h)
