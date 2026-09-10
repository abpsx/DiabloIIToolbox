# -*- coding: utf-8 -*-
"""物品特殊名读取器（unique 名，只读内存）

链路：
  物品 ItemData+0x00 quality==7(unique)
  → 物品码(txt→code, item_codes.json)
  → "Elite Uniques" 名表（搜 ASCII "Elite Uniques" 动态定位）按 code 遍历匹配 → 英文名
  → mod 注释池（搜 UTF-8 "巫师之刺" 锚定）解析"中文名 英文名" → 中文名

用法:
  python special_name.py --test          # 验证骸骨小刀特殊名
  python special_name.py --list-notes     # 列出注释池全部映射
  python special_name.py --scan-code 7dg  # 按物品码查特殊名
  python special_name.py --dump-json      # 生成/更新 special_names.json 缓存
"""
from __future__ import annotations
import sys, ctypes, re, argparse
from ctypes import wintypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
MEM_COMMIT = 0x1000

class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]

def dword(pid, h, a):
    r = mem.read(pid, h, a, 4)
    return int.from_bytes(r, "little") if r else 0

# ---------- setitems 数据表（hackmap d2structs.h / D2CallStub.cpp，1.13c） ----------
#   p_D2DataTables @ D2Common+0x99E1C（d2ptrs.h D2VARPTR2，1.13c 分支 b1=0x6FDE9E1C）
#   → [var] = sgptDataTables → +0xC18=pSetItemsTxt、+0xC1C=nSetItems
#   记录 0x1B8/条：dwIndex@+00、szDesc[32]@+02、wLocaleTxtNo@+24、szCode[4]@+28、dwSetIdx@+2C
SGPT_OFFSET = 0x99E1C
SET_REC_SIZE = 0x1B8


def locate_set_table(pid, h):
    """返回 (pSetItemsTxt, nSetItems)；找不到返回 (0, 0)。"""
    base = mem.module_base(pid, "D2Common.dll")
    if not base:
        return 0, 0
    sgpt = dword(pid, h, base + SGPT_OFFSET)
    if not (0x1000000 <= sgpt < 0x80000000):
        return 0, 0
    pSet = dword(pid, h, sgpt + 0xC18)
    nSet = dword(pid, h, sgpt + 0xC1C)
    if not pSet or not (0 < nSet < 2000):
        return 0, 0
    # 校验首记录：dwIndex==0 且 desc 为可打印 ASCII
    b = mem.read(pid, h, pSet, 0x2C)
    if not b or len(b) != 0x2C or int.from_bytes(b[0:2], "little") != 0:
        return 0, 0
    desc = b[2:34].split(b"\x00")[0]
    if not desc or not all(0x20 <= x < 0x7F for x in desc[:4]):
        return 0, 0
    return pSet, nSet


def dump_set_items(pid, h, pSet, nSet):
    """遍历 setitems 表 → {dwIndex: {code, desc, set_idx, wloc}}。"""
    out = {}
    for i in range(nSet):
        r = pSet + i * SET_REC_SIZE
        b = mem.read(pid, h, r, 0x30)
        if not b or len(b) != 0x30:
            continue
        dw_idx = int.from_bytes(b[0:2], "little")
        desc = b[2:34].split(b"\x00")[0].decode("latin-1", "ignore")
        wloc = int.from_bytes(b[0x24:0x26], "little")
        code = b[0x28:0x2C].rstrip(b"\x00 ").decode("latin-1", "ignore")
        set_idx = int.from_bytes(b[0x2C:0x30], "little") & 0xFFFF
        out[dw_idx] = {"code": code, "desc": desc, "set_idx": set_idx, "wloc": wloc}
    return out

