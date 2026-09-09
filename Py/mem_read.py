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
    """取目标进程内某模块的加载基址（32 位进程，返回 4 字节地址）。"""
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid)
    if snap == INVALID_HANDLE_VALUE:
        return None
    try:
        entry = MODULEENTRY32W()
        entry.dwSize = ctypes.sizeof(MODULEENTRY32W)
        if not kernel32.Module32FirstW(snap, ctypes.byref(entry)):
            return None
        while True:
            if entry.szModule.lower() == module_name.lower():
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
        raw = read(pid, h, idat + 0x69, 1) if idat else b""
        loc = raw[0] if raw else -1               # nLocation: 0地 1背包 2腰带 3装备
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
