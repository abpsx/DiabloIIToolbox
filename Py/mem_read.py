#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""暗黑2原版多实例只读内存读取（按 PID，供启动器标签卡显示）。

只读边界：OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ)
+ ReadProcessMemory，不写入、不注入。

用法：
  python mem_read.py --config "Setting/memory/1.13c.json" --pid 10264 --pid 10300 --out out.json
  # 每个 --pid 读一份；无 --pid 时按 exe 名找第一个实例
  python mem_read.py --config cfg.json --exe D2Loader.exe --names "界面标记,人物位置索引"

输出：stdout 单行 JSON（ensure_ascii=True 纯 ASCII，AHK FileRead 不乱码），
      --out 时同时写文件。
      {"ok": true, "results": {"10264": {"界面标记": 10, ...}, ...}}
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import struct
import sys
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


# ---------- 进程与模块 ----------

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_wchar * 256),
        ("szExePath", ctypes.c_wchar * 260),
    ]


def find_process(exe_name: str) -> int | None:
    """按可执行文件名找进程 PID（取第一个匹配）。"""
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE:
        return None
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snap, ctypes.byref(entry)):
            return None
        while True:
            if entry.szExeFile.lower() == exe_name.lower():
                return int(entry.th32ProcessID)
            if not kernel32.Process32NextW(snap, ctypes.byref(entry)):
                return None
    finally:
        kernel32.CloseHandle(snap)


def module_base(pid: int, module_name: str) -> int | None:
    """取目标进程内某模块的加载基址（32 位进程，返回 4 字节地址）。
    模块名容错：不区分大小写、忽略 .dll 扩展名差异。"""
    want = module_name.strip().lower().removesuffix(".dll")
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    if snap == INVALID_HANDLE_VALUE:
        return None
    try:
        entry = MODULEENTRY32W()
        entry.dwSize = ctypes.sizeof(MODULEENTRY32W)
        if not kernel32.Module32FirstW(snap, ctypes.byref(entry)):
            return None
        while True:
            if entry.szModule.lower().removesuffix(".dll") == want:
                return int(ctypes.addressof(entry.modBaseAddr.contents))
            if not kernel32.Module32NextW(snap, ctypes.byref(entry)):
                return None
    finally:
        kernel32.CloseHandle(snap)


def open_process_readonly(pid: int) -> int:
    h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    return int(h) if h else 0


# ---------- 读取原语 ----------

def read(pid: int, h: int, addr: int, size: int) -> bytes:
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t(0)
    ok = kernel32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n))
    return buf.raw if ok and n.value == size else b""


def read_dword(pid: int, h: int, addr: int) -> int:
    raw = read(pid, h, addr, 4)
    return int.from_bytes(raw, "little") if raw else 0


def read_ptr(pid: int, h: int, addr: int) -> int:
    return read_dword(pid, h, addr)  # 32 位目标：指针即 4 字节


def read_value(pid: int, h: int, addr: int, typ: str,
               length: int = 32, unicode: bool = False):
    t = typ.lower()
    if t in ("dword", "uint", "int32", "ptr"):
        return read_dword(pid, h, addr)
    if t == "word":
        raw = read(pid, h, addr, 2)
        return int.from_bytes(raw, "little") if raw else 0
    if t == "byte":
        raw = read(pid, h, addr, 1)
        return raw[0] if raw else 0
    if t == "qword":
        raw = read(pid, h, addr, 8)
        return int.from_bytes(raw, "little") if raw else 0
    if t == "float":
        raw = read(pid, h, addr, 4)
        return struct.unpack("<f", raw)[0] if len(raw) == 4 else 0.0
    if t == "double":
        raw = read(pid, h, addr, 8)
        return struct.unpack("<d", raw)[0] if len(raw) == 8 else 0.0
    if t == "string":
        nbytes = length * (2 if unicode else 1)
        raw = read(pid, h, addr, nbytes)
        if not raw:
            return ""
        raw = raw.split(b"\x00")[0]
        try:
            return raw.decode("utf-16-le" if unicode else "gbk", errors="replace")
        except Exception:
            return raw.decode("latin-1", errors="replace")
    raise ValueError(f"未知类型 {typ}")


