#!/usr/bin/env python3
# cont82_armA_fishrings.py — Arm A (baseline toolchain) for Q1: why does
# fish.rings stay on the splash (deferred-launch family)?
# Baseline = androguard ad-hoc decode + zipfile asset census. Timed.
import sys
import time
import zipfile

T0 = time.monotonic()
log = []


def step(msg):
    log.append(f"[{time.monotonic()-T0:7.2f}s] {msg}")
    print(log[-1])


APK = "upload/canonical_apks/fishrings_v1.23_vc6.apk"

step("armA start: zipfile census for assets/banner.html")
with zipfile.ZipFile(APK) as z:
    names = z.namelist()
    assets = [n for n in names if n.startswith("assets/")]
    banner = [n for n in names if "banner" in n.lower()]
    step(f"zip census: {len(names)} entries, {len(assets)} assets/*, banner hits={banner}")
    # the runtime log said: loadUrl asset MISSING (honest placeholder): entry=assets/banner.html
    step(f"assets/banner.html present? {'assets/banner.html' in names}")
    htmls = [n for n in names if n.endswith((".html", ".htm"))]
    step(f"html files in APK: {htmls}")

step("androguard decode: SplashActivity + main game activity")
from loguru import logger; logger.remove()
from androguard.core.dex import DEX

with zipfile.ZipFile(APK) as z:
    dexes = [n for n in z.namelist() if n.endswith(".dex")]
    step(f"dex files: {dexes}")
    for dn in dexes:
        d = DEX(z.read(dn))
        for c in d.get_classes():
            cn = c.get_name()
            if cn in ("Leu/veldsoft/fish/rings/SplashActivity;",
                      "Leu/veldsoft/fish/rings/SplashActivity$1;",
                      "Leu/veldsoft/fish/rings/MainActivity;",
                      "Leu/veldsoft/fish/rings/GameActivity;"):
                step(f"class {cn} super={c.get_superclassname()}")
                for m in c.get_methods():
                    body = None
                    try:
                        body = m.get_source() if False else None
                    except Exception:
                        pass
                    code = m.get_code()
                    if code is None:
                        continue
                    # walk the bytecode for invokes + const strings
                    idx = 0
                    ins = code.get_bc().get_instructions()
                    found = []
                    for ins_i in ins:
                        op = ins_i.get_name()
                        if op.startswith("invoke-"):
                            ref = ins_i.get_operands()
                            found.append(("", op,
                                          str(ref[-1]) if ref else ""))
                        elif op.startswith("const-string"):
                            found.append(("", op,
                                          str(ins_i.get_operands()[-1])))
                    if found:
                        step(f"  {cn}->{m.get_name()}{m.get_descriptor()}")
                        for f in found[:28]:
                            step(f"    {f[0]} {f[1]} {f[2]}")

step("armA done")
print(f"\nARM-A TOTAL: {time.monotonic()-T0:.2f}s, {len(log)} steps")
