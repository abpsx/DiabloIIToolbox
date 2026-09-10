# -*- coding: utf-8 -*-
"""全物品交换 v3：背包 <-> 仓库 整体对调（规划 + 链式交换 + 人性化操作）。
- 面板基准（第一格左上客户区）: 背包(857,541) / 仓库(538,370)，格步长 29px
- 核心:
  1) 规划: 每件物品分配"目标面板 + 目标格"。多格物品优先（SIZES 表），
     先扫目标面板找连续空区，1x1 物品升序填剩余空位。
  2) 链式交换: 拿起一件沿"当前格->目标格"链走，目标格被占则带走占者继续，
     直到落到空格——天然实现"直接对调"（2格环）且不需要临时区（仓库满也可）。
  3) 多格物品: 目标区域若有未归位物品由链式自动带离；放不下则跳过该格。
- 人性化: _human.click 贝塞尔轨迹+位置抖动, _human.wait 间隔扰动
- 尺寸表: txt -> (宽,高)，默认 1x1；mod 大件在此扩展（47=城镇卷之书 1x3 垂直）。
- 机制: WM_MOUSEMOVE + SendMessage 点击; 每步读 pCursorItem 验证; 步数上限防死循环。
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
BASES = {0: (857, 541), 4: (538, 370)}
NAMES = {0: "背包", 4: "仓库"}
GRIDS = {0: (10, 4), 4: (10, 10)}
SIZES = {47: (1, 3)}  # txt -> (宽,高) 占格，默认 1x1

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

def get_panel(pid, h, loc):
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
            w, hh = SIZES.get(txt, (1, 1))
            out.append({"unit": cur, "txt": txt, "loc": loc, "size": (w, hh),
                        "gx": dword(pid, h, pip + 0x0C),
                        "gy": dword(pid, h, pip + 0x10)})
        cur = dword(pid, h, idat + 0x64) if idat else 0
    return out, pInv

def cursor_item(pid, h, pInv):
    return dword(pid, h, pInv + 0x20)

def pt(base, gx, gy):
    return (base[0] + gx * CELL + CELL // 2,
            base[1] + gy * CELL + CELL // 2)

def cells_of(item, gx, gy):
    w, h = item["size"]
    return [(gx + dx, gy + dy) for dy in range(h) for dx in range(w)]

def plan(pid, h, items):
    """分配目标: 返回 {unit: (target_loc, gx, gy)}。多格优先、升序填剩余。"""
    plan_map = {}
    used = {}  # (loc,gx,gy) -> unit
    groups = {0: [], 4: []}
    for it in items:
        groups[it["loc"]].append(it)
    for src_loc, tgt_loc in ((0, 4), (4, 0)):
        lst = sorted(groups[src_loc], key=lambda x: (x["size"][0] * x["size"][1] > 1, x["txt"]))
        for it in lst:
            w, h = it["size"]
            cols, rows = GRIDS[tgt_loc]
            placed = None
            for gy in range(rows - h + 1):
                for gx in range(cols - w + 1):
                    cs = cells_of(it, gx, gy)
                    if all((tgt_loc, x, y) not in used for x, y in cs):
                        placed = (gx, gy)
                        break
                if placed: break
            if placed is None:
                print(f"  [规划失败] txt={it['txt']} 无法放入{NAMES[tgt_loc]}"); return None
            for x, y in cells_of(it, *placed):
                used[(tgt_loc, x, y)] = it["unit"]
            plan_map[it["unit"]] = (tgt_loc, *placed)
    return plan_map

def main():
    global CELL, BASES, GRIDS
    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    try:
        lays = _layout.get(pid, h)
        if "stash" not in lays or "inventory" not in lays:
            print("布局表未找到（仓库/背包）"); return 1
        CELL = lays["stash"][4]
        BASES = {0: (lays["inventory"][0], lays["inventory"][1]),
                 4: (lays["stash"][0], lays["stash"][1])}
        GRIDS = {0: (lays["inventory"][2], lays["inventory"][3]),
                 4: (lays["stash"][2], lays["stash"][3])}
        print("布局: 背包基准%s 格%dx%d | 仓库基准%s 格%dx%d | 格=%dpx" %
              (BASES[0], GRIDS[0][0], GRIDS[0][1], BASES[4], GRIDS[4][0], GRIDS[4][1], CELL))
        hwnd = find_hwnd(pid)
        _human.reset()
        bag, pInv = get_panel(pid, h, 0)
        st, _ = get_panel(pid, h, 4)
        items = bag + st
        print(f"交换前: 背包 {len(bag)} 件 / 仓库 {len(st)} 件")
        for it in items:
            print(f"  txt={it['txt']} {NAMES[it['loc']]}({it['gx']},{it['gy']}) 占{it['size'][0]}x{it['size'][1]}")

        plan_map = plan(pid, h, items)
        if plan_map is None:
            return 1
        for it in items:
            tl, tx, ty = plan_map[it["unit"]]
            mark = "✓" if (tl == it["loc"] and (tx, ty) == (it["gx"], it["gy"])) else ""
            print(f"  规划: txt={it['txt']} {NAMES[it['loc']]}({it['gx']},{it['gy']}) -> {NAMES[tl]}({tx},{ty}) {mark}")
            it["tgt_loc"], it["tgt_gx"], it["tgt_gy"] = tl, tx, ty

        # ---- 链式交换 ----
        todo = {it["unit"]: it for it in items}
        max_steps = len(items) * 4 + 20
        while todo:
            it = next((x for x in todo.values()
                       if x["size"][0] * x["size"][1] > 1 and (x["loc"], x["gx"], x["gy"]) != (x["tgt_loc"], x["tgt_gx"], x["tgt_gy"])), None)
            if it is None:
                it = next((x for x in todo.values()
                           if (x["loc"], x["gx"], x["gy"]) != (x["tgt_loc"], x["tgt_gx"], x["tgt_gy"])), None)
            if it is None:
                break
            # 拿起 it
            pa = pt(BASES[it["loc"]], it["gx"], it["gy"])
            _human.click(hwnd, *pa); _human.wait()
            if cursor_item(pid, h, pInv) != it["unit"]:
                print(f"  拿起失败 txt={it['txt']}"); return 1
            cur = it
            pos = (it["loc"], it["gx"], it["gy"])
            steps = 0
            while steps < max_steps:
                steps += 1
                tl, tx, ty = cur["tgt_loc"], cur["tgt_gx"], cur["tgt_gy"]
                pb = pt(BASES[tl], tx, ty)
                _human.click(hwnd, *pb); _human.wait()
                c = cursor_item(pid, h, pInv)
                if c == 0:  # 放下, 链结束
                    cur["loc"], cur["gx"], cur["gy"] = tl, tx, ty
                    todo.pop(cur["unit"], None)
                    print(f"  txt={cur['txt']} -> {NAMES[tl]}({tx},{ty}) ✓")
                    break
                if c == cur["unit"]:  # 放不下(自身占格冲突)
                    _human.click(hwnd, *pt(BASES[pos[0]], pos[1], pos[2])); _human.wait()
                    print(f"  txt={cur['txt']} 目标({NAMES[tl]},{tx},{ty})放不下，跳过")
                    break
                # c 上光标: cur 已放下到目标格(归位)，c 从该格被拿起，继续链
                cur["loc"], cur["gx"], cur["gy"] = tl, tx, ty
                todo.pop(cur["unit"], None)
                cobj = todo.get(c)
                if cobj is None:  # 已归位物品被拿起: 放回
                    _human.click(hwnd, *pb); _human.wait()
                    print(f"  目标格有已归位物品 {c:#x}，放回"); break
                cur = cobj
                pos = (tl, tx, ty)
            else:
                print("  链步数超限，中止"); return 1

        # ---- 验证 ----
        _human.wait(0.5, 0.8)
        print("== 交换后 ==")
        for loc in (0, 4):
            its, _ = get_panel(pid, h, loc)
            print(f"  {NAMES[loc]} ({len(its)}): " + ", ".join(f"{i['txt']}({i['gx']},{i['gy']})" for i in its))
        for it in items:
            idat = dword(pid, h, it["unit"] + 0x14)
            lc = mem.read(pid, h, idat + 0x45, 1)[0]
            ok = "✓" if lc == it["tgt_loc"] else "✗"
            print(f"  txt={it['txt']} loc={lc} 期望{it['tgt_loc']} {ok}")
    finally:
        ctypes.windll.kernel32.CloseHandle(h)
    return 0

if __name__ == "__main__":
    sys.exit(main())
