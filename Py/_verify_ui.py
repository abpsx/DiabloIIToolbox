# -*- coding: utf-8 -*-
"""验证 UI 开关标志（按 CE 语义：0x50D00 是指针）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

d2c = mem.module_base(pid, "D2CLIENT.DLL")
base = d2c + 0x50D00
p = dword(base)
print(f"D2CLIENT+0x50D00 = {base:#x}  ->  [ptr] = {p:#x}")
for off, name in [(0x0, "背包开"), (0x4, "属性开"), (0xC, "技能树开"),
                  (0x20, "设置开"), (0x38, "任务开"), (0x5C, "信息页开"),
                  (0x60, "仓库开"), (0x64, "盒子开")]:
    v = dword(p + off) if p else -1
    print(f"  [{p + off:#x}] +0x{off:X} {name}: {v}")

ctypes.windll.kernel32.CloseHandle(h)
