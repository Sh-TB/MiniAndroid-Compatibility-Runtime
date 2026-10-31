#!/usr/bin/env python3
"""cont11_train7_disasm.py — TRAIN-7: decode a dooz method with FULL name resolution.
Combines cont11_decode's complete-width table with cont9_dexdump's method/field
resolvers. The dispatch->hit-test chain law (compose 1.6.7 pinned sources) is the
reference; the bytecode is matched against it call-site by call-site.
Usage: cont11_train7_disasm.py <apk> <Lcls;> <method> [max_pc]
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    'cd', '/home/z/my-project/scripts/cont9_dexdump.py')
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)

spec2 = importlib.util.spec_from_file_location(
    'c11', '/home/z/my-project/scripts/cont11_decode.py')
# cont11_decode runs main() only under __main__; import tables via exec of source
import types
src = open('/home/z/my-project/scripts/cont11_decode.py').read()
mod = types.ModuleType('c11')
exec(compile(src.split('def main()')[0], 'cont11_tables', 'exec'), mod.__dict__)
W, NAMES = mod.W, mod.NAMES


def resolve_m(d, idx):
    try:
        cls, name, proto = d.method_ref(idx)
        return f'{cls}->{name}{proto}'
    except Exception as e:
        return f'method@{idx:#x} (?)'


def resolve_f(d, idx):
    try:
        cls, name, ftype = d.field_ref(idx)
        return f'{cls}.{name}:{ftype}'
    except Exception as e:
        return f'field@{idx:#x} (?)'


def decode_method(apk, cls, meth, max_pc=100000):
    z = zipfile.ZipFile(apk)
    out = []
    for name in z.namelist():
        if not (name.startswith('classes') and name.endswith('.dex')):
            continue
        d = cd.Dex(z.read(name))
        for i in range(d.class_defs_size):
            off = d.class_defs_off + i * 32
            if d.type_str(d.u(off, 4)) != cls:
                continue
            info = d.class_methods(off)
            for kind in ('direct', 'virtual'):
                for mname, mdesc, acc, sz, code in info[kind]:
                    if mname != meth or not code:
                        continue
                    insns_size = d.u(code + 12, 4)
                    base = code + 16
                    words = [d.u(base + 2 * w, 2) for w in range(insns_size)]
                    out.append(f'{cls}.{meth}{mdesc} dex={name} insns={insns_size}')
                    w = 0
                    while w < insns_size and w <= max_pc:
                        wd = words[w]
                        op = wd & 0xff
                        u, f = W.get(op, (1, '?UNKNOWN'))
                        ws = ' '.join(f'{words[w + k]:04x}' for k in range(min(u, 4, insns_size - w)))
                        nm = NAMES.get(op, f'op{op:#04x}')
                        line = f'  pc={w:3d} {nm:22s} {ws}'
                        # resolve references
                        if f == '35c' or f == '3rc':
                            midx = words[w + 1]
                            line += '   ; ' + resolve_m(d, midx)
                        elif f == '22c' or f == '21c' or f == '23c':
                            fidx = words[w + 1]
                            if 0x44 <= op <= 0x6d:  # field ops
                                line += '   ; ' + resolve_f(d, fidx)
                            else:  # type ops (const-class/check-cast/new-instance...)
                                try:
                                    line += '   ; type=' + d.type_str(fidx)
                                except Exception:
                                    pass
                        elif f == '31c':
                            sidx = words[w + 1]
                            try:
                                line += '   ; "' + d.string(sidx) + '"'
                            except Exception:
                                pass
                        out.append(line)
                        w += u
                    if out:
                        return '\n'.join(out)
    return '\n'.join(out) or f'NOT FOUND: {cls}.{meth}'


if __name__ == '__main__':
    apk = sys.argv[1]
    cls = sys.argv[2]
    meth = sys.argv[3]
    maxpc = int(sys.argv[4]) if len(sys.argv) > 4 else 100000
    print(decode_method(apk, cls, meth, maxpc))
