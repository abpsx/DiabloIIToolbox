# -*- coding: utf-8 -*-
"""扫描内存找 InventoryLayout 结构（特征：SlotPixelWidth/Height=32, Left<Right<Top<Bottom 合理）。"""
from __future__ import annotations
import sys, ctypes, struct
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from _scan_grid_ptr import regions_of

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

def main():
    pid = mem.find_process("D2Loader.exe")
    h = mem.open_process_readonly(pid)
    try:
        regions = regions_of(pid, h)
        print(f"可读区 {len(regions)}")
        cands = []
        for lo, size in regions:
            # 只扫 4MB 以内区域（布局结构在堆/数据段，不扫大段）
            if size > 0x400000:
                continue
            raw = mem.read(pid, h, lo, size)
            if not raw:
                continue
            # 找 SlotPixelWidth=32 SlotPixelHeight=32 成对出现的位置
            p = 0
            while True:
                i = raw.find(b"\x20\x20", p)
                if i < 0:
                    break
                # 结构起点 = i - 0x14（SlotPixelWidth 在 +0x14）
                base = i - 0x14
                if base >= 0 and base + 0x18 <= len(raw):
                    sw, sh = raw[base], raw[base + 1]
                    left, right, top, bottom = struct.unpack("<IIII", raw[base + 4:base + 20])
                    if (0 < sw <= 30) and (0 < sh <= 30) and (0 < left < right < 3000) and (0 < top < bottom < 2200):
                        cands.append((lo + base, sw, sh, left, right, top, bottom))
                p = i + 2
        print(f"候选布局 {len(cands)} 个:")
        for a, sw, sh, l, r, t, b in cands[:60]:
            print(f"  {a:#x}: 格数{sw}x{sh} L{l} R{r} T{t} B{b} 宽{r-l} 高{b-t}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
