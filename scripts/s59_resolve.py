#!/usr/bin/env python3
"""
scripts/s59_resolve.py — resolve DEX ref indices + find setTag/getTag(const-key) sites.

1. Resolve indices appearing in Lxd1;.g (types 346, 3110; methods 6966, 1461, 11968).
2. Scan ALL methods: find every invoke of View.setTag(I, Object) / View.getTag(I)
   and pair each with the nearest const/const/16/const (high-reg or nearby) int in
   the same basic block window (±8 insns) — the R$id key candidates.
3. Dump the enclosing class/method for each setTag site (who sets WHICH key on WHOM).
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"

def load():
    tmp = tempfile.mkdtemp(prefix="s59r_")
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
        def meth(i):
            try:
                m = cm.get_method(i)
                return f"{m.get_class_name()}->{m.get_name()}{m.get_descriptor()}"
            except Exception as e:
                return f"<meth {i}: {e}>"
        def type_of(i):
            try:
                return cm.get_type(i)  # some builds: get_string via tf_map
            except Exception:
                try:
                    return d.get_type(i)
                except Exception as e:
                    return f"<type {i}: {e}>"

        print("== index resolution for Lxd1;.g ==")
        for i in (346, 3110, 6966, 1461, 11968, 1179, 2451, 660):
            print(f"  idx {i}: meth? {meth(i) if i in (6966,1461,11968,1179) else ''}")

        # type resolution for instance-of/check-cast operands
        for i in (346, 3110, 1016, 1565):
            t = None
            try:
                t = cm.get_type(i)
            except Exception:
                try:
                    t = d.get_type(i)
                except Exception:
                    pass
            print(f"  TYPE idx {i}: {t}")

        print("\n== setTag/getTag call-site census (key from nearby const) ==")
        sites = []
        for c in d.get_classes():
            cname = c.get_name()
            for m in c.get_methods():
                code = m.get_code()
                if not code:
                    continue
                insns = list(code.get_bc().get_instructions())
                for j, ins in enumerate(insns):
                    opv = ins.get_op_value()
                    is_call = (0x6e <= opv <= 0x72) or (0x74 <= opv <= 0x78)
                    if not is_call:
                        continue
                    try:
                        tgt = meth(ins.get_ref_index() if hasattr(ins, "get_ref_index") else 0)
                    except Exception:
                        continue
                    if "setTag" not in tgt and "getTag" not in tgt:
                        continue
                    # nearest const within 8 insns before
                    key = None
                    for k in range(j - 1, max(j - 9, -1), -1):
                        pk = insns[k].get_name()
                        if pk.startswith("const"):
                            try:
                                ops = insns[k].get_operands()
                                for o in ops:
                                    if o[0] != 0 and isinstance(o[1], int) and 2000000000 < o[1] < 2200000000:
                                        key = o[1]
                                        break
                            except Exception:
                                pass
                        if key:
                            break
                    sites.append((cname, m.get_name(), tgt.split("->")[-1].split("(")[0], key, tgt))
        print(f"total tag call sites: {len(sites)}")
        # group: setTag sites by (enclosing class, key)
        print("\n-- setTag sites --")
        for s in sites:
            if s[2] == "setTag":
                print(f"  {s[0]}->{s[1]}  key={s[3]}  → {s[4]}")
        print("\n-- getTag sites with key const --")
        for s in sites:
            if s[2] == "getTag" and s[3]:
                print(f"  {s[0]}->{s[1]}  key={s[3]}  → {s[4]}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
