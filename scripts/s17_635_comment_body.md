**S17 — #632 focused laws (AUD-54 phase 2): 14 pinning laws over the inflater decode layer, 14/14 PASS, negative-mutation checked, law battery 43/43 PASS rc=0; 11 more rows settled (114/234 total; queue 131 → 120)**

**1. What was tested.** S16 settled *which* claims are mechanically checkable; S17 pins the
claims themselves with executable laws. `tests/s17_focus_laws_test.cpp` drives the layer no
earlier test covered end-to-end — the inflater DECODE layer (attribute → node flag/px) — by
feeding hand-built AxmlElements through the real `LayoutInflater::inflate_element` (moved
private→public for the law battery; behavior unchanged) and `measure_layout`. No APK needed.

| law | finding | result |
|---|---|---|
| R2 dp/px/dip | L3/M1 | 20dp→53px (density 2.625, round-half-away, ONE multiplication), 8px pass-through, 12dip→32 (once-dead `dip` suffix decoded) |
| R3 sp | M2 | 10sp @font-scale 1.3 → 34px — sp uses scaledDensity; **S16's M2 "still live" mark CORRECTED** (literal-grep miss: code says `scaled_density`) |
| W1 weights | E3 | weight-0 MATCH_PARENT measures parent width, NOT weighted-as-1 — **claim refuted**; sole weight-1 0dp child takes the full 1080 excess (AOSP §9 port confirmed) |
| A1 attr drops | NEW-33/35/37 | paddingStart/clipChildren/alpha/translationX/useDefaultMargins all dropped AND `stats.warnings` stays EMPTY — silent vanish pinned |
| G1 both-anchors | D2 | alignParentTop+Bottom → EXACTLY anchor span (top=0, h=1920, lp height overridden) — the 0x30&0x50 mask-overlap defect does **not** reproduce on the live inflater path |
| F1 forward ref | G3 | dependent inflated before its anchor resolves via the Kahn order — B.left == A.right == 300 |
| R1 decode | G2/G4 | alignParentBottom+centerHorizontal flags coexist; toRightOf name captured (decode layers pinned; position laws queued) |

**2. Harness integrity.** Negative-mutation check: three pins flipped (53→54, 34→35,
1080→1079) → exactly 3 FAILs → reverted → 14/14 PASS. One rig lesson is recorded in the
evidence: element names must be the real short XML tags — full descriptors bypass the
KNOWN-tag map and degrade to generic View, which produced the two early false readings.

**3. Battery.** Registered in TEST_LAW; law battery re-run: `BATTERY SUMMARY: total=43
passed=43 failed=0` rc=0 (RAW_LOGS/s17_focus_laws_2026-11-20.log, incl. the s17
self-report appendix). First battery attempt hit ENOSPC (100% disk) mid-link; the two
regenerable untracked build-output trees (build_fast, build_p2b — sizes already archived in
the A1 finding evidence) were removed to free 3.2 GB; build_w24_cand_a (AUD-51 evidence)
untouched. MASTER_AUDIT §1 item 15 added; §4 114/234; ledger untouched at 64 rows,
validator PASS.

**Remaining open (unchanged):** 120 runtime-behavior claims still NO-CITE (gravity-table
laws at the shadows layer, nine-patch, font metrics, SQL shadow contract, golden-image and
Robolectric harnesses) — several depend on the missing original APKs (#597/#618/#623);
coder-local artifacts (#634 MG-012, #295/#296/#297, RC-12, #630/#631); AUD-10b/42; PR #626
close decision (SUPERSEDED-IN-FULL classification public).
