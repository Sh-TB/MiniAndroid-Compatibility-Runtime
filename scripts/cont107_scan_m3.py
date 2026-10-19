#!/usr/bin/env python3
"""CONT-107 / F-NEW-448 decode: who writes Ll/m3;.a in chess (jwtc 298)?

Walks all dex bodies, finds sput/sget on the field named by the CONT-106
decode (class Ll/m3;, static int 'a'), prints the writer methods with their
code windows, then tries a one-hop caller search for each writer.
Output: run/c107/m3_scan.txt
"""
import sys, re
from androguard.core.apk import APK
from androguard.core.dex import DEX

APK_PATH = sys.argv[1] if len(sys.argv) > 1 else "upload/chess_jwtc_298.apk"
OUT = "run/c107/m3_scan.txt"

a = APK(APK_PATH)
target_cls = None
target_fld = None
lines = []

# find the class: CONT-106 says appcompat Toolbar.onMeasure does `sget Ll/m3;.a`.
# R8 names may differ per build; search EVERY class for a static int field 'a'
# that Toolbar.onMeasure sgets. First locate Toolbar.onMeasure.
dexes = [DEX(d) for d in a.get_all_dex()]

toolbar_cls = None
for di, d in enumerate(dexes):
    for c in d.get_classes():
        if c.get_name() == "Landroidx/appcompat/widget/Toolbar;":
            toolbar_cls = c
            lines.append(f"[toolbar] class {c.get_name()} in dex#{di}")
            for m in c.get_methods():
                if m.get_name() == "onMeasure":
                    lines.append(f"[toolbar] onMeasure {m.get_descriptor()}")
                    code = m.get_code()
                    if code:
                        head = []
                        for i in list(code.get_bc().get_instructions())[:40]:
                            head.append(f"{i.get_name()} {i.get_output()}")
                        lines.append(f"[toolbar] onMeasure head: {' '.join(head)[:900]}")
if toolbar_cls is None:
    lines.append("[toolbar] NOT FOUND — R8 renamed; falling back to field scan")

# The field: search all classes for static int field 'a' on Ll/m3; style names
# (single-letter class, single-letter field, static int) referenced from
# Toolbar.onMeasure. Simplest robust route: find sget-static on
# L.*?/m\d+;->a:I inside onMeasure (already printed above), else scan for the
# static-int-single-letter-field pattern with MANY readers.
cands = {}
for di, d in enumerate(dexes):
    for c in d.get_classes():
        cn = c.get_name()
        if not re.match(r"^L[\w/$]{1,6};$", cn):
            continue
        for f in c.get_fields():
            if (f.get_name() == "a" and f.get_descriptor() == "I"
                    and int(f.get_access_flags()) & 0x8):
                cands[cn] = f
lines.append(f"[cands] static int 'a' single-letter classes: {sorted(cands)[:20]}")

# find writers (sput) and readers (sget) for each candidate
for cn, f in sorted(cands.items()):
    writers, readers = [], []
    key_f, key_c = f.get_name(), f.get_descriptor()
    for di, d in enumerate(dexes):
        for c in d.get_classes():
            for m in c.get_methods():
                code = m.get_code()
                if not code:
                    continue
                for ins in code.get_bc().get_instructions():
                    op = ins.get_name()
                    if op not in ("sput", "sput-object", "sget", "sget-object"):
                        continue
                    try:
                        if (ins.get_string()  # field ref "Lcls;->name:desc"
                                == f"{cn}->{key_f}:{key_c}"):
                            tag = f"{c.get_name()}->{m.get_name()}{m.get_descriptor()}"
                            (writers if op.startswith("sput") else readers).append(tag)
                    except Exception:
                        pass
    if writers:
        lines.append(f"[field] {cn}->a:I WRITERS({len(writers)}): {writers[:12]}")
        lines.append(f"[field] {cn}->a:I READERS({len(readers)}): {readers[:12]}")

with open(OUT, "w") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines[:40]))
print("...", OUT)
