# GOLDEN-01-EXTERNAL-HELLO-VISUAL — gate record (EXT-01 HelloWorldSelfAware)

Campaign: MASTER VISUAL COMPATIBILITY CAMPAIGN · Date: 2026-09-05
Current HEAD at record: (pre-commit; fixes below are being committed together)
Fixture: `EXT-01-HELLOWORLDSELFAWARE-1.1.0` (see EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md)

## Gates traversed this session

| Gate | Capability | Status | Evidence |
|---|---|---|---|
| G01 | External APK selected (2 candidates inspected) | PASS | fixture doc §G01 |
| G02 | Real APK artifact downloaded + SHA-256 | PASS | `009b4671…cc41`, 120,512 B |
| G03 | Authenticity (ZIP/AXML/ARSC/DEX/badging) | PASS | fixture doc §G02/03 |
| G04 | Upstream provenance (repo/tag/commit) | PASS | v1.1.0 → `9526576` |
| G05/06 | Trusted reference (no emulator/KVM here → Rule 11 option 3: author-published phone screenshot) | PASS (recorded honestly) | `reference_phone.png` |
| G07 | Fixture frozen | PASS | fixture doc §G07 |
| G08 | Untouched-HEAD baseline | **FAIL (honest)** — white/black-band default screen, empty text | `baseline_g08_broken.png` |
| G09–G14 | ZIP/manifest/ARSC load (real APK) | PASS | `[U007-RES] named_ids` logs; aapt2 badging cross-checked |
| G17 | Layout resolution | PASS (after FIX-1) | `[U007-INFLATE] root_id=4 views=1` |
| G21–G24 | onCreate → setContentView → findViewById | PASS (after FIX-1) | run log |
| G25 | setText(resource, formatArgs) | PASS (after FIX-2/3) | `[EXT01-CTXGETSTR] → "hello world\ni'm 6f1c3a9d2e5b4780\na version 14 android\nwith api level 34"` |
| G27 | Deterministic trace/compare | PASS | 3 runs byte-identical |
| G30 | No-bypass verification | PASS | real APK bytes only; JSON sidecar ABSENT (`resource_values.json loaded=false`); chain proven by per-layer logs |
| G49 | Background (theme windowBackground) | PASS (after FIX-4) | `[EXT01-WINBG] windowBackground=@0xff000000 rgb(0,0,0)` |
| G50/G58 | Surface + centering | PASS | text block center (540.0, 961.5) on 1080×1920 |
| G63 | Pixel golden vs reference | **STRUCTURAL 6/7** | `structural_comparison.txt` |
| G46/G47 | Text relative size + line spacing | **FAIL (documented)** | width ratio 0.383 vs 0.642; band height 1.4% vs 2.34% — NEXT GATES |

## 2026-09-06 UPDATE — G31–G48 CLOSED (typography campaign)

The typography gates above (G46/G47 FAIL) are now CLOSED. Full records:
`G31_FONT_SOURCE.md`, `G32_G48_TYPOGRAPHY_GATES.md`, `G48_TYPOGRAPHY_GOLDEN.md`.

| Gate group | Status | Root causes fixed (all law-based, no tuned constants) |
|---|---|---|
| G31/G32 | PASS | fontFamily="monospace" was parsed by NOTHING → AOSP fonts.xml law + DroidSansMono.ttf (byte-identical to AOSP API 34/35/36) + ARSC version-qualifier law (device config size=0 gated the whole isBetterThan body off; apk_path_for ignored config matching entirely) |
| G33–G35 | PASS | FreeType raster/glyph/metrics evidence via committed probe output |
| G36/G37 | PASS | ad-hoc "+5% leading" and "size×1.2" replaced by Paint.FontMetrics + StaticLayout line-box laws |
| G39–G42 | PASS | digits/punct/whitespace/mixed-case measured on the real render path |
| G43–G45 | `not exercised by primary fixture` (implemented; queued fixtures) | — |
| G46 | **PASS** | TextAppearance.Large (22sp) was unhandled → renderer default 14dp; now 22sp→58px via TypedValue rounding law |
| G47 | **PASS** | lineSpacingMultiplier=2.0/elegant/includeFontPadding parsed + StaticLayout extra law plumbed to measure AND draw |
| G48 | **PASS 9/9 static checks** | `compare_ext01_typography.py`; determinism 3 runs byte-identical `142238fd…` |

