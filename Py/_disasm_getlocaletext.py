# -*- coding: utf-8 -*-
"""反汇编 GetLocaleText(0x2509450) 完整 + 内部查表函数，找 idx→值指针表"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def simple_disasm(base, code, n=200):
    """极简 x86 反汇编：标记 mov reg,[imm]/call/lea/jcc"""
    out = []
    i = 0
    while i < len(code) and len(out) < n:
        b = code[i]
        op = f"{base+i:08x}: {b:02x}"
        if b == 0xE8:  # call rel32
            rel = int.from_bytes(code[i+1:i+5], "little", signed=True)
            out.append(f"{op} call {base+i+5+rel:#x}")
            i += 5
        elif b in (0xE9,):  # jmp rel32
            rel = int.from_bytes(code[i+1:i+5], "little", signed=True)
            out.append(f"{op} jmp {base+i+5+rel:#x}")
            i += 5
        elif b == 0x74 or b == 0x75 or b == 0x72 or b == 0x73 or b == 0x76 or b == 0x77 or b == 0x7C or b == 0x7F:
            rel = code[i+1]
            if rel & 0x80:
                rel -= 256
            out.append(f"{op} jcc{'+0x'+('' if rel>=0 else '-')}{abs(rel):x} -> {base+i+2+rel:#x}")
            i += 2
        elif b == 0xEB:
            rel = code[i+1]
            if rel & 0x80:
                rel -= 256
            out.append(f"{op} jmp -> {base+i+2+rel:#x}")
            i += 2
        elif b == 0xA1:  # mov eax,[imm32]
            imm = int.from_bytes(code[i+1:i+5], "little")
            out.append(f"{op} mov eax,[{imm:#x}]")
            i += 5
        elif code[i:i+2] == b"\x8B\x0D":
            imm = int.from_bytes(code[i+2:i+6], "little")
            out.append(f"{op} mov ecx,[{imm:#x}]")
            i += 6
        elif code[i:i+2] == b"\x8B\x15":
            imm = int.from_bytes(code[i+2:i+6], "little")
            out.append(f"{op} mov edx,[{imm:#x}]")
            i += 6
        elif code[i:i+2] == b"\x8B\x05":
            imm = int.from_bytes(code[i+2:i+6], "little")
            out.append(f"{op} mov eax,[{imm:#x}]")
            i += 6
        elif code[i:i+2] == b"\x8B\x1D":
            imm = int.from_bytes(code[i+2:i+6], "little")
            out.append(f"{op} mov ebx,[{imm:#x}]")
            i += 6
        elif b == 0xB8 or b == 0xB9 or b == 0xBA or b == 0xBB or b == 0xBE or b == 0xBF:
            imm = int.from_bytes(code[i+1:i+5], "little")
            out.append(f"{op} mov e{'a' if b==0xB8 else 'c' if b==0xB9 else 'd' if b==0xBA else 'b' if b==0xBB else 's' if b==0xBE else 'd'}{'x' if b in (0xB8,0xB9,0xBA,0xBB) else 'i'},0x{imm:x}")
            i += 5
        elif code[i:i+2] == b"\x66\x81":
            out.append(f"{op} cmp word,[..],imm")
            i += 7
        elif code[i:i+2] == b"\x81\xFE":
            imm = int.from_bytes(code[i+2:i+6], "little", signed=True)
            out.append(f"{op} cmp esi,{imm}")
            i += 6
        elif code[i:i+2] == b"\x81\xF9":
            imm = int.from_bytes(code[i+2:i+6], "little", signed=True)
            out.append(f"{op} cmp ecx,{imm}")
            i += 6
        elif code[i:i+2] == b"\x83\xFE":
            out.append(f"{op} cmp esi,{code[i+2]}")
            i += 3
        elif code[i:i+2] == b"\x8D\x96":
            disp = int.from_bytes(code[i+2:i+6], "little", signed=True)
            out.append(f"{op} lea edx,[esi{disp:+d}]")
            i += 6
        elif code[i:i+2] == b"\x8D\x8E":
            disp = int.from_bytes(code[i+2:i+6], "little", signed=True)
            out.append(f"{op} lea ecx,[esi{disp:+d}]")
            i += 6
        else:
            i += 1
    return out

# 读 GetLocaleText 完整
code = mem.read(pid, h, 0x2509450, 0x200)
print("== GetLocaleText @0x2509450 ==")
for line in simple_disasm(0x2509450, code, 80):
    print(" ", line)

# 读内部查表函数（GetLocaleText 的 call 目标）
for fn in (0x250905C,):
    c2 = mem.read(pid, h, fn, 0x180)
    print(f"\n== 内部函数 @{fn:#x} ==")
    for line in simple_disasm(fn, c2, 60):
        print(" ", line)

ctypes.windll.kernel32.CloseHandle(h)
