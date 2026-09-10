# -*- coding: utf-8 -*-
"""验证: GetItemTxt(D2Common+0x719A0) 头部是否引用 items.txt 表基静态指针"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    d2c = mem.module_base(pid, "D2Common.dll")
    print("D2Common base: 0x%X" % d2c)
    # 反汇编 GetItemTxt 头部 0x60 字节
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        have_cap = True
    except ImportError:
        have_cap = False
    code = mem.read(pid, h, d2c + 0x719A0, 0x60)
    if have_cap:
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        print("--- GetItemTxt 反汇编 (D2Common+0x719A0) ---")
        for ins in md.disasm(code, d2c + 0x719A0):
            print("  0x%X: %-14s %s" % (ins.address, ins.mnemonic, ins.op_str))
    else:
        print(code.hex(" "))
finally:
    ctypes.windll.kernel32.CloseHandle(h)
