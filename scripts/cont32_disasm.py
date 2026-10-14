#!/usr/bin/env python3.13
# cont32_disasm.py — CONT-32 Checkpoint C: decode the "Dialog has no window" face.
# Targets: Lea;.r (thrower), Lis;.<init> (ctor chain), Lx30;.n (catch-all site),
# plus the DEX string census for the message and window-related calls.
import sys
from androguard.misc import AnalyzeDex

APK_DEX = sys.argv[1] if len(sys.argv) > 1 else None
if not APK_DEX:
    print("usage: cont32_disasm.py <classes.dex>")
    sys.exit(1)

a, d, dx = AnalyzeDex(APK_DEX)

# 1) string census
print("=== STRING CENSUS (window/dialog) ===")
for s in d.get_strings():
    if "no window" in s.lower() or ("dialog" in s.lower() and "window" in s.lower()):
        print(repr(s[:120]))

# 2) target classes
TARGETS = ["Lea;", "Lis;", "Lx30;", "Lel;", "Lpj;", "Lfs;"]
for cls in d.get_classes():
    name = cls.get_name()
    if name in TARGETS:
        print(f"\n=== CLASS {name}  (super={cls.get_superclassname()}) ===")
        for m in cls.get_methods():
            if m.get_name() in ("r", "<init>", "n", "j") or (name == "Lel;" and m.get_name() == "j"):
                print(f"\n--- METHOD {name}{m.get_name()}{m.get_descriptor()}  regs={m.get_code().get_registers_size() if m.get_code() else '?'} ---")
                if m.get_code():
                    for i, inst in enumerate(m.get_instructions()):
                        print(f"  {i:4d} {inst.get_name():30s} {inst.get_output()}")
                        if i > 220: print("   ... (truncated)"); break
