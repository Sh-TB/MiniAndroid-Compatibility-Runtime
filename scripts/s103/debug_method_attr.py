#!/usr/bin/env python3
"""debug: method attribution for one class in ballbreak."""
import sys, struct, zipfile
sys.path.insert(0, '/home/z/my-project/scripts/s103')
from dex_typescan import parse_strings, parse_types, parse_method_ids, uleb

z = zipfile.ZipFile('/home/z/my-project/run/s99/apks/de.georgsieber.ballbreak.apk')
d = z.read('classes.dex')
strs = parse_strings(d)
types = parse_types(d, strs)
method_ids = parse_method_ids(d, strs, types)
cdefs_n, cdefs_off = struct.unpack_from('<II', d, 96)

# locate class_def for WindowDecorActionBar
target = 'Landroidx/appcompat/app/WindowDecorActionBar;'
for i in range(cdefs_n):
    base = cdefs_off + i * 32
    class_idx = struct.unpack_from('<I', d, base)[0]
    if types[class_idx] != target:
        continue
    _, _, _, _, _, _, cdata_off, _ = struct.unpack_from('<IIIIIIII', d, base)
    p = cdata_off
    sf, p = uleb(d, p); iff, p = uleb(d, p); dm, p = uleb(d, p); vm, p = uleb(d, p)
    print(f'static={sf} instance={iff} direct={dm} virtual={vm}')
    # fields
    for _ in range(sf + iff):
        _, p = uleb(d, p); _, p = uleb(d, p)
    midx = None
    for kind, count in (('direct', dm), ('virtual', vm)):
        for _ in range(count):
            diff, p = uleb(d, p)
            acc, p = uleb(d, p)
            code_off, p = uleb(d, p)
            midx = diff if midx is None else midx + diff
            name = method_ids[midx] if midx < len(method_ids) else f'OOB({midx})'
            has_io = ''
            if code_off:
                regs, ins, outs, tries, dbg, insns_size = struct.unpack_from('<HHHHII', d, code_off)
                insns = d[code_off+16:code_off+16+insns_size*2]
                # quick scan for 0x20/0x1f opcodes at even code-unit positions
                types_hit = []
                for j in range(0, len(insns)-3, 2):
                    op = insns[j+1]
                    if op in (0x20, 0x1f):
                        tidx = struct.unpack_from('<H', insns, j+2)[0]
                        if tidx < len(types):
                            types_hit.append((hex(op), types[tidx]))
                if types_hit:
                    has_io = f'  TYPEOPS={types_hit}'
            print(f'  {kind} idx={midx} {name} code_off={code_off}{has_io}')
    break
