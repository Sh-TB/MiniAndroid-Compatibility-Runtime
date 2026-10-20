#!/usr/bin/env python3
"""F-NEW-462 decode: dump AndroidGraphics/GLSurfaceView20 class facts from tower3d APK.
Shows superclass chain + <init> invoke/iput pattern around nested view construction."""
import sys, zipfile, struct, re

APK = sys.argv[1] if len(sys.argv) > 1 else 'upload/canonical_apks/stack.tower3d_1.apk'
WANT = sys.argv[2] if len(sys.argv) > 2 else 'AndroidGraphics'

z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]
print(f"APK {APK}: {len(dex_names)} dex files")

def uleb(buf, off):
    result = 0; shift = 0
    while True:
        b = buf[off]; off += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, off

def get_str(buf, str_idx, string_ids_off, string_ids_size):
    if str_idx >= string_ids_size: return f"<str{str_idx}>"
    data_off = struct.unpack_from('<I', buf, string_ids_off + 4*str_idx)[0]
    nlen, off = uleb(buf, data_off)
    raw = buf[off:off+nlen*4].split(b'\x00')[0]
    return raw.decode('utf-8', 'replace')

for dn in dex_names:
    buf = z.read(dn)
    if len(buf) < 112: continue
    string_ids_size, string_ids_off = struct.unpack_from('<II', buf, 56)
    type_ids_size, type_ids_off = struct.unpack_from('<II', buf, 64)
    proto_ids_size, proto_ids_off = struct.unpack_from('<II', buf, 72)
    field_ids_size, field_ids_off = struct.unpack_from('<II', buf, 80)
    method_ids_size, method_ids_off = struct.unpack_from('<II', buf, 88)
    class_defs_size, class_defs_off = struct.unpack_from('<II', buf, 96)

    def type_str(ti):
        if ti >= type_ids_size: return f"<type{ti}>"
        di = struct.unpack_from('<I', buf, type_ids_off + 4*ti)[0]
        return get_str(buf, di, string_ids_off, string_ids_size)

    def field_str(fi):
        if fi >= field_ids_size: return f"<field{fi}>"
        cls, typ, nam = struct.unpack_from('<HHI', buf, field_ids_off + 8*fi)
        return f"{type_str(cls)}.{get_str(buf, nam, string_ids_off, string_ids_size)}"

    def method_str(mi):
        if mi >= method_ids_size: return f"<method{mi}>"
        cls, proto, nam = struct.unpack_from('<HHI', buf, method_ids_off + 8*mi)
        return f"{type_str(cls)}.{get_str(buf, nam, string_ids_off, string_ids_size)}"

    hits = 0
    for ci in range(class_defs_size):
        coff = class_defs_off + 32*ci
        cls_idx, access, super_idx, _src, ifaces_off, ifaces_n, _cdata = struct.unpack_from('<IIIIIII', buf, coff)
        cname = type_str(cls_idx)
        if WANT not in cname: continue
        hits += 1
        sname = type_str(super_idx) if super_idx != 0xFFFFFFFF else '<none>'
        print(f"\n=== {cname} extends {sname} (dex {dn}) ===")
        # class_data
        cls_data_off = struct.unpack_from('<I', buf, coff+24)[0]
        if cls_data_off == 0:
            print(f"\n=== {cname} extends {sname} (dex {dn}) — NO class_data ===")
            continue
        off = cls_data_off
        static_fields_n, off = uleb(buf, off)
        instance_fields_n, off = uleb(buf, off)
        direct_methods_n, off = uleb(buf, off)
        virtual_methods_n, off = uleb(buf, off)
        # instance fields (consume static fields FIRST — class_data order:
        # static_fields, instance_fields, direct_methods, virtual_methods)
        # NOTE: each list has its OWN diff base starting at 0 (DEX spec).
        fidx = 0
        for i in range(static_fields_n):
            d, off = uleb(buf, off); fidx += d
            acc, off = uleb(buf, off)
        print(f"instance fields ({instance_fields_n}) [static skipped: {static_fields_n}]:")
        fidx = 0
        for i in range(instance_fields_n):
            d, off = uleb(buf, off); fidx += d
            acc, off = uleb(buf, off)
            print(f"  {field_str(fidx)}")
        # methods
        midx = 0
        for section, n in (('direct', direct_methods_n), ('virtual', virtual_methods_n)):
            midx = 0
            for i in range(n):
                d, off = uleb(buf, off); midx += d
                acc, off = uleb(buf, off)
                code_off, off = uleb(buf, off)
                mname = method_str(midx)
                if '<init>' not in mname: continue
                print(f"\n  METHOD {mname} code_off=0x{code_off:x}")
                if code_off == 0: continue
                regsz, insz, outsz, triesz, dbg, insnsz = struct.unpack_from('<HHHHII', buf, code_off)
                print(f"    registers={regsz} ins={insz} outs={outsz} insns={insnsz} units")
                ip = code_off + 16
                end = ip + insnsz*2
                # linear scan for key ops (approximate but sufficient for decode)
                while ip + 2 <= end:
                    op = buf[ip]
                    if op == 0x22:  # new-instance 22c
                        aa = buf[ip+1]; ti = struct.unpack_from('<H', buf, ip+2)[0]
                        print(f"    @{(ip-code_off-16)//2:04d} new-instance v{aa}, {type_str(ti)}")
                        ip += 4; continue
                    if op == 0x70 or op == 0x6f or op == 0x6e:  # invoke-direct/super/virtual 35c
                        aa = buf[ip+1]; mi2 = struct.unpack_from('<H', buf, ip+2)[0]
                        regs_word = struct.unpack_from('<H', buf, ip+4)[0]
                        nm = method_str(mi2)
                        kind = {0x70:'invoke-direct',0x6f:'invoke-super',0x6e:'invoke-virtual'}[op]
                        if 'GLSurfaceView' in nm or '<init>' in nm or 'Graphics' in nm:
                            print(f"    @{(ip-code_off-16)//2:04d} {kind} {nm} regs={[ (regs_word>>(4*k))&0xF for k in range(4)]+[(aa>>0)&0xF]}")
                        ip += 6; continue
                    if op == 0x5b or op == 0x5f or op == 0x5a or op == 0x59:  # iput family 22c
                        aa = buf[ip+1]; fi2 = struct.unpack_from('<H', buf, ip+2)[0]
                        src = (aa >> 0) & 0xF; obj = (aa >> 4) & 0xF
                        print(f"    @{(ip-code_off-16)//2:04d} iput-family v{src}, v{obj}, {field_str(fi2)}")
                        ip += 4; continue
                    if op == 0x0e:  # return-void
                        print(f"    @{(ip-code_off-16)//2:04d} return-void")
                        ip += 2; continue
                    ip += 2
    if hits: break
if not hits:
    print(f"class containing '{WANT}' not found in first pass")
