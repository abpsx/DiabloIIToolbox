# -*- coding: utf-8 -*-
"""探查仓库物品的格子坐标/绘制坐标/占格尺寸 + StashLayout。

输出物品的: txt_id, 缩写, 物品名, loc(1背包/4仓库...), 格坐标 wX/wY,
ItemPath 像素坐标, 占格 xsize x ysize。
"""
from __future__ import annotations
import sys, struct
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
from locale_text import find_itemtxt_base, read_item_row, txt_to_name

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def main():
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    try:
        d2c = mem.module_base(pid, "D2CLIENT.DLL")
        pPlayer = dword(pid, h, d2c + 0x11B800)
        if not pPlayer:
            print("人物指针为空"); return 1
        pInv = dword(pid, h, pPlayer + 0x60)
        if dword(pid, h, pInv) != 0x01020304:
            print("背包印章校验失败"); return 1

        # StashLayout（仓库面板布局）
        stash = dword(pid, h, d2c + 0x1015E0)
        print(f"StashLayout ptr = {stash:#x}")
        if stash:
            raw = mem.read(pid, h, stash, 0x18)
            if raw:
                sw, sh = raw[0], raw[1]
                left, right, top, bottom = struct.unpack("<IIII", raw[4:20])
                spw, sph = raw[0x14], raw[0x15]
                print(f"  格数 {sw}x{sh}  区域 L{left} R{right} T{top} B{bottom}  每格 {spw}x{sph}px")
                # 格坐标 -> 游戏逻辑坐标 公式验证：左上角
                print(f"  示例: 格(0,0) -> ({left},{top})  格({sw-1},{sh-1}) -> ({left+(sw-1)*spw},{top+(sh-1)*sph})")

        base = find_itemtxt_base(pid, h)
        cur = dword(pid, h, pInv + 0x0C)
        seen = set()
        items = []
        idx = 0
        while cur and cur not in seen:
            seen.add(cur)
            txt = dword(pid, h, cur + 0x04)
            idat = dword(pid, h, cur + 0x14)
            loc45 = mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1
            loc69 = mem.read(pid, h, idat + 0x69, 1)[0] if idat else -1
            wx = dword(pid, h, cur + 0x8C) & 0xFFFF
            wy = (dword(pid, h, cur + 0x8C) >> 16) & 0xFFFF
            pip = dword(pid, h, cur + 0x2C)
            px = dword(pid, h, pip + 0x0C) if pip else -1
            py = dword(pid, h, pip + 0x10) if pip else -1
            row = read_item_row(pid, h, base, txt) if base else None
            xsize = row["xsize"] if row else 0
            ysize = row["ysize"] if row else 0
            name = ""
            if base:
                try: name = txt_to_name(pid, h, txt)[0]
                except Exception: pass
            code = row["code"] if row else ""
            items.append({
                "idx": idx, "txt": txt, "code": code, "name": name,
                "loc45": loc45, "loc69": loc69,
                "gx": wx, "gy": wy, "px": px, "py": py,
                "xs": xsize, "ys": ysize, "unit": f"{cur:#x}",
            })
            cur = dword(pid, h, idat + 0x64) if idat else 0
            idx += 1

        print(f"\n共 {len(items)} 件物品:")
        for it in items:
            print(
                f"  [{it['idx']:>2}] txt={it['txt']:<4} {it['code']!r:<10} "
                f"{it['name']!r:<22} loc(45={it['loc45']},69={it['loc69']}) "
                f"格({it['gx']},{it['gy']}) 绘制({it['px']},{it['py']}) "
                f"占格{it['xs']}x{it['ys']} {it['unit']}"
            )
    finally:
        import ctypes
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
