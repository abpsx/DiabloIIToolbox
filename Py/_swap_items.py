# -*- coding: utf-8 -*-
"""仓库物品交换脚本（用户算法）:
- 物品坐标 = UnitAny.pPath(ObjectPath)+0x0C/+0x10 格坐标
- UI 基于屏幕中心等距绘制: 面板中心 = 客户区中心; 每格 32px
- 点击 = 客户区中心 + (格坐标 - 中心格) * 32 + 16(格中心)
- 交换: 点A拿起 -> 点B(放A+拿起B) -> 点A原格(放B)
- 每步读 pCursorItem(pInv+0x20) 验证
"""
from __future__ import annotations
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
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

def click(hwnd, x, y):
    lp = (y << 16) | (x & 0xFFFF)
    # 先发 WM_MOUSEMOVE 让游戏更新内部光标位置（后台可行，不抢真实鼠标）
    user32.SendMessageW(hwnd, 0x0200, 0, lp)  # WM_MOUSEMOVE
    time.sleep(0.05)
    # SendMessage 同步直达窗口过程（PostMessage 异步会被 D2 忽略/延迟）
    user32.SendMessageW(hwnd, 0x0201, 0, lp)  # WM_LBUTTONDOWN
    user32.SendMessageW(hwnd, 0x0202, 0, lp)  # WM_LBUTTONUP

def click_wait(hwnd, pid, h, pInv, expect, x, y, label):
    """点击并轮询等待 pCursorItem 达到期望值，超时(6s)重试一次。"""
    for attempt in (1, 2):
        click(hwnd, x, y)
        for _ in range(30):  # 最多 6s（后台点击延迟可能数秒）
            time.sleep(0.2)
            c = cursor_item(pid, h, pInv)
            if c == expect:
                print(f"{label}: pCursorItem={c:#x} ✓")
                return True
        c = cursor_item(pid, h, pInv)
        print(f"{label} 尝试{attempt}: pCursorItem={c:#x} (期望 {expect:#x})")
        if attempt == 1:
            time.sleep(1.0)
    return False

def get_items(pid, h):
    """读仓库物品: [(unit, txt, gx, gy, 占格记录首地址)]"""
    d2c = mem.module_base(pid, "D2CLIENT.DLL")
    pPlayer = dword(pid, h, d2c + 0x11B800)
    pInv = dword(pid, h, pPlayer + 0x60)
    cur = dword(pid, h, pInv + 0x0C)
    seen = set()
    out = []
    while cur and cur not in seen:
        seen.add(cur)
        txt = dword(pid, h, cur + 0x04)
        idat = dword(pid, h, cur + 0x14)
        loc45 = mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1
        if loc45 == 4:  # 仓库
            pip = dword(pid, h, cur + 0x2C)
            gx = dword(pid, h, pip + 0x0C)
            gy = dword(pid, h, pip + 0x10)
            out.append({"unit": cur, "txt": txt, "gx": gx, "gy": gy, "pInv": pInv})
        cur = dword(pid, h, idat + 0x64) if idat else 0
    return out

def cursor_item(pid, h, pInv):
    return dword(pid, h, pInv + 0x20)

def main():
    COLS, ROWS = 10, 10   # 仓库每页格数（实测校准）
    CELL = 29             # 格步长 = 28 内容 + 1 间隔
    DX, DY = -157, -9     # 面板中心相对客户区中心偏移（实测校准）
    dry = "--dry" in sys.argv
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    try:
        items = get_items(pid, h)
        print(f"仓库物品 {len(items)} 件:")
        for it in items:
            print(f"  txt={it['txt']} unit={it['unit']:#x} 格({it['gx']},{it['gy']})")
        if len(items) < 2:
            print("仓库物品不足 2 件，无法交换"); return 1
        A, B = items[0], items[1]
        pInv = A["pInv"]
        c0 = cursor_item(pid, h, pInv)
        if c0 != 0:
            print(f"警告: 光标上已有物品 {c0:#x}（残留/延迟生效），请先放回后重跑")
            return 1
        # 客户区中心
        hwnd = find_hwnd(pid)
        r = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(r))
        cx, cy = r.right // 2, r.bottom // 2
        print(f"hwnd=0x{hwnd:X} 客户区 {r.right}x{r.bottom} 中心({cx},{cy})")
        def pt(it):
            px = cx + DX + (it["gx"] - COLS // 2) * CELL + CELL // 2
            py = cy + DY + (it["gy"] - ROWS // 2) * CELL + CELL // 2
            return px, py
        pa, pb = pt(A), pt(B)
        print(f"A 格({A['gx']},{A['gy']}) -> 点击 {pa}")
        print(f"B 格({B['gx']},{B['gy']}) -> 点击 {pb}")
        if dry:
            print("[干跑] 未执行点击。坐标如上，确认后去掉 --dry 执行。")
            return 0
        # 1. 拿起 A
        click(hwnd, *pa)
        c = cursor_item(pid, h, pInv)
        exp = A["unit"]
        print(f"步1 点A: pCursorItem={c:#x} " + ("拿起A ✓" if c == exp else f"失败(期望 {exp:#x})"))
        if c != A["unit"]:
            print("中止"); return 1
        # 2. 点 B: 放 A + 拿起 B
        click(hwnd, *pb)
        c = cursor_item(pid, h, pInv)
        exp = B["unit"]
        print(f"步2 点B: pCursorItem={c:#x} " + ("拿起B ✓" if c == exp else f"失败(期望 {exp:#x})"))
        if c != B["unit"]:
            print("中止"); return 1
        # 3. 点 A 原格: 放 B
        click(hwnd, *pa)
        c = cursor_item(pid, h, pInv)
        print(f"步3 点A原格: pCursorItem={c:#x} {'放下✓' if c == 0 else '未放下'}")
        # 最终验证：A 的格坐标应变成 B 的原格坐标
        items2 = get_items(pid, h)
        for it in items2:
            print(f"  交换后: txt={it['txt']} 格({it['gx']},{it['gy']})")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
