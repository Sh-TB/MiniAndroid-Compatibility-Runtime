#!/usr/bin/env python3
"""WAVE C (F-NEW-181): ONE-PASS scan of the WhatsApp APK guava map-build chain.
Dumps: (1) every class whose name matches PATTERN, with its method list;
(2) full disassembly of the Builder build family + RegularImmutableMap methods
that reference createHashTable; (3) all call sites of createHashTable anywhere
in the dex (class + method names), so the tableSize feed chain is named.
"""
import logging, sys, zipfile
logging.disable(logging.CRITICAL)
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = '/tmp/my-project/apk_cache/WhatsApp_real.apk'
OUT = '/tmp/wavec'

z = zipfile.ZipFile(APK)
dexes = sorted(n for n in z.namelist()
               if n.startswith('classes') and n.endswith('.dex'))

want = ['ImmutableMap$Builder', 'ImmutableMapEntry', 'RegularImmutableMap',
        'CollectPreconditions', 'X/09d', 'X/09i']
build_methods = ('buildOrThrow', 'build', 'regularBuild', 'chooseTableSize',
                 'createHashTable', 'copyOf', 'fromEntries')
call_sites = []
meth_dump = open(f'{OUT}/build_chain_disasm.txt', 'w')

for dname in dexes:
    try:
        d = DalvikVMFormat(z.read(dname))
    except Exception as e:
        print(f'# {dname}: parse failed {e}')
        continue
    for c in d.get_classes():
        cname = c.get_name()
        hit = any(w in cname for w in want)
        for m in c.get_methods():
            mn = m.get_name()
            # record every call site of createHashTable / chooseTableSize
            code = m.get_code()
            if code is None:
                continue
            for ins in code.get_bc().get_instructions():
                try:
                    op = ins.get_name()
                    if 'invoke' in op:
                        outp = ins.get_output()
                        if 'createHashTable' in outp or 'chooseTableSize' in outp:
                            call_sites.append(
                                f'[{dname}] {cname}.{mn}: {op} {outp}')
                except Exception:
                    pass
            if hit and (mn in build_methods or mn.startswith('build')):
                print(f"=== [{dname}] {cname}.{mn} {m.get_descriptor()} ===",
                      file=meth_dump)
                idx = 0
                for ins in code.get_bc().get_instructions():
                    try:
                        o = ins.get_output()
                    except Exception as e:
                        o = f'<{e}>'
                    print(f'  {idx:04x}: {ins.get_name()} {o}', file=meth_dump)
                    idx += ins.get_length()
            if hit:
                with open(f'{OUT}/methods_index.txt', 'a') as ix:
                    ix.write(f'{cname} . {mn} {m.get_descriptor()}\n')

meth_dump.close()
with open(f'{OUT}/createHashTable_callers.txt', 'w') as f:
    f.write('\n'.join(call_sites))
print(f'call sites: {len(call_sites)}')
for cs in call_sites[:30]:
    print(cs)