def resolve_base(pid: int, spec: str) -> int | None:
    """解析 "ModuleName+0xOFFSET" 或 "0xADDR" 为绝对地址。"""
    spec = spec.strip()
    if "+" in spec:
        mod, _, off = spec.partition("+")
        base = module_base(pid, mod.strip())
        if base is None:
            raise ValueError(f"找不到模块 {mod.strip()}")
        return (base + int(off.strip(), 16)) & 0xFFFFFFFF
    return int(spec, 16) & 0xFFFFFFFF


def read_config_entry(pid: int, h: int, item: dict):
    """按配置条目读取（CE 指针链语义：Address 先解引用，再逐级偏移）。

    deref_str=1 时：最后一级偏移后先解引用一次得到字符串指针，再按 string 读
    （用于 unit 结构中"偏移处存字符串指针"的字段）。
    """
    base = resolve_base(pid, f"{item['module']}+{item['offset']}")
    offs = [int(o, 16) for o in item.get("offsets", [])]
    if offs:
        ptr = read_ptr(pid, h, base)
        for off in offs[:-1]:
            ptr = read_ptr(pid, h, ptr + off)
        addr = ptr + offs[-1]
    else:
        addr = base
    if item.get("deref_str"):
        addr = read_ptr(pid, h, addr)
    return read_value(pid, h, addr, item["type"],
                      item.get("length", 32), bool(item.get("unicode", 0)))


def read_all(pid: int, items: list, config_dir: str) -> dict:
    """读单个进程全部条目，返回 {name: value}；失败返回 {"_error": msg}。"""
    h = open_process_readonly(pid)
    if not h:
        return {"_error": "OpenProcess 失败（需要管理员权限）"}
    try:
        out = {}
        for it in items:
            try:
                if it.get("type") == "bag":
                    out[it["name"]] = read_bag(pid, h, it, config_dir)
                elif it.get("type") == "stash":
                    out[it["name"]] = read_stash_state(
                        pid, h,
                        ui_offset=it.get("ui_offset", "0x50D00"),
                        ui_open=it.get("ui_open", "0x60"),
                        page_addr=int(it.get("page_addr", "0x02CBE36C"), 16),
                        page_aob=it.get("page_aob", ""))
                elif it.get("type") == "controls":
                    out[it["name"]] = read_controls(pid, h, it, config_dir)
                else:
                    out[it["name"]] = read_config_entry(pid, h, it)
            except Exception as e:
                out[it["name"]] = f"<{type(e).__name__}>"
        return out
    finally:
        kernel32.CloseHandle(h)


# ---------- 背包物品（bag 类型） ----------

_code_table_cache = {}


