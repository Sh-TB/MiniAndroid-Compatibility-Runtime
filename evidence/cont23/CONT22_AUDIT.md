# CONT-23 — CONT-22 CLAIM AUDIT (Phase 0)

Wave: CONT-23. Verified starting state: remote HEAD `62809396501e13a1e1ab0c88f7b106d866d9c62a`
(= the reported CONT-22 commit `62809396`), working tree clean except `tmp/flappycow`
submodule marker, local == origin/main (0/0). Engine binary rebuilt during the audit
phase and reproduced **byte-exactly**: `fa88902fdee6e982e7f9696c339dda6e53af8fbb2c98de88651531d4ec428405`
— the exact binary the CONT-22 report claims. Every verdict below is from fresh
execution at that binary, at canonical parameters (1080x1920, 5 frames, 15 s)
unless noted. Exit-code law: `main.cpp` exits 0 only on Status SUCCESS; the
affected targets exit 1 = PARTIAL SUCCESS (frame-truth DEFAULT_BACKGROUND_ONLY).

| # | CONT-22 claim | Source file (claimed) | Verification performed | Verdict |
|---|---|---|---|---|
| 1 | F-NEW-274 constructor-contract gate present + firing | dalvik_engine.cpp (`class_has_no_arg_ctor`, `[F274-CTORGATE]`) | 2 marker sites found in checkout; fresh dooz run: `[F274-CTORGATE] Lgf1;.g initializer type Lwg0; has no ()V ctor -> honest null (recv=Lgf1; caller=Lg8;.a pc=460)` | **TESTED** |
| 2 | F-NEW-275 getServiceInfo/GET_SERVICES present + firing | dalvik_engine.cpp (`[F275-SVCINFO]`, GET_SERVICES arm) | 3 marker sites in checkout; fresh opencalc run: `[F275-SVCINFO] MISS → PackageManager$NameNotFoundException (AOSP contract)` ×2, app catches (deferred handler = NameNotFoundException) | **TESTED** |
| 3 | dooz uncaught 1→0 (zero uncaught faces) | evidence/cont22/CONT22_REPORT.md §9 | Fresh dooz ×2 (`run/cont23/dooz_prefix_r1/r2`): 0 uncaught lines, 0 SYNTH-EXC uncaught, `[UEH-DEFAULT]` kill path absent; fresh sweep census: dooz 0, stopwatch 0 | **TESTED** |
| 4 | dooz anchor `d602648e8e401895` zero-drift | evidence/cont22/CONT22_REPORT.md §8/§11 | Fresh anchor ×2 + sweep + full anchor suite: dooz `d602648e8e401895` MATCH ×5 today | **TESTED** |
| 5 | 18/18 anchors ×3 byte-identical | evidence/cont22/CONT22_REPORT.md §8 | Re-run `cont21_family_sweep.sh anchors` at fa88902f: 6 anchors × 3 runs, all MATCH (dooz/microtimer/unote/gmdice/opencalc/tictactoedeluxe) | **TESTED** |
| 6 | opencalc uncaught 5→4, ServiceInfo NPE 0, NameNotFoundException app-caught | evidence/cont22/CONT22_REPORT.md §9 | Fresh opencalc sweep: 4 uncaught faces, 0 ServiceInfo NPE rows, `[F275-SVCINFO] MISS → NameNotFoundException` app-caught; anchor `a976d2f9fb675cb3` MATCH ×4 | **TESTED** |
| 7 | Probe battery green (fcol 20/20, f259 7/7, f259g 12/13 known-L, f266 6/6, f268 12/12) | evidence/cont22/CONT22_REPORT.md §8 | Rebuilt probes canonically (`cont21_build_probes.sh`), re-ran battery: fcol 20/20, f259 7/7, f259g 12/13 (the SAME known-honest `F259-L throwing slot propagated=false` row, unchanged since CONT-18h), f266 6/6, f268 | **TESTED** |
| 8 | Corrected sweep harness exit-code handling (`local` bug fix) | scripts/cont21_family_sweep.sh | Inspected: locals declared before the engine call, `rc=$?` immediately after; re-ran sweep — rc truth printed (all 5 targets rc=1 PARTIAL, matching the engine law) | **TESTED** |
| 9 | Registry 585 rows; F-274/F-275 → ROOT-CAUSED-FIXED | root_registry.json | 585 rows confirmed; both entries carry fix + evidence + probe fields | **TESTED** |
| 10 | dooz visual gate = F-265 measure-pass chain, untouched | evidence/cont22/CONT22_REPORT.md §11/§13 | Fresh dooz trace at fa88902f: the F-265 measure-pass DEATH FACE IS GONE — `Lzs0;.m` (MeasureAndLayoutDelegate.measureAndLayout) executes ×9 with ZERO exceptions; the frontier has moved deeper (see FIRST_DIVERGENCES.md). CONT-22's wording ("blocked at F-265 measure-pass") described the W6-era root, now superseded | **SUPERSEDED** (honest update of the frontier) |

## Audit finding (this wave)

The measure/layout frontier named by CONT-22 as "next P0" no longer dies: the
W6-era mid-flight unwind (`Lzs0.m depth-17`) is gone at fa88902f. The remaining
dooz visual blocker is NOT in the measure/layout pass — it is a composition/
scheduler frontier: the first-frame applyChanges REMOVES the app content
subtree and no second applyChanges ever runs to insert the destination content
(full chain: `evidence/cont23/FIRST_DIVERGENCES.md`). Registry F-NEW-265's
`verified_current` extended accordingly.
