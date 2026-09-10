# -*- coding: utf-8 -*-
"""GetLocaleText / ItemTxt 公共模块（1.13c mod，只读内存）。

通路（已全部实证）:
  TXT id = 物品 dwTxtFileNo = 码表 id = ItemTxt 行号
  ItemTxt 行: szCode@+0x80  wLocaleTxtNo@+0xF4  nType@+0x11E
  GetLocaleText(wLocaleTxtNo):
    表A[0x2510A64] = 索引表:  idx -> entry 序号
      [A+0x02] WORD  索引数组长度
      [A+0x04] DWORD entry 总数
      [A+0x11] DWORD entry 区结束偏移
      [A+0x15] 起 WORD 索引数组[idx] = entry 序号
    entry 区 = A + len*2 + 0x15 起, 每 entry 17 字节, [entry]==1 有效
    表B[0x2510A68] = 值指针数组:  [B + entry*4] = wchar_t*  (UTF-16, 含颜色码)
  分派: idx<10000 -> (0x2510A64, 0x2510A68)
        10000-19999 -> (0x2510A80, 0x2510A6C)
        >=20000     -> (0x2510A84, 0x2510A70)
"""
from __future__ import annotations
import ctypes, json, os, re, sys, time
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

ROW = 0x1A8
_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tables_cache.json")

# 进程内缓存（单次调用多 PID 复用）
_CACHE: dict = {"base": None, "base_pid": None, "disp": None, "disp_pid": None}


# ---------- 文件级缓存（跨调用复用，按内容校验） ----------

def _load_file_cache() -> dict | None:
    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_file_cache(itemtxt_base, dispatch) -> None:
    try:
        d = {"itemtxt_base": itemtxt_base, "dispatch": dispatch,
             "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        tmp = _CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(tmp, _CACHE_FILE)  # 原子替换，避免读到半截文件
    except Exception:
        pass


def _verify_base(pid: int, h: int, base) -> bool:
    """校验 ItemTxt 表基：行0 szCode='hax '、行529 szCode='tsc '。"""
    if not base:
        return False
    try:
        c0 = mem.read(pid, h, base + 0x80, 4)
        c529 = mem.read(pid, h, base + 529 * ROW + 0x80, 4)
        return c0 == b"hax " and c529 == b"tsc "
    except Exception:
        return False


def _verify_dispatch(pid: int, h: int, disp) -> bool:
    """校验分派表：各指针地址非空，且主表指针可读、表头合理。"""
    if not disp:
        return False
    try:
        for k in ("p_a64", "p_a68", "p_a80", "p_a6c", "p_a84", "p_a70"):
            v = disp.get(k)
            if not v or not int(str(v), 16):
                return False
        a64 = int(disp["p_a64"], 16)
        a68 = int(disp["p_a68"], 16)
        ta = mem.read_dword(pid, h, a64)
        tb = mem.read_dword(pid, h, a68)
        if not ta or not tb:
            return False
        w = int.from_bytes(mem.read(pid, h, ta + 2, 2) or b"", "little")
        return 100 <= w <= 20000  # 索引数组长度应在合理范围
    except Exception:
        return False


def _scan_base(pid: int, h: int) -> int | None:
    """VirtualQuery 枚举可读区，搜 'flphax'(行0 szFlippyfile) 定位 ItemTxt 表基。"""
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class MBI(ctypes.Structure):
        _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", wintypes.DWORD), ("RegionSize", ctypes.c_size_t),
                    ("State", wintypes.DWORD), ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]

    regions = []
    addr = 0x10000
    while addr < 0x7FFFFFFF:
        mbi = MBI()
        if not kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            break
        if mbi.State == 0x1000 and (mbi.Protect & 0xFF) & 0xFE:
            regions.append((int(mbi.BaseAddress), int(mbi.RegionSize)))
        addr = (int(mbi.BaseAddress) + int(mbi.RegionSize) + 0xFFFF) & ~0xFFFF

    needle = b"flphax\x00"
    for lo, size in regions:
        chunk = 0x10000
        for off in range(0, size, chunk):
            buf = mem.read(pid, h, lo + off, min(chunk, size - off))
            if not buf:
                continue
            p = 0
            while True:
                i = buf.find(needle, p)
                if i < 0:
                    break
                base = lo + off + i
                if _verify_base(pid, h, base):
                    return base
                p = i + 1
    return None


