# -*- coding: utf-8 -*-
"""从 MPQ 提取 misc.bin（优先 Patch_D2 即 mod 覆盖）"""
import mpyq, os, sys

out_dir = r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_mpq"
os.makedirs(out_dir, exist_ok=True)

target = "data\\global\\excel\\misc.bin"

for mpq in (r"G:\game\diablo 2\Patch_D2.mpq",
            r"G:\game\diablo 2\D2data.mpq",
            r"G:\game\diablo 2\D2exp.mpq"):
    print("==", os.path.basename(mpq))
    a = mpyq.MPQArchive(mpq)
    # 找目标
    hits = [n for n in a.files if n.lower().endswith("misc.bin")]
    print("  misc.bin 条目:", hits)
    for h in hits:
        try:
            data = a.read_file(h)
            fn = os.path.join(out_dir, os.path.basename(mpq).replace(".mpq", "") + "__misc.bin")
            open(fn, "wb").write(data)
            print(f"  已提取 {fn} ({len(data)} 字节)")
        except Exception as e:
            print(f"  提取失败 {h}: {e}")
