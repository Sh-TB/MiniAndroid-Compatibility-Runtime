#!/usr/bin/env python3
# ============================================================================
# S43 probe #2 — corrected Function2-shape search + MainActivity lambda chain
# ----------------------------------------------------------------------------
# Probe #1 findings:
#   - Lkotlin/jvm/functions/Function2; NOT in DEX (R8 renamed function
#     interfaces — the interface NAME is not the contract anymore).
#   - Zero (Object,I)Object methods — wrong shape assumption on my part:
#     Function2<P1,P2,R>.invoke erases to invoke(Object,Object)Object, and
#     the int arg (changed flags = 1) is BOXED via Integer.valueOf at the
#     invokeComposable call site.
#
# This probe establishes the REAL dispatch ground truth:
#   Q1: all interfaces with an (Object,Object)Object method — renamed
#       Function.invoke candidates.
#   Q2: MainActivity.onCreate full bytecode — find setContent call + the
#       content-lambda class instantiated there (new-instance just before).
#   Q3: dump the content-lambda class: interfaces + methods (its renamed
#       invoke is what realFn(composer,1) must dispatch to).
#   Q4: find checkcast-to-renamed-Function2 sites (the invokeComposable
#       equivalent inside the GapComposer-obfuscated class).
#   Q5: confirm which obfuscated class is the composer (Lxk0; per S42) and
#       list its method names mentioned in the S42 trace (m0, Z0, l1, l0).
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

def disasm(m, maxn=600):
    """Full bounded disasm: list of (offset, opname, output)."""
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

# ══════════════════════════════════════════════════════════════════════════
# Q1: renamed Function2 candidates — interfaces declaring
#     (Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
# ══════════════════════════════════════════════════════════════════════════
print("===== Q1: interfaces with invoke(Object,Object)Object shape =====")
shape = '(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;'
iface_hits = {}
for (cn, mn, md) in methods:
    if md == shape:
        iface_hits.setdefault(cn, []).append(mn)
print(f"  classes declaring the shape: {len(iface_hits)}")
for cn, mns in sorted(iface_hits.items()):
    cd = classes.get(cn)
    is_iface = False
    if cd:
        try:
            is_iface = cd[1].is_interface()
        except Exception:
            is_iface = '?'
    print(f"    {cn}  iface={is_iface}  methods={mns}")

# ══════════════════════════════════════════════════════════════════════════
# Q2: MainActivity.onCreate — the setContent call and its lambda
# ══════════════════════════════════════════════════════════════════════════
print("\n===== Q2: MainActivity.onCreate bytecode =====")
MA = 'Lio/github/yamin8000/dooz/ui/MainActivity;'
oncreate = methods.get((MA, 'onCreate', '(Landroid/os/Bundle;)V'))
if oncreate:
    for off, op, outp in disasm(oncreate, 400):
        line = f"  {off:04x}: {op} {outp}"
        # annotate the interesting ops only to keep output readable
        if any(k in op for k in ('invoke', 'new-instance', 'iget', 'sput', 'const-string')):
            print(line[:200])
else:
    print("  (MainActivity.onCreate NOT FOUND)")

# ══════════════════════════════════════════════════════════════════════════
# Q3+Q4 and Q5 executed after reading Q1/Q2 output (iterative forensics).
# ══════════════════════════════════════════════════════════════════════════
