# -*- coding: utf-8 -*-
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
print("PID", pid)
if not pid:
    sys.exit()
h = mem.open_process_readonly(pid)

# 目标：hpo=大血瓶、hpf=治疗药剂、mpo=强力法力药?、pr=完美红宝石?
targets = {
    "大血瓶": ("utf8", "大血瓶".encode("utf-8")),
    "大血瓶16": ("utf16", "大血瓶".encode("utf-16-le")),
    "完美红宝石": ("utf8", "完美红宝石".encode("utf-8")),
    "完美红宝石16": ("utf16", "完美红宝石".encode("utf-16-le")),
    "轻微药": ("utf8", "轻微药".encode("utf-8")),
}

regions = [
    (0x124F0000, 0x12500000),
    (0x13550000, 0x13570000),
    (0x12A00000, 0x12A50000),
]


def search(addr, size, needle):
    hits = []
    buf = mem.read(pid, h, addr, size)
    pos = 0
    while True:
        i = buf.find(needle, pos)
        if i < 0:
            break
        hits.append(addr + i)
        pos = i + 1
        if len(hits) >= 8:
            break
    return hits


for rname, (lo, hi) in zip("tbl_b区 tbl_a区 utf8表区".split(), regions):
    for tname, (enc, needle) in targets.items():
        hits = search(lo, hi - lo, needle)
        if hits:
            print(rname, tname, [hex(x) for x in hits])
ctypes.windll.kernel32.CloseHandle(h)
