# -*- coding: utf-8 -*-
"""探索背包结构: 人物链 + 0x2337600/0x2337400 格子区"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else None

d2c = mem.module_base(pid, "D2CLIENT.DLL")
print(f"D2CLIENT 基址: {d2c:#x}")

pPlayer = dword(d2c + 0x11B800)
print(f"[D2CLIENT+0x11B800] pPlayer = {pPlayer:#x}" if pPlayer else "pPlayer 空")

# 探索 pPlayer 各偏移
if pPlayer:
    for off in (0x00, 0x04, 0x14, 0x2C, 0x5C, 0x60, 0x6C):
        v = dword(pPlayer + off)
        print(f"  pPlayer+{off:#x} = {v:#x}" if v else f"  pPlayer+{off:#x} = 0")

# 读用户确认的背包第一格/第二格地址
for a, lbl in ((0x2337600, "第一格(城镇卷)"), (0x2337400, "第二格(辨识卷)")):
    raw = mem.read(pid, h, a, 0x60)
    print(f"\n{a:#x} {lbl} 0x60 bytes:")
    for i in range(0, 0x60, 16):
        row = raw[i:i+16]
        hexs = " ".join(f"{b:02x}" for b in row)
        print(f"  +{i:02x}: {hexs}")

# 读格子区大块找规律: 0x2337400 往下 0x400
raw = mem.read(pid, h, 0x2337000, 0x800)
print(f"\n0x2337000..0x2337800 摘要 (每 0x20 一个 dword@+4 候选码表id):")
for i in range(0, 0x800, 0x20):
    d = int.from_bytes(raw[i+4:i+8], "little")
    d0 = int.from_bytes(raw[i:i+4], "little")
    print(f"  +{i:04x} addr={0x2337000+i:#x}: dword0={d0:#x} dword4={d:#x}")

ctypes.windll.kernel32.CloseHandle(h)
