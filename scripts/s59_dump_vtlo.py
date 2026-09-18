#!/usr/bin/env python3
"""
scripts/s59_dump_vtlo.py — resolved disasm of the R-NEW-379 ViewTreeLifecycleOwner chain.

Dumps with FULL ref resolution:
  1. The class holding "ViewTreeLifecycleOwner not found from" (get/throw side)
  2. Its superclass chain (so we know what Lr; actually is)
  3. All CALLERS of the owner-tag get/set methods (XREF both directions)
  4. The view-tree owner family: every method containing the string
     "view_tree_lifecycle_owner" or tag-key getTag/setTag patterns around it
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"

def load_dex():
    tmp = tempfile.mkdtemp(prefix="s59_")
    with zipfile.ZipFile(APK) as z:
        names = [n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex")]
        ps = []
        for n in names:
            p = os.path.join(tmp, os.path.basename(n))
            with z.open(n) as f, open(p, "wb") as g:
                shutil.copyfileobj(f, g)
            ps.append(p)
    return ps

def fmt_insn(ins, d):
    try:
        ops = ins.get_operands()
    except Exception:
        ops = []
    parts = []
    for o in ops:
        kind, val = o[0], o[1]
        # resolve refs when androguard gives index triples
        if kind == 0:  # register
            parts.append(f"v{val}")
        elif isinstance(val, tuple) and len(val) >= 2:
            parts.append(str(val))
        else:
            parts.append(str(val))
    try:
        # androguard: use the format's string/type/method resolution helpers
        if ins.get_op_value() in (0x1a, 0x1b):
            return f"{ins.get_name()} {parts[0] if parts else ''}, {ins.get_string()!r}"
    except Exception:
        pass
    return f"{ins.get_name()} {', '.join(parts)}"

def disasm_method(m, d):
    out = []
    name = f"{m.get_name()}{m.get_descriptor()}"
    out.append(f"--- {name} access={hex(m.get_access_flags())}")
    code = m.get_code()
    if not code:
        out.append("  (abstract/native)")
        return out
    pc = 0
    for ins in code.get_bc().get_instructions():
        line = f"  @{pc:#06x} {fmt_insn(ins, d)}"
        # annotate invokes with resolved target
        opv = ins.get_op_value()
        if 0x6e <= opv <= 0x72 or 0x74 <= opv <= 0x78 or opv in (0x60, 0x61, 0x62, 0x63, 0x64, 0x65):
            try:
                idx = ins.get_ref_index()
                if 0x6e <= opv <= 0x72 or 0x74 <= opv <= 0x78:
                    ref = d.get_method_ref(idx)
                    cls = d.get_string(ref.get_class_name())
                    proto = d.get_string(ref.get_proto())
                    mname = d.get_string(ref.get_method_name())
                    line += f"   // {cls}->{"\n" if False else ''}{mname}{proto}"
                else:
                    ref = d.get_field_ref(idx)
                    cls = d.get_string(ref.get_class_name())
                    fname = d.get_string(ref.get_field_name())
                    ftype = d.get_string(ref.get_descriptor())
                    line += f"   // {cls}.{fname}:{ftype}"
            except Exception as e:
                line += f"   // <resolve-fail {e}>"
        out.append(line)
        pc += ins.get_length()
    return out

def main():
    dexps = load_dex()
    print(f"== {len(dexps)} dex ==")
    d = None
    for p in dexps:
        dd = DalvikVMFormat(open(p, "rb").read())
        # find the literal holder class
        for c in dd.get_classes():
            for m in c.get_methods():
                code = m.get_code()
                if not code:
                    continue
                for ins in code.get_bc().get_instructions():
                    if ins.get_op_value() in (0x1a, 0x1b):
                        try:
                            if "ViewTreeLifecycleOwner not found from" in ins.get_string():
                                d = dd
                                target = c
                                print(f"\n=== HOLDER: {c.get_name()} super={c.get_superclassname()}")
                                for f in c.get_fields():
                                    print(f"  FIELD {f.get_name()}:{f.get_descriptor()}")
                                for mm in c.get_methods():
                                    for line in disasm_method(mm, d):
                                        print(line)
                                # XREF: who calls the public methods of this class
                                pub = [mm.get_name() for mm in c.get_methods()
                                       if (mm.get_access_flags() & 0x1) and mm.get_code()]
                                print(f"\n=== XREF callers of {c.get_name()} public methods {pub}:")
                                for cc in d.get_classes():
                                    for mm in cc.get_methods():
                                        code2 = mm.get_code()
                                        if not code2:
                                            continue
                                        for ins in code2.get_bc().get_instructions():
                                            opv = ins.get_op_value()
                                            if (0x6e <= opv <= 0x72) or (0x74 <= opv <= 0x78):
                                                try:
                                                    ref = d.get_method_ref(ins.get_ref_index())
                                                    rc = d.get_string(ref.get_class_name())
                                                    rn = d.get_string(ref.get_method_name())
                                                    if rc == c.get_name() and rn in pub:
                                                        print(f"  CALLER {cc.get_name()}->" 
                                                              f"{mm.get_name()} calls {rc}.{rn}")
                                                except Exception:
                                                    pass
                                return 0
                        except Exception:
                            pass
    print("HOLDER NOT FOUND")
    return 1

if __name__ == "__main__":
    sys.exit(main())
