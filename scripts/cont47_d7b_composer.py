#!/usr/bin/env python3
"""CONT-47 D7b — composer record-time decode via androguard.

Target: name the slot-table record path — Lfe1;.E constructs the per-group
records (Lui1;/Lvi1; per D6 notes). Decode:
  1. Lfe1;.E signature + instruction census (which Lui1/Lvi1 ctors it calls,
     which fields it writes).
  2. Lui1;/Lvi1; field tables (the per-group RECORD records).
  3. Any method on Lfe1; that READS a slot table (startNode/endNode group
     bookkeeping) — the useNode-vs-insert handoff witness point.
Ground truth: androguard (the hand uleb parser desyncs on dooz classes).
Output: census lines to stdout; caller redirects to run/cont47/d7b_composer.log
"""
import sys
import logging

logging.getLogger().disabled = True
from androguard.core.dex import DEX

APK = "upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
ZIP_MEMBERS = ["classes.dex", "classes2.dex", "classes3.dex", "classes4.dex",
               "classes5.dex", "classes6.dex", "classes7.dex", "classes8.dex"]


def main():
    import zipfile
    z = zipfile.ZipFile(APK)
    targets = {"Lfe1;", "Lui1;", "Lvi1;"}
    for member in ZIP_MEMBERS:
        try:
            raw = z.read(member)
        except KeyError:
            continue
        d = DEX(raw)
        for cls in d.get_classes():
            name = cls.get_name()
            # get_name returns 'Lfe1;' style already
            if name not in targets:
                continue
            print(f"=== {name} (dex={member}) ===")
            print(f"  super={cls.get_superclassname()}")
            flds = list(cls.get_fields())
            print(f"  nfields={len(flds)}")
            for f in flds:
                print(f"    field {f.get_name()} : {f.get_descriptor()}")
            meths = list(cls.get_methods())
            print(f"  nmethods={len(meths)}")
            for m in meths:
                mn = m.get_name()
                md = m.get_descriptor()
                print(f"  --- method {mn}{md}")
                code = m.get_code()
                if code is None:
                    print("    <abstract/native>")
                    continue
                # instruction census: invoked methods + iput/iget fields
                invokes = {}
                ifields = {}
                for ins in m.get_instructions():
                    op = ins.get_name()
                    if op.startswith("invoke"):
                        try:
                            ref = ins.get_operands()
                            # last operand holds the method ref string
                            txt = str(ref[-1][2]) if ref else "?"
                            invokes[txt] = invokes.get(txt, 0) + 1
                        except Exception:
                            pass
                    elif op.startswith(("iput", "iget")):
                        try:
                            ref = ins.get_operands()
                            txt = str(ref[-1][2]) if ref else "?"
                            ifields[txt] = ifields.get(txt, 0) + 1
                        except Exception:
                            pass
                for k, v in sorted(invokes.items(), key=lambda x: -x[1])[:14]:
                    print(f"    invoke {v}x {k}")
                for k, v in sorted(ifields.items(), key=lambda x: -x[1])[:14]:
                    print(f"    {op.split('-')[0] if False else 'acc'} {v}x {k}")
        print(f"[[DEX-DONE {member}]]")
    print("D7B-CENSUS-DONE")


if __name__ == "__main__":
    sys.exit(main())
