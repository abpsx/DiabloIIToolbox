# -*- coding: utf-8 -*-
"""dump 0x12A3C4EE 附近的全称对照表"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as m

pid = int(sys.argv[1])
h = m.open_process_readonly(pid)
if not h:
    print("open failed"); sys.exit(1)

BASE = 0x12A3C4EE

# 读前 0x40 后 0x400
raw = m.read(pid, h, BASE - 0x40, 0x40 + 0x400)
if not raw:
    print("读取失败")
    sys.exit(1)

print("--- 0x12A3C4EE 前 0x40 字节 ---")
for off in range(0, 0x40, 16):
    chunk = raw[off:off + 16]
    hexs = " ".join(f"{b:02x}" for b in chunk)
    ascii_s = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"{(BASE - 0x40 + off):#x}: {hexs:<47} {ascii_s}")

print("\n--- 0x12A3C4EE 起 0x400 字节内可打印字符串（尝试 GBK） ---")
import re
for mch in re.finditer(rb"[\x20-\x7e\x80-\xff]{3,}", raw[0x40:]):
    s = mch.group()
    try:
        txt = s.decode("gbk")
    except Exception:
        try:
            txt = s.decode("utf-8")
        except Exception:
            txt = repr(s)
    print(f"@ {BASE + mch.start():#x}: {txt!r}")

# 精确读 0x12A3C4EE+4 处字符串
print("\n--- 目标位置字符串 ---")
for off in (0, 4, 8, 0xC, 0x10):
    addr = BASE + off
    raw8 = m.read(pid, h, addr, 32)
    if raw8:
        end = raw8.find(b"\x00")
        if end <= 0:
            end = 32
        part = raw8[:end]
        try:
            txt = part.decode("gbk")
        except Exception:
            txt = repr(part)
        print(f"{addr:#x} (+{off:#x}): {txt!r}  raw={part[:16]!r}")

m.kernel32.CloseHandle(h)
