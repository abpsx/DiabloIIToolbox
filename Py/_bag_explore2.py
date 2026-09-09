# -*- coding: utf-8 -*-
"""探索背包 v2: pInventory(0x49571C0) 结构 + 物品链表"""
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
pPlayer = dword(d2c + 0x11B800)
pInv = dword(pPlayer + 0x60)
print(f"pPlayer={pPlayer:#x}  pInventory=[pPlayer+0x60]={pInv:#x}")

# 读 pInventory UnitAny 结构
raw = mem.read(pid, h, pInv, 0x80)
print(f"\npInventory 0x80 bytes:")
for i in range(0, 0x80, 16):
    row = raw[i:i+16]
    print(f"  +{i:02x}: " + " ".join(f"{b:02x}" for b in row))

# 关键字段
t0 = dword(pInv + 0x00)
t4 = dword(pInv + 0x04)
t14 = dword(pInv + 0x14)
t64 = dword(pInv + 0x64)
print(f"\npInv+0x00(type)={t0}  +0x04(txt)={t4:#x}({t4})  +0x14(pItemData)={t14:#x}  +0x64={t64:#x}")

# 若 pItemData 是 ItemData: 读 pNextInvItem = [pItemData+0x64]? 或 [pItemData+0x??]
if t14:
    idata = mem.read(pid, h, t14, 0x70)
    print(f"\npItemData 0x70 bytes:")
    for i in range(0, 0x70, 16):
        row = idata[i:i+16]
        print(f"  +{i:02x}: " + " ".join(f"{b:02x}" for b in row))
    for off in (0x64, 0x6C, 0x60):
        print(f"  [pItemData+{off:#x}] = {dword(t14+off):#x}")

# 尝试遍历: 假设 pInventory 就是第一个物品 UnitAny, next = [pItemData+0x64]
print("\n--- 链表遍历尝试 (pItemData+0x64 as next) ---")
cur = pInv
seen = set()
for i in range(50):
    if not cur or cur in seen:
        break
    seen.add(cur)
    typ = dword(cur)
    txt = dword(cur + 4)
    idat = dword(cur + 0x14)
    nxt = dword(idat + 0x64) if idat else 0
    print(f"  [{i}] unit={cur:#x} type={typ} txt={txt}(0x{txt:x}) pItemData={idat:#x} next={nxt:#x}")
    cur = nxt

ctypes.windll.kernel32.CloseHandle(h)
