#!/usr/bin/env python3
"""cont70 ANT-1 decode — why does the in-frame catch(Exception) at
CoordinatorLayout.getResolvedLayoutParams pc=67 miss the F106
NoSuchMethodException? Print the method's try/catch ranges + pc context.

H1 (primary): is_exception_subtype lacks NoSuchMethodException ->
    ReflectiveOperationException -> Exception, so a typed
    catch(Ljava/lang/Exception;) fails the walk.
H2 (alternative): no covering try at the throw pc.
"""
import zipfile
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk"

CLS = "Landroidx/coordinatorlayout/widget/CoordinatorLayout;"
METH = "getResolvedLayoutParams"

z = zipfile.ZipFile(APK)
dexes = []
for n in sorted(z.namelist()):
    if n.startswith("classes") and n.endswith(".dex"):
        dexes.append(DEX(z.read(n)))

found = False
for d in dexes:
    for c in list(d.get_classes()):
        if c.get_name() != CLS:
            continue
        for m in list(c.get_methods()):
            if m.get_name() != METH:
                continue
            found = True
            code = m.get_code()
            if code is None:
                print("abstract/native method")
                break
            print(f"class {CLS} method {meth_name() if False else m.get_name()}"
                  f" regs={code.registers_size} ins={code.insns_size} words")
            bc = m.get_instructions()
            pc = 0
            around = []
            for ins in bc:
                op = ins.get_name()
                length = ins.get_length()
                if 55 <= pc <= 85:
                    around.append((pc, op, ins.get_output()))
                pc += length
            print(f"total bytecode words = {pc}")
            print("--- pcs 55..85 (throw site is pc=67) ---")
            for p, op, out in around:
                mark = "  <<<< THROW SITE" if p == 67 else ""
                print(f"  pc={p:3d} {op:22s} {out}{mark}")
            # try/catch items
            tries = code.tries
            print(f"--- tries ({len(tries)}) ---")
            for t in tries:
                start = t.start_addr
                end = start + t.insn_count
                handlers = t.handler
                if handlers is None:
                    print(f"  try [{start:#x}..{end:#x}) catch-all @ {t.handler_off}")
                    continue
                ch = handlers
                print(f"  try [{start:#x}..{end:#x}) covers_pc67={start <= 67 < end}")
                if hasattr(ch, "handlers") and ch.handlers:
                    for h in ch.handlers:
                        print(f"     typed catch {h.exception_type_descriptor} -> @{h.handler_offset_addr}"
                              f" covers_pc67={start <= 67 < end}")
                if ch.catch_all_addr is not None:
                    print(f"     catch-all -> @{ch.catch_all_addr}")
            break
        if found:
            break
    if found:
        break
if not found:
    print("method not found")
