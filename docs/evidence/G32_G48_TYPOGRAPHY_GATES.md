# G32–G47 — FONT / TEXT / TYPOGRAPHY GATES RECORD

Campaign: MASTER VISUAL COMPATIBILITY CAMPAIGN
Date: 2026-09-06 · Final HEAD: see GOLDEN01 record (C6 commit below)
Fixture: `EXT-01-HELLOWORLDSELFAWARE-1.1.0` (frozen; APK + reference
re-fetched this session, SHA-256 match against the frozen record).
Companion: `G31_FONT_SOURCE.md` (font source), `G48_TYPOGRAPHY_GOLDEN.md`
(final visual comparison).

## G32 — FONT RESOLUTION TRACE — PASS (`verified`)

Chain on the final HEAD, with runtime evidence lines:

```
AXML android:fontFamily="monospace"          (from res/UD.xml, the variant
                                              the ARSC config law selects)
  → LayoutInflater parses attr               (layout_inflater.cpp "fontFamily")
  → ViewShadow::ViewNode::font_family = "monospace"
  → fonts::TextShaper::resolve_family()      (AOSP fonts.xml L253-255 law)
      → kFaceMonospace = runtime/data/fonts/DroidSansMono.ttf
  → FreeType face (index 0) at 58px
```

Runtime log:
```
[G46-TEXTAPPEARANCE] TextAppearance.Large textSize=22sp -> 58px (scaledDensity=2.625)
FONT_RESOLUTION source=SYSTEM family=monospace font=DroidSansMono.ttf (AOSP fonts.xml law)
```

Font file facts (`scripts/ttf_metrics.py` + `tests/font_pipeline_probe 58`,
full output committed as `external_hello_golden/font_pipeline_probe_58px.txt`):

| Field | Value |
|---|---|
| File | `miniandroid/runtime/data/fonts/DroidSansMono.ttf` |
| SHA-256 | `db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862` (= AOSP android-14.0.0_r50 **and** android-15.0.0_r2 **and** android-16.0.0_r2 copies — byte-identical) |
| Family / style | `Droid Sans Mono` / `Regular`, 895 glyphs, 1 face |
| unitsPerEm | 2048 |
| hhea | ascender 1900 (0.92773 em), descender −500 (0.24414 em), lineGap 0 |
| OS/2 | usWinAscent 1901, usWinDescent 483, typo 1567/−492/132, USE_TYPO_METRICS=0 |
| @58px FreeType | ascender 54.00, descender −15.00 (ceil law), max advance 35.00 |

**MiniAndroid-vs-Android font identity**: same family law, same font file,
same face index — proven by the byte-identical AOSP file across API 34/35/36
plus the G35 advance agreement below. NOT a different font (the pre-fix
runtime used DejaVu Sans — that divergence is fixed and evidenced).

## G33 — FREETYPE RASTERIZATION — PASS (`tested`)

`tests/font_pipeline_probe 58` (committed output) renders each probe glyph
through the real FreeType pipeline and records bitmap bounds + raster
dimensions, e.g.:

| Char | gid | advance | lsb | ink (w×h @ dx,+dy) |
|---|---|---|---|---|
| h | 73 | 35.00 | 4.00 | 27×44 @ +4,−44 |
| e | 70 | 35.00 | 3.00 | 29×33 @ +3,−32 |
| l | 77 | 35.00 | 5.00 | 26×44 @ +5,−44 |
| o | 80 | 35.00 | 3.00 | 29×33 @ +3,−32 |
| w | 88 | 35.00 | −1.00 | 36×31 @ −1,−31 |
| r | 83 | 35.00 | 7.00 | 23×32 @ +7,−32 |
| d | 69 | 35.00 | 3.00 | 28×45 @ +3,−44 |
| H | 41 | 35.00 | 3.00 | 28×41 @ +3,−41 |
| E | 38 | 35.00 | 6.00 | 24×41 @ +6,−41 |
| digits 0-9 | 17-26 | 35.00 | — | uniform monospace advance |

Anti-aliased (FT_RENDER_MODE_NORMAL, 8-bit coverage) — matches the
reference screenshot's antialiased grayscale ink.

## G34 — GLYPH LOOKUP — PASS (`tested`)

`FT_Get_Char_Index` resolves every EXT-01 charset codepoint (lowercase,
uppercase, digits, apostrophe, period, comma, space, exclamation) to a
non-zero gid — `PROBE RESULT: PASS (0 bad glyphs)`. No replacement
characters, no code-unit corruption (the string arrives via the hardened
MUTF-8 pool decoder + DEX string handling, battery below).

