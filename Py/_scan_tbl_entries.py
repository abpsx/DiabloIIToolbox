# -*- coding: utf-8 -*-
"""扫描 0x129F0ECC 表的 entry 区，找 off 指向白羊宫钥匙(0x124F5A6C) 的条目"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

TB = 0x129F0ECC
# 读表头 + entry 区（尝试 12 字节 entry）
hdr = mem.read(pid, h, TB, 16)
print("表头:", hdr.hex(" "))

# 池基假设：0x124F0000（D2Lang 池区起点？）
# 先扫描 entry 区，找 off 字段（entry+4）匹配 0x124F5A6C - 池基 的候选
for pool_base in (0x124F0000, 0x124F4000, 0x124A0000, 0x12400000):
    target_off = 0x124F5A6C - pool_base
    print(f"\n== 池基 {pool_base:#x}, target_off={target_off:#x} ==")
    found = []
    for esz in (12, 16, 8):
        hits = []
        for i in range(0, 20000):
            ent = mem.read(pid, h, TB + 16 + i * esz, esz)
            if not ent or len(ent) < esz:
                break
            # 取 off 候选：entry 内任意 4 字节 == target_off
            for k in range(0, esz - 3):
                v = int.from_bytes(ent[k:k+4], "little")
                if v == target_off:
                    hits.append((i, k))
            if hits and len(hits) > 50:
                break
        if hits:
            print(f"  entry宽{esz}: {len(hits)} 命中, 前5: {[(i,k) for i,k in hits[:5]]}")
            for i, k in hits[:3]:
                full = mem.read(pid, h, TB + 16 + i * esz, esz)
                print(f"    entry[{i}] @ {TB+16+i*esz:#x}: {full.hex(' ')} (off@+{k})")

# 直接 dump entry 区前 20 个 12 字节
print("\n== entry 区前 20 个 (12B) ==")
for i in range(20):
    ent = mem.read(pid, h, TB + 16 + i * 12, 12)
    if ent and len(ent) == 12:
        a, b, c = int.from_bytes(ent[0:4], "little"), int.from_bytes(ent[4:8], "little"), int.from_bytes(ent[8:12], "little")
        print(f"  [{i}] {a:#x} {b:#x} {c:#x}")

ctypes.windll.kernel32.CloseHandle(h)
