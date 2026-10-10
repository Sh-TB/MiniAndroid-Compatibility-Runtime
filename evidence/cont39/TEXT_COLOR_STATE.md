# CONT-39 — The TextView Color-State Law (F-NEW-301)

**Binary**: `111340a583d48d92` (base: CONT-38 `80d9ea341f1b6ccc`)
**Probe**: `fixtures/colorpipe_probe` (com.probe.cpipe, real aapt2/ECJ/D8 toolchain, 17 rows) — rows PC-01..04, the checkpoint recorded by CONT-38.

## 1. The recorded face (CONT-38 checkpoint)

The colorpipe probe's TR/SC rows (the Compose-side color pipeline: the
identity-keyed HAMT scope-map shapes, the provider-scope flow, the packed
Color law, takeOrElse) passed ×3 from the day they were written. The PC
rows — TextView.setTextColor(int) → getCurrentTextColor() state
round-trip — failed ×3 deterministically:

```
PC-01|FAIL|explicit non-black getCurrentTextColor=0
PC-02|FAIL|explicit black preserved
PC-03|FAIL|alpha preserved=0
PC-04|FAIL|color change between draws ok
```

The value 0 is the typed-default int stub's answer — not the setter's
state, not the renderer's default.

## 2. Decode (op-level, trace-proven)

The setter side was ALREADY faithful. The run log of every PRE run shows
the ViewShadow `setTextColor` law (M3 FIX-M3-005b + ADDITIONAL-AUDIT
P1-10 provenance) firing with the EXACT argb values, including PC-04's
recolor:

```
[M3-SETTEXTCOLOR] view_id=823 color=0xff3366cc provenance=EXPLICIT_RUNTIME (prev=0x0 prov=0)
[M3-SETTEXTCOLOR] view_id=826 color=0xff000000 provenance=EXPLICIT_RUNTIME (prev=0x0 prov=0)
[M3-SETTEXTCOLOR] view_id=828 color=0x80ff8800 provenance=EXPLICIT_RUNTIME (prev=0x0 prov=0)
[M3-SETTEXTCOLOR] view_id=831 color=0xffff0000 provenance=EXPLICIT_RUNTIME (prev=0x0 prov=0)
[M3-SETTEXTCOLOR] view_id=831 color=0xff00ff00 provenance=EXPLICIT_RUNTIME (prev=0xffff0000 prov=2)
```

The GETTER side had no law anywhere in the engine — `rg
'getCurrentTextColor' src/` = zero matches pre-fix. Every call fell
through all shadows to the typed-default int stub and answered 0.

AOSP law (TextView.java): `getCurrentTextColor()` returns
`mCurTextColor` — the color the view's text actually paints with.
`setTextColor(int)` sets it to EXACTLY the argument
(`mTextColor = ColorStateList.valueOf(color); updateTextColors();` →
`mCurTextColor = mTextColor.getColorForState(getDrawableState(), 0)` =
`color` for a value-of list), preserving alpha.

## 3. Fix (ONE generic point)

The ViewShadow gains the `getCurrentTextColor` law immediately after the
`setTextColor` law (same file, same state store):

- node exists && `text_color != 0` → answer `text_color` (covers BOTH
  `EXPLICIT_RUNTIME` and `STYLE_RESOLVED` provenance);
- else mirror the RENDERER's default law EXACTLY as
  `view_renderer draw_text_into` applies it: `text_color == 0` → opaque
  black `0xFF000000`; Button-label (non-ImageButton) → white
  `0xFFFFFFFF`. Getter state and rendered pixels cannot diverge.
- A getter never creates render nodes (`find_node` only).
- The ColorStateList variant's default-color resolution stays the
  recorded draw-time gap (`text_color_state_object` has no failing
  consumer; NOT value-guessed in the getter).
- Env-gated `MINIANDROID_TEXT_COLOR_TRACE` diag `[F-301-GETTEXTCOLOR]`.

Build config: `android_shadows.cpp` hit the cc1plus `-g` OOM peak during
this wave's build (dmesg: kill at ~936 MB RSS) — the CONT-37 per-file
`-g0` Makefile precedent extended to this TU (same `-O2`, debug sections
dropped).

## 4. PRE / POST ×3 both binaries

| Run | Binary | Result |
|-----|--------|--------|
| PRE r1..r3 | `80d9ea341f1b6ccc` | 13/4 — PC-01..04 FAIL (`getCurrentTextColor=0`) |
| POST r1..r3 | `111340a583d48d92` | **17/0 — PC-01..04 PASS** |

POST PC rows:

```
PC-01|PASS|explicit non-black getCurrentTextColor=ff3366cc
PC-02|PASS|explicit black preserved
PC-03|PASS|alpha preserved=80ff8800
PC-04|PASS|color change between draws ok
```

(TR-01..08 + SC-01..05 unchanged PASS on both binaries.)

## 5. Full regression gate at `111340a583d48d92`

- anchors 8/8 ×3 BYTE-IDENTICAL: dooz `31ddd4d5b8e6d18e`, microtimer
  `da73010a37dd0189`, unote `4f1a9e4e8f64fae8`, gmdice
  `f3b483fe7b7cf51b`, opencalc `a976d2f9fb675cb3`, tttdeluxe
  `af6094295ecb50e3`, flappycow `13cf47464d9787f4`, g2048
  `59ca1526611c4622`.
- composeStopwatch ×3 `3442d9a9dc0fa0f9` MATCH (the F-NEW-300 themed
  frame retained byte-exactly — the law does not touch the Compose path).
- battery == CONT-28..38 records EXACTLY (fcol 140/0, f259 49/0, f259g
  84/7-known, f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289
  28/0, ckey 15/0, fnew252 56/0, fnew290 56/0, fnew291 56/0, fnew292
  70/0, fnew293 56/0, fnew294 77/0, fnew295 49/0, fnew296 42/0, fnew297
  42/0, fnew298 19/0 KEEP=5 corner=PASS) + **cpipe 17/0** (was 13/4).
- SimpleCalc ×3 rc=0 `7960bce447ac6d8f` FULL SUCCESS retained.

**ZERO DRIFT anywhere.**

## 6. Honest bounds

- `getTextColors()` (the ColorStateList object getter) and the CSL
  default-color draw-time resolution remain honest untested scope.
- The law covers the View/ViewShadow path; the Compose path's color
  resolution is F-NEW-300's package-routed law (its frame is byte-stable
  through this wave, proving non-interference).