## G35 — GLYPH METRICS — PASS (`verified`)

Advance/bearing/bbox table above (G33). Android-reference agreement:
monospace advance measured from the reference screenshot (line 2, 20
chars): 0.03208 of image width/char vs MiniAndroid 0.03111 → **3.03%**
difference (G48 check). The pre-fix state was 0.3843 vs 0.6433 block
width with a proportional face — the font identity + size + metrics now
agree within measurement noise of a 600-px-wide reference.

## G36 — FONT METRICS LAW — PASS (`verified`)

Laws transferred (AOSP `frameworks/base@android-14.0.0_r50`):

1. **Paint.FontMetrics** (Paint.java / Paint.cpp JNI):
   - `ascent`/`descent` = single-spaced box = FreeType size metrics
     (hhea-scaled; USE_TYPO_METRICS honored — matches hb/AOSP behavior),
     ints CEILed in magnitude (Paint.cpp SkScalarCeilToScalar).
   - `top`/`bottom` = maximum extents = OS/2 usWinAscent/usWinDescent,
     never tighter than ascent/descent.
   - `leading` = bottom − descent + top − ascent (0 for this font).
2. **Paint.getFontMetricsInt(null)** = descent − ascent
   (TextView.getLineHeight L2623 uses this).
3. **elegantTextHeight** (TextView L4485 → Paint.setElegantTextHeight):
   the font's own hhea box becomes the font-padding extents. NOTE: the
   AOSP AssetManager2 version law selects the **v16** layout variant for
   EXT-01 (see G47 note) which does NOT carry elegantTextHeight — so the
   attribute is parsed+implemented but NOT exercised by this fixture
   (`status: implemented; not exercised by primary fixture`).

## G37 — BASELINE — PASS (`verified`)

Baseline law (StaticLayout.java out() L1246 + draw):
`baseline_k = v_k + |above_k|`, `v_{k+1} = v_k + (below_k − above_k) + extra_k`.
`above` = |fm.top| for the first line (includeFontPadding=true, the
TextView default) else |fm.ascent|; `below` = fm.bottom on the last line.
Vertical gravity centers the LAW-COMPUTED block (sum of line boxes).
No pixel offsets were added anywhere. Measured baseline agreement in G48.

## G38 — FALLBACK — `not exercised by primary fixture`

The EXT-01 charset is fully covered by Droid Sans Mono (G34: 0 notdef).
The fallback chain (system fallback face + NotoColorEmoji CBDT) exists in
TextShaper and was exercised by earlier campaigns, but no externally
sourced glyph outside the primary font was required for this gate.
Recorded as a queued follow-up fixture, NOT claimed.

## G39 — UTF-8 / UNICODE — PASS (`tested`)

The rendered string travels: APK resources.arsc (MUTF-8 pool) →
`getString(resid, formatArgs)` → DEX StringBuilder/format engine →
TextView → text engine → glyphs → PNG. The full 4-line string with the
`\n` separators renders correctly (G48 band structure), MiniAndroid's own
device values (deterministic ANDROID_ID `6f1c3a9d2e5b4780`, "14", "34")
flow through the SAME path. MUTF-8 battery 14/14 (below). Non-ASCII path
is G43 (below).

## G40 — MIXED CASE — PASS (`measured`)

Lowercase (hello world…) and uppercase (…) glyph metrics both dumped by
the probe (G33 table: h/e/l/o/w/r/d + H/E/L). Line-1 ("hello world",
11 chars) relative ink width: ref 0.3483 vs mini 0.3398 (2.4%).

## G41 — DIGITS — PASS (`runtime-proven`)

The rendered digits come from the runtime's OWN device identity (not
hard-coded): `[EXP092-RENDER] text="hello world\ni'm 6f1c3a9d2e5b4780\na
version 14 android\nwith api level 34"` — ANDROID_ID (16 hex digits),
SDK release, API level all from the seeded `Build.VERSION` /
`Settings.Secure` laws (FIX-2 of the EXT-01 session). Digit glyph metrics
uniform 35.00px advance (G33).

## G42 — PUNCTUATION / WHITESPACE — PASS (`measured`)

Apostrophe U+0027 gid 10, period U+002E gid 15, comma U+002C gid 13,
space U+0020 gid 1 (advance 35.00, no ink) — probe table. Space advance
= 35.00px = one monospace cell (line widths include all separators;
G48 width checks pass).

## G43 — NON-ASCII — `not exercised by primary fixture`

