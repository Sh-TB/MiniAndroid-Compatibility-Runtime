# CONT-14-B4 — BATCH-4 of the 20-by-20 directive

(Wave label disambiguated: the tracked `cont14_audit_evidence.json` in this
directory is the parallel-lineage snapshot-wave audit at e99c2fbd/566 roots;
this ledger is the true-lineage batch-4 wave at 717e0058/834 roots.) (user: «ادامه», «گیت هاب برسی پوش قطار ۲۰ تایی»)

Date: 2026-10-23. Head: `717e0058` (CONT-13 BATCH-3 lineage, after the
314-commit remote sync; the container was at the CONT-10-era snapshot
`e99c2fbd` — already contained in origin/main per the b0620f75 recovery
record, so the sync was a fast-forward reset, zero local work lost).

Wave target: the CONT-13 ledger's named next fix candidate — the
**`ColorStateList.getDefaultColor` NPE recurring ×2** (fossify_notes +
batterymonitor) — plus the batch-of-20 re-census and the full regression
wall.

## ROOT CAUSE — F-NEW-519 (TextView.getTextColors() NO LAW)

The census face message ("invoke virtual method
`Landroid/content/res/ColorStateList;.getDefaultColor` on a null object
reference" at `Landroidx/viewpager/widget/PagerTitleStrip;.<init> pc=138`)
NAMES the wrong suspect. DEX truth machine-verified from the APK bytes
(`scripts/cont14_pager_dex_truth.py`, androguard, batterymonitor_1007003):

```
0x10c: invoke-virtual {v10}, TextView;->getTextColors()  ← produces NULL
0x112: move-result-object v10
0x114: invoke-virtual {v10}, ColorStateList;->getDefaultColor()  ← NPE
0x11a: move-result v10
0x11c: iput v10, PagerTitleStrip;->mTextColor I
```

`0x114` bytes = **138 16-bit code units** — the census pc is EXACT.
The receiver of `getDefaultColor` is the RESULT OF `TextView.getTextColors()`
— which had NO engine law → null. The engine's ColorStateList law itself is
fine (it answers `__default_color__` or the honest 0).

AOSP TextView.java law (source-first):
- `private ColorStateList mTextColor = ColorStateList.valueOf(0xFF000000);`
  — the FIELD INITIALIZER guarantees `getTextColors()` NEVER returns null.
- `setTextColor(int)` → `mTextColor = ColorStateList.valueOf(color)`;
  `setTextColor(ColorStateList)` → `mTextColor = colors` (identity).

## FIX (read-side only; no setter change; zero renderer coupling)

`dalvik_engine.cpp bridge_to_api` (before the F-NEW-226 getPaint law):

1. Captured CSL object (`ViewNode.text_color_state_object`, the
   `setTextColor(ColorStateList)` capture) still a live
   `Landroid/content/res/ColorStateList;` → return THAT object
   (AOSP identity contract).
2. Else the AOSP `valueOf` arm: recorded `text_color` (explicit runtime OR
   style-resolved) → `csl_wrap_single(recorded color)` — renderer parity
   with the F-NEW-301 `getCurrentTextColor` law (getter state and rendered
   pixels cannot diverge); UNSET → the field-initializer black /
   Button-family white (F-NEW-301 default law).

Bounded `[F-NEW-519]` diagnostics (identity vs valueOf arm, 12-row cap).

## VERIFICATION (binary `feee06117f0e7c3c` = HEAD 717e0058 + F-NEW-519)

- **batterymonitor** (pre-fix: rc=1 at 1.9 s, NPE at PagerTitleStrip pc=138,
  zero view tree): post-fix the PagerTitleStrip NPE face is GONE — the app
  materializes its REAL UI tree (LinearLayout → ViewPager → PagerTitleStrip
  children=3 with the real titles **HISTORY / CURRENT STATE / ALARMS**),
  run completes PARTIAL SUCCESS with non-killing F-016 provider faces
  (Shizuku/Sui provider init ISE/NPE + the AppLocalesMetadataHolderService
  getServiceInfo NameNotFoundException — which the androidx catch HANDLES
  via the F-NEW-518 chain (log: "Checking for metadata for
  AppLocalesMetadataHolderService : Service not found") and rethrows as the
  AOSP IllegalStateException — on real Android the merged manifest usually
  carries the service; this APK's merged manifest does NOT, and the
  androidx code path is engineered to survive it; the engine now mirrors
  that survival).
- **fossify_notes** (census face + F084 budget halts pre-fix): post-fix
  **0 uncaught**, stable past splash into MainActivity at 90 s and 300 s
  (wall 2.5 s); verdict DEFAULT_BACKGROUND_ONLY / APP_DRAW_OPS — the
  corpus-wide draw-path frontier (honest, ledgered, not claimed).
- Pre-fix rebuilt-binary anchor battery: 5/5 EXACT (the fresh container
  rebuild's byte-SHA `33038c783656331a` differs from the recorded CONT-13
  `806225767105cb11` — flagged honestly; the anchors prove semantic
  faithfulness: chess `a0319686` / opencalc `63020bc7` / microtimer
  `bbd350b6` / unote `7481e9b4` / tower3d `11a38a5a`).
- Post-fix anchor battery: 5/5 **ZERO DRIFT** (same five SHAs, uncaught=0).

## BATCH-4 CENSUS (the batch-3 20 titles re-run at the post-fix binary)

Harness: `scripts/cont14_batch20.py` (cont13 runner re-pointed at
evidence/cont14; fresh stores, 90 s census window). Output:
`evidence/cont14/batch20_census_v2.json`.

| title | px | screenshot sha16 | face |
|---|---|---|---|
| bouncy | 72,622 | 8a6c24ac8a7d718e | real content (retained) |
| netguard | 27,335 | a0736914697be5a4 | real content (retained; kotlin-reflect CNF next) |
| fossify_math | 13,071 | 43fa6bf67b88dbd7 | REAL MainActivity UI (retained) |
| fossify_calendar | 12,336 | 9afd473e163b9c33 | real UI (retained) |
| fossify_notes | 0 | b270ff040b3601dc | 0 uncaught (CSL face dead; draw-path frontier) |
| fossify_clock | 0 | b270ff040b3601dc | non-killing FitWindows NSM (upstream-caught) |
| other 14 | 0 | byte-identical to batch-3 | named frontiers (f141 singles, S102 loader CNF/NSM, DataStore ENOENT, Koin, budget) |

**ZERO DRIFT: all 20 screenshot SHAs byte-identical to the CONT-13 batch-3
census.** The read-side law flips nothing that never hit the face.

Direct F-NEW-519 census effect (batch-3's named ×2 face):
- batterymonitor (121-title census): NPE crash → real UI tree.
- fossify_notes (batch-20): uncaught face → 0 uncaught.

## Remaining faces (honest, for the next waves — unchanged names)

1. S102 compose-locals loader CNF/NSM (`AndroidCompositionLocals_androidKt`:
   matewave CNF, sparkledns NSM).
2. DataStore first-read ENOENT (awagam, compose_stopwatch) — route the
   deferred FNFE to the DataStore coroutine chain's handler (F-NEW-515
   boundary face).
3. f141 null-contract singles pool (F-NEW-516): prism Cursor.moveToNext,
   wocheneinkauf TrustManagerFactory.init, aurora/webstack/audiobook
   getClass, goodtime, dmfs getPagePosition, surgeengine List.size.
4. k9: Koin NoDefinitionFoundException (service-registry face).
5. batterymonitor next faces: Shizuku/Sui provider init (non-killing) +
   real-content draw path for the PagerTitleStrip family.

## Regression wall (post-fix binary)

| gate | result |
|---|---|
| anchors (pre-fix rebuild) | 5/5 EXACT |
| anchors (post-fix) | 5/5 ZERO DRIFT |
| batch-20 | 20/20 screenshot SHAs byte-identical |
| negatives | 19/19 PASS (probe store regenerated at run/gatea/probe_store) |
| skill selftest | 13/13 PASS |
| registry | 833 → 834 (F-NEW-519 ROOT-CAUSED-FIXED, id-unique) |

Evidence: `evidence/cont14/{CONT14_BATCH4_LEDGER.md, wave_faces_prefix.json,
wave_faces_postfix.json, batch20_census_v2.json}`,
`run/cont14_waves/r_batterymonitor/{run.log, view_tree.json}`,
`run/cont14_batch20/r_*/`. Scripts:
`scripts/cont14_pager_dex_truth.py, cont14_wave_faces.py,
cont14_batch20.py, cont14_registry_update.py, cont14_comment.py`.
