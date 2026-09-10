#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""项链1数值定位：1) 扩展表行完整字节找 mod 数值字段 2) 大范围扫描物品结构找 19/2/4"""
import sys
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mr

pid = mr.find_process("D2Loader.exe")
h = mr.open_process_readonly(pid)
sP = 0x1244DFCC

def w(a): return mr.read_value(pid, h, a, "word")
def dw(a): return mr.read_value(pid, h, a, "dword")

# ---------- 1) 扩展表行完整结构 ----------
print("== 扩展表行结构（id 985/1312/1051/742）==")
for iid in (985, 1312, 1051, 742):
    raw = mr.read(pid, h, sP + iid * 0x90, 0x90)
    nm = raw.split(b"\x00")[0]
    print(f"\nid{iid} 行{iid}: name={nm.decode('utf-8', 'replace')}")
    # 前 0x10 是 name 区，之后分析 dword
    vals = []
    for off in range(0x0C, 0x90, 4):
        v = dw(sP + iid * 0x90 + off)
        if v:
            vals.append(f"+{off:02X}={v}")
    print("  非零 dword:", ", ".join(vals[:20]))

# ---------- 2) 大范围扫描 ----------
base = mr.read_ptr(pid, h, mr.module_base(pid, "D2Client.dll") + 0x11B800)
inv = mr.read_ptr(pid, h, base + 0x60)
first = mr.read_ptr(pid, h, inv + 0x0C)
cur = first
while cur:
    txt = w(cur + 0x04)
    idat = mr.read_ptr(pid, h, cur + 0x14)
    if idat:
        words = [w(idat + 0x38 + i * 2) for i in range(6)]
        if words == [985, 1312, 1051, 742, 0, 0]:
            break
    nxt = mr.read_ptr(pid, h, idat + 0x64) if idat else 0
    cur = nxt

if cur:
    print(f"\n== 项链1 cur={hex(cur)} idat={hex(idat)} ==")
    # 扫 cur ±0x80
    print("cur 附近找 19/2/4:")
    for off in range(-0x80, 0x80, 2):
        v = w(cur + off)
        if v in (19, 2, 4):
            print(f"   cur{off:+04X} = {v}")
    # 扫 idat 大范围
    print("idat -0x100..+0x100 找 19:")
    for off in range(-0x100, 0x100, 2):
        v = w(idat + off)
        if v == 19:
            print(f"   idat{off:+04X} = {v}")
    print("idat 前 0x30 的 dword 结构:")
    for off in range(0, 0x30, 4):
        print(f"   +{off:02X} = {dw(idat+off)}")
    # cur 关键字段
    print("cur 前 0x20 dword:")
    for off in range(0, 0x20, 4):
        print(f"   +{off:02X} = {dw(cur+off)}")