def find_itemtxt_base(pid: int, h: int) -> int | None:
    """定位 ItemTxt 表基：进程内缓存 → 文件缓存（校验）→ 全扫。"""
    if _CACHE["base"] and _CACHE["base_pid"] == pid:
        return _CACHE["base"]
    fc = _load_file_cache()
    if fc and _verify_base(pid, h, fc.get("itemtxt_base")):
        v = fc["itemtxt_base"]
        base = int(str(v), 16) if isinstance(v, str) else int(v)
        _CACHE["base"], _CACHE["base_pid"] = base, pid
        return base
    base = _scan_base(pid, h)
    if base:
        _CACHE["base"], _CACHE["base_pid"] = base, pid
        _save_file_cache(base, _CACHE["disp"] or (fc or {}).get("dispatch"))
    return base


def _scan_dispatch(pid: int, h: int) -> dict | None:
    """从 D2Lang+0x9450 代码扫描 mov eax/ecx/edx,[imm] 提取分派表指针地址。"""
    lang = mem.module_base(pid, "D2Lang.dll")
    if not lang:
        return None
    code = mem.read(pid, h, lang + 0x9450, 0xA0)
    if not code:
        return None
    found = {}
    i = 0
    while i < len(code) - 4:
        b = code[i]
        if b in (0xC3, 0xC2):  # ret / ret imm16 -> 函数结束
            break
        if b == 0xA1:  # mov eax,[imm32]
            found.setdefault("eax", []).append(int.from_bytes(code[i+1:i+5], "little"))
            i += 5
        elif code[i:i+2] in (b"\x8B\x0D", b"\x8B\x15"):
            r = "ecx" if code[i+1] == 0x0D else "edx"
            found.setdefault(r, []).append(int.from_bytes(code[i+2:i+6], "little"))
            i += 6
        else:
            i += 1
    if not found.get("eax") or not found.get("edx"):
        return None
    disp = {
        "p_a84": f"{found['eax'][0]:#x}" if len(found["eax"]) > 0 else None,
        "p_a70": f"{found['ecx'][0]:#x}" if found.get("ecx") else None,
        "p_a80": f"{found['eax'][1]:#x}" if len(found["eax"]) > 1 else None,
        "p_a6c": f"{found['ecx'][1]:#x}" if found.get("ecx") and len(found["ecx"]) > 1 else None,
        "p_a64": f"{found['eax'][-1]:#x}" if found["eax"] else None,
        "p_a68": f"{found['edx'][-1]:#x}" if found["edx"] else None,
    }
    return disp


def find_locale_dispatch(pid: int, h: int) -> dict | None:
    """定位 GetLocaleText 分派表：进程内缓存 → 文件缓存（校验）→ 扫描代码。"""
    if _CACHE["disp"] and _CACHE["disp_pid"] == pid:
        return _CACHE["disp"]
    fc = _load_file_cache()
    if fc and _verify_dispatch(pid, h, fc.get("dispatch")):
        disp = fc["dispatch"]
        _CACHE["disp"], _CACHE["disp_pid"] = disp, pid
        return disp
    disp = _scan_dispatch(pid, h)
    if disp and _verify_dispatch(pid, h, disp):
        _CACHE["disp"], _CACHE["disp_pid"] = disp, pid
        _save_file_cache(_CACHE["base"] or (fc or {}).get("itemtxt_base"), disp)
    return disp


