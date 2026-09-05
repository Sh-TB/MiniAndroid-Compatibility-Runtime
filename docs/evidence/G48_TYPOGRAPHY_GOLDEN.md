# G48 — FINAL TYPOGRAPHY GOLDEN — GOLDEN-01-EXTERNAL-HELLO-VISUAL

Campaign: MASTER VISUAL COMPATIBILITY CAMPAIGN · Date: 2026-09-06
Fixture: `EXT-01-HELLOWORLDSELFAWARE-1.1.0` (frozen, SHA-256
`009b4671…cc41`; APK + trusted reference re-fetched this session with
exact SHA-256 match after the sandbox corpus wipe — no substitution).
Head: this record committed together with the final evidence (see C6).

## Reference vs MiniAndroid

| | Source | SHA-256 / size |
|---|---|---|
| Reference | author-published phone screenshot (Rule 11 option 3; no emulator/KVM in this environment — recorded) | `121d479c…2ba5`, 600×1067 |
| MiniAndroid | `miniandroid_typography.png` (this commit) | `142238fd92b69e11d3407526de95cad29bf46e3f4191767d09a24379fbe0bbf2`, 1080×1920 |

Run command: `build/miniandroid run
/home/z/corpus/external_hello/HelloWorldSelfAware-1.1.0-android.apk -o <dir>`

## Rule 10 measurements (scripts/compare_ext01_typography.py,
typography_golden.json committed; NEVER a single whole-image number)

Per-line ink geometry:

| line | ref y0–y1 | ref h×w | mini y0–y1 | mini h×w |
|---|---|---|---|---|
| 1 | 406–431 | 26×209 | 729–773 | 45×367 |
| 2 | 486–511 | 26×385 | 867–911 | 45×672 |
| 3 | 562–586 | 25×386 | 1005–1049 | 45×673 |
| 4 | 637–669 | 33×329 | 1143–1200 | 58×576 |

(reference is 600px wide, MiniAndroid 1080px — compare relative values)

| Quantity | Reference | MiniAndroid | Δ |
|---|---|---|---|
| background (modal) | 0 (black) | 0 (black) | 0 |
| ink pixels (gray, >60) | 9,237 | 25,659 | n/a (scale²=3.24×) |
| block rel. width | 0.6433 | 0.6231 | 3.14% |
| block rel. height | 0.2474 | 0.2458 | **0.64%** |
| center x | 0.4992 | 0.5000 | 0.08% |
| center y | 0.5037 | 0.5023 | 0.14% |
| line spacing (median B2B/height) | 0.07076 | 0.07187 | **1.58%** |
| monospace advance (width/char, line 2) | 0.03208 | 0.03111 | 3.03% |

Baseline spacing detail: mini top_to_top [138,138,138] vs ref
[144,137,135] @1080-scale — middle/last gaps within 1–2px; the first gap
is +6px on the device (fm.top≠fm.ascent behavior) — recorded as the one
known, quantified residual; no constant was fitted to hide it.

## Dynamic-content handling

Text content is NEVER compared (device-specific ANDROID_ID / version /
API values differ by design: ref `9f225072a49defd4`/16/36, mini
`6f1c3a9d2e5b4780`/14/34). The dynamic values are the same character
LENGTH on both sides (20-char hex id; 1–2 digit numbers), so per-line
STATIC geometry (widths, bands, baselines) stays comparable — recorded in
the comparator docstring. Typography validation is not weakened: font,
size, advance, spacing, centering, color, background are all checked.

## Verdict

```
GOLDEN-01 TYPOGRAPHY GOLDEN: PASS (9/9 static checks)
```

1. background identical (black) — PASS
2. ink present — PASS
3. 4-line band structure — PASS
4. horizontal centering ≤3% — PASS
5. vertical centering ≤6% — PASS
6. text block width ratio ≤10% — PASS (3.14%)
7. text block height ratio ≤10% — PASS (0.64%)
8. line spacing ratio ≤10% — PASS (1.58%)
9. monospace advance ratio ≤10% — PASS (3.03%)

(Exceeds the 7/7 target; every check is a STATIC quantity.)

## Rule 12 determinism

3 independent runs (c5, detA, detB) → PNG byte-identical,
SHA-256 `142238fd92b69e11d3407526de95cad29bf46e3f4191767d09a24379fbe0bbf2`.

## BEFORE → AFTER (the G31 campaign input numbers)

| Quantity (rel.) | BEFORE | AFTER | Reference |
|---|---|---|---|
| text block width | 0.3843 | 0.6231 | 0.6433 |
| text block height | 0.0906 | 0.2458 | 0.2474 |
| line spacing (top-to-top) | 46px | 138px | 137–144px |
| font | DejaVu Sans (proportional, family attr dropped) | Droid Sans Mono 58px | Droid Sans Mono 22sp@420dpi |
| ink band heights | 28px | 45px | 46.8px @1080-scale |

## Regression battery at the final HEAD (all zero-skip)

- helloworld_golden validator: **26/26 ALL PASS** (AOSP line-height law
  changed default-sans pixels; the validator's structural checks hold —
  no golden re-baselining was needed)
- tictactoe_golden validator: **8/8 ALL PASS**
- MUTF-8 battery: **14/14 PASS**
- semantic: long_cmp 14/14 + switch_neg 25/25 + pass3_bridge 57/57 = **96/96**
- corpus (external APKs re-fetched by scripts/fetch_corpus.py, hash-verified):
  simplestopwatch / gmdice / microtimer — run status recorded in the
  battery transcript (see run_test_battery.sh stage [9])
- font_pipeline_probe @58px: PASS (0 bad glyphs) — committed output
- build: clean, no new warnings beyond the pre-existing set

## Claim discipline

- `visually-proven (typography)`: the EXT-01 external APK's text renders
  with the AOSP font family law, TextAppearance size law, FontMetrics and
  StaticLayout spacing laws on this HEAD, and the measured geometry
  matches the trusted phone reference within the tolerances above.
- NOT claimed: pixel-identity to the phone reference (device-dependent
  content + antialiasing), GOLDEN-02 interaction, shaping/bidi/non-ASCII
  compatibility (not exercised — queued).
