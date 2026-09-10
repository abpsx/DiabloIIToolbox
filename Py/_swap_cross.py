# -*- coding: utf-8 -*-
"""跨面板交换：背包物品 ↔ 仓库物品 对调。
- 面板基准（第一格左上角客户区坐标）: 背包(857,541) / 仓库(538,370)，格步长 29px
- 默认: 背包格(0,0)物品 <-> 仓库格(1,0)物品（可传参 --src-gx --src-gy --dst-gx --dst-gy 指定）
- 机制: WM_MOUSEMOVE + SendMessage 点击（后台、不抢鼠标）
- 验证: 每步读 pCursorItem，结束后读 loc45 确认面板归属
"""
from __future__ import annotations
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import _human
import _layout

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

CELL = 29
BASES = {0: (857, 541), 4: (538, 370)}  # loc -> 第一格左上客户区
NAMES = {0: "背包", 4: "仓库"}

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

def get_panel(pid, h, loc):
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
        if loc45 == loc:
            pip = dword(pid, h, cur + 0x2C)
            out.append({"unit": cur, "txt": txt, "idat": idat,
                        "gx": dword(pid, h, pip + 0x0C),
                        "gy": dword(pid, h, pip + 0x10)})
        cur = dword(pid, h, idat + 0x64) if idat else 0
    return out, pInv

def item_at(items, gx, gy):
    for it in items:
        if it["gx"] == gx and it["gy"] == gy:
            return it
    return None

def cursor_item(pid, h, pInv):
    return dword(pid, h, pInv + 0x20)

def loc_of(pid, h, unit):
    idat = dword(pid, h, unit + 0x14)
    return mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1

def pt(base, gx, gy):
    return (base[0] + gx * CELL + CELL // 2,
            base[1] + gy * CELL + CELL // 2)

def click(hwnd, x, y):
    _human.click(hwnd, x, y)

def main():
    global CELL, BASES
    pid0 = mem.find_process("D2Loader.exe")
    if pid0:
        h0 = mem.open_process_readonly(pid0)
        lays = _layout.get(pid0, h0)
        ctypes.windll.kernel32.CloseHandle(h0)
        if "stash" in lays and "inventory" in lays:
            CELL = lays["stash"][4]
            BASES = {0: (lays["inventory"][0], lays["inventory"][1]),
                     4: (lays["stash"][0], lays["stash"][1])}
    # 默认交换: 背包(0,0) <-> 仓库(1,0)
    SRC_LOC, DST_LOC = 0, 4
    SRC_G, DST_G = (0, 0), (1, 0)
    for a in sys.argv:
        if a.startswith("--src="):
            x, y = a[6:].split(","); SRC_G = (int(x), int(y))
        elif a.startswith("--dst="):
            x, y = a[6:].split(","); DST_G = (int(x), int(y))

    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    try:
        hwnd = find_hwnd(pid)
        src_items, pInv = get_panel(pid, h, SRC_LOC)
        dst_items, _ = get_panel(pid, h, DST_LOC)
        A = item_at(src_items, *SRC_G)
        B = item_at(dst_items, *DST_G)
        if not A:
            print(f"{NAMES[SRC_LOC]} 格{SRC_G} 无物品"); return 1
        print(f"A = {NAMES[SRC_LOC]} txt={A['txt']} {A['unit']:#x} 格({A['gx']},{A['gy']})")
        print(f"B = {NAMES[DST_LOC]} " + (f"txt={B['txt']} {B['unit']:#x} 格({B['gx']},{B['gy']})" if B else f"格{DST_G} 空"))

        # 1) 拿起 A
        pa = pt(BASES[SRC_LOC], *SRC_G)
        click(hwnd, *pa)
        _human.wait()
        c = cursor_item(pid, h, pInv)
        if c != A["unit"]:
            print("拿起 A 失败"); return 1
        print(f"拿起 A {A['txt']:#x} ✓")

        # 2) 点 B 的格: 空则放下A; 有物品则拿起B
        pb = pt(BASES[DST_LOC], *DST_G)
        click(hwnd, *pb)
        _human.wait()
        c = cursor_item(pid, h, pInv)
        if c == 0:
            print(f"A -> {NAMES[DST_LOC]} {DST_G} 放下 ✓ (原格空，纯移动)")
            return 0
        if c == A["unit"]:
            print("目标格放不下，A 未放下"); return 1
        B = next((x for x in dst_items if x["unit"] == c), None)
        print(f"A 放入 {NAMES[DST_LOC]} {DST_G}，拿起 B txt={B['txt']:#x} ✓")

        # 3) 点 A 原格: 放下 B
        click(hwnd, *pa)
        _human.wait()
        c = cursor_item(pid, h, pInv)
        if c == 0:
            print(f"B -> {NAMES[SRC_LOC]} {SRC_G} 放下 ✓")
        else:
            print(f"B 未放下(光标残留 {c:#x})")

        # 验证
        _human.wait()
        print(f"验证: A loc={loc_of(pid,h,A['unit'])} (应为{DST_LOC})  B loc={loc_of(pid,h,B['unit'])} (应为{SRC_LOC})")
        print("当前面板:")
        for loc in (0, 4):
            items, _ = get_panel(pid, h, loc)
            print(f"  {NAMES[loc]}: " + ", ".join(f"{i['txt']}({i['gx']},{i['gy']})" for i in items))
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