def _load_code_table(path: str) -> dict:
    """读物品码表文件 → {id: abbr}，带缓存。"""
    if path in _code_table_cache:
        return _code_table_cache[path]
    m = {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for it in data.get("items", []):
            m[int(it["id"])] = it["code"]
    except Exception:
        pass
    _code_table_cache[path] = m
    return m


def read_bag(pid: int, h: int, item: dict, config_dir: str) -> list:
    """背包物品列表（UnitInventory 链表，实证结构）。

    schema: module/offset/offsets 定位 pPlayer（如 D2CLIENT+0x11B800, offsets ["0x60"]）；
    内部:
      pInv  = [pPlayer + 0x60]              UnitInventory（+00=0x01020304 印章）
      cur   = [pInv + 0x0C]                 pFirstItem
      节点  = UnitAny: dwTxtFileNo@+0x04  pItemData@+0x14
      next  = [pItemData + 0x64]            pNextInvItem
    每节点 = 一件物品；名称经 GetLocaleText 解析。
    返回 [{abbr, code, name, slots:[序号]}]，空格/无效背包返回 []。
    """
    base = resolve_base(pid, f"{item['module']}+{item['offset']}")
    offs = [int(o, 16) for o in item.get("offsets", [])]
    if offs:
        ptr = read_ptr(pid, h, base)
        for off in offs[:-1]:
            ptr = read_ptr(pid, h, ptr + off)
        pInv = read_ptr(pid, h, ptr + offs[-1])   # 最后一级解引用 -> UnitInventory*
    else:
        pInv = base

    # 背包印章校验（未进游戏/非背包时返回空）
    if read_dword(pid, h, pInv) != 0x01020304:
        return []

    table_path = os.path.join(config_dir, item.get("table", "item_codes.json"))
    code_map = _load_code_table(table_path)

    # GetLocaleText 环境（进程内缓存）
    try:
        from locale_text import txt_to_name
    except Exception:
        txt_to_name = None

    entries: list = []
    cur = read_ptr(pid, h, pInv + 0x0C)  # pFirstItem
    seen: set = set()
    idx = 0
    while cur and cur not in seen:
        seen.add(cur)
        txt = read_dword(pid, h, cur + 0x04)       # dwTxtFileNo = 码表 id
        idat = read_ptr(pid, h, cur + 0x14)        # pItemData
        # 位置判定：nLocation(+0x69) 区分 腰带(2)/装备(3)；nItemLocation(+0x45) 区分 背包(0)/盒子(3)/仓库(4)
        raw69 = read(pid, h, idat + 0x69, 1) if idat else b""
        raw45 = read(pid, h, idat + 0x45, 1) if idat else b""
        loc69 = raw69[0] if raw69 else -1
        loc45 = raw45[0] if raw45 else -1
        if loc69 == 2:
            loc = 2        # 腰带
        elif loc69 == 3:
            loc = 3        # 装备
        elif loc45 == 0:
            loc = 1        # 背包
        elif loc45 == 4:
            loc = 4        # 仓库
        elif loc45 == 3:
            loc = 5        # 盒子
        else:
            loc = 0        # 地面/未知
        # loc: 0地面 1背包 2腰带 3装备 4仓库 5盒子
        name = ""
        if txt_to_name and txt is not None:
            try:
                name = txt_to_name(pid, h, txt)[0]
            except Exception:
                name = ""
        entries.append({
            "abbr": code_map.get(txt, f"<{txt}>"),
            "code": txt,
            "name": name,
            "loc": loc,
            "slots": [idx],
        })
        cur = read_ptr(pid, h, idat + 0x64) if idat else 0
        idx += 1
    return entries

_stash_page_cache: dict = {}   # pid -> 页签结构地址（AOB 定位缓存）


# ---------- D2WIN 控件链（controls 类型） ----------

# D2BS Constants.h 控件类型
CONTROL_TYPES = {
    0x01: "EDITBOX", 0x02: "IMAGE", 0x03: "UNUSED", 0x04: "TEXTBOX",
    0x05: "SCROLLBAR", 0x06: "BUTTON", 0x07: "LIST", 0x08: "TIMER",
    0x09: "SMACK", 0x0A: "PROGRESSBAR", 0x0B: "POPUP", 0x0C: "ACCOUNTLIST",
}
# Control 结构偏移（D2BS D2Structs.h:132，1.13c 待实测验证）
_CTRL_TYPE   = 0x00   # dwType
_CTRL_DIS    = 0x08   # dwDisabled
_CTRL_POSX   = 0x0C
_CTRL_POSY   = 0x10
_CTRL_SIZEX  = 0x14
_CTRL_SIZEY  = 0x18
_CTRL_NEXT   = 0x3C   # pNext 链表
_CTRL_STATE  = 0x44   # unkState（按钮 1=置灰）
_CTRL_TEXTS  = 0x48   # pFirstText
_CTRL_INLINE = 0x5C   # EDITBOX/TEXTBOX 内联 wText[256]
# ControlText 结构（size=0x20）
_TXT_W0      = 0x00   # wchar_t* 文本指针
_TXT_NEXT    = 0x1C   # pNext


def _wstr_cut(raw: bytes) -> bytes:
    """按 UTF-16LE wchar 对齐截到首个 0x0000 前（避免字节级双零误切吃掉尾字节）。"""
    for i in range(0, len(raw) - 1, 2):
        if raw[i] == 0 and raw[i + 1] == 0:
            return raw[:i]
    return raw


def _read_wstr(pid: int, h: int, ptr: int, max_chars: int = 64) -> str:
    """读 UTF-16LE 字符串（到首个 0x0000 wchar）。"""
    if not ptr:
        return ""
    raw = read(pid, h, ptr, max_chars * 2)
    if not raw:
        return ""
    raw = _wstr_cut(raw)
    try:
        return raw.decode("utf-16-le", errors="replace")
    except Exception:
        return ""


_BAD_W = set(range(0x00, 0x20)) - {0x09, 0x0A, 0x0D}  # 控制字符（保留 \t\r\n）


def _w_ok(w: int) -> bool:
    """文本字符白名单：拒控制字符/代理/特殊区（组合符、PUA、0xFFF0+）。"""
    if w in _BAD_W:
        return False
    if 0xD800 <= w <= 0xDFFF or w == 0xFFFF or w == 0xFFFE:
        return False
    if 0xE000 <= w <= 0xF8FF:      # PUA 私有区
        return False
    if 0x0300 <= w <= 0x036F:      # 组合重音
        return False
    return True


def _inline_text(pid: int, h: int, ctrl: int, off: int) -> str:
    """读控件内联文本区（如 BUTTON @+0x64）。

    1.13c 实测：文本可能分多段（段间 0x0000 分隔，UI 上为换行）；
    起始可能错位 1 字节。策略：
      - 双对齐（0/1）各解一次，取可打印比例最高者
      - 非零 wchar 段拼接，段间换行 \n；垃圾段（含白名单外字符）跳过
    """
    raw = read(pid, h, ctrl + off, 512)
    if not raw:
        return ""
    best, best_score = "", 0.0
    for align in (0, 1):
        segs: list = []
        cur: list = []
        for i in range(align, len(raw) - 1, 2):
            w = raw[i] | (raw[i + 1] << 8)
            if w == 0:
                if cur:
                    segs.append(cur)
                    cur = []
            else:
                cur.append(w)
        if cur:
            segs.append(cur)
        if not segs:
            continue
        lines = []
        for seg in segs:
            if not all(_w_ok(w) for w in seg):
                continue  # 垃圾段跳过
            s = "".join(chr(w) for w in seg).rstrip("\x00")
            if s:
                lines.append(s)
        if not lines:
            continue
        s = "\n".join(lines)
        if not s:
            continue
        good = sum(1 for ch in s if ch != "\ufffd" and (ord(ch) >= 0x20 or ch in "\r\n\t"))
        score = good / max(len(s), 1)
        if score >= 0.8 and score > best_score:
            best, best_score = s, score
    return best


def read_control_texts(pid: int, h: int, ctrl: int) -> list:
    """控件文本：pFirstText ControlText 链优先，内联兜底。

    1.13c 实测：
      - 角色列表等 TEXTBOX 文本在 ControlText 链（wText[0..4] 5 个指针 + pNext）
      - 主菜单 BUTTON 文本内联 @+0x64（UTF-16LE，段间换行）
      - EDITBOX 内联 @+0x5C；IMAGE 无文本
    """
    texts: list = []
    t = read_dword(pid, h, ctrl + _CTRL_TYPE)
    # 1) pFirstText 链（TEXTBOX/复杂控件主路径）
    ptext = read_ptr(pid, h, ctrl + _CTRL_TEXTS)
    seen: set = set()
    for _ in range(64):
        if not ptext or ptext in seen:
            break
        seen.add(ptext)
        for j in range(5):  # ControlText.wText[0..4]
            wp = read_ptr(pid, h, ptext + j * 4)
            s = _read_wstr(pid, h, wp)
            if s:
                texts.append(s)
        ptext = read_ptr(pid, h, ptext + _TXT_NEXT)
    if texts:
        return texts
    # 2) 链空：内联兜底
    if t == 0x06:  # BUTTON @+0x64
        s = _inline_text(pid, h, ctrl, 0x64)
        if s:
            texts.append(s)
    elif t in (0x01, 0x04):  # EDITBOX/TEXTBOX @+0x5C（仅接受单段文本）
        s = _inline_text(pid, h, ctrl, 0x5C)
        if s and "\n" not in s:
            texts.append(s)
    return texts


def read_control_chain(pid: int, h: int, first: int) -> list:
    """遍历 D2WIN FirstControl 控件链（pNext @+0x3C），最多 512 个防死循环。"""
    out: list = []
    cur, seen = first, set()
    for _ in range(512):
        if not cur or cur in seen:
            break
        seen.add(cur)
        c = {
            "addr": cur,
            "type": read_dword(pid, h, cur + _CTRL_TYPE),
            "disabled": read_dword(pid, h, cur + _CTRL_DIS),
            "pos": [read_dword(pid, h, cur + _CTRL_POSX),
                    read_dword(pid, h, cur + _CTRL_POSY)],
            "size": [read_dword(pid, h, cur + _CTRL_SIZEX),
                     read_dword(pid, h, cur + _CTRL_SIZEY)],
            "state": read_dword(pid, h, cur + _CTRL_STATE),
        }
        c["type_name"] = CONTROL_TYPES.get(c["type"], f"0x{c['type']:02X}")
        c["texts"] = read_control_texts(pid, h, cur)
        out.append(c)
        cur = read_ptr(pid, h, cur + _CTRL_NEXT)
    return out


def _has_ctrl(controls: list, typ: int, x=None, y=None) -> bool:
    for c in controls:
        if c["type"] != typ:
            continue
        if x is not None and c["pos"][0] != x:
            continue
        if y is not None and c["pos"][1] != y:
            continue
        return True
    return False


def _page_name(controls: list) -> str:
    """按 Profile.cpp 特征控件坐标识别菜单页（800x600 布局）。"""
    if not controls:
        return ""
    if _has_ctrl(controls, 0x06, 264, 324) and _has_ctrl(controls, 0x06, 264, 366):
        return "主菜单"
    if _has_ctrl(controls, 0x01, 322, 342) and _has_ctrl(controls, 0x01, 322, 396):
        return "登录"
    if _has_ctrl(controls, 0x06, 264, 297) and _has_ctrl(controls, 0x06, 264, 340):
        return "难度选择"
    if _has_ctrl(controls, 0x06, 264, 310) and _has_ctrl(controls, 0x06, 264, 350):
        return "其他多人"
    if _has_ctrl(controls, 0x0C) or _has_ctrl(controls, 0x07):
        return "角色选择/列表"
    return "菜单"


def read_controls(pid: int, h: int, item: dict, config_dir: str) -> dict:
    """读 D2WIN 控件链 + 页面状态（ClientState 式判定）。

    schema: module/offset = D2Win.dll + 0x8DB34（FirstControl 指针）；
    player_off 可选（默认 D2CLIENT+0x11B800）用于区分 游戏内/菜单。
    返回 {first, count, state, page, controls}。
    """
    base = resolve_base(pid, f"{item['module']}+{item['offset']}")
    first = read_ptr(pid, h, base)
    controls = read_control_chain(pid, h, first)

    player = 0
    po = item.get("player_off", "D2CLIENT+0x11B800")
    try:
        player = read_ptr(pid, h, resolve_base(pid, po))
    except Exception:
        player = 0

    if player and not first:
        state, page = "game", "游戏内"
    elif not player and first:
        state, page = "menu", _page_name(controls)
    else:
        state, page = "null", "未就绪"
    return {"first": first, "count": len(controls), "state": state,
            "page": page, "controls": controls}


def find_pattern(pid: int, h: int, pattern: bytes, max_hits: int = 8) -> list:
    """全内存搜索字节模式（只读），返回命中地址列表（最多 max_hits 个）。

    遍历 0x10000-0x7FFFFFFF 可读可写区域，每次读 1MB 块内 find。
    用于定位堆内动态分配的 UI 结构（如仓库页签控件）。
    """
    from ctypes import wintypes as _wt
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class MBI(ctypes.Structure):
        _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", _wt.DWORD), ("RegionSize", ctypes.c_size_t),
                    ("State", _wt.DWORD), ("Protect", _wt.DWORD), ("Type", _wt.DWORD)]

    hits: list = []
    addr = 0x10000
    while addr < 0x7FFFFFFF and len(hits) < max_hits:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
            lo, size = int(mbi.BaseAddress), int(mbi.RegionSize)
            chunk = 0x100000
            for off in range(0, size, chunk):
                buf = read(pid, h, lo + off, min(chunk, size - off))
                if not buf:
                    continue
                p = 0
                while True:
                    i = buf.find(pattern, p)
                    if i < 0:
                        break
                    hits.append(lo + off + i)
                    if len(hits) >= max_hits:
                        return hits
                    p = i + 1
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF
    return hits


