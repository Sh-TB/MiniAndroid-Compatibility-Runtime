#!/usr/bin/env python3
"""CONT-18 T-01: extract the REAL kotlinx MutexImpl/SemaphoreAndMutexImpl method
bytecode from the corpus DEX (source-first reconstruction — the app's actual
bytecode is the authority for what the runtime must execute)."""
import struct, sys, zipfile

ARG = sys.argv[1] if len(sys.argv) > 1 else 'tmp/f217_dex/classes.dex'
OUT = 'evidence/cont18/f217_dex_extract.json'

if ARG.endswith('.apk'):
    z = zipfile.ZipFile(ARG)
    dex_names = [n for n in z.namelist() if n.endswith('.dex')]
else:
    import os
    # Wrap a raw .dex into an in-memory zip so one code path serves both.
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as t:
        t.write(ARG, 'classes.dex')
    z = zipfile.ZipFile(buf)
    dex_names = ['classes.dex']

def uleb(buf, off):
    r = 0; s = 0
    while True:
        b = buf[off]; off += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, off

results = {}
for dn in dex_names:
    b = z.read(dn)
    if b'kotlinx/coroutines/sync/MutexImpl' not in b:
        continue
    # header
    string_ids_size, string_ids_off = struct.unpack_from('<II', b, 0x38)
    type_ids_size, type_ids_off = struct.unpack_from('<II', b, 0x40)
    proto_ids_size, proto_ids_off = struct.unpack_from('<II', b, 0x48)
    method_ids_size, method_ids_off = struct.unpack_from('<II', b, 0x58)
    class_defs_size, class_defs_off = struct.unpack_from('<II', b, 0x60)

    def get_string(idx):
        off = struct.unpack_from('<I', b, string_ids_off + 4 * idx)[0]
        n, off = uleb(b, off)
        end = b.index(b'\x00', off)
        return b[off:end].decode('utf-8', 'replace')

    def get_type(idx):
        si = struct.unpack_from('<I', b, type_ids_off + 4 * idx)[0]
        return get_string(si)

    methods = []
    for mi in range(method_ids_size):
        cls, proto, name = struct.unpack_from('<HHI', b, method_ids_off + 8 * mi)
        methods.append((get_type(cls), get_string(name)))

    for ci in range(class_defs_size):
        off = class_defs_off + 32 * ci
        cls_idx = struct.unpack_from('<I', b, off)[0]
        cls = get_type(cls_idx)
        if not any(k in cls for k in ('kotlinx/coroutines/sync/MutexImpl;',
                                      'SemaphoreAndMutexImpl;')):
            continue
        class_data_off = struct.unpack_from('<I', b, off + 24)[0]
        if class_data_off == 0:
            continue
        p = class_data_off
        sf, inf, dm, vm, p = uleb(b, p), uleb(b, p), uleb(b, p), uleb(b, p), p
        # uleb sequence: static_fields_size, instance_fields_size,
        # direct_methods_size, virtual_methods_size
        sf_n, sf_o = uleb(b, class_data_off)
        if_n, if_o = uleb(b, sf_o)
        dm_n, dm_o = uleb(b, if_o)
        vm_n, vm_o = uleb(b, dm_o)
        p = vm_o
        # skip static_fields + instance_fields (each entry = 2 ulebs)
        for _ in range(sf_n + if_n):
            _d, p = uleb(b, p)
            _a, p = uleb(b, p)
        for kind, count in (('direct', dm_n), ('virtual', vm_n)):
            midx = 0
            for _ in range(count):
                midx_d, p = uleb(b, p); midx += midx_d
                acc, p = uleb(b, p)
                code_off, p = uleb(b, p)
                if code_off == 0:
                    continue
                mcls, mname = methods[midx]
                regs, ins, outs, tries, dbg, insns_sz = struct.unpack_from(
                    '<HHHHII', b, code_off)
                insns = b[code_off + 16: code_off + 16 + insns_sz * 2]
                key = kind[0] + ':' + cls + '->' + mname
                results[key] = {
                    'dex': dn, 'access': acc, 'registers': regs,
                    'ins': ins, 'outs': outs, 'insns_size': insns_sz,
                    'insns_hex': insns.hex(),
                }

import json
json.dump(results, open(OUT, 'w'), indent=1)
for k, v in sorted(results.items()):
    print(f"{k}  insns={v['insns_size']} regs={v['registers']}")
print('saved', OUT, f'({len(results)} methods)')
