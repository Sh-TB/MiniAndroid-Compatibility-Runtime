#!/usr/bin/env python3
"""S41 Attack-1c: find all CALLERS of Loj0;->Q (JobSupport.awaitInternal) in dooz_23 DEX,
and dump a bytecode window around each call to identify the awaiting code path."""
import zipfile, sys
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/tmp/my-project/apk_cache/s36new/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
d = DEX(z.read('classes.dex'))

CALLS = [
    'Loj0;->Q(Z Lkj0;)Ley;',   # JobSupport.awaitInternal
]

for c in d.get_classes():
    for m in c.get_methods():
        code = m.get_code()
        if code is None:
            continue
        ins_list = list(code.get_bc().get_instructions())
        for i, ins in enumerate(ins_list):
            try:
                out = ins.get_output()
            except Exception:
                continue
            if any(call in out for call in CALLS):
                print(f"\n=== CALLER {c.get_name()}.{m.get_name()} {m.get_descriptor()} @ {i} ===")
                lo = max(0, i - 25)
                hi = min(len(ins_list), i + 12)
                for j in range(lo, hi):
                    ins2 = ins_list[j]
                    try:
                        out2 = ins2.get_output()
                    except Exception as e:
                        out2 = f'<{e}>'
                    mark = '>>' if j == i else '  '
                    print(f'  {mark} {j:04x}: {ins2.get_name()} {out2}')
