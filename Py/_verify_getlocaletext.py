# -*- coding: utf-8 -*-
"""按破译的 GetLocaleText 逻辑验证: 表A索引[idx] -> entry -> 表B[entry] -> 值指针"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def word(a):
    raw = mem.read(pid, h, a, 2)
    return int.from_bytes(raw, "little") if raw else 0
def dword(a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

# 分派表
D = {
    "<10000": (dword(0x2510A64), dword(0x2510A68)),
    "10000-19999": (dword(0x2510A80), dword(0x2510A6C)),
    ">=20000": (dword(0x2510A84), dword(0x2510A70)),
}
print("分派表:", {k: (f"{a:#x}", f"{b:#x}") for k, (a, b) in D.items()})

def lookup(ta, tb, idx):
    """复刻 0x2509050：返回值指针，None 表示失败。"""
    cx = word(ta + 2)                 # 索引数组长度
    e = idx if idx < cx else 0x1F4    # cmp dx,cx; jb 保持 idx，否则 0x1F4
    entry_no = word(ta + 0x15 + e * 2)  # 索引数组[e] -> entry 序号
    n_entries = dword(ta + 4)         # entry 总数
    if entry_no >= n_entries:
        return None, "entry>=count"
    # entry 有效标志校验（模拟 0x250907A-0x2509096）
    idx_arr_end = ta + cx * 2 + 0x15  # esi = ta + cx*2 + 0x15
    entry_addr = idx_arr_end + entry_no * 17  # shl4 + add = *17
    entry_end = ta + dword(ta + 0x11)
    if entry_addr >= entry_end:
        return None, "entry越界"
    if mem.read(pid, h, entry_addr, 1) != b"\x01":
        return None, "entry标志!=1"
    return dword(tb + entry_no * 4), f"entry={entry_no}"

def read_str(addr, maxlen=200):
    if not addr:
        return None
    raw = mem.read(pid, h, addr, maxlen)
    if not raw:
        return None
    s = raw.decode("utf-16-le", errors="ignore").split("\x00")[0]
    return s

tests = [
    (5391, "pr1 白羊宫钥匙?"),
    (5425, "pr56 天鹰座?"),
    (2200, "tsc 城镇卷?"),
    (2202, "isc 辨识卷?"),
    (1976, "hax?"),
    (2039, "sst?"),
    (2266, "hp1?"),
    (0, "idx0?"),
]
for idx, lbl in tests:
    ta, tb = D["<10000"]
    ptr, info = lookup(ta, tb, idx)
    s = read_str(ptr)
    print(f"GetLocaleText({idx}) {lbl}: ptr={ptr:#x} info={info} str={s!r}")

ctypes.windll.kernel32.CloseHandle(h)
