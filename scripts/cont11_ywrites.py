#!/usr/bin/env python3
"""cont11_ywrites.py — find classes with methods writing Lbt0;.y (isPlacedByParent).
Uses the proven cont9_dexdump parser. Scans small classes first (R8 lambdas)."""
import sys, zipfile, struct, re

src = open("/home/z/my-project/scripts/cont9_dexdump.py").read()
src = src.split("def main()")[0]
ns = {}
exec(src, ns)
Dex = ns['Dex']

def main():
    apk = sys.argv[1]
    pat = sys.argv[2] if len(sys.argv) > 2 else r"iput-boolean v\d+, v\d+, Lbt0;\.y:Z"
    rx = re.compile(pat)
    z = zipfile.ZipFile(apk)
    hits = []
    for name in [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]:
        d = Dex(z.read(name))
        for ci in range(d.class_defs_size):
            coff = d.class_defs_off + 32*ci
            cname = d.type_str(struct.unpack_from('<I', d.b, coff)[0])
            try:
                info = d.class_methods(coff)
            except Exception:
                continue
            for kind in ('direct', 'virtual'):
                for mname, mdesc, acc, sz, code in info[kind]:
                    if not code:
                        continue
                    try:
                        lines = d.disasm(code)
                    except Exception:
                        continue
                    for line in lines:
                        if rx.search(line):
                            hits.append(f"{cname}.{mname}{mdesc} :: {line.strip()[:90]}")
                            break
        break
    for h in hits[:30]:
        print(h)
    print("TOTAL", len(hits))

if __name__ == '__main__':
    main()