def _stash_struct_ok(pid: int, h: int, addr: int) -> bool:
    """校验页签结构有效性：+0x00 总页数(1-100) 且 +0x04 文本缓冲首 dword(0-100)。"""
    tot = read_dword(pid, h, addr)
    if not (1 <= tot <= 100):
        return False
    pbuf = read_ptr(pid, h, addr + 0x04)
    if not pbuf:
        return False
    idx = read_dword(pid, h, pbuf)
    return 0 <= idx <= 100


def find_stash_page_addr(pid: int, h: int, aob: str = "") -> int:
    """AOB 定位仓库页签结构地址，带进程级缓存。

    aob: 十六进制特征串；仓库页签结构模板特征（1.13c 实证）：
      +0x00 总页数(1基)  +0x04 文本缓冲指针(首 dword=0 基当前页数)
      +0x10 起 'FF 00 00 00 01 01 00 00 68 67 6C 20'
    结构地址 = 特征命中 - 0x10。误命中经 _stash_struct_ok 过滤。
    注：翻页/重开仓库后结构会重新分配，缓存校验失败即重新 AOB。
    """
    global _stash_page_cache
    cached = _stash_page_cache.get(pid)
    if cached and _stash_struct_ok(pid, h, cached):
        return cached
    _stash_page_cache.pop(pid, None)
    if aob:
        try:
            pattern = bytes.fromhex(aob.replace(" ", ""))
        except Exception:
            pattern = b""
        if pattern:
            for hit in find_pattern(pid, h, pattern, max_hits=8):
                addr = hit - 0x10
                if _stash_struct_ok(pid, h, addr):
                    _stash_page_cache[pid] = addr
                    return addr
    return 0


