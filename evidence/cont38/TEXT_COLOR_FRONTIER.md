# CONT-38 — The Compose Text-Color Pipeline: the framework-color root
## F-NEW-300 — the package-routed color law (Resources.getColor / android:color/*)

Date: 2026-10-10 · Wave start: `11a6c2b9` (the CONT-38v verification push), binary `a181d7b317e015c8`
→ decode-diag binaries (env-gated only) → wave end: **`80d9ea341f1b6ccc`** (one generic fix, F-NEW-300).
Directive frame: probe first · frame-truth only · no app-specific branches · the anchor may move ONLY for an
explained semantic correction.

---

## 0. The CONT-37 checkpoint this wave owns

CONT-37 left composeStopwatch presenting its OWN first frame (`bbaf8f76308dc267`) with the three
StaticLayout texts at the app's positions/sizes — but every TextPaint carried **pipeline-default black**
(`0xff000000`), invisible on the dark surface. The recorded checkpoint: "the Compose draw-brush color
application ([F298-SETCOLOR]: the TextPaints carry pipeline-default 0xff000000; the brush→paint application
point is the LAST leg of text visibility)."

## 1. The decode chain (all field-ref-exact, no guessing)

The full executed path was decoded op-by-op (androguard + env-gated engine diags):

1. **`Lbe1;.b` (M3 Text composable)** — the textColor resolution: color-param → `TextStyle.color`
   (`Lue1;.b()J`) → `LocalContentColor` (`Lfm;.a`, read via `Lx30;.j` → `Ls90;.F` scope-map get →
   the SolidColor's packed J at [213]). The final fallback = SolidColor(Color.Black).
2. **`Luh;.b` (M3 Surface/AlertDialog provider)** — `LocalContentColor provides SolidColor(contentColor)`
   where contentColor = `Lqe;->a/b/c/d` ← the colorScheme (`Lei;`) ← **the scheme factory `Lgi;.e`**
   ← the app's `darkColorScheme(...)` (`AppActivity.h` calls it TWICE with colors from
   **`Lih1;.t(activity, resId)`**).
3. **`Lih1;.t`** = `Color(context.getResources().getColor(resId, theme))` — **the app's theme colors are
   `android:color/system_*` FRAMEWORK resources** (resids `0x01060060-0x010600c0` — the API-31+
   Material You dynamic-color entries; package byte 0x01).
4. **The packing ground truth** (verified against the androidx source): `Color(int) = (argb << 32)`,
   `toArgb = packed >>> 32`, **`Color.Unspecified.packedValue = 0x10`** (androidx Color.kt line 389:
   `UnspecifiedColor: ULong = 0x10UL`), the `Lzh;.f` static = `Color(0f,0f,0f,0f,ColorSpaces.Unspecified)`
   → slow path → low-6-bit colorspace tag 16 → **0x10**. The engine's materialization verified:
   `Lzh;.f = 0x10`, `Lzh;.b = 0xff00000000000000` — **the engine's color machinery is EXACT**.
5. **The painter chain** (`Lte1;.I`, byte-pc verified): pc=116 `sget-wide Lzh;.f` (hit, 0x10) →
   cmp vs 16 → the style color → Unspecified → pc=138 `sget-wide Lzh;.b` → `Lg6;.e(black)` →
   `Ld7;.d(black)` → `Paint.setColor(0xff000000)` — **all Compose-design-correct** — the app's own
   color never reached the style because **the theme that fed it was all-black**.

## 2. THE ROOT CAUSE (F-NEW-300)

`Resources.getColor(int, Theme)`'s law (the S54/F-080 handler) resolved every resid through the **APP
table only** (`rt.arsc().resolve_value`). The app's theme colors are **0x01-package (framework)
resources** — the app-table lookup misses every one, the R-field-name fallback misses, and the law
answered the historical fallback **`0xFF000000`**. The run log recorded it verbatim:

```
[RES] getColor resid=0x1060060 -> 0xff000000 (M3-COLOR-UNRESOLVED)   ×2
[RES] getColor resid=0x10600ba..0x10600c0 -> 0xff000000 (M3-COLOR-UNRESOLVED)  ×7 more
```

