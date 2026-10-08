# CONT-22 — Execution-Family Follow-Up: measurable generic runtime progress

Wave: CONT-22 (Issue #384 continuation). Binary lineage:
`882b7cdf389aabc3` (CONT-21) → **`fa88902fdee6e982`**. Registry: 585 rows;
F-NEW-274 + F-NEW-275 → ROOT-CAUSED-FIXED (terminal 329 / queued 256).

---

## 1. CONT-21 audit

Full file: `evidence/cont22/CONT21_AUDIT.md`. Headline results, all by fresh
re-execution at byte-verified binary `882b7cdf`:

| Claim | Verdict |
|---|---|
| F-NEW-272 Thread UEH law (source + runtime) | **TESTED** — impl at dalvik_engine.cpp:23272+; [UEH-DEFAULT] fires; APP BOUNDARY 0 |
| F-NEW-273 getProviderInfo/ComponentName/Bundle.keySet | **TESTED** — impl at dalvik_engine.cpp:39605–39853; [F273-PROVINFO] entries=3; NPE faces gone ×5 |
| 5-target recovery (sweep) | **PARTIAL** — all faces/anchors verified, but the "rc 1→0" wording is REJECTED (see finding) |
| Dooz APP-BOUNDARY 2→0 | **TESTED** — 0 in fresh runs |
| 18/18 anchors ×3, zero drift | **TESTED** — 18/18 MATCH re-run at this container |
| dooz single remaining face = F-NEW-274 @ line ~3036 | **TESTED** — exact face reproduced at line 3036, uncaught count 1 |

**AUDIT FINDING (rejected claim)**: `scripts/cont21_family_sweep.sh` declared
`local sha rc` between the engine call and `rc=$?`; bash `local` resets `$?`,
so the sweep always printed rc=0. Engine law (main.cpp:992) exits 0 ONLY on
full SUCCESS. Python-measured truth at 882b7cdf: dooz/opencalc/stopwatch/
telegram/forkgram were all rc=1 (Status PARTIAL SUCCESS — frame-truth +
remaining faces). The FACE-level CONT-21 claims survive; the exit-code claim
did not. Script fixed and committed this wave; truth re-measured (§12).

## 2. Execution-family coverage

14 representatives re-run fresh (harness `scripts/cont21_family_harness.py B`)
across F1/F2/F3/F4/F6/F7; **F5 remains NO-TARGET-IN-CORPUS** (honest, no
fabrication). New preserved before-state: `run/cont22/family_paths_PREFIX_CONT21.json`.

## 3. First-divergence candidates

Wide cluster scan over fresh post-fix logs
(`scripts/cont22_cluster_scan.py` → `run/cont22/cluster_scan.json`), clustered
by FRAMEWORK-side signature (obfuscated app classes never clustered across
targets). Uncaught-face census (post-CONT-21): dooz 1, opencalc 5,
chessclock 1 (Uri-null), bouncy 2 (libGDX native), tictactoe 2 (libGDX EGL),
telegram 9, forkgram 9 (Telegram-engine family-internal), others 0.

## 4. Root ranking

Rule: cross-target × cross-family × execution-depth × genericity × visual.

| Rank | Candidate | Targets/Families | Decision |
|---|---|---|---|
| 1 | **F-NEW-275** getServiceInfo/GET_SERVICES law gap | opencalc (F1, FATAL-face) + telegram (F4, degraded) = 2/2 | **FIXED** — sibling of the proven F-273 identity chain |
| 2 | **F-NEW-274** dooz savedstate-face root | dooz (F6) P0; root-caused to an R414 defect that ALSO fires in opencalc (F1) → 2/2 | **FIXED** (root was deeper than the registered face) |
| 3 | libGDX surface/native family (P10) | tictactoe (F2) + bouncy (F3) = 2/2 but requires GL/EGL + native-load subsystems | DEFERRED (family candidate; native execution out of runtime scope) |
| 4 | ConstraintLayout.onLayout null (opencalc ×3) | 1 target | not clustered; layout-engine root deferred |
| 5 | chessclock Uri-null (P7) | 1 target | discipline: not fixed without a second target |

## 5. Root(s) selected

**R1 = F-NEW-275** (package-manager component-identity sibling).
**R2 = F-NEW-274** (P0; the dooz face decoded into a generic
heap/field-representation root).

## 6. Upstream/source semantic law

**F-NEW-275** — AOSP PackageManager: `getServiceInfo(ComponentName, flags)`
returns the manifest-declared ServiceInfo, NEVER null (NameNotFoundException
when absent); metaData under GET_META_DATA (0x80); `getPackageInfo` with
GET_SERVICES (0x20) fills PackageInfo.services. Live DEX proof: opencalc
`Lg/t;.b` (AppCompatDelegate AppLocalesMetadataHolderService discovery, flags
640, iget metaData with no null-check, catches ONLY NameNotFoundException);
telegram `Lkg/i;.P` (Firebase ComponentDiscovery, flags 128, graceful
degradation). Local source read FIRST: F-273 getProviderInfo law +
GET_PROVIDERS array law found as the mirrors; manifest service table
(`manifest_service_classes_`) + service meta-data already parsed.

**F-NEW-274** — ART constructor/field law: a never-written instance field
reads NULL; an initializer-default object exists only after its constructing
`<init>` ran. R-NEW-414 fabricated zero-objects of the initializer type
WITHOUT running any constructor — valid only when the type has a `()V` ctor.
Live chain (androguard, `scripts/cont22_disasm*.py`): `Lgf1;.<init>` ALWAYS
writes `.g` via real ctors (`new Lrf1;` + `new Lwg0;(registry, 20)`);
`Lwg0;` is an R8 merged-lambda class with NO `()V` ctor (capture `.f` written
only by its parameterized ctor); the reader `Lg8;.a` carries the app's own
`if-eqz` null-guard; R414's fabricated non-null broken lambda defeated the
guard and produced the `iget Lrf1;.f on null` face in `Lwg0;.y`
(SavedStateRegistry.performSave).

## 7. Local implementation

`miniandroid/src/dex/dalvik_engine.cpp` + `.h` only:
1. `class_has_no_arg_ctor()` helper (DEX direct_methods `()V` scan;
   framework-owned types → true, preserving the chess Rect evidence).
2. Constructor-contract gate in the in-heap R414 arm + the R414b non-heap
   arm → honest null + bounded `[F274-CTORGATE]`/`[F274-CTORGATE-B]` diag.
3. `PackageManager.getServiceInfo` law (identity walk exact/bare/suffix;
   ServiceInfo seed; metaData under 0x80 from `component_meta_data_`;
   NameNotFoundException via `throw_deferred`) + `[F275-SVCINFO]` diag.
4. GET_SERVICES (0x20) arm inside getPackageInfo filling
   `PackageInfo.services` (GET_PROVIDERS array-law mirror).

Zero app-name/package checks, zero exception suppression, zero PC
advancement, zero fake objects, zero screenshot logic.

## 8. Tests

- Regression battery at the new binary: anchors 18/18 ×3; g2048 ×3; fcol
  20/20; f259 7/7; f259g 12/13 (same honest F259-L row); f266 6/6; f268
  12/12; 5-target sweep screenshots byte-identical.
- New first-divergence harvesting integrated: `cont22_cluster_scan.py`.

## 9. Runtime before/after (same params)

| Target | Before (882b7cdf) | After (fa88902f) |
|---|---|---|
| dooz | 1 uncaught (`Lrf1;.f` ×37 log mentions), [UEH-DEFAULT] kill path | **0 uncaught**, 0 mentions, no fatal exception, +113 log lines deeper, [F274-CTORGATE] fires |
| opencalc | 5 uncaught / 5 APP BOUNDARY / ServiceInfo NPE | **4/4**, ServiceInfo NPE 0, NameNotFoundException app-caught, [F275-SVCINFO] + [F274-CTORGATE-B] fire |
| telegram | Firebase discovery REC-MISS ×2 → null degradation | discovery served ×2, app catches NameNotFoundException |

## 10. Cross-family confirmation

- **F-NEW-275**: opencalc (F1) + telegram (F4) — 2 families.
- **F-NEW-274**: dooz (F6) + opencalc (F1) — 2 families; the opencalc hit
  (`Lm0/i0;.e` → RecyclerView accessibility delegate `Lm0/h0;`, only
  `<init>(Lm0/i0;)V`) was DISCOVERED at runtime, not assumed.
- Anchors/probes span F1/F2/F3/F6/F7 (unote, microtimer, gmdice, opencalc,
  tictactoedeluxe, g2048, dooz, flappycow, bouncy, minibrowser).

## 11. Graphical evidence

Screenshots + PNG content metrics per run under `run/cont22/`
(anchor_*, sweep_*, after_*, probes/). All anchors byte-identical ×3
(zero visual drift from the fixes — the fixes are execution-path laws, and
the affected faces were below the visual frontier). dooz remains honestly
RENDER_STARTED / frame-truth DEFAULT_BACKGROUND_ONLY: its visual gate is the
F-265 measure-pass chain, untouched this wave.

## 12. Regression

See `evidence/cont22/CROSS_FAMILY_PROGRESS.md` tables (all green, with the
honest rc truth: affected targets exit 1 = PARTIAL SUCCESS by the engine's
own law; rc=0 requires frame-truth SUCCESS).

## 13. Remaining blockers

1. **F-265 measure-pass chain** — the dooz (F6) visual gate; place-writers
   behind composition. Next P0 for visual progress.
2. **libGDX surface/input + native-load family** (P10, now 2 targets:
   tictactoe F2 + bouncy F3) — GL/EGL subsystem; native execution out of
   scope, surface/input law needs its own root.
3. **Telegram-engine UI-init faces** (telegram/forkgram, family-internal).
4. chessclock Uri-null (single-target candidate — needs a second target).
5. F-NEW-276 data-path duplication (P2; multi-target, non-blocking).

## 14. Next highest-value root

**F-265 measure-pass completion chain (dooz)** — with F-274/275 closed, dooz
has ZERO uncaught faces and executes 113 log lines deeper; the single
remaining gap between RENDER_STARTED and app-owned pixels is the Compose
measure/layout placement chain, shared by every future Compose target (the
F6 family surface). Second: the libGDX surface/input law (now a proven 2-
target family cluster).

## 15. Final answer

> **Did the execution-family/source-first method produce another measurable
> generic runtime improvement, and which shared Android semantic root should
> we attack next?**

**Yes — two generic roots, both proven cross-family at runtime.** (1)
F-NEW-274: the CONT-21 audit decoded the "savedstate" face into a heap/field
constructor-contract violation inside the existing R-NEW-414 law; the fix
removed dooz's LAST uncaught exception face (1→0, kill-path gone) and the
same gate was independently caught firing in opencalc — 2 targets / 2
families from one law, with zero visual drift (18/18 anchors ×3 + full probe
battery). (2) F-NEW-275: the predicted getServiceInfo/GET_SERVICES sibling
closed the opencalc ServiceInfo NPE through the AOSP NameNotFoundException
contract (the app's own designed path — verified upstream-faithful against
its manifest) and served telegram's Firebase ComponentDiscovery twice —
2 targets / 2 families. The method also caught and corrected a false
CONT-21 exit-code claim (bash `local` bug) — the audit layer is doing its
job. **Next shared root: the F-265 measure-pass chain** (the dooz/Compose
visual gate; with zero uncaught faces left, every step now lands on
layout/placement primitives shared by all future Compose targets).
