#!/usr/bin/env python3
"""cont48_f1_dex_rfields.py — F1 decode step 2: enumerate telegram's DEX R$
classes, histogram the resid type-bytes per R subclass, and compare with the
ARSC type table. Names the real mismatch layer for the 11098 resolve()=null
resids of the T8 census."""
import warnings, logging, zipfile, collections, json
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat

apk_path = "/home/z/my-project/upload/telegram_official.apk"
a = APK(apk_path)

hist = collections.defaultdict(collections.Counter)  # subclass -> typebyte -> n
valrange = {}                                        # subclass -> (min,max)
samples = {}
dex_names = [n for n in a.get_files() if n.startswith("classes") and n.endswith(".dex")]
print("dex files:", len(dex_names))
for dn in dex_names:
    try:
        d = DalvikVMFormat(a.get_file(dn))
    except Exception as e:
        print("DEX-ERR", dn, str(e)[:60]); continue
    for c in d.get_classes():
        n = c.get_name()
        if "R$" not in n: continue
        # subclass name after R$
        sub = n.split("R$")[-1].rstrip(";").split("/")[-1]
        lo, hi = valrange.get(sub, (1 << 62, -1))
        for f in c.get_fields():
            v = None
            try:
                iv = f.get_init_value()
                if iv is not None:
                    v = iv.get_value()
            except Exception:
                pass
            if not isinstance(v, int) or v < 0x10000: continue
            tb = (v >> 16) & 0xFF
            hist[sub][tb] += 1
            lo, hi = min(lo, v), max(hi, v)
            if sub not in samples and tb == 0x0F:
                samples[sub] = (f.get_name(), hex(v))
        valrange[sub] = (lo, hi)

out = {}
for sub in sorted(hist):
    out[sub] = {f"0x{tb:02x}": n for tb, n in hist[sub].most_common(6)}
    print(f"R${sub:12s} n={sum(hist[sub].values()):6d} range={valrange[sub][0]:#x}..{valrange[sub][1]:#x} top={out[sub]} sample0x0f={samples.get(sub)}")
json.dump({"hist": {k: dict(v) for k, v in hist.items()},
           "range": {k: [v[0], v[1]] for k, v in valrange.items()},
           "samples": {k: list(map(str, v)) for k, v in samples.items()}},
          open("/home/z/my-project/run/cont48/f1_dex_rfields.json", "w"), indent=1)
print("WROTE run/cont48/f1_dex_rfields.json")
