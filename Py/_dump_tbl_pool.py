# -*- coding: utf-8 -*-
"""dump 0x12A55700 明文池与 0x124F5A6C UTF-16 池，找 tbl key 结构"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def dump_utf8_pool(base, size):
    raw = mem.read(pid, h, base, size)
    print(f"== UTF-8 明文池 {base:#x}~{base+size:#x} ==")
    # 解析：可打印字符串（含 UTF-8 中文），\x00 分隔
    i = 0
    out = []
    while i < len(raw):
        j = i
        while j < len(raw) and raw[j] != 0:
            j += 1
        seg = raw[i:j]
        if seg:
            try:
                s = seg.decode("utf-8", errors="strict")
                if s and len(s) <= 40:
                    out.append((base + i, s))
            except Exception:
                pass
        i = j + 1
    return out

def dump_utf16_pool(base, size):
    raw = mem.read(pid, h, base, size)
    print(f"== UTF-16 池 {base:#x}~{base+size:#x} ==")
    out = []
    i = 0
    while i + 1 < len(raw):
        # 对齐检查：utf-16 起点
        j = i
        buf = []
        while j + 1 < len(raw):
            c = raw[j] | (raw[j+1] << 8)
            if c == 0:
                break
            buf.append(c)
            j += 2
        if buf:
            try:
                s = "".join(chr(c) for c in buf)
                if 2 <= len(s) <= 40 and all(32 <= ord(ch) < 0x9FFF for ch in s):
                    out.append((base + i, s))
            except Exception:
                pass
        i = j + 2 if j + 1 < len(raw) else i + 2
    return out

# 先看 UTF-8 明文池 0x12A55000 ~ 0x12A5D000
items = dump_utf8_pool(0x12A55000, 0x8000)
print("字符串数:", len(items))
# 找关键 key
for addr, s in items:
    if s.startswith("portal") or s.startswith("pr") or s.startswith("cm") or "钥匙" in s or s.startswith("elx") or s.startswith("hp"):
        print(f"  {addr:#x}: {s!r}")

ctypes.windll.kernel32.CloseHandle(h)
