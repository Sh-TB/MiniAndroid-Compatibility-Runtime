#!/usr/bin/env python3
"""S18-7: upgrade the 11 rows the S18 law families actually settled — append
'S18-LAW 2026-11-20: <verdict> — <detail>' to their S18-CLASS source_check."""
import csv, sys

FIND = "/home/z/my-project/miniandroid/evidence/audit/632_FINDINGS.csv"

U = {
 "632-M3": ("RESOLVED-IN-TREE",
   "Family A pins the rounding law exactly (s18_dimension_rounding_laws_test, "
   "7/7): round-half-away + nonzero-floor tail (0.1dp->1, -0.1dp->-1), physical "
   "units off xdpi (1in->420, 1mm->17, 1pt->6), typed-word path agreement. "
   "NOTE: the floor tail is a DIVERGENCE from AOSP complexToDimensionPixelSize "
   "(which can answer 0) — pinned as current contract."),
 "632-E2": ("ALREADY-RESOLVED",
   "Family B law-verifies it (s18_weightsum_laws_test, 4/4): weightSum=3 -> "
   "360/360, weightSum=0 -> derived-sum fallback, weightSum=2 with three "
   "children -> 540/540/0 sequential exhaustion (AOSP law), no-attr -> derived. "
   "The retracted 'never read' claim is settled both ways."),
 "632-N2": ("RESOLVED-IN-TREE",
   "Family C pins the G47 field law (s18_text_layout_laws_test C1/C2): "
   "first-line line_above = |top| with includeFontPadding, |ascent| without "
   "(TextLayout.ascent stays the raw box, text_shaper.cpp:1369)."),
 "632-N3": ("RESOLVED-IN-TREE",
   "Family C pins the spacing law (C4/C5): spacing_add grows non-last line "
   "boxes by exactly add; multiplier m scales (below-above) per the G47 "
   "extra_k law; last line unmultiplied (addLastLineLineSpacing=false)."),
 "632-N4": ("RESOLVED-IN-TREE",
   "Family C pins ellipsize+maxLines (C6/C7): END truncates an OVER-WIDE last "
   "line with U+2026 ('throu…' @57<=60px) and NONE keeps content; maxLines "
   "caps block lines (1-line cap != singleLine)."),
 "632-NEW-23": ("PARTIAL",
   "Family C pins the FIRST-STRONG half (C8): pure-Arabic run rtl_base=true, "
   "Latin false. The locale/textDirection heuristic parity stays "
   "NEEDS-EXTERNAL-ORACLE."),
 "632-SQL-4": ("CONFIRMED-LIVE",
   "Family F pins the silence (s18_sql_shadow_laws_test F1.c): BLOB cell "
   "through the REAL sqlite3 path (x'01020304') — row materializes (rows=1, "
   "id column reads '1') but cursor_value_string on the BLOB column answers "
   "NOTHING (s1=false). BLOB cells are not materialized — claim confirmed."),
 "632-SQL-5": ("CONFIRMED-LIVE",
   "Family F pins the ignore (F2): open via the AOSP <init>(Context, name, "
   "factory, version) slot WITH a factory object -> open+query still work "
   "identically — accepted-and-ignored, claim confirmed."),
 "632-SQL-6": ("CONFIRMED-LIVE",
   "Family F confirms it STRONGER than claimed (F3): the open path runs "
   "PRAGMA journal_mode=WAL (sqlite_shadow.cpp:234) but the readback answers "
   "'delete' — the WAL set does not stick on the read connection, so WAL buys "
   "exactly nothing."),
 "632-O4": ("CONFIRMED-LIVE",
   "Family G pins it (s18_renderer_surface_laws_test G1): a fresh FrameBuffer "
   "initializes EVERY pixel to WHITE {255,255,255,255} "
   "(software_renderer.h:122) — an Android surface starts transparent/black; "
   "the white default is the claimed defect."),
 "632-O5": ("CONFIRMED-LIVE",
   "Family G pins the bypass (G2): a write through get_pixels_mut lands "
   "bit-exact {1,2,3,4} with no blending; the API contrast (G3) shows "
   "set_pixel composites per the sa=1 blend law."),
}

rows = list(csv.DictReader(open(FIND, newline="", encoding="utf-8")))
n = 0
for r in rows:
    fid = r["finding_id"]
    if fid in U and r["source_check"].startswith("S18-CLASS"):
        v, d = U[fid]
        r["source_check"] += f" | S18-LAW 2026-11-20: {v} — {d}"
        n += 1
with open(FIND, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader(); w.writerows(rows)
print(f"upgraded {n} rows with S18-LAW marks")
