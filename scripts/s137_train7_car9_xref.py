#!/usr/bin/env python3
"""s137_train7_car9_xref.py — static cross-reference of ALL invoke sites
targeting Lkr1;.a (pointerInput(key, PointerInputEventHandler)) across every
dex of dooz v23, PLUS the Lpv; <clinit> singleton law and any sibling
pointerInput overloads (same param shape). Answers car-10 question:
WHO constructs real (non-no-op) pointerInput elements, and which factory
never issues its call?
"""
import sys, zipfile, re
try:
    from androguard.core.dex import DEX
except ImportError:
    from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

APK = '/home/z/my-project/upload/canonical_apks/dooz_23_toplevel.apK'.replace('apK', 'apk')

_dexs = None
def dexs():
    global _dexs
    if _dexs is None:
        _dexs = []
        with zipfile.ZipFile(APK) as z:
            for n in sorted(x for x in z.namelist() if re.match(r'classes\d*\.dex$', x)):
                _dexs.append((n, DEX(z.read(n))))
    return _dexs

def xref(target_class, target_meth, target_sig=None):
    """Match on the formatted operand text (androguard prints
    'Lcls;->meth(desc)ret' as the last operand); spaces stripped on both
    sides — avoids get_method(idx) API divergence across versions."""
    want = (target_class + "->" + target_meth + "(").replace(" ", "")
    want_sig = (target_sig or "").replace(" ", "")
    hits = []
    for dn, d in dexs():
        for c in d.get_classes():
            cname = c.get_name()
            for m in c.get_methods():
                code = m.get_code()
                if not code:
                    continue
                for ins in code.get_bc().get_instructions():
                    nm = ins.get_name()
                    if not nm.startswith('invoke'):
                        continue
                    try:
                        ops = ins.get_operands()
                        ref = None
                        for o in ops:
                            if o[0] >= 0x100 and len(o) >= 3 and \
                                    isinstance(o[2], str) and '->' in o[2]:
                                ref = str(o[2])
                        if not ref:
                            continue
                        flat = ref.replace(" ", "")
                        if not flat.startswith(want):
                            continue
                        if target_sig is not None:
                            # flat = 'Lcls;->meth(desc)ret' — split at ')'
                            if flat != (target_class + "->" + target_meth +
                                        target_sig).replace(" ", ""):
                                continue
                        hits.append((dn, cname, m.get_name(),
                                     m.get_descriptor(), nm))
                    except Exception:
                        continue
    return hits

def disasm_method(cls, meth, max_ins=300):
    for dn, d in dexs():
        for c in d.get_classes():
            if c.get_name() != cls:
                continue
            for m in c.get_methods():
                if m.get_name() != meth:
                    continue
                code = m.get_code()
                if not code:
                    print(f"== {cls}.{meth} abstract/native")
                    return
                print(f"== {cls}.{meth} {m.get_descriptor()} len={code.get_length()}")
                pc = 0
                for ins in code.get_bc().get_instructions():
                    op = ins.get_name()
                    out = f"  {pc:04x}: {op}"
                    pc += ins.get_length()
                    try:
                        parts = []
                        for o in ins.get_operands():
                            if o[0] >= 0x100:
                                parts.append(str(o[2]))
                            else:
                                parts.append(f"v{o[1]}")
                        out += " " + ", ".join(parts)
                    except Exception as e:
                        out += f" <err>"
                    print(out)
                return

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'xref'
    if mode == 'xref':
        print("=== ALL callers of Lkr1;.a (Lxt0; Object PointerInputEventHandler)Lxt0;")
        for h in xref('Lkr1;', 'a',
                      '(Lxt0;Ljava/lang/Object;Landroidx/compose/ui/input/pointer/PointerInputEventHandler;)Lxt0;'):
            print(f"   dex={h[0]} {h[1]}.{h[2]} {h[3]}  [{h[4]}]")
        print("=== ALL callers of Ljr1;.<init> (Object Object PointerInputEventHandler I)V")
        for h in xref('Ljr1;', '<init>',
                      '(Ljava/lang/Object;Ljava/lang/Object;Landroidx/compose/ui/input/pointer/PointerInputEventHandler;I)V'):
            print(f"   dex={h[0]} {h[1]}.{h[2]} {h[3]}  [{h[4]}]")
        print("=== ALL callers of Lpv; methods (no-op usage map)")
        for h in xref('Lpv;', 'a'):
            print(f"   dex={h[0]} {h[1]}.{h[2]} {h[3]}  [{h[4]}]")
    elif mode == 'kr1a':
        disasm_method('Lkr1;', 'a')
    elif mode == 'pmc':
        # dump Lpm;.c fully to tmp file, then print the region around the
        # Ljr1;.<init> construction site (the REAL clickable pointerInput)
        import io
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        disasm_method('Lpm;', 'c', 100000)
        sys.stdout = old
        lines = buf.getvalue().splitlines()
        with open('/home/z/my-project/tmp/pm_c_disasm.txt', 'w') as f:
            f.write('\n'.join(lines))
        idxs = [i for i, l in enumerate(lines) if 'Ljr1;-><init>' in l]
        print(f"total lines={len(lines)} Ljr1; ctor sites={idxs}")
        for i in idxs:
            lo = max(0, i - 55)
            print(f"===== context before {i} =====")
            for l in lines[lo:i + 6]:
                print(l)
    elif mode == 'jr1':
        disasm_method('Ljr1;', '<init>')
        disasm_method('Ljr1;', 'f')
