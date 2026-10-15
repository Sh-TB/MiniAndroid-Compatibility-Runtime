#!/usr/bin/env python3
"""cont69 — disassemble the memory cold-path methods (F-NEW-369 decode).

The cold first-launch NPE chain:
  MemoGameDefaultImages.getResIDs (LinkedList.<init> REC-MISS x2)
  -> ResIdAdapter.getResourceName (List.iterator REC-MISS -> hasNext NPE)
Prints the exact bytecode so the law comes from the LIVE APP DEX.
(androguard 4.x API: androguard.core.dex.DEX; containers need list().)
"""
import zipfile
from androguard.core.dex import DEX

APK = "/home/z/my-project/upload/canonical_apks/org.secuso.privacyfriendlymemory_100.apk"

JOBS = [
    ("Lorg/secuso/privacyfriendlymemory/model/MemoGameDefaultImages;", "getResIDs"),
    ("Lorg/secuso/privacyfriendlymemory/model/MemoGameDefaultImages;", "<clinit>"),
    ("Lorg/secuso/privacyfriendlymemory/model/MemoGameDifficulty;", "<clinit>"),
    ("Lorg/secuso/privacyfriendlymemory/common/ResIdAdapter;", "getResourceName"),
]

z = zipfile.ZipFile(APK)
dexes = []
for n in sorted(z.namelist()):
    if n.startswith("classes") and n.endswith(".dex"):
        dexes.append(DEX(z.read(n)))

for cls, meth in JOBS:
    print(f"\n===== {cls} . {meth} =====")
    found = False
    for d in dexes:
        for c in list(d.get_classes()):
            if c.get_name() != cls:
                continue
            for m in list(c.get_methods()):
                if m.get_name() != meth:
                    continue
                found = True
                code = m.get_code()
                if code is None:
                    print(f"-- {m.get_descriptor()} (no code)")
                    continue
                print(f"-- descriptor {m.get_descriptor()} regs={code.registers_size}")
                for ins in m.get_instructions():
                    op = ins.get_name()
                    out = str(ins.get_output())
                    if any(k in op for k in ("invoke", "new-instance", "iget", "sget",
                                             "move-result", "return", "check-cast",
                                             "const", "if-", "goto", "aget", "throw")):
                        print(f"  {ins.get_offset():04x}: {op:22s} {out[:110]}")
    if not found:
        print("  NOT FOUND")