EXT-01 renders ASCII only. No external fixture with a non-ASCII codepoint
was required for GOLDEN-01; queued as a separate fixture gate (not
claimed, not skipped silently).

## G44 — SHAPING — `implemented; not exercised by primary fixture`

HarfBuzz shaping IS in the live path (FriBidi → HarfBuzz → FreeType) and
shaped the four real lines (probe section "live pipeline shaping": glyph
counts 12/21/21/18, widths 313/658/586/470 @58px through the LIVE
TextShaper, notdef=0). But a plain-Latin monospace string does not
require complex shaping — per the gate discipline this is NOT claimed as
shaping compatibility. A shaping-required external fixture is queued.

## G45 — BIDI — `implemented; not exercised by primary fixture`

FriBidi first-strong base direction + visual reorder runs on every
string (rtl_base=0 for the EXT-01 lines). No RTL/foreign-direction text
in the fixture — not claimed. External RTL fixture queued.

## G46 — TEXT SIZE — PASS (`verified`) — THE PRIMARY BLOCKER

Full chain, each step evidenced:

| Step | Law | Value |
|---|---|---|
| Layout attr | AXML (APK bytes) | `textAppearance=@android:style/TextAppearance.Large` (0x01030042), NO `android:textSize` |
| Style law | styles.xml@android-14 L862-864 | `TextAppearance.Large` → **textSize 22sp** |
| TextView law | TextView.java L4346/L4470 | appearance textSize applies (no explicit size on the view) |
| Unit law | TypedValue.complexToDimensionPixelSize | px = (int)(22 × scaledDensity + 0.5) |
| Density | DeviceMetrics (Pixel-class 1080×1920 @ 420dpi) | scaledDensity = 2.625 × fontScale 1.0 |
| Result | runtime log | **`[G46-TEXTAPPEARANCE] TextAppearance.Large textSize=22sp -> 58px (scaledDensity=2.625)`** |

Cross-validation against the reference (independent of the law): measured
reference em ≈ 57.5px @1080-scale (monospace advance ÷ 0.60205 em-ratio)
vs 58px law result — 0.9% apart. The root cause of the original
discrepancy was NOT an SP-conversion bug (SP→px was already correct for
explicit sizes) — it was the **missing TextAppearance resolution**: the
renderer fell back to 14dp×2.625 = 36.75px with a proportional face.

## G47 — LINE SPACING — PASS (`verified`)

Laws transferred:
- TextView.java L1473/L1477: `lineSpacingExtra` = dimension px,
  `lineSpacingMultiplier` = float (APK AXML: FLOAT 0x40000000 = 2.0).
- TextView.java L1440: includeFontPadding default TRUE.
- TextView.java L2623: `getLineHeight() = round(getFontMetricsInt(null) ×
  mult + add)`.
- StaticLayout.java out() L1236-1259: per-line
  `extra = (below − above) × (mult − 1) + add` for non-last lines;
  `v += (below − above) + extra`; first/last line font-padding swaps.
- AssetManager2/ResourceTypes version law (android-14.0.0_r50
  ResourceTypes.cpp L2489-2501 + AssetManager2 FindEntryInternal): the
  AOSP-faithful runtime inflates the **v16** layout variant of EXT-01 —
  aapt2 dump ground truth: `() res/v9.xml, (v16) res/UD.xml,
  (v21) res/02.xml`. The v16 variant carries fontFamily + multiplier 2.0
  (elegantTextHeight only exists in the v21 variant, which the version
  law does not reach).

Measured (G48 JSON): MiniAndroid baseline-to-baseline 138px @1080-scale
vs reference 137/144 (middle/last gaps agree within 1px; the reference's
first gap is +6px = the device's fm.top≠fm.ascent behavior — quantified
as a known deviation; MiniAndroid's top==ascent for this font because
usWinAscent(1901)≈hhea(1900)). Line spacing median ratio differs 1.58%.
No tuned constants.

## Commits (this gate group)

| Commit | Content |
|---|---|
| `d2d4469a` | G31/G32 diagnostics (APK AXML dumper, TTF metrics parser, typography measurement, FreeType probe) |
| `ea51d96a` | G32 font resolution (DroidSansMono + family law + ARSC version law) |
| `598e2432` | G36/G37 FontMetrics + line-box law |
| `b9e6e66f` | G46 TextAppearance.Large 22sp law |
| `98794ed0` | G47 line-spacing law plumbing |

## Regression status at final HEAD

See `G48_TYPOGRAPHY_GOLDEN.md` § Regression (battery + corpus + EXT-01).
