#!/usr/bin/env python3
"""cont29_isreleased_scan.py — AUTHORITY: oracle DEX.
(1) every method that WRITES isReleased (iput-boolean -> isReleased),
    showing the preceding const (0/1);
(2) every call site of release$ui_graphics / release / reset on the facade;
(3) every call of GraphicsContext.releaseGraphicsLayer-family methods.
"""
import sys, io, zipfile
from androguard.core.dex import DEX

apk = sys.argv[1]
raw = open(apk, "rb").read()
zf = zipfile.ZipFile(io.BytesIO(raw))
dexes = [DEX(zf.read(n)) for n in zf.namelist() if n.endswith(".dex")]

TARGET = "isReleased"
CALLS = ("release$ui_graphics", "releaseGraphicsLayer", "->reset(")

for d in dexes:
    for c in d.get_classes():
        cname = c.get_name()
        for m in c.get_methods():
            code = m.get_code()
            if not code:
                continue
            ins_list = list(code.get_bc().get_instructions())
            names = [i.get_name() for i in ins_list]
            outs = [i.get_output() for i in ins_list]
            full = " ".join(outs)
            hits = []
            # writes to isReleased
            for k, (nm, out) in enumerate(zip(names, outs)):
                if nm.startswith("iput-boolean") and "->isReleased" in out:
                    val = None
                    for j in range(k - 1, max(-1, k - 4), -1):
                        if names[j] == "const/4":
                            val = outs[j].split(",")[1].strip()
                            break
                    hits.append(f"  WRITE  @{k:#06x} val={val} :: {nm} {out}")
            # calls of interest
            for k, (nm, out) in enumerate(zip(names, outs)):
                if nm.startswith("invoke") and any(t in out for t in CALLS):
                    hits.append(f"  CALL   @{k:#06x} :: {nm} {out}")
            if hits:
                print(f"{cname}.{m.get_name()}{m.get_descriptor()}")
                for h in hits:
                    print(h)
