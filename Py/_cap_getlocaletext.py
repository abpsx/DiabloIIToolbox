# -*- coding: utf-8 -*-
"""capstone 完整反汇编 GetLocaleText 0x2509450"""
import sys, ctypes
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)
md = Cs(CS_ARCH_X86, CS_MODE_32)

raw = mem.read(pid, h, 0x2509450, 0x300)
print(f"===== GetLocaleText @ 0x2509450 =====")
for ins in md.disasm(raw, 0x2509450):
    print(f"  {ins.address:#08x}: {ins.mnemonic}\t{ins.op_str}")

ctypes.windll.kernel32.CloseHandle(h)
