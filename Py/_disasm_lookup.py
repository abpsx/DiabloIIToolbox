# -*- coding: utf-8 -*-
"""完整反汇编查表函数 0x2509050（GetLocaleText 内部）"""
import sys, ctypes
sys.path.insert(0, r"C:\Users\abps\Desktop\DiabloIIToolbox\Py")
import mem_read as mem

pid = mem.find_process("D2Loader.exe")
if not pid:
    print("进程未运行"); sys.exit()
h = mem.open_process_readonly(pid)

def disasm(base, code, n=120):
    out = []
    i = 0
    while i < len(code) and len(out) < n:
        b = code[i]
        op = f"{base+i:08x}: {b:02x}"
        if b == 0xE8:
            rel = int.from_bytes(code[i+1:i+5], "little", signed=True)
            out.append(f"{op} call {base+i+5+rel:#x}")
            i += 5
        elif b in (0xE9,):
            rel = int.from_bytes(code[i+1:i+5], "little", signed=True)
            out.append(f"{op} jmp {base+i+5+rel:#x}")
            i += 5
        elif b in (0x74, 0x75, 0x72, 0x73, 0x76, 0x77, 0x7C, 0x7F, 0x70, 0x71, 0x7D, 0x7E):
            rel = code[i+1]
            if rel & 0x80:
                rel -= 256
            jn = {"0x74":"jz","0x75":"jnz","0x72":"jb","0x73":"jae","0x76":"jbe","0x77":"ja","0x7c":"jl","0x7f":"jg","0x70":"jo","0x71":"jno","0x7d":"jge","0x7e":"jle"}[hex(b)]
            out.append(f"{op} {jn} -> {base+i+2+rel:#x}")
            i += 2
        elif b == 0xEB:
            rel = code[i+1]
            if rel & 0x80:
                rel -= 256
            out.append(f"{op} jmp -> {base+i+2+rel:#x}")
            i += 2
        elif b == 0xA1:
            imm = int.from_bytes(code[i+1:i+5], "little")
            out.append(f"{op} mov eax,[{imm:#x}]")
            i += 5
        elif code[i:i+2] in (b"\x8B\x0D", b"\x8B\x15", b"\x8B\x05", b"\x8B\x1D"):
            r = {b"\x8B\x0D":"ecx", b"\x8B\x15":"edx", b"\x8B\x05":"eax", b"\x8B\x1D":"ebx"}[code[i:i+2]]
            imm = int.from_bytes(code[i+2:i+6], "little")
            out.append(f"{op} mov {r},[{imm:#x}]")
            i += 6
        elif b in (0xB8, 0xB9, 0xBA, 0xBB, 0xBE, 0xBF, 0xBD):
            imm = int.from_bytes(code[i+1:i+5], "little")
            r = {0xB8:"eax", 0xB9:"ecx", 0xBA:"edx", 0xBB:"ebx", 0xBE:"esi", 0xBF:"edi", 0xBD:"ebp"}[b]
            out.append(f"{op} mov {r},0x{imm:x}")
            i += 5
        elif code[i:i+2] == b"\x66\x81":
            out.append(f"{op} cmp word,[..],imm")
            i += 7
        elif code[i:i+2] == b"\x3B\x0D":
            imm = int.from_bytes(code[i+2:i+6], "little")
            out.append(f"{op} cmp ecx,[{imm:#x}]")
            i += 6
        elif code[i:i+2] == b"\x3B\x05":
            imm = int.from_bytes(code[i+2:i+6], "little")
            out.append(f"{op} cmp eax,[{imm:#x}]")
            i += 6
        elif code[i] in (0x3B,) and code[i+1] in (0xC1, 0xC2, 0xC3, 0xC6, 0xC7, 0xCE):
            out.append(f"{op} cmp r,r")
            i += 2
        elif code[i:i+2] == b"\x8B\x41":
            out.append(f"{op} mov eax,[ecx+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8B\x42":
            out.append(f"{op} mov eax,[edx+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8B\x52":
            out.append(f"{op} mov edx,[edx+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8B\x49":
            out.append(f"{op} mov ecx,[ecx+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8D\x96":
            disp = int.from_bytes(code[i+2:i+6], "little", signed=True)
            out.append(f"{op} lea edx,[esi{disp:+d}]")
            i += 6
        elif code[i:i+2] == b"\x8D\x8E":
            disp = int.from_bytes(code[i+2:i+6], "little", signed=True)
            out.append(f"{op} lea ecx,[esi{disp:+d}]")
            i += 6
        elif code[i:i+2] == b"\x8D\x46":
            out.append(f"{op} lea eax,[esi+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8D\x4E":
            out.append(f"{op} lea ecx,[esi+0x{code[i+2]:x}]")
            i += 3
        elif code[i] == 0x8B and code[i+1] in (0xC6, 0xC7):
            out.append(f"{op} mov eax,esi" if code[i+1]==0xC6 else f"{op} mov eax,edi")
            i += 2
        elif code[i:i+2] == b"\x33\xC0":
            out.append(f"{op} xor eax,eax")
            i += 2
        elif code[i:i+2] == b"\x33\xC9":
            out.append(f"{op} xor ecx,ecx")
            i += 2
        elif code[i:i+2] == b"\x33\xD2":
            out.append(f"{op} xor edx,edx")
            i += 2
        elif code[i:i+2] == b"\x8B\xCA":
            out.append(f"{op} mov ecx,edx")
            i += 2
        elif code[i:i+2] == b"\x8B\xD0":
            out.append(f"{op} mov edx,eax")
            i += 2
        elif code[i:i+2] == b"\x8B\xC2":
            out.append(f"{op} mov eax,edx")
            i += 2
        elif code[i:i+2] == b"\x8B\xCE":
            out.append(f"{op} mov ecx,esi")
            i += 2
        elif code[i:i+2] == b"\x8B\xD6":
            out.append(f"{op} mov edx,esi")
            i += 2
        elif code[i:i+2] == b"\x8B\xDE":
            out.append(f"{op} mov ebx,esi")
            i += 2
        elif code[i:i+2] == b"\x8B\xFE":
            out.append(f"{op} mov edi,esi")
            i += 2
        elif code[i:i+2] == b"\x8B\xC6":
            out.append(f"{op} mov eax,esi")
            i += 2
        elif code[i:i+2] == b"\x85\xC0":
            out.append(f"{op} test eax,eax")
            i += 2
        elif code[i:i+2] == b"\x85\xC9":
            out.append(f"{op} test ecx,ecx")
            i += 2
        elif code[i:i+2] == b"\x85\xD2":
            out.append(f"{op} test edx,edx")
            i += 2
        elif code[i:i+2] == b"\x8B\x40":
            out.append(f"{op} mov eax,[eax+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8B\x48":
            out.append(f"{op} mov ecx,[eax+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8B\x50":
            out.append(f"{op} mov edx,[eax+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8B\x58":
            out.append(f"{op} mov ebx,[eax+0x{code[i+2]:x}]")
            i += 3
        elif code[i:i+2] == b"\x8B\x0C":
            out.append(f"{op} mov ecx,[eax+ecx*1]")
            i += 3
        elif code[i:i+2] == b"\x8B\x04":
            out.append(f"{op} mov eax,[eax+ecx*1]")
            i += 3
        elif code[i:i+2] == b"\x8B\x14":
            out.append(f"{op} mov edx,[edx+eax*1]")
            i += 3
        elif code[i] == 0xC3:
            out.append(f"{op} ret")
            i += 1
        else:
            i += 1
    return out

code = mem.read(pid, h, 0x2509050, 0x140)
print("== 0x2509050 查表函数 ==")
for line in disasm(0x2509050, code, 110):
    print(" ", line)

ctypes.windll.kernel32.CloseHandle(h)