def scan_mem(pid, h, pat: bytes) -> list[int]:
    """全内存搜索模式串, 返回命中地址列表。"""
    found = []
    addr = 0
    mbi = MBI()
    while addr < 0x7FFFFFFF:
        if kernel32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi),
                                   ctypes.sizeof(mbi)) == 0:
            break
        base = int(mbi.BaseAddress or 0); size = int(mbi.RegionSize)
        if size > 0 and (mbi.State & MEM_COMMIT) and (mbi.Protect & 0xFF) in (0x04, 0x02, 0x08, 0x10, 0x20, 0x40):
            buf = ctypes.create_string_buffer(size); n = ctypes.c_size_t(0)
            if kernel32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(n)):
                data = buf.raw[:n.value]
                pos = 0
                while True:
                    i = data.find(pat, pos)
                    if i < 0:
                        break
                    found.append(base + i)
                    pos = i + len(pat)
        addr = base + size
    return found


class SpecialName:
    """动态定位 unique 名表 + 注释池 + 套装部件名池, 提供 code→特殊名。"""

    REC_SIZE = 0x14C      # unique 名表记录大小
    NAME_LEN = 0x26       # 名字字段宽度
    CODE_OFF = 0x26       # code 字段偏移（名字后）

    def __init__(self, pid: int, h: int):
        self.pid, self.h = pid, h
        self.unique_tables = []     # [(记录首, 记录数)]
        self.note_map = {}          # 英文名 -> 中文名
        self.notes_anchor = 0       # 注释池锚点（UTF-8 "巫师之刺" 命中）
        self.set_names = []         # [(英文, 中文)] 套装部件名对
        self.set_anchor = 0         # 套装名 String 表锚点
        self.set_table_addr = 0     # pSetItemsTxt（hackmap sgptDataTables 链路）
        self.set_count = 0          # nSetItems
        self._locate_unique_tables()
        self._locate_notes()
        self._locate_set_names()
        self._locate_set_table()

    # ---------- setitems 数据表（套装部件名，hackmap 权威偏移） ----------
    def _locate_set_table(self):
        self.set_table_addr, self.set_count = locate_set_table(self.pid, self.h)

    def set_special_name(self, dw_file_index: int) -> str:
        """dwFileIndex（ItemData+0x28，setitems 表行号）→ "中文 英文" 套装部件名。

        表地址失效时重定位；双语名取自 set_names 池（英文 desc 精确匹配）。
        """
        if not (0 <= dw_file_index < self.set_count) or not self.set_table_addr:
            return ""
        b = mem.read(self.pid, self.h,
                     self.set_table_addr + dw_file_index * SET_REC_SIZE, 0x30)
        if not b or len(b) != 0x30:
            return ""
        desc = b[2:34].split(b"\x00")[0].decode("latin-1", "ignore")
        if not desc:
            return ""
        cn = ""
        for en, c in self.set_names:
            if en == desc:
                cn = c
                break
        return ("%s %s" % (cn, desc)).strip() if cn else desc

    # ---------- unique 名表 ----------
    def _locate_unique_tables(self):
        for hit in scan_mem(self.pid, self.h, b"Elite Uniques"):
            head = hit - 0xB6
            cnt = dword(self.pid, self.h, head + 4)
            if not (0 < cnt < 2000):
                continue
            rec0 = head + 0x202
            b = mem.read(self.pid, self.h, rec0, 0x30)
            if not b or b[0] == 0 or b[0] == 0xFF:
                continue
            name = b[:self.NAME_LEN].split(b"\x00")[0]
            code = b[self.CODE_OFF:self.CODE_OFF + 4]
            if name and all(0x20 <= x < 0x7F for x in name[:4]) and \
               all((0x20 <= x < 0x7F) or x == 0 for x in code):
                self.unique_tables.append((rec0, cnt, name.decode("latin-1", "ignore")))
        # 去重
        seen = set()
        uniq = []
        for rec0, cnt, first in self.unique_tables:
            if rec0 not in seen:
                seen.add(rec0)
                uniq.append((rec0, cnt, first))
        self.unique_tables = uniq

    def english_name_by_code(self, code: str) -> str | None:
        code = code.rstrip("\x00 ").encode("ascii", "ignore")
        for rec0, cnt, _ in self.unique_tables:
            for i in range(min(cnt, 2000)):
                b = mem.read(self.pid, self.h, rec0 + i * self.REC_SIZE, self.CODE_OFF + 4)
                if not b:
                    break
                if b[self.CODE_OFF:self.CODE_OFF + 4].rstrip(b"\x00 ") == code:
                    return b[:self.NAME_LEN].split(b"\x00")[0].decode("latin-1", "ignore")
        return None

    # ---------- mod 注释池（中文名） ----------
    def _locate_notes(self):
        anchor = None
        for pat in (b"\xe5\xb7\xab\xe5\xb8\x88\xe4\xb9\x8b\xe5\x88\xba",   # 巫师之刺 UTF-8
                    b"\xe5\xb0\x8f\xe5\x88\x80\xe5\xb0\xb1\xe6\x98\xaf"):  # 小刀就是
            hits = scan_mem(self.pid, self.h, pat)
            if hits:
                anchor = hits[0]
                break
        if not anchor:
            return
        self.notes_anchor = anchor
        lo, hi = anchor - 0x30000, anchor + 0x10000
        buf = b""
        for base in range(lo, hi, 0x8000):
            chunk = mem.read(self.pid, self.h, base, 0x8000)
            if chunk:
                buf += chunk
        txt = buf.decode("utf-8", "ignore")
        # 提取 "中文名 英文名"（跳过 ÿcX 色码）
        txt = re.sub(r"\xc3\xbf c[0-9!\"+<:;.*]", "", txt) if False else txt
        txt2 = txt.replace("\xc3\xbf", " ").replace("\n", " ")
        for cn, en in re.findall(r"([\u4e00-\u9fff\u3400-\u4dbf]{2,14})\s+([A-Za-z][A-Za-z '&#;\-]{2,45})", txt2):
            en = en.strip()
            if en and (en not in self.note_map or len(cn) > len(self.note_map[en])):
                self.note_map[en] = cn

    def special_name(self, code: str) -> dict:
        en = self.english_name_by_code(code)
        if not en:
            return {"ok": False, "code": code}
        cn = self.note_map.get(en, "")
        return {"ok": True, "code": code, "en": en, "cn": cn,
                "display": ("%s %s" % (cn, en)).strip() if cn else en}

    # ---------- 套装部件名池（D2Lang String 表/注释池，双语 UTF-16LE） ----------
    # 套装部件名为 "中文 UTF-16 + 空格 + 英文 UTF-16" 单串，多处镜像：
    #   - String 表区（"华宁的祝福"@0x12924514 一带，含部分套装部件名）
    #   - mod 注释池区（"塔-拉夏的赫拉迪克纹章 Tal Rasha's Horadric Crest"@0x191700 一带）
    # 锚定已知套装部件名后 dump 其上下窗口，解析全部 "中文 英文" 对。
    # 注意：set 物品 → 部件名的映射仍需 setitems 数据表（mod 偏移失效，待 CE 定位）；
    # 本方法产出候选列表供后续接入。
    def _locate_set_names(self):
        anchors = []
        for pat in ("塔-拉夏的赫拉迪克纹章".encode("utf-16-le"),
                    "Tal Rasha's Horadric Crest".encode("utf-16-le"),
                    "华宁的祝福".encode("utf-16-le"),
                    "华宁的正义".encode("utf-16-le")):
            hits = scan_mem(self.pid, self.h, pat)
            if hits:
                anchors.append(hits[0])
        if not anchors:
            return
        self.set_anchor = anchors[0]
        pairs = {}
        seen_win = set()
        for anchor in anchors[:4]:
            lo = (anchor - 0x8000) & ~0xFFF
            hi = anchor + 0x8000
            win = (lo, hi)
            if win in seen_win:
                continue
            seen_win.add(win)
            buf = b""
            for base in range(lo, hi, 0x8000):
                chunk = mem.read(self.pid, self.h, base, 0x8000)
                if chunk:
                    buf += chunk
            txt = buf.decode("utf-16-le", "ignore")
            # "中文(2-14字,可含-) 英文(2-45字符)"，英文需大写字母开头（排除对话/数值）
            for cn, en in re.findall(
                    r"([\u4e00-\u9fff\u3400-\u4dbf\-]{2,14}) ([A-Z][A-Za-z '&;:\-]{2,45})(?=\x00)", txt):
                en = en.strip()
                if en and (en not in pairs or len(cn) > len(pairs[en])):
                    pairs[en] = cn
        self.set_names = sorted(pairs.items())


