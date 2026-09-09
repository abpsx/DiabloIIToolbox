# -*- coding: utf-8 -*-
"""TXT id → ItemTxt 行解析器（1.13c mod，只读内存）

用法:
  python item_txt_resolver.py 679
  python item_txt_resolver.py 679 713 529 --json

通路: TXT id = 物品 dwTxtFileNo = 码表 id = ItemTxt 行号
行结构 (d2hackmap 1.13c d2structs.h ItemTxt, 行宽 0x1A8):
  szFlippyfile[32] @+0x00   szInvfile[96] @+0x20
  szCode[20]       @+0x80   wLocaleTxtNo  @+0xF4 (WORD)
  nType           @+0x11E   fQuest        @+0x12A
"""
from __future__ import annotations
import argparse, json, sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

ROW = 0x1A8

def find_itemtxt_base(pid: int, h: int) -> int | None:
    """VirtualQuery 枚举可读区，搜 'flphax'(行0 szFlippyfile) 定位 ItemTxt 表基。"""
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    class MBI(ctypes.Structure):
        _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                    ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]
    regions = []
    addr = 0x10000
    while addr < 0x7FFFFFFF:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
            regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF
    needle = b"flphax\x00"
    for lo, size in regions:
        chunk = 0x10000
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(needle, p)
                if i < 0:
                    break
                base = lo + off + i
                c0 = mem.read(pid, h, base + 0x80, 4)
                c529 = mem.read(pid, h, base + 529 * ROW + 0x80, 4)
                if c0 == b"hax " and c529 == b"tsc ":
                    return base
                p = i + 1
    return None

def read_row(pid, h, base, txt_id):
    a = base + txt_id * ROW
    raw = mem.read(pid, h, a, ROW)
    if not raw:
        return None
    def s(off, n):
        v = raw[off:off+n].split(b"\x00")[0]
        return v.decode("latin-1") if v else ""
    return {
        "txt_id": txt_id,
        "addr": f"{a:#x}",
        "flip": s(0x00, 32),
        "invfile": s(0x20, 96),
        "code": s(0x80, 20).strip(),
        "potionflag": raw[0x94],
        "locale": int.from_bytes(raw[0xF4:0xF6], "little"),
        "ntype": raw[0x11E],
        "fquest": raw[0x12A],
        "socket": raw[0x138],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", type=lambda s: int(s, 0), nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print(json.dumps({"ok": False, "error": "D2Loader.exe 未运行"})); return 1
    h = mem.open_process_readonly(pid)
    try:
        base = find_itemtxt_base(pid, h)
        if not base:
            print(json.dumps({"ok": False, "error": "ItemTxt 表基定位失败（游戏需在城内/大厅）"})); return 1
        rows = [read_row(pid, h, base, i) for i in args.ids]
    finally:
        ctypes.windll.kernel32.CloseHandle(h) if "ctypes" in dir() else None
    if args.json:
        print(json.dumps({"ok": True, "table_base": f"{base:#x}", "rows": rows}, ensure_ascii=False))
    else:
        print(f"ItemTxt 表基: {base:#x}\n")
        for r in rows:
            print(f"TXT:{r['txt_id']}  code={r['code']!r}  locale={r['locale']}  nType={r['ntype']}  fQuest={r['fquest']}  flip={r['flip']!r}  inv={r['invfile']!r}  @{r['addr']}")

import ctypes
if __name__ == "__main__":
    sys.exit(main())
