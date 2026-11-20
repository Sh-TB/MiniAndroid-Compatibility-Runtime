#!/usr/bin/env python3
"""S17-d: settle the 9 law-verified NO-CITE rows + correct the S16 M2 mark.
Row source_check gets 'S17-LAW 2026-11-20: <verdict> — <detail>'."""
import csv

FIND = "/home/z/my-project/miniandroid/evidence/audit/632_FINDINGS.csv"
L = "s17_focus_laws_test"

U = {
 "632-E3": ("RESOLVED-IN-TREE",
   f"W1 pins the opposite: weight-0 MATCH_PARENT child measures the parent width "
   f"(1080) — NOT absorbed into the weighted redistribution (gate is layout_weight>0, "
   f"inflater.cpp:3866); W1.b pins the AOSP G04 §9 excess law (sole weight-1 0dp child "
   f"= full 1080). The claimed match_parent->weight-1 defect does not reproduce. Laws in {L}."),
 "632-G3": ("RESOLVED-IN-TREE",
   f"S16 found the Kahn topological sort in the tree (inflater.cpp:3223/3511); F1 now pins "
   f"it BEHAVIORALLY: dependent inflated before its anchor, B.left(300) == A.right(300). "
   f"Forward references resolve. Law in {L}."),
 "632-L3": ("RESOLVED-IN-TREE",
   f"R2 pins the decode law: 20dp->53 (density 2.625, round-half-away), 8px pass-through, "
   f"12dip->32 (the once-dead `dip` suffix now decoded). Radix + unit decode correct on the "
   f"inflater path. Laws in {L}."),
 "632-M1": ("RESOLVED-IN-TREE",
   f"R2 pins dp->px applied EXACTLY once at decode (complex_unit_to_dimension_pixel_size, "
   f"res_id.cpp:29 — the ONE rounding + nonzero-floor implementation). No double "
   f"multiplication. Law in {L}."),
 "632-M2": ("RESOLVED-IN-TREE",
   f"S16-CHECK CORRECTED (was CONFIRMED-LIVE on a literal-grep miss — the code says "
   f"scaled_density/scale_fonts, not scaledDensity): density_context() passes font scale "
   f"(inflater.cpp:461) and COMPLEX_UNIT_SP -> value*scaled_density (res_id.cpp:30). R3 "
   f"pins it: 10sp @font-scale 1.3 -> 34px = 10*2.625*1.3 rounded. Law in {L}."),
 "632-NEW-33": ("CONFIRMED-LIVE",
   f"A1.d pins the silence BEHAVIORALLY: seven dropped attributes inflate with "
   f"stats.warnings EMPTY — unknown attributes vanish with no diagnostic (the claim). "
   f"Law in {L}."),
 "632-NEW-35": ("CONFIRMED-LIVE",
   f"A1.a pins paddingStart dropped: padding_left/right stay 0 after inflate (no handler "
   f"in the decode table). Law in {L}; clipChildren same rig (NEW-36)."),
 "632-NEW-37": ("CONFIRMED-LIVE",
   f"A1.b/A1.c pin the transform family dropped: alpha stays 255, translation_x stays 0 "
   f"after inflating alpha/translationX attrs. Law in {L}."),
 "632-D2": ("PARTIAL",
   f"G1 pins the inflater path: alignParentTop+Bottom -> EXACTLY the anchor span "
   f"(top=0, h=1920, lp height overridden) — AOSP both-anchor law, NO mask-overlap "
   f"misrouting. The original 0x30&0x50 claim targeted the old divergent engine "
   f"(real_layout, absent); the gravity-mask claim is settled for the live inflater, "
   f"the android_shadows gravity path remains queued. Law in {L}."),
 "632-G2": ("CITE-STALE",
   f"R1.a pins the DECODE layer: alignParentBottom + centerHorizontal BOTH survive to "
   f"node flags (no decode-level collapse); the final-position mutual-exclusion question "
   f"still needs the position pin — queued."),
 "632-G4": ("CITE-STALE",
   f"R1.b pins toRightOf name capture through the XML decode; the measure-width question "
   f"(child constrained by toRightOf measured with full parent width?) still needs its "
   f"position law — queued."),
}

rows = list(csv.DictReader(open(FIND, newline="", encoding="utf-8")))
n = 0
for r in rows:
    fid = r["finding_id"]
    if fid in U and r["source_check"].startswith("S16-CHECK"):
        v, d = U[fid]
        r["source_check"] = f"S16-CHECK 2026-11-20 + S17-LAW 2026-11-20: {v} — {d}"
        n += 1
with open(FIND, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader(); w.writerows(rows)
print(f"updated {n} rows")
from collections import Counter
kinds = Counter(r["source_check"].split("—")[0].split(": ", 2)[-1] for r in rows if "S17-LAW" in r["source_check"])
for k, v in kinds.most_common(): print(f"  {k}: {v}")
