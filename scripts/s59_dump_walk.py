#!/usr/bin/env python3
"""
scripts/s59_dump_walk.py — R-NEW-379 walk ground truth: Lrd1;.v, Lxd1;.g, Log0;.c,
plus the setTag/getTag sites and the R$id constants they load.

Androguard operand resolution: pass the DalvikVMFormat to get_operands(d) so
method/field/string refs come out resolved.
"""
import sys, os, zipfile, tempfile, shutil
from androguard.core.bytecodes.dvm import DalvikVMFormat

APK = "/home/z/my-project/apk_cache/io.github.yamin8000.dooz_23.apk"
TARGETS = {"Lrd1;", "Lxd1;", "Log0;"}

def load():
    tmp = tempfile.mkdtemp(prefix="s59w_")
    with zipfile.ZipFile(APK) as z:
        ps = []
        for n in z.namelist():
            if n.startswith("classes") and n.endswith(".dex"):
                p = os.path.join(tmp, os.path.basename(n))
                with z.open(n) as f, open(p, "wb") as g:
                    shutil.copyfileobj(f, g)
                ps.append(p)
    return ps

def ops_str(ins, d):
    try:
        ops = ins.get_operands(d)
    except Exception:
        ops = ins.get_operands()
    parts = []
    for o in ops:
        parts.append(str(o[1]) if o[0] == 0 else f"{o[1]}")
    return ", ".join(parts)

def disasm(m, d, show_pc=True):
    out = [f"--- {m.get_name()}{m.get_descriptor()} access={hex(m.get_access_flags())}"]
    code = m.get_code()
    if not code:
        out.append("  (abstract/native)")
        return out
    pc = 0
    for ins in code.get_bc().get_instructions():
        line = f"  @{pc:#06x} {ins.get_name()} {ops_str(ins, d)}"
        opv = ins.get_op_value()
        if 0x6e <= opv <= 0x72 or 0x74 <= opv <= 0x78:
            try:
                ops = ins.get_operands(d)
                # last operand of invoke is the resolved method ref string
                line += f"   // CALL {ops[-1][1]}"
            except Exception:
                pass
        elif 0x60 <= opv <= 0x65:
            try:
                ops = ins.get_operands(d)
                line += f"   // FIELD {ops[-1][1]}"
            except Exception:
                pass
        out.append(line)
        pc += ins.get_length()
    return out

def main():
    for p in load():
        d = DalvikVMFormat(open(p, "rb").read())
        classes = {c.get_name(): c for c in d.get_classes()}
        for t in sorted(TARGETS):
            if t not in classes:
                continue
            c = classes[t]
            print(f"\n======== {t} super={c.get_superclassname()} ========")
            for m in c.get_methods():
                for line in disasm(m, d):
                    print(line)
        # find R$id-like class: any class with int fields valued 2131230802/2131230840
        for c in d.get_classes():
            sc = c.get_superclassname() or ""
            if "R$id" in c.get_name() or c.get_name().endswith("$id;") or c.get_name().endswith("/R$id;"):
                vals = {}
                for f in c.get_fields():
                    try:
                        ev = f.get_init_value()
                        if ev is not None:
                            v = ev.get_value()
                            if isinstance(v, int) and 2131230000 < v < 2131240000:
                                vals[f.get_name()] = v
                    except Exception:
                        pass
                if vals:
                    print(f"\n======== R$id candidates {c.get_name()} ({len(vals)} ids) ========")
                    for k, v in sorted(vals.items(), key=lambda kv: kv[1]):
                        print(f"  {k} = {v} (0x{v:08x})")
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
