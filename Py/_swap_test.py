# -*- coding: utf-8 -*-
"""实验: 验证 D2 点击是否使用真实鼠标位置(CursorHover)而非 PostMessage lParam。
流程: 读物品 -> 拿起(0,0) -> SetCursorPos 到 (1,1) + PostMessage 点击 -> 读状态
"""
from __future__ import annotations
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

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
                        "gy": dword(pid, h, pip + 0x10)})
        cur = dword(pid, h, idat + 0x64) if idat else 0
    return out, pInv

def state(pid, h, d2c, pInv):
    return (dword(pid, h, pInv + 0x20), dword(pid, h, d2c + 0x11C98C),
            dword(pid, h, d2c + 0xEE4AC), dword(pid, h, d2c + 0xEE4B0))

def client_to_screen(hwnd, x, y):
    p = wintypes.POINT(x, y)
    user32.ClientToScreen(hwnd, ctypes.byref(p))
    return p.x, p.y

def main():
    COLS, ROWS, CELL = 10, 10, 29
    DX, DY = -157, -9
    pid = mem.find_process("D2Loader.exe")
    if not pid: print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    try:
        d2c = mem.module_base(pid, "D2CLIENT.DLL")
        items, pInv = get_items(pid, h)
        for it in items:
            print(f"  txt={it['txt']} 格({it['gx']},{it['gy']})")
        A = items[0]
        hwnd = find_hwnd(pid)
        r = wintypes.RECT(); user32.GetClientRect(hwnd, ctypes.byref(r))
        cx, cy = r.right // 2, r.bottom // 2
        def pt(it):
            return (cx + DX + (it["gx"] - COLS // 2) * CELL + CELL // 2,
                    cy + DY + (it["gy"] - ROWS // 2) * CELL + CELL // 2)
        pa = pt(A)
        print(f"A({A['gx']},{A['gy']}) 客户区点击 {pa}")
        # 步1: 拿起 A
        user32.PostMessageW(hwnd, 0x0201, 0, (pa[1] << 16) | pa[0])
        user32.PostMessageW(hwnd, 0x0202, 0, (pa[1] << 16) | pa[0])
        time.sleep(1.0)
        c, rct, hx, hy = state(pid, h, d2c, pInv)
        print(f"步1后: pCursorItem={c:#x} CursorType={rct} Hover=({hx},{hy})")
        if c != A["unit"]:
            print("拿起失败"); return 1
        # 步2: 真实鼠标移到 A 原格(0,0), PostMessage 点 (0,0) —— 应放回原位
        sx, sy = client_to_screen(hwnd, pa[0], pa[1])
        user32.SetCursorPos(sx, sy)
        time.sleep(0.3)
        user32.PostMessageW(hwnd, 0x0201, 0, (pa[1] << 16) | pa[0])
        user32.PostMessageW(hwnd, 0x0202, 0, (pa[1] << 16) | pa[0])
        time.sleep(1.0)
        c, rct, hx, hy = state(pid, h, d2c, pInv)
        print(f"步2(点原格+真实鼠标)后: pCursorItem={c:#x} CursorType={rct} Hover=({hx},{hy})")
        # 步3: 再拿起 A, 真实鼠标移到 B 格, PostMessage 点 B 格
        user32.PostMessageW(hwnd, 0x0201, 0, (pa[1] << 16) | pa[0])
        user32.PostMessageW(hwnd, 0x0202, 0, (pa[1] << 16) | pa[0])
        time.sleep(1.0)
        c, rct, hx, hy = state(pid, h, d2c, pInv)
        print(f"步3(再拿起)后: pCursorItem={c:#x} CursorType={rct} Hover=({hx},{hy})")
        if len(items) > 1:
            B = items[1]
            pb = pt(B)
            sx, sy = client_to_screen(hwnd, pb[0], pb[1])
            user32.SetCursorPos(sx, sy)
            time.sleep(0.3)
            user32.PostMessageW(hwnd, 0x0201, 0, (pb[1] << 16) | pb[0])
            user32.PostMessageW(hwnd, 0x0202, 0, (pb[1] << 16) | pb[0])
            time.sleep(1.0)
            c, rct, hx, hy = state(pid, h, d2c, pInv)
            print(f"步4(真实鼠标在B格+点B格)后: pCursorItem={c:#x} CursorType={rct} Hover=({hx},{hy})")
            items2, _ = get_items(pid, h)
            for it in items2:
                print(f"  现在: txt={it['txt']} 格({it['gx']},{it['gy']})")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
