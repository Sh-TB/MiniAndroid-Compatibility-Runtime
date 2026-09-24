# S95 — GRAPHICS SOURCE LIBRARY → REAL APK VALIDATION (P0 EXECUTION WAVE)

Campaign: S95 · Role: Primary Coder · Date: 2026-09-24
Base: HEAD `e22f41d8` (S94 close) · Environment: container re-bootstrapped, toolchain
(aapt2 8.13.2 + ECJ + D8 + android-34) re-verified, APK cache SHA-pinned.

---

## §0 Directives honored

- **RECON before change.** S94 state was verified, not assumed: HEAD `e22f41d8`
  clean tree; `docs/GRAPHICS_SOURCE_REGISTRY.json` sha256
  `8b451a115e628edf2aad2b217023137379d9be4abd85813e9287a5ab5d0f6ba9`
  (127 entries / 122 distinct GitHub-verified repos, counts block intact);
  `tools/source_lookup.py` answers `WRONG_CLIP` with 6 sources + 6 laws
  (exit 0); CONSTITUTION_V2 §170 present (line 3668); S94 gap_map
  (`run/s94/source_mining/gap_map.json`) maps all 8 S93 failure titles.
  A partial pre-interruption S95 wave was discovered on disk (uncommitted at
  the time, later captured by the environment auto-commit `e22f41d8`): the
  Wave-A vector/adaptive-icon implementation, the capture harness
  (`scripts/s95_capture.py`), BEFORE captures for 11 titles and AFTER captures
  for 7. No S95 worklog entry and no validation report existed — this session
  closed the wave instead of restarting it.
- **Registry existence is not value.** Every claim below lands on a real
  executed APK with a measured before/after delta.
- **Failures are results.** Every hypothesis that did not survive is recorded
  with its rejection evidence (§3.5, §5).

## §1 The chain, exercised end-to-end (S94 → S95)

For every P0 fix the same chain ran; none of the steps was skipped:

```
failure taxonomy (S93)
  → tools/source_lookup.py <category>        (S94 §25 automatic consultation)
  → registry entry → pinned HEAD SHA         (repo identity, S94 §1)
  → upstream file (hash-evidenced fetch)     (license-checked reuse)
  → semantic law (L-S94-*/L-S95-*)           (named, testable)
  → engine implementation                    (LOC measured, §5)
  → fixture / battery stage                  (zero-skip gate)
  → real APK re-execution, same protocol     (before/after, §2)
  → fan-out measurement                      (§4)
```

## §2 Verification set and protocol

Protocol: `scripts/s95_capture.py` — the EXACT S92/S93 per-title execution
(frames, taps, resolution 1080×1920, `--execution-mode real-dalvik`, view-tree +
provenance + click-audit capture), plus a machine-readable capture record with
APK SHA256, screenshot SHA256/dimensions/graphics metrics, and the UNCHANGED
S93 semantic classifier (`scripts/s93_run_semantic.analyze_case`) for verdict
drift-proofing. Pins: `run/s95/apk_pins.json` (11 titles; 3 re-pinned honestly
after the container reset; 1 provenance ERROR corrected — the `a509db2a` pin in
gap_map.json belonged to `io.github.ebraminio.bouncy`, not the S92/S93 case
`com.dozingcatsoftware.bouncy`).

Rule: **same APK + same input + same capture protocol** before and after; the
"AFTER" sweep re-ran the complete set whenever the binary changed so that all
deltas measure the FINAL binary, never a mixture.

## §3 P0 results — auditable table

