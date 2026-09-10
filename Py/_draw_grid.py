# -*- coding: utf-8 -*-
"""在游戏窗口客户区绘制假设的仓库格子网格，供用户对照偏差。
公式: 第一格左上角 = 客户区中心 - 中心格(COLS/2, ROWS/2) * 32
当前假设: COLS=10, ROWS=8, 每格 32px, 面板中心=客户区中心
"""
import ctypes, time, sys
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

COLS, ROWS = 10, 10
CELL = 29      # 格步长 = 28 内容 + 1 间隔
CSZ = 28       # 格子内容尺寸
PS_SOLID = 0
NULL_BRUSH = 5

def find_hwnd(pid):
    found = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lp):
        if user32.IsWindowVisible(hwnd):
            p = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid:
                found.append(hwnd)
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found[0] if found else 0

def main():
    import mem_read as mem
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    hwnd = find_hwnd(pid)
    r = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    cx, cy = r.right // 2, r.bottom // 2
    x0 = cx - (COLS // 2) * CELL - 157   # -154 -3 = 左移 5.4 格
    y0 = cy - (ROWS // 2) * CELL - 9     # 上移 0.3 格
    print(f"hwnd=0x{hwnd:X} 客户区 {r.right}x{r.bottom} 中心({cx},{cy})")
    print(f"第一格左上角 = ({x0},{y0})  每格 {CELL}px  网格 {COLS}x{ROWS}")
    hdc = user32.GetDC(hwnd)
    if not hdc:
        print("GetDC 失败"); return 1
    # 创建画笔
    def make_pen(color, w=2):
        return gdi32.CreatePen(PS_SOLID, w, color)
    red, green = make_pen(0x0000FF, 3), make_pen(0x00FF00, 3)
    white = make_pen(0xFFFFFF, 1)
    gdi32.SelectObject(hdc, gdi32.GetStockObject(NULL_BRUSH))
    print("绘制中... 看游戏窗口里的网格，告诉我偏差。15 秒后自动退出")
    end = time.time() + 15
    while time.time() < end:
        # 逐格画 28x28 边框（格间距 1px）
        gdi32.SelectObject(hdc, white)
        for c in range(COLS):
            for rr in range(ROWS):
                gdi32.Rectangle(hdc, x0 + c * CELL, y0 + rr * CELL,
                                x0 + c * CELL + CSZ, y0 + rr * CELL + CSZ)
        # 高亮 (0,0) 红框、(1,1) 绿框
        gdi32.SelectObject(hdc, red)
        gdi32.Rectangle(hdc, x0, y0, x0 + CSZ, y0 + CSZ)
        gdi32.SelectObject(hdc, green)
        gdi32.Rectangle(hdc, x0 + CELL, y0 + CELL, x0 + CELL + CSZ, y0 + CELL + CSZ)
        time.sleep(0.2)
    user32.ReleaseDC(hwnd, hdc)
    print("结束")
    return 0

if __name__ == "__main__":
    sys.exit(main())
