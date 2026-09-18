#!/usr/bin/env python3
"""
scripts/s59_vtlo_forensic.py — R-NEW-379 DEX ground truth (S59, ROADMAP-3-CLOSURE).

Target: the ViewTreeLifecycleOwner ISE face "ViewTreeLifecycleOwner not found
from Lho;@1074" thrown through Log0;.c during dooz v23 Compose init.

Deliverables:
  1. Which class holds the literal "ViewTreeLifecycleOwner not found from"
  2. Full disasm of that class (set/get pair, tag-key usage, walk loop)
  3. The tag-key resource id (R$id.view_tree_lifecycle_owner) constant
  4. Callers of the SET method (who installs the owner on which view)
  5. Callers of the GET/throw method (who demands the owner)
"""
import sys
from androguard.misc import AnalyzeDex

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"
NEEDLE = "ViewTreeLifecycleOwner not found from"

import zipfile, tempfile, os, shutil

def extract_dexes(apk, tmp):
    out = []
    with zipfile.ZipFile(apk) as z:
        for n in z.namelist():
            if n.startswith("classes") and n.endswith(".dex"):
                p = os.path.join(tmp, os.path.basename(n))
                with z.open(n) as f, open(p, "wb") as g:
                    shutil.copyfileobj(f, g)
                out.append(p)
    return out

def main():
    tmp = tempfile.mkdtemp(prefix="s59_vtlo_")
    dexes = extract_dexes(APK, tmp)
    print(f"== {len(dexes)} dex files ==")

    hit_class = None
    holders = []   # (dex, class, method) holding the needle
    for dp in dexes:
        a, d, dx = AnalyzeDex(dp)
        for c in d.get_classes():
            for m in c.get_methods():
                code = m.get_code()
                if not code:
                    continue
                raw = None
                try:
                    raw = code.get_bc()
                except Exception:
                    continue
                for ins in raw.get_instructions():
                    if ins.get_op_value() in (0x1a, 0x1b):  # const-string / jumbo
                        try:
                            sval = ins.get_string()
                        except Exception:
                            continue
                        if NEEDLE in sval:
                            holders.append((os.path.basename(dp), c.get_name(), m.get_name(), m.get_descriptor()))
                            hit_class = c
    print("== classes holding the ISE literal ==")
    for h in holders:
        print("  %s %s->%s%s" % h)

    if not hit_class:
        print("NO LITERAL HOLDER FOUND")
        return 1

    print(f"\n== FULL DISASM {hit_class.get_name()} ==")
    for m in hit_class.get_methods():
        print(f"\n--- {m.get_name()}{m.get_descriptor()} access={hex(m.get_access_flags())}")
        code = m.get_code()
        if not code:
            print("  (abstract/native)")
            continue
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            out = f"  {op}"
            if ins.get_op_value() in (0x1a, 0x1b):
                out += f" {ins.get_string()!r}"
            else:
                operands = []
                try:
                    for i in range(ins.get_length() // 2 - 1):
                        operands.append("%04x" % ins.get_operands()[i + 1][1] if i + 1 < len(ins.get_operands()) else "")
                except Exception:
                    pass
                try:
                    ops = ins.get_operands()
                    out += " " + ", ".join(f"{o[0]}:{o[1]}" for o in ops[1:]) if len(ops) > 1 else ""
                except Exception:
                    pass
            print(out)

    # Find the tag-key id usage: get_resources / R$id field in this class
    print("\n== sget/sput const refs in class ==")
    for f in hit_class.get_fields():
        print(f"  FIELD {f.get_name()} {f.get_descriptor()}")

    tmp and shutil.rmtree(tmp, ignore_errors=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
