#!/usr/bin/env python3
"""s58_registry_update.py — append the S58 decode to F-NEW-267 (no root inflation)."""
import json

REG = "/home/z/my-project/root_registry.json"
d = json.load(open(REG))
for r in d["roots"]:
    if r.get("id") == "F-NEW-267":
        add = (
            "S58 DECODE (binary 7d8aa389ba6945c0, dooz v23 180s tap 540,960): "
            "the CONT-64 place-then-reset double-measure pattern is GONE after the "
            "F-NEW-267 defer law — whole-run FIELD-TRACE shows ZERO puts to Ld61;.i "
            "(Placeable.position; CONT-64 observed 410 puts: 359 zero + 51 real) — yet the "
            "hit-test still reads ZERO for every walked node (Lc61;.j/l/k/g + Lat0;.a + "
            "Lbt0;.v0 on obj#13945/13942/13939/13893/13862/13951, window at "
            "run/s58/dooz180_ft.log line 5895965+) and the face still renders (3.2% non-bg, "
            "Material3 Scaffold, 3 button-like regions). Conclusion: the REAL placement pass "
            "executes (render geometry reaches the canvas path) but its position store never "
            "lands in the DEX-visible Placeable state — one writer expected, zero writes "
            "observed; the render path reads a DIFFERENT store than the hit-test. The two "
            "stores are disconnected. Named next lever: decode where R8'd placeAt's position "
            "write goes (which method/field), then implement the position-store law so both "
            "paths read the same state. Deferred measure/layout DOES drain during dispatch "
            "(Lzs0;.k x2 via Lyo1;.first/remove) and the hit-test geometry legs run "
            "(Low;.T roundToPx with zero px inputs). M3-19 re-observed live: Lrz1;.j OPEN "
            "(incomplete payload key, real DEX executes) + Lho1;.b CYCLE stub (lifetime_calls=9). "
            "Evidence: run/s58/dooz180_tap2.log, run/s58/dooz180_ft.log, "
            "run/s58/dooz180_tap3.log (ARG-TRACE), evidence/s58/capability_audit_v3.md item 37."
        )
        r["title"] = r["title"] + " | " + add
        r["status"] = "ROOT-CAUSED-PARTIAL"  # unchanged, decode deepened
        r.setdefault("evidence", "")
        r["evidence"] = (r["evidence"] + "; " if r["evidence"] else "") + (
            "evidence/s58/capability_audit_v3.md; run/s58/dooz180_ft.log; "
            "run/s58/dooz180_tap2.log; evidence/s58/s58_mosaic.png"
        )
        print("F-NEW-267 updated, title len:", len(r["title"]))
        break
else:
    raise SystemExit("F-NEW-267 not found")

json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry roots:", len(d["roots"]))
