# -*- coding: utf-8 -*-
"""dump 0x12A3A73E 全名表（用户线索），解析 code+名"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

# 0x12A3A73E 起点，读 0x12A3A700 ~ 0x12A3E000
START = 0x12A3A700
raw = mem.read(pid, h, START, 0x3900)
print("读取:", len(raw))

# 12A3C4EE 处内容
off = 0x12A3C4EE - START
print("12A3C4EE 处:", raw[off:off+40])

# 解析：code(4) + UTF-8名 交替（尝试）
items = []
i = 0
while i < len(raw) - 4:
    c4 = raw[i:i+4]
    if all(32 <= b < 127 for b in c4) and any(chr(b).isalpha() for b in c4):
        j = i + 4
        while j < len(raw) and raw[j] != 0:
            j += 1
        try:
            nm = raw[i+4:j].decode("utf-8", errors="strict")
            if 1 <= len(nm) <= 40:
                items.append((c4.decode("latin-1"), nm, START + i))
                i = j + 1
                continue
        except Exception:
            pass
    i += 1

print("条目:", len(items))
for code, nm, addr in items:
    if code.startswith(("pr", "po", "cm", "hp")) or "钥匙" in nm or "宫" in nm or code == "tsc":
        print(f"  {addr:#x}: {code!r} -> {nm}")
ctypes.windll.kernel32.CloseHandle(h)
