# -*- coding: utf-8 -*-
"""截取游戏窗口（PrintWindow）"""
import ctypes, sys
from ctypes import wintypes

sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def find_windows(pid):
    wins = []
    @EnumWindowsProc
    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            pid2 = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid2))
            if pid2.value == pid:
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                wins.append((hwnd, buf.value))
        return True
    user32.EnumWindows(cb, 0)
    return wins

def shot(hwnd, path):
    user32.SetForegroundWindow(hwnd)
    ctypes.windll.kernel32.Sleep(300)
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    ok = user32.PrintWindow(hwnd, mdc, 2)  # PW_RENDERFULLCONTENT
    # 保存 BMP
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    with open(path, "wb") as f:
        f.write(b"BM")
        f.write((14 + 40 + len(buf)).to_bytes(4, "little"))
        f.write((0).to_bytes(4, "little"))
        f.write((14 + 40).to_bytes(4, "little"))
        # BITMAPINFOHEADER
        f.write(ctypes.string_at(ctypes.byref(bmi), 40))
        f.write(buf.raw)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    return ok, w, h

pid = mem.find_process("D2Loader.exe")
print("PID:", pid)
for hwnd, title in find_windows(pid):
    print(f"  窗口 0x{hwnd:X} title={title!r}")
    ok, w, h = shot(hwnd, rf"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_win_{hwnd:X}.bmp")
    print(f"  PrintWindow ok={ok} 尺寸 {w}x{h}")
