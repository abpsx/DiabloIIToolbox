# -*- coding: utf-8 -*-
"""dump 全名表 0x12A3A73E 区域，找 pr/portal 条目"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

# 从 0x12A3A700 读到 0x12A3C600（覆盖用户给的范围）
raw = mem.read(pid, h, 0x12A3A700, 0x1F00)

# 解析 code(4) + UTF8 名 交替
i = 0
items = []
while i < len(raw) - 4:
    c4 = raw[i:i+4]
    if all(32 <= b < 127 for b in c4) and any(chr(b).isalpha() for b in c4):
        # 尝试 UTF-8 名
        j = i + 4
        while j < len(raw) and raw[j] != 0:
            j += 1
        try:
            nm = raw[i+4:j].decode("utf-8", errors="strict")
            if nm and len(nm) <= 30:
                items.append((c4.decode("latin-1"), nm, 0x12A3A700 + i))
                i = j + 1
                continue
        except Exception:
            pass
    i += 1

print("解析条目数:", len(items))
# 找 pr/portal/key
for code, nm, addr in items:
    if code.startswith("pr") or code.startswith("po") or "白" in nm or "鹰" in nm or "钥匙" in nm:
        print(f"  {addr:#x}: {code!r} -> {nm}")

ctypes.windll.kernel32.CloseHandle(h)
