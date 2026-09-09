# -*- coding: utf-8 -*-
"""验证表 0x12879574[idx=物品行号] 与 ItemTxt wLocaleTxtNo"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

TB = 0x12879574
W = 0x1A8
BASE = 0x127A004C

def read_str(addr, maxlen=128):
    if not addr or addr < 0x10000:
        return None
    raw = mem.read(pid, h, addr, maxlen)
    if not raw:
        return None
    try:
        s = raw.decode("utf-16-le", errors="ignore").split("\x00")[0]
        if s and any(ord(c) > 0x2E80 for c in s[:3]):
            return s
    except Exception:
        pass
    try:
        return raw.split(b"\x00")[0].decode("utf-8", errors="ignore")
    except Exception:
        return None

for row, lbl in [(0, "hax"), (529, "tsc"), (530, "isc"), (587, "hp1"), (63, "sst"), (679, "pr1"), (713, "pr56")]:
    # ItemTxt wLocaleTxtNo
    raw = mem.read(pid, h, BASE + row * W + 0xF4, 2)
    wl = int.from_bytes(raw, "little") if raw else 0
    # 表[idx]
    ent = mem.read_dword(pid, h, TB + row * 4)
    s = read_str(ent)
    print(f"行 {row} ({lbl}): wLocaleTxtNo={wl}  表[{row}]={ent:#x} {s!r}")

# 顺带读表[2200] 和 wLocaleTxtNo=2200 的 ItemTxt 行
ent = mem.read_dword(pid, h, TB + 2200 * 4)
print(f"\n表[2200]={ent:#x} {read_str(ent)!r}")
ent = mem.read_dword(pid, h, TB + 5391 * 4)
print(f"表[5391]={ent:#x} {read_str(ent)!r}")
ent = mem.read_dword(pid, h, TB + 5425 * 4)
print(f"表[5425]={ent:#x} {read_str(ent)!r}")

ctypes.windll.kernel32.CloseHandle(h)
