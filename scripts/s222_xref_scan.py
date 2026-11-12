#!/usr/bin/env python3
"""S222-A step 3: xref scan — who calls Lnt1;.{e,Q,M0}, who writes/reads
Lyu0;.n:Ltw1;, who writes Ltw1;.c:J (packed density), who reads it.
Uses the proven per-method invoke/field scan with the full opcode-size walk."""
import struct, zipfile, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from s222_dex_dump import uleb, str_at, tds, protos, proto_str, mids, fids, m_size, f_size, c_size, c_off, dex, type_size, disasm

# --- resolve method ids of interest ---
def find_methods(cls_desc, names):
    out = []
    for i, (mc, mp, mn) in enumerate(mids):
        if tds[mc] == cls_desc and str_at(mn) in names:
            out.append((i, f"{cls_desc}->{str_at(mn)}{proto_str(mp)}"))
    return out

targets = {}
for cls, names in [("Lnt1;", {"e", "Q", "M0", "L0"}), ("Ltw1;", {"<init>"}), ("Ldi;", {"k"})]:
    for mid, sig in find_methods(cls, names):
        targets[mid] = sig
field_t = {}
for fi, (fc, ft, fn) in enumerate(fids):
    cd, fnm, ft2 = tds[fc], str_at(fn), tds[ft]
    if (cd, fnm) in {("Lyu0;", "n"), ("Ltw1;", "c"), ("Lnt1;", "B")}:
        field_t[fi] = f"{cd}.{fnm}:{ft2}"
print("method targets:", {k: v for k, v in list(targets.items())[:20]})
print("field targets:", field_t)

def SZ_STEP(op):
    SZT = [1]*256
    for x in range(0x04,0x08): SZT[x]=2
    SZT[0x13]=2; SZT[0x14]=3; SZT[0x16]=2; SZT[0x17]=3; SZT[0x18]=5; SZT[0x19]=2
    SZT[0x1a]=2; SZT[0x1b]=3
    SZT[0x1c]=2; SZT[0x1f]=2; SZT[0x20]=2
    SZT[0x24]=3; SZT[0x25]=3; SZT[0x26]=3
    SZT[0x29]=2; SZT[0x2a]=3; SZT[0x2b]=3; SZT[0x2c]=3
    for x in range(0x2d,0x32): SZT[x]=2
    for x in range(0x32,0x3e): SZT[x]=2
    for x in range(0x44,0x52): SZT[x]=2
    for x in range(0x52,0x60): SZT[x]=2
    for x in range(0x60,0x6e): SZT[x]=2
    for x in range(0x6e,0x73): SZT[x]=3
    for x in range(0x74,0x79): SZT[x]=3
    for x in range(0x90,0xb0): SZT[x]=2
    for x in range(0xd0,0xe3): SZT[x]=2
    SZT[0xea]=2; SZT[0xeb]=2; SZT[0xec]=2; SZT[0xed]=2; SZT[0xee]=2; SZT[0xef]=2
    SZT[0xf0]=2; SZT[0xf1]=2
    SZT[0xfa]=3; SZT[0xfb]=3; SZT[0xfc]=3; SZT[0xfd]=3
    SZT[0xfe]=2; SZT[0xff]=2
    return SZT[op]*2

callers = {sig: [] for sig in targets.values()}
fwriters = {sig: [] for sig in field_t.values()}
freaders = {sig: [] for sig in field_t.values()}

for i in range(c_size):
    cls = struct.unpack_from("<IIIIIIII", dex, c_off + i*32)
    ci, sd = cls[0], cls[6]
    if sd == 0: continue
    cdesc = tds[ci]
    sf, o = uleb(dex, sd); inf, o = uleb(dex, o); dm, o = uleb(dex, o); vm, o = uleb(dex, o)
    for _ in range(sf):
        d, o = uleb(dex, o); _, o = uleb(dex, o)
    for _ in range(inf):
        d, o = uleb(dex, o); _, o = uleb(dex, o)
    mi = 0
    for _ in range(dm + vm):
        d, o = uleb(dex, o); mi += d
        a, o = uleb(dex, o); co, o = uleb(dex, o)
        if co == 0 or mi >= m_size: continue
        regs, ins, outs, tries, dbg, insns_size = struct.unpack_from("<4H2I", dex, co)
        if insns_size == 0: continue
        base = co + 16; end = insns_size*2; j = 0
        while j < end:
            op = dex[base + j]
            if 0x6e <= op <= 0x72 and j + 6 <= end:
                midx = struct.unpack_from("<H", dex, base + j + 2)[0]
                if midx in targets:
                    callers[targets[midx]].append((cdesc, co, j//2))
                j += 6
            elif 0x74 <= op <= 0x78 and j + 6 <= end:
                midx = struct.unpack_from("<H", dex, base + j + 2)[0]
                if midx in targets:
                    callers[targets[midx]].append((cdesc, co, j//2))
                j += 6
            elif 0x52 <= op <= 0x5f and j + 4 <= end:
                fidx = struct.unpack_from("<H", dex, base + j + 2)[0]
                if fidx in field_t:
                    rec = (cdesc, co, j//2)
                    (fwriters if 0x59 <= op <= 0x5f else freaders)[field_t[fidx]].append(rec)
                j += 4
            else:
                j += SZ_STEP(op)
for sig, lst in callers.items():
    print(f"\nCALLERS of {sig}: {len(lst)}")
    seen = set()
    for cd, co, u in lst:
        k = cd
        if k in seen: continue
        seen.add(k)
        print(f"  {cd} (code@{hex(co)} @{u:#x})")
        if len(seen) >= 25: break
for sig, lst in fwriters.items():
    print(f"\nWRITERS of {sig}: {len(lst)}")
    seen = set()
    for cd, co, u in lst[:200]:
        if cd in seen: continue
        seen.add(cd)
        print(f"  {cd} (code@{hex(co)} @{u:#x})")
for sig, lst in freaders.items():
    print(f"\nREADERS of {sig}: {len(lst)} sites, classes: {sorted(set(c for c,_,_ in lst))[:20]}")
