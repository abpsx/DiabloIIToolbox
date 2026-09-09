# -*- coding: utf-8 -*-
"""测试 AOB 定位仓库页数（当前应=10）"""
import sys, ctypes, time
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
h = mem.open_process_readonly(pid)

t0 = time.time()
addr = mem.find_stash_page_addr(pid, h, "FF0000000101000068676C20")
t1 = time.time()
print(f"AOB 定位: 页数地址=0x{addr:X} (耗时 {t1-t0:.2f}s)")

st = mem.read_stash_state(pid, h,
                          ui_offset="0x50D00", ui_open="0x60",
                          page_addr=0x02CBE36C,
                          page_aob="FF0000000101000068676C20")
print("仓库状态:", st)

# 第二次调用（缓存）
t2 = time.time()
st2 = mem.read_stash_state(pid, h, ui_offset="0x50D00", ui_open="0x60",
                           page_addr=0x02CBE36C,
                           page_aob="FF0000000101000068676C20")
t3 = time.time()
print(f"缓存命中: {st2} (耗时 {t3-t2:.2f}s)")
ctypes.windll.kernel32.CloseHandle(h)
