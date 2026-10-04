#!/usr/bin/env python3
"""f235_disasm_range.py — CORRECT dalvik disassembly of an arbitrary pc range
of one method, resolving string/type/field/method ids. Official size table.
Usage: f235_disasm_range.py <apk> <Lcls;> <method> <from_pc> <to_pc>
"""
import zipfile, struct, sys

APK, CLS, MTH = sys.argv[1], sys.argv[2], sys.argv[3]
FROM, TO = int(sys.argv[4]), int(sys.argv[5])

SZ = [
 1,1,2,3,1,2,3,1,2,3,1,1,1,1,1,1,
 1,1,1,2,2,2,2,2,3,3,3,2,2,2,2,2,
] + [2]*(0x74-0x20) + [3,3,3,3,3] + [1,1] + [2]*(0x100-0x7a)

z = zipfile.ZipFile(APK)
dex = None
for n in z.namelist():
    if n.endswith('.dex'):
        dex = z.read(n); break
d = dex
ssz, sof = struct.unpack_from('<II', d, 0x38)
tsz, tof = struct.unpack_from('<II', d, 0x40)
psz, pof = struct.unpack_from('<II', d, 0x48)
fsz, fof = struct.unpack_from('<II', d, 0x50)
msz, mof = struct.unpack_from('<II', d, 0x58)
cdsz, cdof = struct.unpack_from('<II', d, 0x60)

def uleb(buf, off):
    r, s = 0, 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s; s += 7
        if not b & 0x80: break
    return r, off

def getstr(idx):
    if idx >= ssz: return f"<str{idx}>"
    so = struct.unpack_from('<I', d, sof + idx*4)[0]
    n, off = uleb(d, so)
    return d[off:off+n].decode('utf-8', 'replace')

def gettype(idx):
    si = struct.unpack_from('<I', d, tof + idx*4)[0]
    return getstr(si)

def getfield(idx):
    if idx >= fsz: return f"<f{idx}>"
    cid, tid, nid = struct.unpack_from('<HHI', d, fof + idx*8)
    return f"{gettype(tid)}.{getstr(nid)}"

def getproto(idx):
    so, ri, pi = struct.unpack_from('<IHH', d, sof + 0)  # placeholder
    return ""

def getmethod(idx):
    if idx >= msz: return f"<m{idx}>"
    cid, pid, nid = struct.unpack_from('<HHI', d, mof + idx*8)
    return f"{gettype(cid)}.{getstr(nid)}"

def u32(off): return struct.unpack_from('<I', d, off)[0]

# find class def
target = None
for i in range(cdsz):
    off = cdof + i*32
    cidx = struct.unpack_from('<I', d, off)[0]
    if gettype(cidx) == CLS:
        target = off; break
if target is None:
    print("class not found"); sys.exit(1)
coff = u32(target+24)  # class_data_off

static_f, inst_f, dm, vm = [], [], [], []
def rd_fields(p, n, arr):
    fi = 0
    for _ in range(n):
        di, p = uleb(d, p)
        fi += di
        a, p = uleb(d, p)
        arr.append((fi, a))
    return p
p = coff
p, sfields_n = uleb(d, p); p, inst_f_n = uleb(d, p)
p, dm_n = uleb(d, p); p, vm_n = uleb(d, p)
p = rd_fields(p, sfields_n, static_f)
p = rd_fields(p, inst_f, [])
def rd_methods(p, n, arr):
    mi = 0
    for _ in range(n):
        di, p = uleb(d, p)
        mi += di
        a, p = uleb(d, p)
        arr.append((mi, a))
    return p
p = rd_methods(p, dm_n, dm)
p = rd_methods(p, vm_n, vm)

for mi, a in dm + vm:
    midx = (mi, a)
    moff = u32(mof + mi*8)
    # code_off comes from method_struct; encoded_method: idx(uleb), access(uleb), code_off(uleb)
# re-read with code offsets:
def rd_methods2(p, n, arr):
    mi = 0
    for _ in range(n):
        di, p = uleb(d, p)
        mi += di
        a, p = uleb(d, p)
        co, p = uleb(d, p)
        arr.append((mi, a, co))
    return p
dm2, vm2 = [], []
p2 = coff
p2, _ = uleb(d, p2); p2, _ = uleb(d, p2)
p2, _ = uleb(d, p2); p2, _ = uleb(d, p2)
# skip field lists again
p2 = rd_fields(p2, len(static_f), [])
p2 = rd_fields(p2, len(inst_f), [])
p2 = rd_methods2(p2, dm_n, dm2)
p2 = rd_methods2(p2, vm_n, vm2)

for mi, a, co in dm2 + vm2:
    if co == 0: continue
    msz_i = struct.unpack_from('<I', d, mof + mi*8)
    nid = struct.unpack_from('<HHI', d, mof + mi*8)[2]
    name = getstr(nid)
    if name != MTH: continue
    insns_n = struct.unpack_from('<I', d, co+12)[0]
    insns_off = co + 16
    print(f"== {CLS}.{MTH} insns={insns_n} (showing {FROM}..{TO}) ==")
    pc = 0
    while pc < insns_n:
        w = struct.unpack_from('<H', d, insns_off + pc*2)[0]
        op = w & 0xff
        sz = SZ[op]
        if FROM <= pc <= TO:
            raw = [struct.unpack_from('<H', d, insns_off + (pc+k)*2)[0] for k in range(sz)]
            idx = raw[1] if sz >= 2 else 0
            note = ""
            if op in (0x1a, 0x1b):  # const-string
                note = getstr(idx)
            elif op == 0x22: note = gettype(idx)
            elif op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60):
                note = getfield(idx)
            elif op in (0x6e,0x6f,0x70,0x71,0x72):
                note = getmethod(idx)
            elif op == 0x74:
                note = getmethod(idx)
            print(f"  {pc:#06x}: op=0x{op:02x} raw={[hex(x) for x in raw]} {note}")
        pc += sz