def read_stash_state(pid: int, h: int,
                     ui_offset: str = "0x50D00",
                     ui_open: str = "0x60",
                     page_addr: int = 0x02CBE36C,
                     page_aob: str = "") -> dict:
    """仓库页状态：仓库是否打开 + 当前页数（只读，不写入）。

    仓库开：   ui_ptr = [D2CLIENT+0x50D00]（先解引用）；stash_open = [ui_ptr+0x60]
    当前页数： 页签结构（AOB 定位）：
                +0x00 总页数；+0x04 文本缓冲指针；页数(1基) = [ [结构+0x04] ] + 1。
               无 AOB 时 fallback：page_addr 处若为指针则解引用+1，否则直接当 1 基页数。
               仓库关时页数返回 0 并清除 AOB 缓存。
    返回 {"stash_open": bool, "page": int}
    """
    base = resolve_base(pid, f"D2CLIENT.DLL+{ui_offset}")
    ui_ptr = read_ptr(pid, h, base)
    stash_open = read_dword(pid, h, ui_ptr + int(ui_open, 16)) if ui_ptr else 0
    page = 0
    if stash_open:
        addr = find_stash_page_addr(pid, h, page_aob)
        if addr:
            pbuf = read_ptr(pid, h, addr + 0x04)
            if pbuf:
                page = read_dword(pid, h, pbuf) + 1   # 0 基 → 1 基
        elif page_addr:
            v = read_dword(pid, h, page_addr)
            if v:
                # 兼容：旧式指针结构（[addr] 指向页索引）则解引用+1；直接 1 基则原样
                inner = read_ptr(pid, h, page_addr)
                if inner and read_dword(pid, h, inner) <= 100 and read_dword(pid, h, inner) != v:
                    page = read_dword(pid, h, inner) + 1
                else:
                    page = v
    else:
        _stash_page_cache.pop(pid, None)
    return {"stash_open": bool(stash_open), "page": page}


