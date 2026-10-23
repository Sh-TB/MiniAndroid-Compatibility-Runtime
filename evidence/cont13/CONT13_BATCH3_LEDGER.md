# CONT-13 — BATCH 3 OF THE 20-BY-20 DIRECTIVE (issue #387)

Date: 2026-10-23 · Head: `856261cf` (post-CONT-12 lineage; the container had
rolled back to the CONT-10-era snapshot e99c2fbd again — detected via
`git fetch` showing origin/main 309 commits ahead; reset + rebuild from the
TRUE tree before any run, per the b0620f75 stale-snapshot protocol).
Binary: `806225767105cb11` (pre-fix) → post-F-NEW-518 rebuild.
Directive: «ادامه و پوشش ۲۰ قطار» — continue + cover 20 titles.

## Batch composition (20 titles, fresh stores, 90 s window, --frames 6)

- **A. Object.getClass umbrella survivors (13)**: prism, wocheneinkauf,
  matewave, sparkledns, aurora, awagam, webstack, compose_stopwatch,
  notepad, k9, audiobook, goodtime, netguard
- **B. fossify family (4)**: fossify_math, fossify_notes, fossify_clock,
  fossify_calendar (the registered F-NEW-515 pool)
- **C. List.size family (3)**: dmfs_tasks, surgeengine, bouncy

Harness: `scripts/cont13_batch20.py` (census-harness law: fresh per-title
store → install → installed-identity run → final-uncaught signature + verdict
+ png metrics). Results: `evidence/cont13/batch20_census.json`.

## The recurring root found and closed — F-NEW-518

**All four fossify titles died on the SAME anchor** (post-CONT-12 binary):
`PackageManager$NameNotFoundException` ("org.fossify.thankyou") raised at
`Lo5/f;.U pc=12`, deferred-unwound, **APP BOUNDARY death** at
`SplashActivity.onCreate`.

Root-cause chain (machine-verified):
- DEX truth (`scripts/cont9_dexdump.py` on the installed base.apk):
  `Lo5/f;.U(Landroid/content/Context;)Z` HAS a try table covering the
  `getPackageInfo` invoke, one typed handler `Ljava/lang/Exception;` →
  pc=17 (`return v1` = the Kotlin `catch (e: Exception) { false }`).
  The app's catch is LAWFUL.
- Engine truth: `is_exception_subtype("Landroid/content/pm/
  PackageManager$NameNotFoundException;", "Ljava/lang/Exception;")` → FALSE —
  the class is absent from `kBuiltinExcParent`, absent from
  `class_to_superclass_` (framework class), and the
  `AndroidException → Exception` row was trapped behind the F-NEW-368
  experiment gate.
- AOSP facts: `PackageManager.NameNotFoundException extends
  android.util.AndroidException` (PackageManager.java);
  `AndroidException extends java.lang.Exception` (AndroidException.java).

**FIX (generic, unconditional)**: two parent rows added to
`kBuiltinExcParent` (+ `ApplicationNotFoundException` companion):
`PackageManager$NameNotFoundException → AndroidException → Exception`.
Same precedent as FIX-D12-ADJACENT (CONT-120): platform exception chains are
AOSP FACTS, not experiment-gateable. No behavior flip under the gate.

## Census effect (before → after, same 20 titles)

| title | pre-fix | post-fix |
|---|---|---|
| fossify_math | APP-BOUNDARY death (NameNotFound) | **MainActivity renders REAL UI** — top toolbar icons, 13,071 content px (`evidence/cont13/fossify_math_post_f518.png`) |
| fossify_calendar | APP-BOUNDARY death | **renders real UI** 12,336 px (next face: `Lu30;.r` NPE) |
| fossify_notes | APP-BOUNDARY death | past splash → MainActivity (next face: `ColorStateList.getDefaultColor` NPE — kin of the census batterymonitor row) |
| fossify_clock | APP-BOUNDARY death | past splash (next face: FitWindows NSM — upstream-caught "Oh well", non-killing) |
| bouncy | — | rc=0, 72,622 content px (determinism anchor renders) |
| netguard | — | 27,335 content px (next face: kotlin-reflect CNF) |
| other 14 | white/dark | unchanged faces (per-API null-contract / loader faces, ledgered below) |

Pre-fix: 1/20 with real content (bouncy). Post-fix: **4/20 render real app
content**; the fossify family moved from hard-crash-before-load to rendered
UI — the loading-screen bar (user directive) is reached for the family.

## Remaining faces (ledgered for the next waves, no false closure)

- `ColorStateList.getDefaultColor` NPE (notes + census batterymonitor) —
  recurring ×2, next fix candidate.
- S102 loader CNF `AndroidCompositionLocals_androidKt` (matewave) +
  NSM on the same class (sparkledns) — Compose compose-locals loader family.
- DataStore first-read ENOENT (awagam, compose_stopwatch) — upstream
  creates on first write; the deferred FNFE must route to the DataStore
  coroutine chain's handler (F-NEW-515's registered boundary face).
- f141 null-contract singles (prism Cursor.moveToNext, wocheneinkauf
  TrustManagerFactory.init, aurora/webstack/audiobook getClass, goodtime,
  dmfs getPagePosition, surgeengine List.size) — per-API F-NEW-516 pool.
- k9: Koin `NoDefinitionFoundException` (service-registry face).

## Regression battery (post-fix binary)

- anchors 5/5 **zero drift**, prefix-exact vs the rebased records:
  chess `a0319686…`, opencalc `63020bc7…`, microtimer `bbd350b6…`,
  unote `7481e9b4…`, tower3d `11a38a5a…`
- negatives **19/19** (after regenerating the probe store at the s41 harness
  path `run/gatea/probe_store` — the earlier 9/19 was a stale-store artifact,
  root-caused and repaired, NOT a runtime regression)
- skill selftest **13/13**
- Registry 832 → **833** (F-NEW-518 ROOT-CAUSED-FIXED, id-unique, no inflation)
