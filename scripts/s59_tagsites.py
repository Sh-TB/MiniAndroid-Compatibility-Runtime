#!/usr/bin/env python3
"""
scripts/s59_tagsites.py — find View.setTag(I,Object)/getTag(I) call sites and
the nearby R$id const, using operand-value ref indices (androguard 3.3.5).

Also: runtime-class probe — what heap class does view 20 carry? (engine side)
"""
import sys, os, zipfile, tempfile, shutil
from collections import defaultdict
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"

def load():
    tmp = tempfile.mkdtemp(prefix="s59t_")
    with zipfile.ZipFile(APK) as z:
        ps = []
        for n in z.namelist():
            if n.startswith("classes") and n.endswith(".dex"):
                p = os.path.join(tmp, os.path.basename(n))
                with z.open(n) as f, open(p, "wb") as g:
                    shutil.copyfileobj(f, g)
                ps.append(p)
    return ps

def main():
    for p in load():
        d = DalvikVMFormat(open(p, "rb").read())
        cm = d.get_class_manager()

        def meth_ref(idx):
            try:
                m = cm.get_method(idx)
                if isinstance(m, list):
                    m = m[0]
                cn = m.get_class_name() if hasattr(m, "get_class_name") else str(m)
                nm = m.get_name() if hasattr(m, "get_name") else "?"
                return f"{cn}->{nm}"
            except Exception:
                return None

        sites = []
        for c in d.get_classes():
            for m in c.get_methods():
                code = m.get_code()
                if not code:
                    continue
                insns = list(code.get_bc().get_instructions())
                for j, ins in enumerate(insns):
                    opv = ins.get_op_value()
                    if not ((0x6e <= opv <= 0x72) or (0x74 <= opv <= 0x78)):
                        continue
                    tgt = None
                    try:
                        ops = ins.get_operands()
                        if len(ops) and len(ops[-1]) >= 3:
                            tgt = str(ops[-1][2])          # resolved ref
                        elif len(ops):
                            tgt = meth_ref(ops[-1][1])
                    except Exception:
                        pass
                    if not tgt or "setTag" not in tgt and "getTag" not in tgt:
                        continue
                    kind = "setTag" if "setTag" in tgt else "getTag"
                    # nearest R-id const BEFORE within 10 insns
                    key = None
                    for k in range(j - 1, max(j - 11, -1), -1):
                        if insns[k].get_name().startswith("const"):
                            try:
                                for o in insns[k].get_operands():
                                    if o[0] != 0 and isinstance(o[1], int) and \
                                       2000000000 < o[1] < 2200000000:
                                        key = o[1]
                                        break
                            except Exception:
                                pass
                        if key:
                            break
                    sites.append((kind, key, f"{c.get_name()}->{m.get_name()}", tgt))
        print(f"== {len(sites)} tag sites ==")
        by = defaultdict(list)
        for kind, key, src, tgt in sites:
            by[(kind, key)].append(src)
        for (kind, key), srcs in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
            print(f"\n[{kind} key={key}] ({len(srcs)} sites)")
            for s in sorted(set(srcs))[:8]:
                print(f"   {s}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
