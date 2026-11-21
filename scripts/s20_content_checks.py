#!/usr/bin/env python3
"""S20 — content-level checks close the LAST 7 classified rows (#632).
Every verdict derived from code reading this session (site + line cited in the
stamp). Per-row uniqueness pre-flight (fail-closed). Target: 234/234 settled."""
import csv
import re
import sys

REPO = "/home/z/my-project/miniandroid"
CSV_PATH = f"{REPO}/evidence/audit/632_FINDINGS.csv"
LOG = f"{REPO}/evidence/audit/RAW_LOGS/s20_content_checks_2026-11-21.log"
TAG = "S20-CONTENT"

STAMPS = [
    ("NEW-2", "Tautological condition in the weight path", f"{TAG}-REFUTED",
     "the LIVE weight re-measure (layout_inflater.cpp:3985-4045) contains no "
     "tautology: rws = (weight_sum_valid && weight_sum > 0) ? weight_sum : "
     "weight_total (:3993-3994), share = wgt*excess/rws with excess -= share "
     "(:4001/:4003), base = a 3-way lp_main ternary — every comparison is "
     "load-bearing; the share math is pinned by the s18_weightsum_laws_test "
     "family and MASTER-2 FIX-MEASURE-003 (:4457-4460); the claim has no live "
     "counterpart"),
    ("NEW-12", "scaleType in the *live* draw path is unverified", f"{TAG}-REFUTED",
     "the live draw path IS law-verified: s246_layout_closure_law_test (47 laws "
     "incl. the ImageView scaleType geometry group, IN-BATTERY, commit "
     "7e5473be) + c48773a0 ('scaleType raster proven at AOSP parity') + the "
     "live enum decode (android_shadows.cpp:10330-10352, per-ordinal cache + "
     "the 8-name AOSP table) + the full 8-case scale law (software_renderer.cpp "
     "scale_image_rect :425-470)"),
    ("NEW-14", "rects that exceed the view box; clipping must be verified",
     f"{TAG}-RESOLVED",
     "the rect math IS the AOSP crop law verbatim (software_renderer.cpp case "
     "5/6/7 + default :440-470 — CENTER_CROP crop = max(box/src) exceeds the "
     "box BY DESIGN, as AOSP); clipping exists as the S68 canvas-clip law "
     "(SoftwareCanvas::set_clip/clip_allows :157-169, per-pixel gate :213); "
     "the verification the row asks for WAS DONE: c48773a0's raster parity "
     "(cropped output matched AOSP pixels) + the s246 geometry group — no "
     "defect remains"),
    ("NEW-24", "Heuristic font metrics fallback", f"{TAG}-REFINED",
     "the ad-hoc heuristic WAS replaced on the shaping side: text_shaper.cpp:840 "
     "('G36 law (was: size*1.2 ad-hoc)') computes FontMetrics from the RESOLVED "
     "FACE (text_shaper.h:117-180, Android Paint.FontMetrics equivalent, "
     "in-battery via the s98 text laws); the ENGINE's Paint-metrics shadow "
     "retains DOCUMENTED em-fraction constants (dalvik_engine.cpp:53597 "
     "ascent -0.928em / descent 0.24em, face-derived, :54032) — no ad-hoc "
     "fallback remains where the claim pointed; the em constants are the "
     "documented engine law, not a heuristic fallback"),
    ("NEW-26", "Residual over-allocation from the phantom-NUL fix", f"{TAG}-CONFIRMED",
     "the residual is REAL and located: text_shaper.cpp:619 allocates "
     "std::vector<FriBidiChar> vis(src.size() + 1) while the in-code comment "
     "(:629) documents 'sized src.size()+1 but log2vis fills only src.size()' "
     "— one extra element per shaped string; the phantom-NUL FEED fix itself is "
     "correct (hb_buffer_add_utf32 fed exactly src.size() at :636/:683 per "
     "MG-085, commit dc69ca41); the scratch +1 is the legacy allocation the "
     "claim names — bounded, per-string, non-corrupting; fix (size "
     "src.size()) = plan item"),
    ("NEW-28", "Config→qualifier string reconstruction is lossy", f"{TAG}-REFUTED",
     "the qualifier string is a ONE-WAY human-readable DESCRIPTION by design "
     "(res_config.h:123 'human-readable qualifier string (b+en+US, 480dpi, "
     "sw360dp...)', arsc_parser.h:121/:152 config_desc fields); resource "
     "MATCHING never consults it — the best-config law compares the STRUCTURED "
     "ResTable_config fields (arsc_parser.cpp:644-666, 'qualified config beats "
     "default when the qualifier matches'; the isBetterThan law :348-353) — a "
     "lossy description cannot corrupt selection; the claim's practical impact "
     "is refuted, the lossiness itself is the documented description contract"),
    ("NEW-32", "Density-scale logic is duplicated between measure and draw",
     f"{TAG}-REFUTED",
     "the density-scale arithmetic is ONE pure law: bitmap_factory_density_law "
     "(bitmap_shadow.h, wrapper bitmap_shadow.cpp:257-268, applied at :373 "
     "'2) density-scale law (BitmapFactory.cpp native): applies iff "
     "in_density != 0'); the decode path feeds it the SHARED config source "
     "resources::device_config().density (:104/:307, G04 §4); the measure side "
     "reads the same config for a DIFFERENT law — the density-BUCKET selection "
     "(layout_inflater.cpp:2841 + the isBetterThan law :348-353) — distinct "
     "laws over one shared config, not duplicated arithmetic"),
]

with open(LOG, "w") as f:
    for rid, sel, cat, txt in STAMPS:
        f.write(f"[{cat}] {rid} (selector: {sel!r})\n      {txt}\n")

with open(CSV_PATH, newline="") as fh:
    rows = list(csv.DictReader(fh))
assert len(rows) == 234, f"registry rows = {len(rows)}, expected 234"

errors = []
for rid, sel, cat, txt in STAMPS:
    m = [r for r in rows
         if r["original_id"] == rid and sel in r["original_wording"]]
    if len(m) != 1:
        errors.append(f"{rid}: selector {sel!r} matched {len(m)} rows")
if errors:
    print("UNIQUENESS PRE-FLIGHT FAILED (no write):")
    for e in errors:
        print("  " + e)
    sys.exit(1)

_RES = re.compile(r"ALREADY-RESOLVED|DUPLICATE|RETRACTED|SUPERSEDED|PLAN-SWEEP")


def _open(r):
    s = r["source_check"]
    return ("S18-CLASS" in s
            and not any(t in s for t in
                        ("S18-LAW", "S18-DE-LAW", "S18-CONT-2", "S19-", "S20-"))
            and not _RES.search(s))


before = sum(1 for r in rows if _open(r))
hit = 0
for rid, sel, cat, txt in STAMPS:
    r = next(r for r in rows
             if r["original_id"] == rid and sel in r["original_wording"])
    if f"{TAG}-" in r["source_check"]:
        continue
    r["source_check"] += f" + {cat} 2026-11-21: {txt}"
    hit += 1

with open(CSV_PATH, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

left = [r["original_id"] for r in rows if _open(r)]
print(f"stamps applied: {hit} (defined: {len(STAMPS)}); open-before: {before}")
print(f"classified queue now: {len(left)} remaining")
print(f"settled: 234 - {len(left)} = {234 - len(left)}")
with open(LOG, "a") as f:
    f.write(f"\napplied: {hit}; open-before: {before}; remaining: {len(left)}; "
            f"settled: {234 - len(left)}/234\n")
