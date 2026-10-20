#!/usr/bin/env python3
"""CONT-121 W-01: FIX-449 endgame — reliable disassembly of the telegram
play_billing protobuf-lite walk chain (c3.<clinit>, n2.r, p3.<clinit>)
using androguard (the in-repo dumper had a latent get_string bug, now fixed,
but its disassembler still desyncs on large methods).

Outputs: run/c121/ directory with per-method disassembly + a summary of
new-array/aput-object/filled-new-array sites (the entries[] construction).
"""
import sys, os, zipfile, json
from loguru import logger
logger.remove()  # silence androguard's DEBUG flood
from androguard.misc import AnalyzeDex

APK = "upload/telegram_official.apk"
OUT = "run/c121"
os.makedirs(OUT, exist_ok=True)

TARGETS = [
    ("Lcom/google/android/gms/internal/play_billing/c3;", "<clinit>"),
    ("Lcom/google/android/gms/internal/play_billing/n2;", "r"),
    ("Lcom/google/android/gms/internal/play_billing/p3;", "<clinit>"),
]

z = zipfile.ZipFile(APK)
data = z.read("classes.dex")
dex_path = os.path.join(OUT, "classes_extracted.dex")
with open(dex_path, "wb") as f:
    f.write(data)

a, d, dx = AnalyzeDex(dex_path)

summary = {}
for cls_desc, meth_name in TARGETS:
    cls = d.get_class(cls_desc)
    if cls is None:
        print(f"{cls_desc}: CLASS NOT FOUND")
        continue
    done = False
    for m in cls.get_methods():
        if m.get_name() != meth_name:
            continue
        done = True
        code = m.get_code()
        if code is None:
            print(f"{cls_desc}.{meth_name}: NO CODE (abstract/native)")
            break
        lines = []
        facts = {"new_array": [], "aput_object": 0, "aput_total": 0,
                 "filled_new_array": 0, "const_strings": []}
        off = 0
        for ins in code.get_bc().get_instructions():
            op = ins.get_name()
            try:
                txt = f"{off:04x}: {op} {ins.get_output()}"
            except Exception as e:
                txt = f"{off:04x}: {op} <decode-err {e}>"
            off += ins.get_length()
            lines.append(txt)
            if op.startswith("new-array"):
                facts["new_array"].append(txt)
            elif op.startswith("aput-object"):
                facts["aput_object"] += 1
            elif op.startswith("aput"):
                facts["aput_total"] += 1
            elif op.startswith("filled-new-array"):
                facts["filled_new_array"] += 1
            elif op.startswith("const-string"):
                facts["const_strings"].append(txt)
        short = cls_desc.split("/")[-1]
        fname = os.path.join(OUT, f"dis_{short}_{meth_name.replace('<','').replace('>','')}.txt")
        with open(fname, "w") as f:
            f.write(f"# {cls_desc}.{meth_name}  registers={code.get_registers_size()}\n")
            f.write("\n".join(lines))
        key = f"{short}.{meth_name}"
        summary[key] = {
            "insns": len(lines), "file": fname,
            "new_array_count": len(facts["new_array"]),
            "aput_object": facts["aput_object"],
            "aput_total": facts["aput_total"],
            "filled_new_array": facts["filled_new_array"],
            "new_array_sites": facts["new_array"][:10],
        }
        print(f"{key}: {len(lines)} insns -> {fname}")
        print(f"   new-array={len(facts['new_array'])} aput-object={facts['aput_object']} "
              f"aput*={facts['aput_total']} filled-new-array={facts['filled_new_array']}")
        break
    if not done:
        print(f"{cls_desc}.{meth_name}: METHOD NOT FOUND")

with open(os.path.join(OUT, "w01_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print("summary written")
