#!/usr/bin/env python3
# ============================================================================
# S43 — R-NEW-348 Attack: invokeComposable → content-lambda dispatch ground truth
# ----------------------------------------------------------------------------
# Purpose (Source-First law, user golden rule):
#   compose-runtime 1.11.4 executes the app content lambda via ONE call:
#       internal actual fun invokeComposable(composer, composable) {
#           val realFn = composable as Function2<Composer, Int, Unit>   // checkcast
#           realFn(composer, 1)                                        // invoke-interface
#       }
#   (upstream/s43/runtime/jvmAndAndroidMain/.../Expect.jvmAndAndroid.kt:24)
#
#   The engine's execute_invoke_interface silently STUBS any interface call
#   whose target it cannot resolve (returns true + void/null + STUBBED trace).
#   A silent miss on realFn(composer, 1) produces EXACTLY the observed
#   R-NEW-348 state: composer ops ran, zero app composables, zero exceptions.
#
# Questions this probe answers from the dooz23 DEX (ground truth, no guessing):
#   Q1: Does Lkotlin/jvm/functions/Function2; exist unrenamed in the DEX?
#       (If R8 renamed it, the interface name is NOT the contract — the
#        descriptor + receiver's implements-closure are.)
#   Q2: Which class is the obfuscated invokeComposable? Signature pattern:
#       checkcast <Function2-like interface>; invoke-interface {composer, 1}
#       immediately after; usually static, descriptor (Lxk0;-composer,
#       Function2)void.
#   Q3: What interface does the MainActivity content lambda implement, and
#       what is its invoke method named? (This is what realFn(composer,1)
#       must dispatch to through the engine.)
#   Q4: The dispatch-chain audit: for the invokeComposable interface call,
#       which engine law answers: runtime-class first (F-068) → declared
#       interface → descriptor walk (F-091b gated for host interfaces)?
# Output: structured text dump for manual root-cause chaining.
# ============================================================================
import zipfile
import logging
# ── silence androguard's chatty loggers (previous sessions' standard) ──────
logging.disable(logging.CRITICAL)
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass
from androguard.core.dex import DEX

# ── the hash-verified dooz23 APK (ledger row 22, sha256 299eab21…) ─────────
APK = '/home/z/my-project/corpus_cache/io.github.yamin8000.dooz_23.apk'

z = zipfile.ZipFile(APK)                        # APK = ZIP container
dex_names = [n for n in z.namelist() if n.endswith('.dex')]
print(f"[i] DEX files: {dex_names}")

# ── build the class/method index across ALL dex files ─────────────────────
classes = {}     # name -> (dex_name, ClassDefItem)
methods = {}     # (class, name, desc) -> EncodedMethod
for dn in dex_names:
    d = DEX(z.read(dn))
    for c in d.get_classes():
        name = c.get_name()
        if name not in classes:
            classes[name] = (dn, c)
        for m in c.get_methods():
            methods[(name, m.get_name(), m.get_descriptor())] = m

print(f"[i] classes={len(classes)} methods={len(methods)}")

# ══════════════════════════════════════════════════════════════════════════
# Q1: Function2 presence — exact name AND any interface with an
#     invoke(Composer,Int)-shaped method (renamed Function2 candidates).
# ══════════════════════════════════════════════════════════════════════════
print("\n===== Q1: kotlin.jvm.functions.Function2 in DEX =====")
fn2_exact = 'Lkotlin/jvm/functions/Function2;'
print(f"  exact '{fn2_exact}' present: {fn2_exact in classes}")

# interfaces declaring (Ljava/lang/Object;I)Ljava/lang/Object; — the
# renamed-shape of Function2<Composer,Int,Unit>.invoke(composer, 1)
import re
cand = []
for (cn, mn, md) in methods:
    # renamed Function2.invoke: (Ljava/lang/Object;I)Ljava/lang/Object;
    if md == '(Ljava/lang/Object;I)Ljava/lang/Object;':
        cand.append((cn, mn, md))
print(f"  methods with (Object,I)Object shape: {len(cand)}")
for cn, mn, md in sorted(cand)[:24]:
    print(f"    {cn}->{mn} {md}")

# ══════════════════════════════════════════════════════════════════════════
# Q2: find invokeComposable — a method whose bytecode contains a checkcast
#     followed closely by an invoke-interface with 2 args on that cast
#     result. Dump every candidate's full bytecode for manual reading.
# ══════════════════════════════════════════════════════════════════════════
print("\n===== Q2: invokeComposable candidates (checkcast + 2-arg invoke-interface) =====")

def disasm(m, maxn=200):
    """Return list of (pc, opname, operands) for a method (bounded)."""
    out = []
    code = m.get_code()
    if code is None:
        return out
    idx = 0
    n = 0
    for ins in code.get_bc().get_instructions():
        if n >= maxn:
            break
        try:
            op = ins.get_name()
            length = ins.get_length()
            out.append((idx, op, ins.get_output()))
        except Exception:
            length = 2
            out.append((idx, "?", ""))
        idx += length
        n += 1
    return out

hits = []
for (cn, mn, md), m in methods.items():
    code = m.get_code()
    if code is None:
        continue
    ops = [i.get_name() for i in code.get_bc().get_instructions()]
    # pattern: a checkcast anywhere followed within 6 ops by invoke-interface
    for k, op in enumerate(ops):
        if op == 'checkcast':
            window = ops[k:k + 7]
            if 'invoke-interface' in window or 'invoke-interface/range' in window:
                hits.append((cn, mn, md, k))
                break

print(f"  candidates: {len(hits)}")
for cn, mn, md, k in hits[:10]:
    print(f"    {cn}->{mn} {md}  (checkcast@op#{k})")

# ══════════════════════════════════════════════════════════════════════════
# Q3: MainActivity content lambda — find MainActivity (manifest class from
#     ledger: io.github.yamin8000.dooz.ui.MainActivity — obfuscated? The
#     manifest class name is UNOBFUSCATED because it's referenced from the
#     manifest). Dump its onCreate bytecode to see the setContent call and
#     the lambda class being instantiated (new-instance of a *$Lambda* or
#     obfuscated class).
# ══════════════════════════════════════════════════════════════════════════
print("\n===== Q3: MainActivity.onCreate setContent lambda =====")
main_candidates = [c for c in classes if 'MainActivity' in c]
for mc in main_candidates[:4]:
    print(f"  found class: {mc}  (dex {classes[mc][0]})")
