#!/usr/bin/env python3
"""CONT-27: tolerant DEX method disassembler (wraps cont26's, skips tail OOR)."""
import sys, io, contextlib
sys.path.insert(0, "/home/z/my-project/scripts")
import importlib.util
spec = importlib.util.spec_from_file_location("d26", "/home/z/my-project/scripts/cont26_dex_method_disasm.py")
d26 = importlib.util.module_from_spec(spec)
# prevent its main() from running
d26.__name__ = "d26"
spec.loader.exec_module(d26)

# patch: bounds-tolerant disasm
orig_disasm = d26.disasm
def safe_disasm(dex, code):
    out = []
    ins = code["insns"]
    def g(i):
        return ins[i] if i < len(ins) else 0
    i = 0
    def s8(v): return v-256 if v > 0x7f else v
    def s16(v): return v-0x10000 if v > 0x7fff else v
    while i < len(ins):
        unit = g(i)
        op = unit & 0xff
        name = d26.OPCODES.get(op, f"op-{op:#04x}")
        A = (unit >> 8) & 0xf
        AA = (unit >> 8) & 0xff
        B = (unit >> 12) & 0xf
        try:
            if op == 0x00:
                out.append(f"  @{i:#06x} nop"); i += 1; continue
            if op == 0x1a:
                out.append(f"  @{i:#06x} const-string v{AA}, \"{dex.s(g(i+1))[:64]}\""); i += 2; continue
            if op == 0x1b:
                idx = g(i+1) | g(i+2) << 16
                out.append(f"  @{i:#06x} const-string/jumbo v{AA}, \"{dex.s(idx)[:64]}\""); i += 3; continue
            if op in (0x6e,0x6f,0x70,0x71,0x72):
                midx = g(i+1); cnt = (unit >> 12) & 0xf; gg = (unit >> 8) & 0xf; w = g(i+2)
                regs = [(w >> (4*k)) & 0xf for k in range(4)] + ([gg] if cnt == 5 else [])
                out.append(f"  @{i:#06x} {name} {{{','.join('v'+str(r) for r in regs[:cnt])}}}, {dex._mid(midx)}"); i += 3; continue
            if op in (0x74,0x76,0x77,0x78):
                midx = g(i+1); cnt = (unit >> 8) & 0xff; start = g(i+2)
                out.append(f"  @{i:#06x} {name} {{v{start}..v{start+cnt-1}}}, {dex._mid(midx)}"); i += 3; continue
            if op in (0x52,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,
                      0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
                fidx = g(i+1)
                out.append(f"  @{i:#06x} {name} v{A}, v{B}, f@{fidx} ({d26.field_name_idx(dex, fidx)})"); i += 2; continue
            if op in (0x1c,0x1f,0x22,0x23,0x24,0x25):
                tidx = g(i+1)
                out.append(f"  @{i:#06x} {name} v{AA}, {dex.t(tidx)}"); i += 2; continue
            if op == 0x20:
                out.append(f"  @{i:#06x} instance-of v{A}, v{B}, {dex.t(g(i+1))}"); i += 2; continue
            if op == 0x27:
                out.append(f"  @{i:#06x} throw v{AA}"); i += 1; continue
            if op in (0x32,0x33,0x34,0x35,0x36,0x37):
                out.append(f"  @{i:#06x} {name} v{A}, v{B}, -> @{i+s16(g(i+1)):#06x}"); i += 2; continue
            if op in (0x38,0x39,0x3a,0x3b,0x3c,0x3d):
                out.append(f"  @{i:#06x} {name} v{AA}, -> @{i+s16(g(i+1)):#06x}"); i += 2; continue
            if op == 0x28:
                out.append(f"  @{i:#06x} goto -> @{i+s8(AA):#06x}"); i += 1; continue
            if op == 0x29:
                out.append(f"  @{i:#06x} goto/16 -> @{i+s16(g(i+1)):#06x}"); i += 2; continue
            if op == 0x2a:
                idx = g(i+1) | g(i+2) << 16
                out.append(f"  @{i:#06x} goto/32 -> @{i+(idx if idx < 0x80000000 else idx-0x100000000):#06x}"); i += 3; continue
            if op == 0x12:
                lit = B; lit = lit-16 if lit > 7 else lit
                out.append(f"  @{i:#06x} const/4 v{A}, {lit}"); i += 1; continue
            if op in (0x13,0x15,0x16):
                out.append(f"  @{i:#06x} {name} v{AA}, {s16(g(i+1))}"); i += 2; continue
            if op in (0x14,0x17):
                val = g(i+1) | g(i+2)<<16 | g(i+3)<<32
                out.append(f"  @{i:#06x} {name} v{AA}, {val:#x}"); i += 3; continue
            if op == 0x18:
                out.append(f"  @{i:#06x} const-wide/high16 v{AA}, {g(i+1):#x}"); i += 2; continue
            if op == 0x19:
                val = g(i+1) | g(i+2)<<16 | g(i+3)<<32
                out.append(f"  @{i:#06x} const-wide v{AA}, {val:#x}"); i += 3; continue
            if op in (0x0e,0x0a,0x0b,0x0c,0x0d,0x0f,0x10,0x11):
                out.append(f"  @{i:#06x} {name} v{AA}"); i += 1; continue
            if op in (0x01,0x04,0x05,0x06,0x07,0x08,0x09):
                out.append(f"  @{i:#06x} {name} v{A}, v{B}"); i += 1; continue
            if op == 0x26:
                out.append(f"  @{i:#06x} fill-array-data v{AA}, payload"); i += 3; continue
            if op in (0x2b,0x2c):
                out.append(f"  @{i:#06x} {name} v{AA}, payload"); i += 3; continue
            if op in (0x7b,0x81,0x82,0x85,0x8f,0x90,0x91):
                out.append(f"  @{i:#06x} {name} v{B}, v{A}"); i += 1; continue
            if op in (0xb0,0xbb,0xda,0xdb,0xdf,0xe0):
                out.append(f"  @{i:#06x} {name} v{A}, v{B}"); i += 1; continue
            out.append(f"  @{i:#06x} {name} unit={unit:#06x}")
            i += 1
        except Exception as e:
            out.append(f"  @{i:#06x} <decode-err {e} op={op:#04x}>")
            i += 1
    return out

d26.disasm = safe_disasm
if __name__ == "__main__":
    d26.main()
