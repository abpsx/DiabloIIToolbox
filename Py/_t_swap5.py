# -*- coding: utf-8 -*-
"""窗口前置 + 连续5次来回交换（530<->47 对调）。"""
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import _swap_cross as sc

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("D2Loader.exe 未运行"); sys.exit(1)
hwnd = sc.find_hwnd(pid)
ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(1.2)
print("窗口已前置:", hex(hwnd))

for i in range(5):
    print(f"===== 第 {i+1} 次交换 =====")
    rc = sc.main()
    time.sleep(1.8)  # 步间停顿便于观察
print("完成 5 次")
