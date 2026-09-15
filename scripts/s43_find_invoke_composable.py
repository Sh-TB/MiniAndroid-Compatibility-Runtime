#!/usr/bin/env python3
# ============================================================================
# S43 probe #4 — locate the EXACT obfuscated invokeComposable call site
# ----------------------------------------------------------------------------
# Contract (established by probes #1-#3 + upstream Expect.jvmAndAndroid.kt:24):
#   invokeComposable(composer, composable):
#       checkcast Lr90;          (composable as Function2 — R8-renamed)
#       invoke-interface {receiver, composer, Integer(1)}
#                        Lr90;->h(Object,Object)Object
#
# This probe scans every method for that exact pair and dumps:
#   - the owning class+method (the obfuscated invokeComposable)
#   - its full bytecode (annotated)
# Then we can grep the RUN LOG for this method to see which branch the
# engine took at the h-dispatch (F-068 runtime-first vs stub fallthrough).
# ============================================================================
import zipfile
import logging
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

APK = '/home/z/my-project/corpus_cache/io.github.yamin8000.dooz_23.apk'
z = zipfile.ZipFile(APK)
dex_names = [n for n in z.namelist() if n.endswith('.dex')]

classes, methods = {}, {}
for dn in dex_names:
    d = DEX(z.read(dn))
    for c in d.get_classes():
        name = c.get_name()
        if name not in classes:
            classes[name] = (dn, c)
        for m in c.get_methods():
            methods[(name, m.get_name(), m.get_descriptor())] = m

def disasm(m, maxn=500):
    out, idx, n = [], 0, 0
    code = m.get_code()
    if code is None:
        return out
    for ins in code.get_bc().get_instructions():
        if n >= maxn:
            out.append((idx, "…TRUNC", "")); break
        try:
            out.append((idx, ins.get_name(), ins.get_output()))
        except Exception:
            out.append((idx, "?", ""))
        idx += ins.get_length(); n += 1
    return out

# ── scan for checkcast Lr90;/Lj90; followed within 8 ops by invoke-interface
#    whose output mentions ->h (the renamed Function2.invoke) ──────────────
print("===== invokeComposable site scan =====")
hits = []
for (cn, mn, md), m in methods.items():
    code = m.get_code()
    if code is None:
        continue
    ops = disasm(m, 3000)
    for k, (off, op, outp) in enumerate(ops):
        if op == 'checkcast' and ('Lr90;' in outp or 'Lj90;' in outp):
            window = ops[k:k + 9]
            iw = [w for w in window if w[1].startswith('invoke-interface')]
            if any('->h' in w[2] and 'Lr90;' in w[2] for w in iw):
                hits.append((cn, mn, md, ops))
                break

print(f"sites found: {len(hits)}")
for cn, mn, md, ops in hits[:4]:
    print(f"\n--- {cn}->{mn} {md} ---")
    for off, op, outp in ops:
        print(f"  {off:04x}: {op} {outp}"[:180])
