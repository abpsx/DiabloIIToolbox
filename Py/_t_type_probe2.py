# -*- coding: utf-8 -*-
"""验证 itemtypes 表 + nType/nRarity/nQLevel/invw/invh 实测"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import locale_text as lt

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)
try:
    dt = mem.read_dword(pid, h, mem.resolve_base(pid, "D2Common.dll+0x99E1C"))
    pit = mem.read_dword(pid, h, dt + 0xBF8)
    print("DataTables=%#x pItemTypesTxt=%#x" % (dt, pit))
    # itemtypes 行 0-13 的 szCode
    for i in range(14):
        code = mem.read(pid, h, pit + i * 0xE4, 8).split(b"\x00")[0]
        print("  type[%d] = %r" % (i, code.decode("latin-1")))
    # 物品实测
    base = lt.find_itemtxt_base(pid, h)
    print("\n物品 (code, ntype->type, rarity, qlvl, invw, invh):")
    for tid in [0, 1, 529, 520, 605, 679, 661, 509, 545, 330, 608, 609]:
        row = lt.read_item_row(pid, h, base, tid)
        a = base + tid * 0x1A8
        ntype = row["ntype"]
        tcode = mem.read(pid, h, pit + ntype * 0xE4, 8).split(b"\x00")[0].decode("latin-1")
        rarity = mem.read_value(pid, h, a + 0xFC, "byte")
        qlvl = mem.read_value(pid, h, a + 0xFD, "byte")
        invw = mem.read_value(pid, h, a + 0x10F, "byte")
        invh = mem.read_value(pid, h, a + 0x110, "byte")
        print("  id=%d code=%r ntype=%d -> %r rarity=%d qlvl=%d invw=%d invh=%d" %
              (tid, row["code"][:6], ntype, tcode, rarity, qlvl, invw, invh))
finally:
    ctypes.windll.kernel32.CloseHandle(h)