→ the app's `darkColorScheme(...)` materialized an **ALL-BLACK theme** → the Surface's
`LocalContentColor provides SolidColor(black)` → the M3 Text merged `style.copy(color = black)` →
the painter applied `setColor(0xff000000)` → **black text on the dark background — invisible**.
(The dark (13,15,18) background survived because the WINDOW background resolves through the theme-attr
machinery, which already routes framework references correctly.)

**The first point where the correct color was lost**: `Lih1;.t` → `Resources.getColor` → the
app-table-only resolve → the black fallback. Everything downstream executed faithfully.

## 3. The fix (one generic point, zero app knowledge)

`miniandroid/src/dex/dalvik_engine.cpp`, the `Resources.getColor` law: the resolve block now calls the
**S127 package-routed terminal-value law** `resolve_color_reference_argb(resid)` — which routes a
0x01-package resid through the **framework table** (`ArscRouter.fw`, the committed framework_res table)
with the `resolve_framework_file_color` ColorStateList fallback, and non-0x01 resids through the app
table exactly as before. AOSP law: `Resources.getColor` resolves through AssetManager2 for EVERY
package; the framework package is not special-cased to the app table.

## 4. PRE / POST evidence

**PRE** (binary `a181d7b317e015c8` + decode-diag binaries, default law):
- `[RES] getColor 0x106005e-0x10600c0 → 0xff000000 (M3-COLOR-UNRESOLVED)` ×9 distinct resids.
- `[F298-SETCOLOR]` TextPaints `0xff000000` (caller `Ld7;.d pc=31`); the frame `bbaf8f76308dc267` ×3:
  black-on-dark text, frame-truth verdict PARTIAL with invisible text.

**POST** (binary `80d9ea341f1b6ccc`):
- `[RES] getColor 0x106005e → 0xffb9cbff, 0x106005f → 0xff30436e, 0x1060060 → 0xff4c5e8b,
  0x1060061 → 0xfff9f8ff, ...` — the framework table's system_* values (the AOSP-honest static
  defaults for the dynamic-color entries).
- `[F298-SETCOLOR]` TextPaints `0xff30323a` ×3 (a real theme text color); the canvas paints
  `0xff4c5e8b` / `0xfffaf8fe` / `0xffb0b1bc` — **no black-default anywhere in the app's own palette**.
- The frame `3442d9a9dc0fa0f9` ×3 (deterministic): the pixel census is now dominated by the themed
  surface (150,148,152) + the accent (45,56,83) + **white text pixels (44,160)** — the app's text is
  VISIBLE with a real foreground/background distinction.

## 5. The probe (Phase 2 — built BEFORE the fix, per the mission)

`fixtures/colorpipe_probe` (package com.probe.cpipe, real aapt2/ECJ/D8) — 17 generic rows:
- **TR-01..TR-08**: the identity-keyed HAMT (the composition-local scope map's exact algorithm shapes —
  5-bit segments, key/sub masks, bitCount-indexed arrays, collision merges, depth-30 chains) — ALL PASS
  ×3 on both the pre-fix and post-fix binaries: **the engine's trie machinery is sound** (this
  eliminated the suspected provider-map root by proof).
- **SC-01..SC-05**: the provider-scope flow, identity-key discipline, identity-hashCode stability,
  the packed-color laws ((argb<<32)/(>>>32)/the 0x10 sentinel), the takeOrElse shape — ALL PASS ×3.
- **PC-01..PC-04**: `TextView.setTextColor` state preservation — **FAIL ×3 both binaries
  (`getCurrentTextColor` answers 0)** — a REAL gap recorded as the next checkpoint (TextView
  text-color state law; NOT fixed this wave — probe-first discipline, separate root).

The probe is wired into the standing battery (`w4_build_probes.sh` + `cont37_regression.sh` → `cpipe`).

## 6. Cross-app validation + regression gate (binary `80d9ea341f1b6ccc`)

- **Anchors 8/8 ×3 BYTE-IDENTICAL** (dooz `31ddd4d5b8e6d18e`, microtimer `da73010a37dd0189`, unote
  `4f1a9e4e8f64fae8`, gmdice `f3b483fe7b7cf51b`, opencalc `a976d2f9fb675cb3`, tttdeluxe
  `af6094295ecb50e3`, flappycow `13cf47464d9787f4`, g2048 `59ca152611c4622`) — **zero collateral
  drift**: none of the other anchors read framework color resources through this path.