| Failure | Root Cause | Source | Law | Fixture | APK Targets | Improved | Controls | Regression | Status |
|---|---|---|---|---|---|---|---|---|---|
| WRONG_COLOR (hotdeath) | vector/state-list drawables + adaptive-icon layers never decoded; placeholder/blank surface | platform_frameworks_base (VectorDrawable / AdaptiveIconDrawable laws), pinned `1cdfff55` | L-S95-VECTOR-1, L-S95-ADAPTIVE-1 | battery s95_vector fixture (9 law checks, stage [44–46]) | hotdeath | hotdeath FAIL→**PASS** (screenshot SHA changed, luminance 239.5→55.5 = real content) | nounours/unote/gmdice PASS×3 | none observed | **DONE** |
| WRONG_COLOR (bouncy) | same vector gap for dialog icons/arrows | same | same | same | bouncy, urlchecker | bouncy: 3×WRONG_COLOR→**0**; urlchecker: 3×WRONG_COLOR→**0** | PASS×3 | none observed | **DONE** (per-asset) |
| WRONG_CLIP (bobball) | Button wrap_content missing Widget.Material.Button minHeight 48dip/minWidth 88dip — buttons measured 44 px, text ink touched node bounds (NOT a Canvas clip bug) | AOSP `core/res/res/values/styles_material.xml` @ `1cdfff55`, sha256 `10eca71aaa2b3e49f63a6aa8a8fbb1a533a1e925fe428999d023f6cf81bd0b07`; TextView.onMeasure suggested-minimum clamp | L-S95-BTNMIN-1 | inferred from real-APK layout dump (`aapt2 dump xmltree res/Jw.xml`: `layout_height=-2`) | bobball | bobball: 4×WRONG_CLIP→**0**, buttons 44→126 px (48dip @ 2.625 density), 6/6 text nodes TEXT_VISUALLY_VERIFIED; verdict FAIL→PARTIAL(0 fails) | PASS×3 | none observed (helloworld golden re-derived, §6) | **DONE** |
| WRONG_CLIP (dodge) | TWO stacked causes: (a) same BTNMIN gap on bottom-row button; (b) menu panel's weighted buttons each measured ~1645 px and laid out to y=6737 (off-screen), drawn over the field — LinearLayout weight distribution measure bug; status-row texts render flush-top (gravity/lines interplay) | LinearLayout.java measure law (weight = leftover/sum-weights) — registry L-S94-LAYOUT-* | L-S95-BTNMIN-1 (a); (b) **diagnosed, not implemented** | none yet for (b) | dodge | dodge: "Continue Free Play" 44→126 px (a) — measured; (b) open | PASS×3 | none observed | **PARTIAL** |
| ANIMATION_FROZEN (mini-tetris, minicraft) | **HARNESS, not engine**: S92/S93 tap (540,1500) hit NO touch target — the games never started (dispatchTouchEvent: "no touch target"); every frame identical | n/a (runtime interaction laws R-NEW-*/F-117 correct; START at (786,1854), DEMO at (925,1862) from view-tree) | capture-protocol law (input must target a real touch target) | corrected taps in `s95_capture.py` | mini-tetris, minicraft | mini-tetris **6 unique frames/24 ×3 deterministic runs** (piece falls, NEXT changes); minicraft world state advances (Blocks 0→2, house built) ×3; both verdicts FAIL→PARTIAL(0 fails) | PASS×3 | none | **OBSERVED** (original classification refuted with evidence; engine animation machinery CORRECT) |
| UNREADABLE_TEXT (simplestopwatch) | FOUR layers: (1) theme-less app given a WHITE window where AOSP default theme is DARK (Theme.DeviceDefault→Theme.Material→background_material_dark #ff303030) — FIXED; (2) theme textColorPrimary never applied to color-less text — FIXED; (3) fabricated blue fill under ImageButtons — FIXED; (4) the app's programmatic color-scheme application (BigTextView.onDraw + runtime setTextColor) never executes: `[C013-ONDRAW] dispatched=NO ops=0`, full-screen #f0f0f0 placeholder covers the UI — **NOT IMPLEMENTED** | themes_device_defaults.xml sha256 `33d335f2…`; themes_material.xml sha256 `8433052c…`; colors_material.xml sha256 `bc9097f3…` (@color/material_grey_850 = #ff303030); TextView default-textColor law | L-S95-DEFTHEME-1, L-S95-TXTCLR-1, L-S95-ICONBTN-1 | helloworld golden re-derived (§6); GATE H re-earned (§6) | simplestopwatch | window/theme/icon layers fixed (verdict still FAIL — failure taxonomy now PLACEHOLDER_CONTENT×2 + UNREADABLE_TEXT×2, root cause localized to one named gap) | PASS×3 | GATE H re-earned (§6) | **PARTIAL** (layers 1–3 DONE; layer 4 = named P1) |

### §3.5 Hypotheses raised and rejected (evidence recorded)

| Hypothesis | Rejection evidence |
|---|---|
| bobball/dodge WRONG_CLIP = Canvas/Skia clip-stack divergence (S94 §19 guess) | Pixel forensics: bobball descender ink lands exactly on the last pixel row of 44-px buttons that wrap_content-measured below the 48dip law; dodge's flagged texts sit on off-panel measure bugs. No clip-state divergence found at the draw sites. First divergence is in MEASURE, not clip. |
| Density mis-selection as the universal WRONG_COLOR root cause | bouncy/urlchecker color failures disappeared with vector/adaptive decoding; density selection was already law-driven (L-S94-DENSITY-1/2). Density was A cause, not THE cause. |
| mini-tetris/minicraft engine animation freeze | 3× deterministic re-runs with correct tap targets: 6 and 2 unique frames respectively; state A ≠ state B proven; the original "frozen" evidence was a harness tap miss. |
| simplestopwatch icon tint bug in the PNG decode path | The icons decode and place correctly (GATE H IoU 0.862/0.994 vs asset alpha); the color context is the app's unexecuted programmatic scheme. |

## §4 Fan-out analysis (measured, not projected)

```
candidate corpus (S93 failure map)   : 8 titles  + 3 controls
executed corpus (same protocol)      : 11/11     (2 titles re-pinned honestly)
affected corpus (state changed)      : 11/11 screenshots changed; 8/11 verdict/category deltas
improved corpus (failure count ↓)    :
    hotdeath        FAIL → PASS
    bobball         FAIL(4)  → PARTIAL(0)
    mini-tetris     FAIL(1)  → PARTIAL(0)   [harness refuted]
    minicraft       FAIL(1)  → PARTIAL(0)   [harness refuted]
    bouncy          FAIL(6)  → FAIL(1)
    urlchecker      FAIL(4)  → FAIL(4)      [composition changed: 3 color→0; floor-artifact flags documented]
    simplestopwatch FAIL(3)  → FAIL(4)      [taxonomy sharpened: 2 named fixes verified, 1 named gap open]
    dodge           FAIL(3)  → FAIL(3)      [1 of 2 root causes fixed, measured]
controls                              : 3/3 SEMANTIC_PASS before AND after (zero verdict drift)
```

Fan-out N for Wave A measured as **3 APKs fully cleared of WRONG_COLOR**
(hotdeath, bouncy, urlchecker) from 1 root cause; Wave B law fanned to
**2 APKs improved** (bobball full, dodge partial). The 57 identity-only
registry entries were NOT mined for this wave (directive honored).

## §5 S94 infrastructure value (Before S94 / With S94)

Machine-readable ROI record (committed as `run/s95/roi_record.json`):

| Metric | Value |
|---|---|
| source_lookup_calls (recorded) | 6 (WRONG_COLOR×2, WRONG_CLIP×2, ANIMATION_FROZEN×1, UNREADABLE_TEXT×1) |
| laws_consulted (registry IDs) | 11 (L-S94-CLIP-1/2, L-S94-NINEPATCH-1, L-S94-LAYOUT-1/2, L-S94-DENSITY-1/2, L-S94-DRAW-1, L-S94-GIF-4, L-S94-PNG-1, L-S94-DECODE-1) |
| upstream files fetched + hash-pinned this wave | 5 (styles_material.xml 10eca71a…, themes_device_defaults.xml 33d335f2…, themes_material.xml 8433052c…, colors_material.xml bc9097f3…, public.xml style-id decode) |
| new laws implemented | 4 this session (L-S95-BTNMIN-1, L-S95-DEFTHEME-1, L-S95-TXTCLR-1, L-S95-ICONBTN-1) + 4 pre-session Wave-A (L-S95-VECTOR-1, L-S95-ADAPTIVE-1, L-S95-BGSTRETCH-1, L-S95-STATELIST-1) |
| implementation LOC delta | ~1,200 (vector_decode 933 + engine/inflater/resolver wiring ~270) |
| APKs re-measured | 11 titles × before/after + 6 determinism runs (games) + battery 99 stages |
| time saved vs blank-editor | **NOT_MEASURED** (honest; no controlled baseline exists) |
| mis-investigations avoided by lookup | 1 recorded (clip-stack guess rejected in favor of measure-law evidence — §3.5) |

What the registry actually bought (evidence, not narrative): the WRONG_CLIP
lookup returned the CDroid/Skia/clip law family that made the non-clip
divergence VISIBLE (the semantic flags pointed at node bounds, the registry
laws pointed at measure semantics — the mismatch itself located the bug);
the BTNMIN law is a verbatim style-table transplant with a pinned SHA instead
of a guessed constant; the DEFTHEME/TXTCLR laws are table-driven from the
GENERATED framework_theme_attrs file (S68), so the fixes carry AOSP's numbers,
not invented ones.

## §6 Battery and golden status

- Full regression battery: **BATTERY GATE ALL PASS (99 stages)** on the final
  binary — including the S95 vector fixture (aapt2+ECJ+D8 real toolchain, 9
  law checks) and all 96 pre-S95 stages.
- **helloworld_golden re-derived** (26/26 PASS): the fixture was theme-less;
  under L-S95-DEFTHEME-1 a theme-less app now gets the AOSP DARK default
  window (#ff303030), so the light-designed fixture declares
  `@android:style/Theme.Material.Light` explicitly (what a real light app
  does) and pins its window through the same resolution chain. Zero-skip
  preserved (26 checks).
- **GATE H re-earned** (3 runs byte-identical; IoU 0.862/0.994 ≥ 0.85 with the
  corrected >148 separator; blue-fill assert inverted to `blue == 0` as an
  L-S95-ICONBTN-1 regression pin). The old blue>3000 assert encoded the
  fabricated engine fill; both re-derivations are documented inline in the
  battery script (G07-precedent rationale style).
- Determinism of the wave itself: all AFTER sweeps re-run per binary change;
  the final table (§3) is from the FINAL binary only.

## §7 Limits and next actions

1. **simplestopwatch programmatic scheme** (P1 candidate): execute app-level
   UI code paths — custom-view onDraw dispatch (`[C013-ONDRAW] dispatched=NO`)
   and programmatic setTextColor/setBackgroundColor application. Every
   remaining simplestopwatch flag reduces to this single named gap.
2. **dodge menu-panel measure bug** (P1): LinearLayout weight distribution
   measures each weighted child at the full leftover (~1645 px) instead of
   leftover/sum-weights; the panel also renders although the real app shows
   it only on menu-key press (view-visibility lifecycle from app code).
3. **urlchecker text-floor false positives**: `<`, `/`, `>` chevron glyphs are
   readable (visual evidence, white-on-dark) but fall below the S93 adaptive
   ink floor (0.0033/0.0016 < 0.004). NOT tuned here to avoid
   threshold-gaming; requires an OCR-grade glyph-truth check (S93 §table).
4. **Push status**: reported by the worklog ledger at close (LOCAL HEAD /
   REMOTE HEAD / AHEAD-BEHIND / PUSH STATUS) — no push claim without a
   verified remote.
