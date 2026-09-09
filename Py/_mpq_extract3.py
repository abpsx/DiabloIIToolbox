# -*- coding: utf-8 -*-
"""listfile=False 直接读 MPQ 内 misc.bin"""
import mpyq, os

out_dir = r"C:\Users\abps\Desktop\DiabloIIToolbox\Py\_mpq"
os.makedirs(out_dir, exist_ok=True)

candidates = [
    "data\\global\\excel\\misc.bin",
    "DATA\\GLOBAL\\EXCEL\\MISC.BIN",
    "data/global/excel/misc.bin",
]

for mpq in (r"G:\game\diablo 2\Patch_D2.mpq",
            r"G:\game\diablo 2\D2data.mpq",
            r"G:\game\diablo 2\D2exp.mpq"):
    print("==", os.path.basename(mpq))
    try:
        a = mpyq.MPQArchive(mpq, listfile=False)
    except Exception as e:
        print("  打开失败:", e)
        continue
    for t in candidates:
        try:
            data = a.read_file(t)
            if data:
                fn = os.path.join(out_dir, os.path.basename(mpq).replace(".mpq", "") + "__misc.bin")
                open(fn, "wb").write(data)
                print(f"  {t} -> {fn} ({len(data)} 字节)")
                break
        except Exception as e:
            print(f"  {t}: {e}")