- **composeStopwatch `bbaf8f76308dc267 → 3442d9a9dc0fa0f9` ×3** — the LEGITIMATE, analyzed movement
  (the semantic correction this wave exists to make; the pre-fix frame was black-on-dark invisible
  text — the frame-truth gate's "meaningful foreground/background distinction" now holds).
- **SimpleCalc ×3 rc=0 `7960bce447ac6d8f`** FULL SUCCESS retained (the non-Compose control).
- **The battery == CONT-28..37 records EXACTLY** (fcol 140/0 · f259 49/0 · f259g 84/7-known · f266 42/0 ·
  f268 96/0 · fnew253 147/0 · fnew286 10/0 · fnew289 28/0 · fnew252 56/0 · fnew290 56/0 · fnew291 56/0 ·
  fnew292 70/0 · fnew293 56/0 · fnew294 77/0 · fnew295 49/0 · fnew296 42/0 · fnew297 42/0 · fnew298 19/0
  · ckey 15/0) + **cpipe 13/4** (the 4 PC rows = the recorded next checkpoint).
- Dooz remained at its honest keep-empty white (its boot-budget root is PENDING from CONT-37, untouched).

## 7. Decode infrastructure added this wave (all env-gated, bounded, zero-drift)

`CallContext.caller` (plumbed through `try_shadow_dispatch` — the SETCOLOR/CDW diags now carry the
executing DEX caller), `[PAINTER]` (the painter instruction stream), `[COLOR-SGET-W]` (the color
statics with values), `[CLINIT-PATH]` (the class-init poison paths), `[SGET-UNRESOLVED]`, the
`MINIANDROID_TRIE_TRACE` class-list extension (the composition-local scope-map family), and the
`MINIANDROID_INSTANCEOF_TRACE` `Lky0;` target. All verified zero-drift (the frame hashes unchanged
with the traces on).

## 8. Line-by-line checklist

| # | Item | Status |
|---|---|---|
| 1 | Phase-0 state frozen (HEAD/binary/registry/evidence) | PASS |
| 2 | The full color pipeline decoded (Text → LocalContentColor → scheme factory → resource read) | PASS |
| 3 | Packing ground truth verified vs the androidx source (0x10 sentinel) | PASS |
| 4 | The engine's color statics verified (f=0x10, b=black — exact) | PASS |
| 5 | The HAMT probe (TR rows) — trie soundness proven ×3 both binaries | PASS |
| 6 | The scope/packing probe rows (SC) ×3 | PASS |
| 7 | The TextView color-state probe rows (PC) — the gap recorded | PARTIAL (next checkpoint) |
| 8 | The resource-color root proven ([RES] rows + the Lih1;.t decode) | PASS |
| 9 | F-NEW-300 implemented (one generic point: the package-routed law) | PASS |
| 10 | PRE/POST [RES]+[SETCOLOR] evidence | PASS |
| 11 | composeStopwatch ×3 (the new baseline, visible text) | PASS |
| 12 | Anchors 8/8 ×3 byte-identical | PASS |
| 13 | SimpleCalc ×3 rc=0 | PASS |
| 14 | The battery == the standing records + cpipe | PASS |
| 15 | Registry 608→609 (F-NEW-300, dedup-checked) | PASS |
| 16 | Commit + push | PASS |

## 9. Remaining unsupported semantics / next checkpoints

1. **`TextView.setTextColor`/`getCurrentTextColor` state law** (cpipe PC-01..04) — the widget-side
   text-color state (separate from the Paint path) — the next wave owns it (probe already standing).
2. **Brush/shader text** (`Lbo1;`/SolidColor-as-brush, `setShader`) — the solid-color path is now
   proven; the brush path stays honest-untested (the d7 brush fields exist; no failing consumer yet).
3. **The dynamic-color caveat** (honest scope note): the framework table answers the system_*
   static defaults; the DEVICE's dynamic palette (Material You wallpaper colors) is not implemented —
   the AOSP-honest static value is the correct engine answer for a static-table runtime.
4. **dooz boot budget** (PENDING from CONT-36/37) — untouched this wave.
