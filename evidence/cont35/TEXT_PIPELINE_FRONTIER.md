# CONT-35 — Text-Pipeline Frontiers: F-NEW-294/295/296
# The Typeface / Alignment / LineBreakConfig laws — three roots, one chain,
# composeStopwatch text pass UNBLOCKED (all uncaught text-pass NPEs dead)

Wave: CONT-35 (user directive: ادامه). Predecessor: evidence/cont34
(VIRTUAL_PATH_FRONTIER.md, checkpoint pinned this wave's targets). This wave:
(1) root-caused and fixed the f141-null-recv at Lk6;.<init> pc=409 to the
missing AOSP Typeface static law (F-NEW-294), (2) root-caused and fixed the
next face (ARR-LEN-NULL at Ljd1;.<clinit> pc=6) to the Layout$Alignment
enum-table gap (F-NEW-295), (3) root-caused and fixed the third face
(f141-null-recv at Lb1;.n pc=0) to the LineBreakConfig$Builder object-law gap
(F-NEW-296), (4) probe-proven ALL THREE roots ×3 in BOTH directions,
(5) the target's text pass now completes with ZERO uncaught text-pipeline
exceptions (only the 3 faithful deferred faces + the F084 budget halts remain),
(6) full zero-drift regression gate, (7) registry 602→605.

## 0. RESUMABLE STATE BLOCK

| item | value |
|---|---|
| HEAD at wave start | 13d233b2 (CONT-34 pushed; local container reset to the CONT-10 era again — fetched + fast-forwarded) |
| pre-wave binary | 702813ff2d5d8be8 (rebuilt from HEAD source BYTE-EXACT == the CONT-34 record) |
| post-F-NEW-294 binary | d354e40ba5e6a6d9 |
| post-F-NEW-295 binary | e974e0204624854e |
| post-F-NEW-296 binary | **6508a51d01b54280** |
| target APK | tmp/cont35_apks/composeStopwatch_1009011.apk (sha256 dbf937ebbe7c0b3d…, F-Droid, re-supplied SHA-exact after the tmp wipe) |
| Track B control APK | tmp/cont35_apks/simplecalc_8.apk (com.simplemobiletools.calculator vc8, 68da25fd9fdf54b4…, F-Droid archive, SHA-exact) |
| probes | fixtures/fnew294_probe, fnew295_probe, fnew296_probe (real aapt2/ECJ/D8, w4 script; ALL THREE wired into the standing battery) |
| regression | run/cont35/regression + scripts/cont35_regression.sh |

## 1. THE FACE (pre-fix, binary 702813ff2d5d8be8)

composeStopwatch baseline ×3 reproduced the CONT-33/34 PARTIAL SUCCESS anchor
**9afb2bd2606f303e ×3** byte-identical, and the run log carried exactly the
recorded singular face:

```
[SGET-MISS] key=Landroid/graphics/Typeface;.DEFAULT storage_size=1479 same_class_keys=0
[SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException;
  (Attempt to invoke virtual method 'Ljava/lang/Object;.getClass' on a null
  object reference) method=Lk6;.<init> pc=409 → uncaught
```

One SGET-MISS → one NPE per run, deterministic ×3. The CONT-33 §8
"next-wave candidate" is this chain.

## 2. DECODE F-NEW-294 (androguard, instruction-level)

- `Lk6;.<init>(String, Lue1;, List, List, Ls10;, Lqr;)V` =
  R8-obfuscated **AndroidParagraphIntrinsics** (text, style, spanStyles,
  paragraphStyles, fontFamilyResolver, density): builds a TextPaint, resolves
  the style's typeface, setTypeface, then processes span styles.
- pc 0x0176–0x019f (the resolve consumer):
  `v7 = Lt10;.b(pc1, i20, I, I) → Luh1;` (FontListFontFamilyTypefaceAdapter
  resolve → TypefaceResult); `instance-of Luh1;` → arm A:
  `v6 = v7.e (Ljava/lang/Object;)` … **pc=0x199 (409):
  `invoke-virtual v6, Object.getClass()`** … `check-cast Typeface` …
  `Paint.setTypeface`. Arm B (async, non-Luh1;): wraps into `Ly9;` and reads
  `.c` — the SAME `getClass()` platform-type null-check shape.
- `getClass()` before `check-cast` is the Kotlin **platform-type `!!`
  intrinsic** — the static type promises non-null; ART throws NPE at the
  invoke site when the value is null.
- `Luh1;` = Compose **TypefaceResult$Immutable** (fields e:Object value,
  f:boolean immediate — shape-matched against ui-text-android-1.11.4.aar via
  the cont33 JVM walker). `.e` = the Typeface returned by `Lzv;.k/l/m`
  (AndroidPlatformTypeface family) → funnels into `Typeface.DEFAULT` sget,
  `Typeface.create(String,I)`, `create(Typeface,I)`, `defaultFromStyle(I)`,
  `Ly0;.b` → `create(Typeface,I,Z)` (API 28+).
- ENGINE SIDE: `grep -c Typeface src/dex/dalvik_engine.cpp` == **0** — no
  constant row (sget → [SGET-MISS] → NULL) and no static-method law (bridge →
  typed-default NULL).

**ART law** (frameworks/base/graphics/java/android/graphics/Typeface.java):
the family constants are static finals built by create() in <clinit>
(DEFAULT=create(null,0), DEFAULT_BOLD=create(null,BOLD),
SANS_SERIF/SERIF/MONOSPACE) and every create/defaultFromStyle overload is
@NonNull — an unknown/empty/null family falls back to the default family. A
live ART <clinit> ALWAYS completes; the constants are NEVER null.

## 3. FIX F-NEW-294 — two generic laws

1. **sget-object arm** (execute_sget_object, constant-synthesis family next
   to Boolean/Locale/Charset/Environment/Collections): a
   `Landroid/graphics/Typeface;` row materializing {DEFAULT, DEFAULT_BOLD,
   SANS_SERIF, SERIF, MONOSPACE} as real heap objects with
   `__typeface_family__`/`__typeface_style__` (AOSP clinit values), cached
   per static_key (identity law).
2. **bridge_to_api static law**: create(String,int) / create(Typeface,int) /
   create(Typeface,int,boolean) / defaultFromStyle(int) — per-request-cached
   non-null Typefaces; null/empty/unknown family → "sans-serif" default;
   weight/italic carried for the API 28+ form. No name dispatch beyond the
   class; no app-specific branches.

Post-fix binary d354e40ba5e6a6d9.

## 4. PROBE F-NEW-294 — fixtures/fnew294_probe

Rows: TF-DEFAULT (THE SGET-MISS row), TF-CONST-FAMILY, TF-CONSUMER-SHAPE (the
EXACT pc=409 twin: wrapper(e=DEFAULT).e.getClass() then check-cast),
TF-CREATE-STR (unknown family), TF-CREATE-NULLFAM, TF-CREATE-EMPTY (the
Lzv;.k empty-name arm), TF-CREATE-TF, TF-CREATE-3ARG (the Ly0;.b shape),
TF-DFS, TF-CREATE-IDEM (same-request identity — AOSP caches created
typefaces).

| run | binary | result |
|---|---|---|
| PRE ×3 | 702813ff2d5d8be8 | SUMMARY **FAIL 0/10** — `TF-DEFAULT got=null`; the consumer row threw the recorded NPE message verbatim |
| POST ×3 | d354e40ba5e6a6d9 | SUMMARY **PASS 10/0** — all rows pass (`getClass=android.graphics.Typeface cast-ok=true`, `same-instance=true`) |

Target ×3 after the fix: the pc=409 NPE **1→0 per run**, SGET-MISS Typeface
1→0, frame UNCHANGED 9afb2bd2606f303e ×3 — divergence moved onward.

## 5. THE NEXT FACE — Layout$Alignment.values() (F-NEW-295)

```
[SYNTH-EXC] ARR-LEN-NULL (deferred): NullPointerException
  (Attempt to get length of null array) method=Ljd1;.<clinit> pc=6 → uncaught
```

Decode: `Ljd1;.<clinit>` = the Compose text-layout alignment resolver —
`Layout.Alignment.values()`, then a NAME SEARCH for "ALIGN_LEFT"/
"ALIGN_RIGHT" falling back to the ALIGN_NORMAL sget. The platform class
android-34.jar decodes (field-ref-exact clinit walk) to exactly THREE
constants: **ALIGN_NORMAL=0, ALIGN_OPPOSITE=1, ALIGN_CENTER=2** — no
ALIGN_LEFT/RIGHT members exist on this API level, so the search correctly
falls back. The engine's 371-CLOSEOUT values()/valueOf() law is GENERIC but
TABLE-DRIVEN: with no kOrdinals rows for the class it answers NULL before
the search can run.

**Fix**: three kOrdinals rows in the decoded AOSP declaration order — the
existing machinery then answers values()/valueOf()/sget coherently from the
same table. Post-fix binary e974e0204624854e.

Probe fixtures/fnew295_probe: LA-VALUES-SIZE (the array-length twin),
LA-VALUES-ORDER, LA-VALUES-ITER (the exact clinit consumer shape),
LA-SGET (sget/values identity), LA-VALUEOF (+identity), LA-VALUEOF-NEG
(unknown → IAE).

| run | binary | result |
|---|---|---|
| PRE ×3 | d354e40ba5e6a6d9 | SUMMARY **FAIL 0/6** — `len=null-arr`; the iter row threw the recorded NPE |
| POST ×3 | e974e0204624854e | SUMMARY **PASS 6/0** — order NORMAL,OPPOSITE,CENTER; fallback law holds; IAE negative honest |

Target ×3: the Ljd1; NPE **1→0 per run**, frame UNCHANGED ×3 — moved onward.

## 6. THE THIRD FACE — LineBreakConfig$Builder (F-NEW-296)

```
[SYNTH-EXC] f141-null-recv (deferred): NullPointerException
  (Attempt to invoke virtual method
   'Landroid/graphics/text/LineBreakConfig$Builder;.setLineBreakWordStyle'
   on a null object reference) method=Lb1;.n pc=0 → uncaught
```

Decode: the Compose StaticLayout.Builder applier (`Llw;.i`) gates on
SDK ≥ 33 and runs `new LineBreakConfig$Builder().setLineBreakStyle(s)
.setLineBreakWordStyle(w).build()` (R8'd into Lb1;.a/.b/.n/.c) then
`StaticLayout$Builder.setLineBreakConfig(config)` (Lb1;.i). The probe
isolated the break LINK precisely: new-instance allocates fine, the FIRST
setter (setLineBreakStyle) returned the typed-default NULL (no law), and the
NPE fires at the SECOND link — exactly matching the target's pc=0 site.
AOSP LineBreakConfig.java (API 33+, Builder API 34): Builder() defaults
(STYLE_NONE=0, WORD_STYLE_NONE=0), setters FLUENT (@NonNull this), build()
@NonNull.

**Fix** (same family as the AudioAttributes$Builder law): bridge_to_api
object law — <init> seeds the builder fields, both setters store + return
THIS, build() allocates a real LineBreakConfig carrying
`__lbc_style__`/`__lbc_word_style__`; PLUS the StaticLayout$Builder
whitelist + storage row for setLineBreakConfig. Post-fix binary
6508a51d01b54280.

Probe fixtures/fnew296_probe: LBC-CHAIN (the exact Llw;.i shape),
LBC-BUILD, LBC-FLUENT (identity-welded chain), LBC-CONSTS, LBC-NEG
(per-instance).

| run | binary | result |
|---|---|---|
| PRE ×3 | e974e0204624854e | SUMMARY **FAIL 2/3** — LBC-CHAIN threw the recorded NPE verbatim |
| POST ×3 | 6508a51d01b54280 | SUMMARY **PASS 5/0** — chain + build non-null, fluent identity-welded, negatives honest |

## 7. TARGET AFTER ALL THREE — the text pass is UNBLOCKED

composeStopwatch ×3 on 6508a51d01b54280:

| run | rc | screenshot | pc=409 NPE | Ljd1 NPE | Lb1 NPE | verdict |
|---|---|---|---|---|---|---|
| csw_post296_r1 | 1 | 9afb2bd2606f303e | 0 | 0 | 0 | PARTIAL SUCCESS retained |
| csw_post296_r2 | 1 | 9afb2bd2606f303e | 0 | 0 | 0 | PARTIAL SUCCESS retained |
| csw_post296_r3 | 1 | 9afb2bd2606f303e | 0 | 0 | 0 | PARTIAL SUCCESS retained |

- The ENTIRE uncaught text-pipeline exception family is DEAD: the only
  remaining SYNTH-EXC rows per run are the 3 faithful deferred/handled faces
  (R350-FORNAME kotlin.reflect CNFE — deferred handler; S102-CLASSLOADER
  AndroidCompositionLocals — catch-all; STREAM-OPEN first-run DataStore
  ENOENT — caught) + the F084 wall-clock budget halts (the app-alive signal,
  count varies with scheduling; the run even interrupts Lh4;.dispatchDraw
  mid-churn).
- Frame UNCHANGED **9afb2bd2606f303e ×3** — the rendered dialog window stays
  byte-stable; the font-object identity laws are behavior-neutral for the
  pixels, as a constant-synthesis law family must be.
- Honest standing frontier (unchanged from CONT-33 §8): `Lh4;` (the Compose
  stopwatch view) still dispatches onDraw with **ops=0** and the dialog body
  is empty (items=0) — the remaining root is the Compose DRAW path (the
  layer drawContent → AndroidCanvas bridge family, F-NEW-256's standing
  frontier), NOT the text pipeline: every text-side uncaught death is gone
  and the app runs to the 15 s budget.

## 8. REGRESSION GATE — ZERO DRIFT at 6508a51d01b54280

scripts/cont35_regression.sh (anchors / probes / control):

| gate | result |
|---|---|
| anchors ×3 ×8 apps | dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622 — **24/24 BYTE-IDENTICAL MATCH** |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7 (known-honest F259-L row), f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, fnew252 56/0, fnew290 56/0, fnew291 56/0, fnew292 70/0, fnew293 56/0 — **== CONT-28..34 records EXACTLY** |
| new probes | fnew294 **77/0**, fnew295 **49/0**, fnew296 **42/0** |
| Track B control | Simple Calculator ×3 rc=0 `7960bce447ac6d8f` — FULL SUCCESS retained |

## 9. STATUS WORDS

- F-NEW-294: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe PRE/POST ×3
  both directions + target NPE elimination ×3).
- F-NEW-295: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (same discipline).
- F-NEW-296: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (same discipline).
- composeStopwatch: **PARTIAL SUCCESS — text pass unblocked**; remaining
  frontier honestly standing: Lh4; ops=0 (the Compose draw path), empty
  dialog body, F084 budget churn (app-alive signal).
- STREAM-OPEN exception-MESSAGE spelling: **PENDING** (CONT-34 §6 residual;
  no failing consumer — not speculatively patched this wave either).
- Registry: 602 → **605** (F-NEW-294/295/296; dedup-checked).

## 10. NEXT RESUMABLE CHECKPOINT

1. composeStopwatch draw frontier: Lh4; onDraw ops=0 — engage the Compose
   layer drawContent → AndroidCanvas bridge (the F-NEW-256 standing root;
   dooz shares it: dooz's materialized NavHost tree also draws 0 canvas ops).
   The empty dialog body (items=0) rides the same family.
2. The 3 faithful deferred faces (R350-FORNAME / S102-CLASSLOADER /
   STREAM-OPEN) stay deferred — no failing consumer.
3. Standing: F-NEW-288 (TextUnit value-class spin, Track A P0) and Simple
   Calculator input-pump (Track B).
