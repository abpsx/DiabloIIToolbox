# -*- coding: utf-8 -*-
"""capstone 完整反汇编 GetLocaleText(0x2509450) 与查表函数(0x2509050/0x2507ADC)"""
import sys, ctypes
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def show(base, size, label, maxins=200):
    raw = mem.read(pid, h, base, size)
    if not raw:
        print(f"{label}: 读失败")
        return
    print(f"\n===== {label} @ {base:#x} =====")
    n = 0
    for ins in md.disasm(raw, base):
        print(f"  {ins.address:#08x}: {ins.mnemonic}\t{ins.op_str}")
        n += 1
        if n >= maxins:
            break

show(0x2509050, 0x160, "查表函数 0x2509050")
show(0x2507ADC, 0x120, "加载tbl回退 0x2507ADC")
show(0x2507AD6, 0x10, "0x2507AD6")
show(0x2507B6C, 0x20, "0x2507B6C")
show(0x2507AE2, 0x20, "0x2507AE2")

ctypes.windll.kernel32.CloseHandle(h)