def find_bone_knife(pid, h):
    """定位骸骨小刀物品（txt=235），返回 (unit, quality, code)。"""
    d2c = mem.module_base(pid, "D2CLIENT.DLL")
    import json
    tbl = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\item_codes.json", encoding="utf-8"))
    code_by_id = {it["id"]: it["code"] for it in tbl["items"]}
    pPlayer = dword(pid, h, d2c + 0x11B800)
    pInv = dword(pid, h, pPlayer + 0x60)
    p = dword(pid, h, pInv + 0x0C)
    seen = set()
    while p and p not in seen:
        seen.add(p)
        txt = dword(pid, h, p + 0x04)
        idat = dword(pid, h, p + 0x14)
        if txt == 235:
            q = dword(pid, h, idat + 0x00)
            return p, q, code_by_id.get(txt, "?")
        p = dword(pid, h, idat + 0x64)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--list-notes", action="store_true")
    ap.add_argument("--scan-code", type=str)
    ap.add_argument("--dump-json", action="store_true")
    args = ap.parse_args()

    pid = mem.find_process("D2Loader.exe")
    if not pid:
        print("D2Loader.exe 未运行"); return 1
    h = mem.open_process_readonly(pid)
    sn = SpecialName(pid, h)
    print("unique 名表:", [(hex(r), c, f) for r, c, f in sn.unique_tables])
    print("注释池映射条数:", len(sn.note_map))

    if args.list_notes:
        for en, cn in sorted(sn.note_map.items()):
            print("  %s = %s" % (en, cn))
        return 0

    if args.scan_code:
        r = sn.special_name(args.scan_code)
        print(r)
        return 0

    if args.dump_json:
        out = {
            "exe": "D2Loader.exe",
            "ts": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
            "tables": [{"rec0": r, "count": c, "first": f} for r, c, f in sn.unique_tables],
            "unique_table_addr": ("0x%X" % sn.unique_tables[0][0]) if sn.unique_tables else "",
            "unique_count": sn.unique_tables[0][1] if sn.unique_tables else 0,
            "notes_addr": ("0x%X" % sn.notes_anchor) if sn.notes_anchor else "",
            "set_names_addr": ("0x%X" % sn.set_anchor) if sn.set_anchor else "",
            "sgpt_offset": ("0x%X" % SGPT_OFFSET),
            "set_table_addr": ("0x%X" % sn.set_table_addr) if sn.set_table_addr else "",
            "set_count": sn.set_count,
            "set_items": dump_set_items(pid, h, sn.set_table_addr, sn.set_count),
            "notes": sn.note_map,
            "set_names": [[en, cn] for en, cn in sn.set_names],
        }
        p = r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\special_names.json"
        json = __import__("json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("已写入", p, "tables:", len(out["tables"]), "notes:", len(out["notes"]),
              "set_names:", len(out["set_names"]), "set_items:", len(out["set_items"]))
        return 0

    if args.test:
        r = find_bone_knife(pid, h)
        if not r:
            print("骸骨小刀未找到"); return 1
        unit, q, code = r
        print("骸骨小刀 unit=%#x quality=%d code=%r" % (unit, q, code))
        print("特殊名:", sn.special_name(code))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