GOLDEN-01 status: **PASS (typography closed)** — 9/9 static visual checks,
dynamic device values excluded by design. Regression at the same HEAD:
helloworld 26/26, tictactoe 8/8, MUTF-8 14/14, semantic 96/96, corpus
(simplestopwatch/gmdice/microtimer) SUCCESS, battery 16/16 stages.

## Root causes found by this external APK (all real bugs, Rule 5 independent reproduction)

### FIX-1 — DEX `encoded_value` size law (dex_parser.cpp) — CRITICAL SPEC BUG
`value_arg` is "byte count − 1" (AOSP art/libdexfile). All fixed-width
readers read `size_arg` bytes instead of `size_arg+1`, dropping the top
byte of every 4-byte int constant: app R constants `0x7f030000`
(layout), `0x7f020000` (id), `0x7f050001` (string) parsed as `0x030000`,
`0x020000`, `0x050001`. Name-mediated lookups stayed self-consistent
(masking the bug for in-house fixtures); every ID-mediated lookup broke:
setContentView → `root_id=0 views=0`, findViewById → null. Fixed
VALUE_BYTE/SHORT/INT/LONG/STRING (+ unknown-type skip). Evidence: SGET
log values changed `327681 → 2131034114 (0x7f050002-class)`; inflation
`views=0 → views=1`.

### FIX-2 — virtual device identity statics (dalvik_engine) 
`Build.VERSION.SDK_INT/RELEASE`, `Build.*`, `Settings.Secure.ANDROID_ID`
were unseeded (read 0/null). `AndroidInfo.getId()` took the pre-O
`Build.SERIAL` branch (SDK_INT=0 < 26) → "i'm null". Seeded honestly
(SDK_INT=34/RELEASE="14" matching the android-34 stub toolchain;
deterministic ANDROID_ID `6f1c3a9d2e5b4780`), insert-if-absent so real
`<clinit>` always wins. `Settings$Secure.getString` + `getContentResolver`
handlers added (AOSP laws).

### FIX-3 — Context/Activity.getString(int, Object…) (dalvik_engine)
`Activity.getString` had NO handler (Activity not matched by the
Application/Context/ContextWrapper bridge) → 8 failed shadow-dispatch
attempts → setText received "". Handler extended per AOSP inheritance law
(Activity → ContextThemeWrapper → ContextWrapper → Context; getString is
FINAL on Context) and now applies formatArgs through the ONE canonical
format engine (`java_format_walk`, extracted verbatim from the CYCLE-E
String.format handler — REUSE-FIRST, no second implementation).

### FIX-4 — theme windowBackground (manifest_reader + arsc_parser + resource_runtime + renderer)
Chain: manifest `android:theme(0x01010000)` → style bag (ARSC
ResTable_map keys now RETAINED — parser previously discarded them) →
`android:windowBackground(0x01010054)` → `@color/colorPrimary` → #000000
painted behind content (AOSP PhoneWindow law). Without it the white text
was invisible on the white default surface (352 anti-alias pixels at
254,254,254). Attr ids verified from `aapt2 dump` ground truth, not
memory.

## Rule 10 pixel comparison (structural — device content differs, recorded)

`structural_comparison.txt`: background identical black; 4-line ink-band
structure identical; horizontal centering exact (540.0/1080 vs 299.5/600);
vertical centering within tolerance; ink present. NOT yet matching:
relative text size (0.383 vs 0.642 screen-width fraction) and line
spacing — font pipeline gates G31–G48 queued next.

## Rule 12 determinism

3 independent runs (g49_run2, det_a, det_b) → screenshot.png byte-identical,
SHA-256 `65f6980b65120b1895f8219378f1586a11f1de6e528b2902b495d7e56d7a89be`
(1080×1920).

## Regression battery at this HEAD (all zero-skip)

- helloworld_golden validator: **26/26 ALL PASS** (golden SHA `87820741…` unchanged)
- tictactoe_golden validator: **8/8 ALL PASS**
- MUTF-8 battery: **14/14 PASS**
- semantic: long_cmp 14/14 + switch_neg 25/25 + pass3_bridge 57/57 = **96/96 PASS**

## Claim discipline

- `runtime-proven`: external APK → manifest → ARSC → AXML layout → DEX →
  View tree → theme background → font render → PNG, on this HEAD.
- `visually-proven (structural)`: background/colors/centering/line
  structure match the trusted reference; typography size/spacing still
  open (G31–G48). NOT claimed: pixel-identity to the phone reference
  (different device content + typography gap), GOLDEN-02 interaction.