def main() -> None:
    ap = argparse.ArgumentParser(description="D2Loader 多实例只读内存（按 PID）")
    ap.add_argument("--config", required=True, help="条目配置 JSON 路径")
    ap.add_argument("--pid", action="append", default=[], type=int,
                    help="目标进程 PID（可重复，多实例）")
    ap.add_argument("--exe", default="D2Loader.exe",
                    help="无 --pid 时按进程名取第一个实例")
    ap.add_argument("--names", default="", help="逗号分隔的条目名过滤，默认全部")
    ap.add_argument("--out", default="", help="结果写入此文件")
    args = ap.parse_args()

    try:
        with open(args.config, encoding="utf-8") as f:
            items = json.load(f)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"配置读取失败: {e}"}))
        sys.exit(1)

    if args.names:
        want = {n.strip() for n in args.names.split(",") if n.strip()}
        items = [it for it in items if it.get("name") in want]

    pids = args.pid
    if not pids:
        p = find_process(args.exe)
        if p is None:
            print(json.dumps({"ok": False, "error": f"进程 {args.exe} 未运行"}))
            sys.exit(1)
        pids = [p]

    results = {}
    cfg_dir = os.path.dirname(os.path.abspath(args.config))
    for pid in pids:
        results[str(pid)] = read_all(pid, items, cfg_dir)

    out = {"ok": True, "results": results}
    text = json.dumps(out, ensure_ascii=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    sys.exit(main())
