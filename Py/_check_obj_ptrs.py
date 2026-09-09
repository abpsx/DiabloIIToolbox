# -*- coding: utf-8 -*-
"""检查 obj 附近指针指向区域，找 ItemTxt 表（code 列模式）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

# obj 附近指针样值
cands = [0x128bedb0, 0x12677314, 0x130c29a0, 0x2ac8b08, 0x48a2db4, 0x1265d434]

def is_code4(b):
    return len(b) == 4 and all(32 <= x < 127 for x in b)

for base in cands:
    print(f"== {base:#x} ==")
    raw = mem.read(pid, h, base, 0x4000)
    if not raw:
        print("  不可读")
        continue
    # 扫 4 字节 code 模式：连续多行同一 stride 处是 code
    # 先找所有 "xxx "（4字母+空格）位置
    import re
    pos = []
    for m in re.finditer(rb"[A-Za-z]{3} ", raw):
        pos.append(m.start())
    print(f"  code样命中 {len(pos)} 个，前 20: {[hex(base+p) for p in pos[:20]]}")
    # 检查第一个命中附近是否行表
    if pos:
        p0 = pos[0]
        # 尝试各种 stride 找连续
        for stride in (0x12C, 0x130, 0x140, 0x150, 0x1A8, 0x200):
            cnt = 0
            for k in range(1, 8):
                q = p0 + k * stride
                if q + 4 <= len(raw) and is_code4(raw[q:q+4]) and raw[q:q+4] == raw[p0:p0+4]:
                    cnt += 1
                else:
                    break
            if cnt >= 3:
                print(f"    stride {stride:#x}: 连续 {cnt+1} 个相同 code @ {base+p0:#x}")
    # 行 0 假设：base 处 +0x40 是否 code
    c = mem.read(pid, h, base + 0x40, 4)
    ntype = mem.read(pid, h, base + 0x11E, 1)
    print(f"  base+0x40={c!r} base+0x11E={ntype[0] if ntype else -1}")

ctypes.windll.kernel32.CloseHandle(h)
