#!/usr/bin/env python3.13
# cont33_disasm.py — CONT-33 Checkpoint B: decode the STR-BRIDGE SIOOBE face.
# Targets: Lwv;.p (thrower, pc=26 substring on length=0), its callers,
# the empty String.format producer, and the DEX format-string census.
import sys
from androguard.misc import AnalyzeDex

APK_DEX = sys.argv[1] if len(sys.argv) > 1 else None
if not APK_DEX:
    print("usage: cont33_disasm.py <classes.dex>")
    sys.exit(1)

a, d, dx = AnalyzeDex(APK_DEX)

# 1) census: time-format literals
print("=== STRING CENSUS (format-like) ===")
for s in d.get_strings():
    if ("%0" in s and len(s) < 40) or s in ("", "."):
        print(repr(s))

# 2) Lwv; full decode
print("\n=== CLASS Lwv; ===")
for cls in d.get_classes():
    if cls.get_name() == "Lwv;":
        print(f"super={cls.get_superclassname()}")
        for m in cls.get_methods():
            code = m.get_code()
            print(f"\n--- METHOD Lwv;.{m.get_name()}{m.get_descriptor()} regs={code.get_registers_size() if code else '?'} ins={code.get_ins_size() if code else '?'} ---")
            if code:
                for i, inst in enumerate(m.get_instructions()):
                    print(f"  {i:4d} {inst.get_name():28s} {inst.get_output()}")
                    if i > 120: print("   ... (truncated)"); break

# 3) who calls Lwv;.p ?
print("\n=== CALLERS OF Lwv;.p ===")
for meth in dx.get_methods():
    if meth.is_external(): continue
    mm = meth.get_method()
    if mm.get_class_name() == "Lwv;" and mm.get_name() == "p":
        for _, call, _ in meth.get_xref_to():
            pass
        for ref in meth.get_xref_from():
            cm = ref[0] if isinstance(ref, tuple) else ref
            try:
                print("called from:", cm.get_class_name(), cm.get_name())
            except Exception:
                print("called from:", repr(ref)[:120])