def _d(disp, k):
    """分派表值（字符串 "0x.." 或 int）转 int。"""
    v = disp.get(k)
    return int(str(v), 16) if v else 0


def get_locale_text(pid, h, disp, idx):
    """复刻 GetLocaleText 分派 + 查表。返回字符串指针，失败返回 None。"""
    def word(a):
        raw = mem.read(pid, h, a, 2)
        return int.from_bytes(raw, "little") if raw else 0
    def dword(a):
        raw = mem.read(pid, h, a, 4)
        return int.from_bytes(raw, "little") if raw else 0

    def lookup(ta, tb, e):
        if not ta or not tb:
            return None
        cx = word(ta + 2)
        if e >= cx:
            e = 0x1F4
        entry = word(ta + 0x15 + e * 2)
        if entry >= dword(ta + 4):
            return None
        end = ta + cx * 2 + 0x15 + entry * 17
        if end >= ta + dword(ta + 0x11):
            return None
        if mem.read(pid, h, end, 1) != b"\x01":
            return None
        return dword(tb + entry * 4)

    if idx >= 20000 and _d(disp, "p_a84"):
        ptr = lookup(dword(_d(disp, "p_a84")), dword(_d(disp, "p_a70")), idx - 20000)
        if ptr:
            return ptr
    if 10000 <= idx < 20000 and _d(disp, "p_a80"):
        ptr = lookup(dword(_d(disp, "p_a80")), dword(_d(disp, "p_a6c")), idx - 10000)
        if ptr:
            return ptr
    return lookup(dword(_d(disp, "p_a64")), dword(_d(disp, "p_a68")), idx)


def read_utf16(pid, h, addr, maxlen=256):
    raw = mem.read(pid, h, addr, maxlen)
    if not raw:
        return ""
    return raw.decode("utf-16-le", errors="ignore").split("\x00")[0]


def clean_name(s: str) -> str:
    s = re.sub(r"\u00ffc[0-9a-fA-F/]", "", s)   # 颜色码 ÿcX / ÿc/
    s = re.sub(r"[\uff0a]+", "", s)             # 星号装饰 ＊＊＊
    s = s.replace("\n", "")
    # 一次性去掉两端 空白/全角空格/图标/装饰符（≡△▽◣◢◥◤▷◁⬢□■◆◇●○）
    s = s.strip(" \t\u3000\u2261\u25b3\u25bd\u25e3\u25e2\u25e5\u25e4\u25b7\u25c1\u2b22\u25a1\u25a0\u25c6\u25c7\u25cf\u25cb\u00ff")
    return s


def read_item_row(pid, h, base, txt_id):
    a = base + txt_id * ROW
    raw = mem.read(pid, h, a, ROW)
    if not raw:
        return None
    def s(off, n):
        v = raw[off:off+n].split(b"\x00")[0]
        return v.decode("latin-1") if v else ""
    return {
        "txt_id": txt_id,
        "addr": f"{a:#x}",
        "flip": s(0x00, 32),
        "invfile": s(0x20, 96),
        "code": s(0x80, 20).strip(),
        "locale": int.from_bytes(raw[0xF4:0xF6], "little"),
        "ntype": raw[0x11E],
        "fquest": raw[0x12A],
        "socket": raw[0x138],
        "xsize": raw[0xFC],   # 占格宽（格数）
        "ysize": raw[0xFD],   # 占格高（格数）
    }


def txt_to_name(pid, h, txt_id):
    """TXT id -> 清洗后物品名；返回 (name_clean, row)。失败 name 为空串。"""
    base = find_itemtxt_base(pid, h)
    if not base:
        return "", None
    row = read_item_row(pid, h, base, txt_id)
    if not row:
        return "", None
    disp = find_locale_dispatch(pid, h)
    if not disp:
        return "", row
    ptr = get_locale_text(pid, h, disp, row["locale"])
    if not ptr:
        return "", row
    return clean_name(read_utf16(pid, h, ptr)), row
