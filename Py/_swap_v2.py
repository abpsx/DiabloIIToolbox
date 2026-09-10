# -*- coding: utf-8 -*-
"""仓库物品交换 v2：先扫描定位物品真实可点击格，再执行交换。
- 点击: WM_MOUSEMOVE + SendMessage WM_LBUTTONDOWN/UP（后台，不抢鼠标）
- 扫描: 在 dwPos±1 格范围点击，命中(拿起)即记录真实格并放回
- 交换: 点A真实格(拿起) -> 点B真实格(放A拿B) -> 点A真实格(放B)
"""
from __future__ import annotations
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import _human

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

COLS, ROWS, CELL = 10, 10, 29
DX, DY = -157, -9

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def find_hwnd(pid):
    found = []
    def cb(hwnd, lp):
        if user32.IsWindowVisible(hwnd):
            p = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid:
                found.append(hwnd)
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found[0] if found else 0

def get_items(pid, h):
    d2c = mem.module_base(pid, "D2CLIENT.DLL")
    pPlayer = dword(pid, h, d2c + 0x11B800)
    pInv = dword(pid, h, pPlayer + 0x60)
    cur = dword(pid, h, pInv + 0x0C)
    seen = set(); out = []
    while cur and cur not in seen:
        seen.add(cur)
        txt = dword(pid, h, cur + 0x04)
        idat = dword(pid, h, cur + 0x14)
        loc45 = mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1
        if loc45 == 4:
            pip = dword(pid, h, cur + 0x2C)
            out.append({"unit": cur, "txt": txt,
                        "gx": dword(pid, h, pip + 0x0C),
                        "gy": dword(pid, h, pip + 0x10),
                        "pInv": pInv})
        cur = dword(pid, h, idat + 0x64) if idat else 0
    return out

def cursor_item(pid, h, pInv):
    return dword(pid, h, pInv + 0x20)

def pt(cx, cy, gx, gy):
    return (cx + DX + (gx - COLS // 2) * CELL + CELL // 2,
            cy + DY + (gy - ROWS // 2) * CELL + CELL // 2)

def click(hwnd, x, y):
    _human.click(hwnd, x, y)

def main():
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    try:
        items = get_items(pid, h)
        for it in items:
            print(f"读: txt={it['txt']} dwPos({it['gx']},{it['gy']})")
        if len(items) < 2:
            print("仓库物品不足 2 件"); return 1
        hwnd = find_hwnd(pid)
        r = wintypes.RECT(); user32.GetClientRect(hwnd, ctypes.byref(r))
        cx, cy = r.right // 2, r.bottom // 2
        pInv = items[0]["pInv"]

        def real_cell(it):
            """在 dwPos±1 范围扫描，返回(真实格x, 真实格y)。命中后放回。"""
            for dy in (0, 1, -1):
                for dx in (0, 1, -1):
                    gx, gy = it["gx"] + dx, it["gy"] + dy
                    if not (0 <= gx < COLS and 0 <= gy < ROWS):
                        continue
                    x, y = pt(cx, cy, gx, gy)
                    click(hwnd, x, y)
                    _human.wait(0.3, 0.5)
                    c = cursor_item(pid, h, pInv)
                    if c == it["unit"]:
                        click(hwnd, x, y)  # 放回
                        _human.wait(0.3, 0.5)
                        if cursor_item(pid, h, pInv) != 0:
                            print(f"  放回失败 {gx},{gy}")
                            sys.exit(1)
                        return gx, gy
                    elif c != 0:
                        # 点到了别的物品：放回它
                        click(hwnd, x, y)
                        _human.wait(0.3, 0.5)
            return None, None

        real = []
        for it in items:
            gx, gy = real_cell(it)
            if gx is None:
                print(f"txt={it['txt']} 扫描 9 格未命中"); return 1
            real.append((gx, gy, it))
            print(f"txt={it['txt']} 真实格({gx},{gy})")

        (ax, ay, A), (bx, by, B) = real
        pa = pt(cx, cy, ax, ay)
        pb = pt(cx, cy, bx, by)
        print(f"A({ax},{ay}) -> ({pa[0]},{pa[1]})")
        print(f"B({bx},{by}) -> ({pb[0]},{pb[1]})")

        # 步1: 点A 拿起
        click(hwnd, pa[0], pa[1])
        _human.wait()
        c = cursor_item(pid, h, pInv)
        print(f"步1 点A: pCursorItem={c:#x} " + ("拿起A ✓" if c == A["unit"] else f"失败(期望 {A['unit']:#x})"))
        if c != A["unit"]:
            print("中止"); return 1
        # 步2: 点B 放A拿B
        click(hwnd, pb[0], pb[1])
        _human.wait()
        c = cursor_item(pid, h, pInv)
        print(f"步2 点B: pCursorItem={c:#x} " + ("拿起B ✓" if c == B["unit"] else f"失败(期望 {B['unit']:#x})"))
        if c != B["unit"]:
            print("中止"); return 1
        # 步3: 点A原格 放B
        click(hwnd, pa[0], pa[1])
        _human.wait()
        c = cursor_item(pid, h, pInv)
        print(f"步3 点A原格: pCursorItem={c:#x} " + ("放下✓" if c == 0 else "未放下"))
        items2 = get_items(pid, h)
        for it in items2:
            print(f"  交换后: txt={it['txt']} 格({it['gx']},{it['gy']})")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
