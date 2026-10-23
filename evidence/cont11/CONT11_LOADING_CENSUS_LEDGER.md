# CONT-11 LOADING-CENSUS WAVE — RECONCILIATION LEDGER (issue #387)

Date: 2026-10-23 · This branch landed on the remote W9 head (5787d85b,
registry 828→831 with F-NEW-514/515/516) after the parallel-lineage
deduplication.

## What the census wave did

1. **121-APK loading census** (fresh stores, honest final-uncaught pairing,
   recurring-anchor clustering) — harness: scripts/cont11_loading_census.py
   (+ reparse/cluster2); evidence census_v2_baseline / pre_rc / rc.
2. **Three recurring roots root-caused independently** — then DEDUPLICATED
   against the parallel W7–W9 lineage which had already fixed all three:
   - interface exactness gate → already landed as **F-NEW-281c** (remote)
   - Thread UEH law → already landed as **F-NEW-272** (remote)
   - WindowMetrics family → already landed as **F-NEW-486** (remote)
   No engine duplicates were double-landed.
3. **Reconciliation completions** (the genuinely missing pieces, proven by
   probe rows F273-A1/A3 on the remote binary):
   - ThreadShadow void no-op family swallowed the UEH pair BEFORE the
     engine F-NEW-272 law (registry-level dispatch order) → pair removed
     (same precedent as the F-150 sleep removal).
   - The STATIC arm of F-NEW-272 was unreachable: execute_invoke_static →
     bridge_to_api never reaches try_shadow_dispatch on this lineage →
     the same law added to bridge_to_api (two-view pattern, R-NEW-339
     precedent), reusing the remote's default_uncaught_handler_ /
     thread_uncaught_handlers_ state.
   - Registered the genuinely-NEW faces: **F-NEW-514**
     (WindowInsetsCompat/LocalView compose-locals cluster),
     **F-NEW-515** (fossify unknown-authority coroutine-boundary unwind,
     7 titles), **F-NEW-516** (List.size-on-null family + backlog).
4. **Probe** fixtures/cont11_probe (real aapt2/ECJ/D8): **12/12 PASS** on
   the reconciled binary (F272 interface-default exactness ×3,
   F273 UEH static+instance+chain ×6, F274 WindowMetrics ×2 + block row).
5. **Issue #387 created** — the SEPARATE recurring-task registration.

## Census effect (APP-BOUNDARY crash titles / 121)

- baseline (old lineage): **93**
- + first census fixes: **90**
- reconciled remote lineage + completions: **81** — and the 4 nominal
  "regressions" are NO_ROOT white-screens → deeper SPECIFIC faces
  (cordova AllowList NumberFormat; Future.get NPE) = success-path progress.
- uturn → **SUCCESS**; librecontactsbackup → **SUCCESS**; floatdeck →
  past its crash (DEFAULT_BACKGROUND_ONLY); notepad/sopadeletras/peri →
  deeper faces (Insets.left / FNFE / NSM).

## Regression battery (reconciled binary)

- anchors ×3 byte-identical matching the rebased records EXACTLY:
  opencalc 63020bc7 · chess a0319686 · dooz 851cc176 (the recorded
  fresh-store first-run face) · microtimer bbd350b6 · unote 7481e9b4 —
  ZERO DRIFT from my two completions.
- negatives 19/19 PASS.
- reinstall-identity 5/5 PASS (earlier in the wave, same APK set).
