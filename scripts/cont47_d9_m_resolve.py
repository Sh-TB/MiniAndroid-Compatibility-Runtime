#!/usr/bin/env python3
"""CONT-47 D9b2: resolve the exact field/method/string refs used inside
Lzs0;.m()V and Lzs0;.k(Lj4;)Z — name the guard that kills m->k."""
import warnings, logging, zipfile
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX

APK = "upload/canonical_apks/io.github.yamin8000.dooz_23.apk"
zf = zipfile.ZipFile(APK)
d = DEX(zf.read("classes.dex"))

def fstr(i):
    try:
        return d.get_string(i)
    except Exception:
        try:
            return d.get_strings()[i]
        except Exception:
            return f"str#{i}"

def mname(i):
    try:
        mid = d.get_method_id(i)
        return f"{mid.get_class_name()}->{mid.get_name()}{mid.get_descriptor()}"
    except Exception:
        return f"mth#{i}"

def fname(i):
    try:
        fid = d.get_field_id(i)
        return f"{fid.get_class_name()}.{fid.get_name()}:{fid.get_descriptor()}"
    except Exception:
        return f"fld#{i}"

import re
src = open("run/cont47/d9_lzs0_decode.txt").read()
# capture the m()V and k() blocks
for sig in ("Lzs0;->m()V", "Lzs0;->k(Lj4;)Z", "Lzs0;->r(Lel0; Z)Z", "Lzs0;->s(J)V"):
    blk = src.split("=== [classes.dex] " + sig)
    if len(blk) < 2:
        continue
    body = blk[1].split("\n=== ")[0]
    print("#### " + sig)
    refs = re.findall(r"\?(\d+)", body)
    for r in sorted(set(int(x) for x in refs)):
        # try method first, then field, then string
        mm = mname(r)
        ff = fname(r)
        ss = None
        try:
            ss = fstr(r)
        except Exception:
            pass
        cands = [c for c in (mm, ff, ss) if c and not c.endswith(f"#{r}")]
        print(f"  ?{r}  ->  {cands[:3]}")
    print()
