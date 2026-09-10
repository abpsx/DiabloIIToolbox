# -*- coding: utf-8 -*-
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

def dword(pid, h, a):
    r = mem.read(pid, h, a, 4)
    return int.from_bytes(r, "little") if r else 0

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

d2common = mem.module_base(pid, "D2Common.dll")
print("D2Common base = %#x" % d2common)

sgpt = dword(pid, h, d2common + 0x86A20)
print("sgptDataTables = %#x" % sgpt)
if sgpt:
    pSet = dword(pid, h, sgpt + 0xC18)
    nSet = dword(pid, h, sgpt + 0xC1C)
    print("pSetItemsTxt = %#x  count = %d" % (pSet, nSet))
    if pSet and 0 < nSet < 100000:
        REC = 0x1B8
        found_xsk = None
        for i in range(min(nSet, 2000)):
            rec = pSet + i * REC
            code = mem.read(pid, h, rec + 0x28, 4)
            if code in (b"xsk\0", b"xsk"):
                found_xsk = i
                print("\n★ xsk 记录索引 = %d (rec=%#x)" % (i, rec))
                b = mem.read(pid, h, rec, 0x40)
                wSetItemId = int.from_bytes(b[0:2], "little")
                szName = b[2:34].split(b"\x00")[0].decode("latin-1", "ignore")
                wVersion = int.from_bytes(b[0x22:0x24], "little")
                wStringId = int.from_bytes(b[0x24:0x26], "little")
                nSetId = int.from_bytes(b[0x2C:0x2E], "little", signed=True)
                print("  wSetItemId=%d  szName=%r  wVersion=%d  wStringId=%d  nSetId=%d" % (wSetItemId, szName, wVersion, wStringId, nSetId))
                # 用 wStringId 索引 String 表（0x11e8e4c0 数组）
                arr = 0x11e8e4c0
                p = dword(pid, h, arr + wStringId * 4)
                if p:
                    t = mem.read(pid, h, p, 0x40).decode("utf-16-le", "ignore")
                    print("  String[%d] = %r" % (wStringId, t[:50]))
                break
        if not found_xsk:
            print("  xsk 未在表内；dump 记录0/80/137 对照：")
            for i in (0, 80, 137):
                rec = pSet + i * REC
                b = mem.read(pid, h, rec, 0x30)
                code = b[0x28:0x2C]
                wStringId = int.from_bytes(b[0x24:0x26], "little")
                print("  rec[%d]: code=%r wStringId=%d" % (i, code, wStringId))

ctypes.windll.kernel32.CloseHandle(h)
