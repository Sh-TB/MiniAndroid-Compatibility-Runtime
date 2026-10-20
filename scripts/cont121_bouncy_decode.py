#!/usr/bin/env python3
"""CONT-121 W-02: decode BouncyActivity.requestThumbnail Set.add null root.
Dumps the method, the Set field declaration, and every <init>/onCreate store
site for that field."""
import os
from loguru import logger
logger.remove()
from androguard.misc import AnalyzeDex
import zipfile

apk = "upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk"
OUT = "run/c121"
os.makedirs(OUT, exist_ok=True)
z = zipfile.ZipFile(apk)
dex_names = sorted(n for n in z.namelist() if n.endswith(".dex"))
dex_path = os.path.join(OUT, "bouncy_extracted.dex")
open(dex_path, "wb").write(z.read(dex_names[0]))

a, d, dx = AnalyzeDex(dex_path)
BA = "Lcom/dozingcatsoftware/bouncy/BouncyActivity;"
cls = d.get_class(BA)

# 1. requestThumbnail dump
print("=== requestThumbnail ===")
for m in cls.get_methods():
    if m.get_name() == "requestThumbnail":
        off = 0
        for ins in m.get_code().get_bc().get_instructions():
            op = ins.get_name()
            try:
                txt = f"{off:04x}: {op} {ins.get_output()}"
            except Exception:
                txt = f"{off:04x}: {op} <err>"
            off += ins.get_length()
            print("  " + txt)

# 2. all fields of type Set
print("\n=== Set-typed fields ===")
for f in cls.get_fields():
    if "java/util/Set" in f.get_descriptor() or "HashSet" in f.get_descriptor():
        print(f"  {f.get_name()} : {f.get_descriptor()}  access={hex(f.get_access_flags())}")

# 3. stores to those fields anywhere in the class
set_fields = [f.get_name() for f in cls.get_fields()
              if "java/util/Set" in f.get_descriptor() or "HashSet" in f.get_descriptor()]
print("\n=== store/init sites for Set fields ===")
for m in cls.get_methods():
    code = m.get_code()
    if not code:
        continue
    off = 0
    for ins in code.get_bc().get_instructions():
        op = ins.get_name()
        try:
            outp = ins.get_output()
        except Exception:
            outp = ""
        for sf in set_fields:
            if op.startswith(("sput", "iput")) and f", {BA}{sf} " in outp:
                print(f"  {m.get_name()}{m.get_descriptor()} @{off:04x}: {op} {outp}")
        off += ins.get_length()
