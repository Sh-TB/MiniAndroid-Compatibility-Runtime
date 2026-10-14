#!/usr/bin/env python3
"""cont48_dooz_draw_scan.py — CONT-48 static decode for Dooz v23.

Scans every classes*.dex in the APK and finds every method that invokes:
  Canvas.drawRect / drawRoundRect / drawCircle / drawPath
  Path.moveTo / lineTo / quadTo / cubicTo / rMoveTo / rLineTo / close / reset / rewind
Prints caller class+method+pcs. Pins (a) the black-RECT (849,53,912,116)
producer and (b) the empty-PATH (Compose ImageVector) builder chain.
"""
import sys, zipfile, struct
sys.path.insert(0, '/home/z/my-project/scripts')
from cont46_disasm import Dex, OPS, FMT_W

APK = '/home/z/my-project/upload/canonical_apks/io.github.yamin8000.dooz_23.apk'
TARGETS = (
    'Landroid/graphics/Canvas;->drawRect',
    'Landroid/graphics/Canvas;->drawRoundRect',
    'Landroid/graphics/Canvas;->drawCircle',
    'Landroid/graphics/Canvas;->drawPath',
    'Landroid/graphics/Path;->moveTo',
    'Landroid/graphics/Path;->lineTo',
    'Landroid/graphics/Path;->quadTo',
    'Landroid/graphics/Path;->cubicTo',
    'Landroid/graphics/Path;->rMoveTo',
    'Landroid/graphics/Path;->rLineTo',
    'Landroid/graphics/Path;->close',
    'Landroid/graphics/Path;->reset',
    'Landroid/graphics/Path;->rewind',
    'Landroid/graphics/Path;->op',
    'Landroid/graphics/Path;->set(',
)

def main():
    z = zipfile.ZipFile(APK)
    hits = {}
    total = 0
    for dn in [n for n in z.namelist() if n.endswith('.dex')]:
        d = Dex(z.read(dn))
        for ci in range(d.cdef_n):
            hdr = struct.unpack_from('<8I', d.b, d.cdef_off + ci * 32)
            cls_idx = struct.unpack_from('<I', d.b, d.cdef_off + ci * 32)[0]
            try:
                cls = d.t(cls_idx)
            except Exception:
                continue
            try:
                methods = d.methods_of(hdr)
            except Exception:
                continue
            for kind, midx, acc, code_off in methods:
                total += 1
                if not code_off:
                    continue
                try:
                    mcls, mname, mproto = d.meth(midx)
                except Exception:
                    continue
                regs, ins, outs, base, n = d.code(code_off)
                i = 0
                while i < n:
                    unit = struct.unpack_from('<H', d.b, base + i * 2)[0]
                    op = unit & 0xff
                    fmt = OPS.get(op, ('?', '10x'))[1]
                    sz = FMT_W.get(fmt, 1)
                    if fmt == '35c':
                        BBBB = struct.unpack_from('<H', d.b, base + i * 2 + 2)[0]
                        try:
                            callee = d.meth(BBBB)
                            cstr = f"{callee[0]}->{callee[1]}"
                            for t in TARGETS:
                                if cstr.startswith(t):
                                    key = (cls, mname)
                                    hits.setdefault(key, {}).setdefault(t, []).append(i)
                                    break
                        except Exception:
                            pass
                    i += sz
    def short(c):
        return (c.replace('Landroidx/compose/', 'C/')
                 .replace('Landroidx/', 'Ax/')
                 .replace('Landroid/', 'An/')
                 .replace('Lio/github/yamin8000/dooz/', 'Dooz/'))
    print(f"scanned {total} methods; {len(hits)} caller methods hit")
    for (cls, meth), callees in sorted(hits.items()):
        n_hits = sum(len(v) for v in callees.values())
        print(f"\nCALLER {short(cls)}::{meth}  ({n_hits} hits)")
        for t, pcs in sorted(callees.items()):
            print(f"   {short(t)}  pcs={pcs[:10]}{'...' if len(pcs) > 10 else ''}")

if __name__ == '__main__':
    main()
