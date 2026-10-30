#!/usr/bin/env python3
"""cont11_xref.py — cross-reference: which methods invoke TARGET class.method.
Usage: cont11_xref.py <apk> <Lcls;> <method> [max results]
Full-scan of all classes*.dex code items."""
import sys, zipfile, struct
sys.path.insert(0, '/home/z/my-project/scripts')
import importlib.util
spec = importlib.util.spec_from_file_location("d", "/home/z/my-project/scripts/cont9_dexdump.py")
d = importlib.util.module_from_spec(spec)
import types
# cont9_dexdump runs main() only under __main__; safe to import via exec of module code
src = open("/home/z/my-project/scripts/cont9_dexdump.py").read()
src = src.split("def main()")[0]  # strip main
exec(src, d.__dict__)

def main():
    apk, tcls, tmeth = sys.argv[1], sys.argv[2], sys.argv[3]
    maxr = int(sys.argv[4]) if len(sys.argv) > 4 else 25
    z = zipfile.ZipFile(apk)
    hits = []
    for name in [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]:
        dx = d.Dex(z.read(name))
        hits = []
        for cls_off in range(dx.class_defs_size):
            coff = dx.class_defs_off + 32 * cls_off
            info = dx.class_methods(coff)
            cname = dx.type_str(struct.unpack_from('<I', dx.b, coff)[0])
            for kind in ('direct', 'virtual'):
                for mname, mdesc, acc, sz, code in info[kind]:
                    if not code:
                        continue
                    for line in dx.disasm(code):
                        if f"invoke" in line and f"{tcls}.{tmeth}" in line:
                            hits.append(f"{cname}.{mname}{mdesc}")
                            break
        break
    from collections import Counter
    for k, v in Counter(hits).most_common(maxr):
        print(v, k)
    if not hits:
        print("NO HITS")

if __name__ == '__main__':
    main()
