#!/usr/bin/env python3
"""CONT-47 T5 part 3: decode the R8-renamed RequestDelegate family.
Find classes with run(Lorg/telegram/tgnet/TLObject;, Lorg/telegram/tgnet/TLRPC$TL_error;)
and dump the instanceof check + response field reads for the config chain
(TL_config / TL_webBrowserSettings)."""
import sys, zipfile, struct, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cont47_t5_scan import DEXES, Dex, find_class

TARGETS = ['Lorg/telegram/tgnet/TLRPC$TL_config;',
           'Lorg/telegram/tgnet/tl/TL_account$TL_webBrowserSettings;',
           'Lorg/telegram/tgnet/tl/TL_account$TL_contentSettings;',
           'Lorg/telegram/tgnet/TLRPC$TL_langpack_language;']

for cls in ['Lorg/telegram/messenger/ka;']:
    d = find_class(cls)
    if not d:
        print(f"{cls}: NOT FOUND"); continue
    dm, vm = d.class_methods(cls)
    print(f"=== {cls} in {d.name}: {len(dm)} direct + {len(vm)} virtual ===")
    for midx, acc, co in dm + vm:
        if not co: continue
        cn, mn = d.methods[midx]
        if cn != cls: continue
        ins = d.disasm(co)
        txt = [t for _, t in ins]
        if any(t.startswith('instance-of') for t in txt) or mn == 'run':
            print(f"--- {mn} code_off={co:#x}")
            for pc, t in ins:
                print(f"  @{pc:04x} {t}")
