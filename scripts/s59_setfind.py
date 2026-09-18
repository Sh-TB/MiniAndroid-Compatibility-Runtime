#!/usr/bin/env python3
"""
scripts/s59_setfind.py — find who sets view_tree_lifecycle_owner (2131230840).

1. Find the app R$id holder class: static int fields valued 2131230840.
2. Find every method loading that const OR sget'ing that field within 12 insns
   before an invoke of setTag (or getTag) — the COMPLETE set/get census for this key.
3. Dump each hit's enclosing method body window.
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"
KEY = 2131230840

def load():
    tmp = tempfile.mkdtemp(prefix="s59sf_")
    with zipfile.ZipFile(APK) as z:
        ps = []
        for n in z.namelist():
            if n.startswith("classes") and n.endswith(".dex"):
                p = os.path.join(tmp, os.path.basename(n))
                with z.open(n) as f, open(p, "wb") as g:
                    shutil.copyfileobj(f, g)
                ps.append(p)
    return ps

def ops_str(ins):
    parts = []
    for o in ins.get_operands():
        parts.append(f"v{o[1]}" if o[0] == 0 else str(o[2] if len(o) >= 3 else o[1]))
    return ", ".join(parts)

def main():
    for p in load():
        d = DalvikVMFormat(open(p, "rb").read())
        classes = {c.get_name(): c for c in d.get_classes()}

        # 1. R$id holder: static fields with init value KEY
        holders = []
        for c in d.get_classes():
            for f in c.get_fields():
                try:
                    ev = f.get_init_value()
                    if ev is not None and ev.get_value() == KEY:
                        holders.append((c.get_name(), f.get_name()))
                except Exception:
                    pass
        print(f"== R$id holder fields valued {KEY}: {holders}")

        # 2. census: const KEY or sget of holder field within 12 insns before set/getTag
        holder_specs = {f"{c}->{n}" for c, n in holders}
        for c in d.get_classes():
            for m in c.get_methods():
                code = m.get_code()
                if not code:
                    continue
                insns = list(code.get_bc().get_instructions())
                for j, ins in enumerate(insns):
                    nm = ins.get_name()
                    if "setTag" not in nm and "getTag" not in nm:
                        # invoke check via resolved op
                        if not (nm.startswith("invoke") and "Tag" in ops_str(ins)):
                            continue
                    # window before
                    hit_kind = None
                    for k in range(j - 1, max(j - 13, -1), -1):
                        kn = insns[k].get_name()
                        s = ops_str(insns[k])
                        if kn.startswith("const") and str(KEY) in s:
                            hit_kind = "const"
                            break
                        if kn.startswith("sget") and any(f"{c}->{n}" in s for c, n in holders):
                            hit_kind = "sget"
                            break
                    if not hit_kind:
                        continue
                    print(f"\n== {hit_kind} HIT: {c.get_name()}->{m.get_name()}{m.get_descriptor()} @{j}")
                    lo = max(0, j - 14)
                    pc = 0
                    pcs = []
                    for ii in insns:
                        pcs.append(pc)
                        pc += ii.get_length()
                    for k in range(lo, min(j + 4, len(insns))):
                        print(f"  @{pcs[k]:#06x} {insns[k].get_name()} {ops_str(insns[k])}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
