# -*- coding: utf-8 -*-
"""验证新结构: +0x04 文本缓冲首 dword = 当前页数(0基)"""
import sys, ctypes, re
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    return mem.read_dword(pid, h, a)

# AOB 全部命中 + 校验
hits = mem.find_pattern(pid, h, bytes.fromhex("FF0000000101000068676C20"), max_hits=8)
for a in hits:
    S = a - 0x10
    tot = dword(S)          # +0x00 总页数?
    pBuf = dword(S + 4)     # +0x04 文本缓冲指针
    buf0 = dword(pBuf) if pBuf else -1   # 文本缓冲首 dword (0基页数?)
    raw = mem.read(pid, h, pBuf, 100) if pBuf else b""
    s = raw.decode("utf-16-le", errors="replace")
    m = re.search(r"当前页数\s*:\s*(\d+)页", s)
    print(f"结构@0x{S:X}:  +0x00={tot}  +0x04->0x{pBuf:X}  缓冲首dword={buf0}  文本={m.group(1) if m else '?'}")
ctypes.windll.kernel32.CloseHandle(h)
