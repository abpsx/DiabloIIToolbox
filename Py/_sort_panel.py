# -*- coding: utf-8 -*-
"""仓库/背包物品整理（面板基准版）。
- 面板: loc=0 背包 / loc=4 仓库
- 基准: 每个面板"第一格左上角"的客户区坐标（已通过鼠标悬停物品反推校准）
  仓库 (538,370) / 背包 (857,541)；格步长 29px（格内容 28 + 间隔 1）
- 排序: 按 txt(物品码) 升序，目标格从左到右、从上到下
- 移动: 拿起A -> 点目标格(空则放/有物品则交换) -> 放回原格或处理冲突
- 每步读 pCursorItem 验证; --dry 只打印计划
"""
from __future__ import annotations
import sys, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem
import _human
import _layout

user32 = ctypes.WinDLL("user32", use_last_error=True)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

CELL = 29
# loc -> (第一格左上客户区x, 第一格左上客户区y, 格数(列,行))
PANELS = {
    0: {"name": "背包", "base": (857, 541), "grid": (10, 4)},
    4: {"name": "仓库", "base": (538, 370), "grid": (10, 10)},
}

def dword(pid, h, a):
    raw = mem.read(pid, h, a, 4)
    return int.from_bytes(raw, "little") if raw else 0

def find_hwnd(pid):
    found = []
    def cb(hwnd, lp):
        if user32.IsWindowVisible(hwnd):
            p = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid:
                found.append(hwnd)
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found[0] if found else 0

def get_items(pid, h, loc):
    """读指定面板(loc)的物品, 返回 [{unit,txt,gx,gy}]"""
    d2c = mem.module_base(pid, "D2CLIENT.DLL")
    pPlayer = dword(pid, h, d2c + 0x11B800)
    pInv = dword(pid, h, pPlayer + 0x60)
    cur = dword(pid, h, pInv + 0x0C)
    seen = set(); out = []
    while cur and cur not in seen:
        seen.add(cur)
        txt = dword(pid, h, cur + 0x04)
        idat = dword(pid, h, cur + 0x14)
        loc45 = mem.read(pid, h, idat + 0x45, 1)[0] if idat else -1
        if loc45 == loc:
            pip = dword(pid, h, cur + 0x2C)
            out.append({"unit": cur, "txt": txt,
                        "gx": dword(pid, h, pip + 0x0C),
                        "gy": dword(pid, h, pip + 0x10)})
        cur = dword(pid, h, idat + 0x64) if idat else 0
    return out, pInv

def cursor_item(pid, h, pInv):
    return dword(pid, h, pInv + 0x20)

def pt(base, gx, gy):
    """面板格中心 = 基准(第一格左上) + 格x步长 + 半格"""
    return (base[0] + gx * CELL + CELL // 2,
            base[1] + gy * CELL + CELL // 2)

def click(hwnd, x, y):
    _human.click(hwnd, x, y)

def grid_seq(cols, rows, n):
    return [(x, y) for y in range(rows) for x in range(cols)][:n]

def main():
    dry = "--dry" in sys.argv
    pid = None
    locs = [0, 4]  # 默认整理背包+仓库
    out = None
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--pid" and i + 1 < len(sys.argv):
            pid = int(sys.argv[i + 1]); i += 2; continue
        if a == "--loc" and i + 1 < len(sys.argv):
            locs = [int(sys.argv[i + 1])]; i += 2; continue
        if a == "--out" and i + 1 < len(sys.argv):
            out = sys.argv[i + 1]; i += 2; continue
        i += 1
    if not pid:
        pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    if out:
        try:
            sys.stdout = open(out, "w", encoding="utf-8-sig")
        except Exception:
            pass
    h = mem.open_process_readonly(pid)
    try:
        lays = _layout.get(pid, h)
        if "stash" in lays and "inventory" in lays:
            PANELS.update({
                0: {"name": "背包", "base": (lays["inventory"][0], lays["inventory"][1]),
                    "grid": (lays["inventory"][2], lays["inventory"][3])},
                4: {"name": "仓库", "base": (lays["stash"][0], lays["stash"][1]),
                    "grid": (lays["stash"][2], lays["stash"][3])},
            })
        hwnd = find_hwnd(pid)
        for loc in locs:
            if loc not in PANELS:
                continue
            P = PANELS[loc]
            items, pInv = get_items(pid, h, loc)
            if not items:
                print(f"[{P['name']}] 无物品"); continue
            cols, rows = P["grid"]
            if len(items) > cols * rows:
                print(f"[{P['name']}] 物品 {len(items)} 件超过 {cols}x{rows} 格"); continue
            srt = sorted(items, key=lambda it: it["txt"])
            targets = grid_seq(cols, rows, len(srt))
            print(f"===== [{P['name']}] {len(srt)} 件 (按 txt 升序) =====")
            for it, tg in zip(srt, targets):
                mark = " ✓" if (it["gx"], it["gy"]) == tg else ""
                print(f"  txt={it['txt']} {it['unit']:#x} ({it['gx']},{it['gy']}) -> ({tg[0]},{tg[1]}){mark}")
            if dry:
                continue
            # ---- 执行整理：选排+交换 ----
            by_unit = {it["unit"]: it for it in srt}
            for i, A in enumerate(srt):
                tg = targets[i]
                if (A["gx"], A["gy"]) == tg:
                    continue
                # 拿起 A
                ax, ay = A["gx"], A["gy"]
                pa = pt(P["base"], ax, ay)
                click(hwnd, pa[0], pa[1])
                _human.wait()
                c = cursor_item(pid, h, pInv)
                if c != A["unit"]:
                    print(f"  txt={A['txt']} 拿起失败({ax},{ay})"); continue
                # 点目标格
                pb = pt(P["base"], tg[0], tg[1])
                click(hwnd, pb[0], pb[1])
                _human.wait()
                c = cursor_item(pid, h, pInv)
                if c == 0:
                    A["gx"], A["gy"] = tg
                    print(f"  txt={A['txt']} -> ({tg[0]},{tg[1]}) 放下 ✓")
                elif c == A["unit"]:
                    # 放不下：放回原位
                    click(hwnd, pa[0], pa[1])
                    _human.wait()
                    print(f"  txt={A['txt']} 目标({tg[0]},{tg[1]})冲突，放回原位")
                else:
                    # 交换：A 放入目标，c 在光标 -> 放回 A 原格
                    B = by_unit.get(c)
                    click(hwnd, pa[0], pa[1])
                    _human.wait()
                    c2 = cursor_item(pid, h, pInv)
                    if c2 == 0:
                        A["gx"], A["gy"] = tg
                        if B:
                            B["gx"], B["gy"] = ax, ay
                        print(f"  txt={A['txt']} -> ({tg[0]},{tg[1]}) ✓  交换出 {c:#x} 到 ({ax},{ay})")
                    else:
                        A["gx"], A["gy"] = tg
                        print(f"  txt={A['txt']} -> ({tg[0]},{tg[1]}) ✓  交换出 {c:#x} 放回失败(光标残留)")
            # 最终状态
            print(f"  -- [{P['name']}] 整理后 --")
            items2, _ = get_items(pid, h, loc)
            for it in sorted(items2, key=lambda x: x["txt"]):
                print(f"    txt={it['txt']} 格({it['gx']},{it['gy']})")
    finally:
        try:
            sys.stdout.flush()
        except Exception:
            pass
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
