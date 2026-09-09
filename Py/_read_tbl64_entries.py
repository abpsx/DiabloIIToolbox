# -*- coding: utf-8 -*-
"""读 0x129F0ECC 表条目（4B 偏移），验证 2200/5391/5425 是否指向城镇卷/白羊宫钥匙"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

TB = 0x129F0ECC
# 尝试多种头偏移与条目宽
for hdr in (0, 4, 8, 12, 16, 20, 24, 32):
    for esz in (4, 8):
        vals = {}
        for idx in (0, 1, 529, 2200, 2202, 5391, 5425):
            ent = mem.read(pid, h, TB + hdr + idx * esz, esz)
            if ent and len(ent) == esz:
                v = int.from_bytes(ent[:4], "little")
                vals[idx] = v
        # 检查 2200 是否指向城镇卷候选
        ok_cnt = 0
        for idx in (2200, 5391, 5425):
            v = vals.get(idx, -1)
            # 可能池基
            for pb in (0x124F4000, 0x124F0000, 0x124E0000, 0x12400000, 0x12500000):
                if pb + v == 0x124EC712 or pb + v == 0x124F5A6C:
                    ok_cnt += 1
        if ok_cnt:
            print(f"hdr={hdr} esz={esz}: MATCH {vals}")
print("done")
# 直接读几个关键位置
for a in (TB+16+2200*4, TB+16+5391*4, TB+16+5425*4, TB+16+529*4, TB+4+2200*4, TB+8+2200*4, TB+12+2200*4, TB+20+2200*4):
    ent = mem.read(pid, h, a, 4)
    print(f"{a:#x}: {int.from_bytes(ent,'little') if ent else None:#x}")

ctypes.windll.kernel32.CloseHandle(h)
