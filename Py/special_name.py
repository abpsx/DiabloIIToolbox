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
    """动态定位 unique 名表 + 注释池, 提供 code→特殊名。"""

    REC_SIZE = 0x14C      # unique 名表记录大小
    NAME_LEN = 0x26       # 名字字段宽度
    CODE_OFF = 0x26       # code 字段偏移（名字后）

    def __init__(self, pid: int, h: int):
        self.pid, self.h = pid, h
        self.unique_tables = []     # [(记录首, 记录数)]
        self.note_map = {}          # 英文名 -> 中文名
        self._locate_unique_tables()
        self._locate_notes()

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
            "ts": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
            "tables": [{"rec0": r, "count": c, "first": f} for r, c, f in sn.unique_tables],
            "notes": sn.note_map,
        }
        p = r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\special_names.json"
        json = __import__("json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("已写入", p, "tables:", len(out["tables"]), "notes:", len(out["notes"]))
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
