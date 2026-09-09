# -*- coding: utf-8 -*-
"""搜指向 '白羊宫钥匙'(0x12A55741) 与 '城镇卷'(0x12A3C4F4) 值的指针，验证索引表"""
import sys, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

regions = []
addr = 0x10000
while addr < 0x7FFFFFFF:
    mbi = MBI()
    if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
        break
    if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
        regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
    addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

for target, name in [(0x12A55741, "白羊宫钥匙值"), (0x12A3C4F4, "城镇卷值")]:
    tb = target.to_bytes(4, "little")
    phits = []
    for lo, size in regions:
        chunk = 0x100000
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(tb, p)
                if i < 0:
                    break
                phits.append(lo + off + i)
                p = i + 1
    print(f"\n指向 {name} ({target:#x}) 的指针: {len(phits)} 处")
    for ph in phits[:20]:
        # 检查是否数组元素：前后指针是否指向 0x12A5xxxx/0x12A3xxxx（同池）
        pv = mem.read_dword(pid, h, ph - 4)
        nv = mem.read_dword(pid, h, ph + 4)
        print(f"  {ph:#x}: prev={pv:#x} next={nv:#x}")

ctypes.windll.kernel32.CloseHandle(h)
