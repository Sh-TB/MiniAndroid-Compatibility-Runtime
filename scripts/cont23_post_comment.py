#!/usr/bin/env python3
"""CONT-23 — post the wave report to Issue #384."""
import subprocess, json, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 384

proc = subprocess.run(["git", "credential", "fill"],
                      input="url=https://github.com\n\n",
                      capture_output=True, text=True)
token = None
for line in proc.stdout.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]

HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

BODY = r"""# CONT-23 wave report — cross-family graphical progress: the dooz measure/layout frontier decoded to the scheduler root (one fix hypothesis falsified by its own probe; no engine change shipped)

Starting lineage verified: HEAD `62809396` == origin/main; binary rebuilt **byte-exactly** `fa88902fdee6e982`. Ending lineage: **the same byte-exact binary** — no engine source change shipped. Registry 585 → **586** (F-NEW-277 CLASSIFIED P0; F-NEW-265 `verified_current` extended). Commit `26cf1b49`. Evidence: `evidence/cont23/{CONT22_AUDIT,FIRST_DIVERGENCES,GRAPHICAL_PROGRESS,CONT23_REPORT}.md`, runs `run/cont23/`.

## Headline (honest)

1. **The CONT-22 frontier description is superseded**: the W6-era dooz measure-pass death (`Lzs0.m` unwind) is GONE at fa88902f — the measure pass runs ×9 with zero exceptions, place-writers execute, isPlaced flips TRUE, and the draw walk descends into placed children.
2. The remaining dooz pixel blocker was decoded to its exact mechanism and registered as **F-NEW-277 (P0): recomposition starvation at the frame-pump quiescence boundary** — the first-frame applyChanges removes the NavHost content subtree (upstream-faithful, runtime call chain captured), and the recomposition that would insert the destination content never runs because the Recomposer runner's frame-clock await never re-arms after the launch pump quiesces (3 ticks even in a 120 s run).
3. **One fix hypothesis was raised, tested, and falsified by its own probe** — recorded here in full (§ checklist items 13–14): the engine's start/resume lifecycle transaction was already implemented (outer engine, FIND-G09-LC-001 law); the trial DEX-engine patch double-dispatched and was reverted to byte-exact fa88902f. The probe ships as a locked regression test (5/5 PASS).
4. Zero engine changes → zero regression risk, and the full gate was run anyway: anchors 18/18 ×3 MATCH, probe battery identical to the recorded green state, family sweep rc-truth unchanged.

## CONT-23 acceptance criteria — line-by-line completion checklist

Every item carries STATUS / EVIDENCE / COMMAND / FILE-LINE. `BLOCKED`/`PARTIAL` items are marked, not omitted.

- [x] **Phase 0 — fetch remote, verify HEAD/working tree/binary SHA**
  STATUS: DONE · EVIDENCE: HEAD `62809396501e13a1e1ab0c88f7b106d866d9c62a`, local==origin 0/0, rebuild byte-exact `fa88902fdee6e982e7f9696c339dda6e53af8fbb2c98de88651531d4ec428405` · COMMAND: `git fetch && git rev-list --left-right --count main...origin/main && make -j1 BUILD_DIR=build && sha256sum build/miniandroid` · FILE: `evidence/cont23/CONT22_AUDIT.md` L5-8
- [x] **Read Issue #384 + checklist, CONT-21/22 reports, registry, diffs**
  STATUS: DONE · EVIDENCE: registry entries F-265/F-271..275 re-read; CONT-22 report + audit re-read before work · COMMAND: `python3 -c` registry dumps (transcript) · FILE: `evidence/cont23/CONT22_AUDIT.md`
- [x] **Confirm F-NEW-274/275 present, tests pass**
  STATUS: DONE · EVIDENCE: `[F274-CTORGATE] Lgf1;.g initializer type Lwg0; has no ()V ctor -> honest null` fires in fresh dooz; `[F275-SVCINFO] MISS → PackageManager$NameNotFoundException` ×2 app-caught in fresh opencalc; anchor a976d2f9 unchanged · COMMAND: `miniandroid run ...` (run/cont23/dooz_prefix_r1, opencalc_prefix) · FILE: dalvik_engine.cpp (2×F274-CTORGATE sites, 3×F275-SVCINFO sites)
- [x] **Re-run corrected sweep harness; exit-code handling verified**
  STATUS: DONE · EVIDENCE: locals declared before engine call, `rc=$?` immediately after; fresh sweep prints rc truth (all 5 targets rc=1 PARTIAL SUCCESS per engine law main.cpp:992) · COMMAND: `bash scripts/cont21_family_sweep.sh sweep` · FILE: `scripts/cont21_family_sweep.sh` L14-24
- [x] **Preserve pre-fix evidence before overwrite runs**
  STATUS: DONE · EVIDENCE: CONT-22 wave artifacts untouched (committed); fresh wave work isolated under `run/cont23/` · FILE: `run/cont23/`
- [x] **Separate SUCCESS / PARTIAL_SUCCESS / failure by exit-code contract**
  STATUS: DONE · EVIDENCE: all affected targets rc=1 PARTIAL SUCCESS; dooz frame truth `DEFAULT_BACKGROUND_ONLY, first_missing_stage=APP_DRAW_OPS` · COMMAND: `grep -E "Status|verdict=" run/cont23/dooz_prefix_r1/run.log` · FILE: `evidence/cont23/GRAPHICAL_PROGRESS.md`
- [x] **Phase 1 — read local measure/layout implementation + call chain**
  STATUS: DONE · EVIDENCE: R8↔upstream map extended (Lzs0=MeasureAndLayoutDelegate; Lel0=LayoutNode; Lbt0=MeasurePassDelegate; Lpz0/Lxk0/Lug0=Node/Outer/InnerCoordinator; Ls21=UiApplier) with disassembly (`scripts/cont3_disasm_full.py`) + 62-method Lel0 descriptor dump (`scripts/cont23_dexinfo.py`) · FILE: `evidence/cont23/FIRST_DIVERGENCES.md` §2 table
- [x] **Read upstream AndroidX Compose source for the failing contract**
  STATUS: DONE · EVIDENCE: `upstream/s43/ui_android_src` LayoutNode.kt (attach/detach/removeAt/insertAt/onChildRemoved), UiApplier.android.kt, MeasureAndLayoutDelegate.kt (performMeasureAndLayout — owner-swallowed exceptions law), MeasurePassDelegate.kt (placeAt→onNodePlaced→markNodeAndSubtreeAsPlaced→layoutChildren); navigation-compose/runtime 2.9.8 sources fetched (NavHost.kt visibleEntries gate); dooz app source (github.com/yamin8000/Dooz) · FILE: `evidence/cont23/FIRST_DIVERGENCES.md` §2-§4
- [x] **Trace the real path; establish which stages execute and which do not**
  STATUS: DONE · EVIDENCE: Composer/SlotTable executes (Lrn1 ×10366, Lom lambda invokes ×14); applier insert+remove execute (6 attaches/3 detaches, runtime chain captured); measure executes ×9; placement executes ×2; draw walk descends (I()=TRUE ×32); CanvasDrawScope.draw = 0 (content absent, not draw-broken) · COMMAND: `MINIANDROID_METHOD_TRACE=1 / MINIANDROID_FIELD_TRACE=Lel0;.r / MINIANDROID_CL_TRACE=...` runs · FILE: `evidence/cont23/FIRST_DIVERGENCES.md` §1-§3, `run/cont23/dooz_mtrace|dooz_ft_owner|dooz_cl*`
- [x] **Identify the first semantically incorrect operation, not the final symptom**
  STATUS: DONE · EVIDENCE: the decisive op = UiApplier.remove(0,1) on the NavHost content subtree in the first applyChanges (upstream-legal per the app's recomposition semantics) + the SECOND applyChanges never running (frame-pump quiescence at tick 3; Recomposer runner never re-arms; reproduced at 120 s/60 frames) → F-NEW-277 · FILE: `evidence/cont23/FIRST_DIVERGENCES.md` §4, registry F-NEW-277
- [x] **Record upstream method, local method, contract, inputs, expected/actual, first-divergence trace**
  STATUS: DONE · EVIDENCE: per-link table with law sources and runtime chains (including the kotlinx " is cancelling" teardown and [PARK-DRAIN] park work_units=1 stall state) · FILE: `evidence/cont23/FIRST_DIVERGENCES.md`
- [x] **Reuse existing runtime abstraction where it represents the correct behavior**
  STATUS: DONE (n/a for shipped code — no patch landed; the falsified trial reused the existing `dispatch_activity_lifecycle_callbacks` law and was reverted when the outer engine's existing law was confirmed)
- [x] **Smallest generic semantic fix; no package checks / Dooz branches / hardcoded dims / fabricated objects / forced flags / PC advancement / exception suppression / full-runtime port**
  STATUS: DONE — the trial patch satisfied all constraints AND was still reverted because it duplicated an existing law; shipped tree = byte-exact prior binary (verified by sha) · COMMAND: `git checkout -- miniandroid/src/dex/dalvik_engine.{cpp,h} && make -j1 BUILD_DIR=build && sha256sum build/miniandroid` → fa88902fdee6e982 · FILE: `evidence/cont23/CONT23_REPORT.md` §2
- [x] **Focused regression test that fails before the fix and passes after**
  STATUS: PARTIAL (honest split) — EVIDENCE: `fixtures/lifecycle_transaction_probe` locks the existing G09 start/resume transaction law (5/5 PASS at fa88902f; would FAIL if the pairing regressed — it is the regression test for the law this wave's hypothesis wrongly believed missing); no shipped-engine fix exists this wave, hence no before/after fix pair for a NEW engine change · COMMAND: `bash scripts/cont23_build_probe.sh && miniandroid run upload/lifecycle_transaction_probe.apk ...` · FILE: `fixtures/lifecycle_transaction_probe/src/com/probe/lctx/MainActivity.java`, `run/cont23/lctx_probe/run.log`
- [x] **Validate the same primitive on an independent target**
  STATUS: DONE — the lifecycle-transaction primitive validated on an independent plain-`Activity` app (the probe) vs dooz's `ComponentActivity` (both dispatch the full pairing at fa88902f: probe 5/5; dooz androidx callbacks ins=2427/1842) · FILE: `evidence/cont23/FIRST_DIVERGENCES.md` §5
- [x] **Required graphical proof for Dooz (before/after: nodes, measure counts, child measurement, placement, draw ops, pixels, screenshot SHA, uncaught, exit, interaction)**
  STATUS: DONE (deltas honestly all 0 — engine unchanged) · EVIDENCE: full table — nodes 6/6/3, measure ×9(0 exc), placeAt ×2, isPlaced TRUE ×32, CanvasDrawScope.draw 0, app pixels 0, sha d602648e8e401895, uncaught 0, rc=1 PARTIAL, interaction unverified · FILE: `evidence/cont23/GRAPHICAL_PROGRESS.md`
- [x] **Phase 2 — cross-family confirmation per first-divergence evidence**
  STATUS: PARTIAL (honest) — EVIDENCE: the F-277 fanout is predicted (flow-collect/navigation Compose apps) but not confirmable until a fix lands; family sweep re-run with rc-truth (dooz 0, stopwatch 0, opencalc 4, telegram 9, forkgram 9 family-internal — identical to CONT-22) · FILE: `evidence/cont23/GRAPHICAL_PROGRESS.md`
- [x] **View-based regression target**
  STATUS: DONE · EVIDENCE: anchors opencalc/unote/microtimer/tictactoedeluxe ×3 all MATCH (shared framework behavior unchanged)
- [x] **libGDX target examination (tictactoe/bouncy)**
  STATUS: BLOCKED (recorded, not fixed) — EVIDENCE: the Compose frontier consumed the wave per the mission's honesty clause; P10 record stands (bouncy GL20Renderer/EGL native init; tictactoe preserveEGLContextOnPause/onResume faces — native ABI prerequisite before frame submission) · FILE: `evidence/cont23/CONT23_REPORT.md` §6
- [x] **Phase 3 — anchor, negative, probe suites with canonical commands**
  STATUS: DONE · EVIDENCE: anchors 18/18 ×3 MATCH; probe battery fcol 20/20, f259 7/7, f259g 12/13 (same known-honest F259-L row), f266 6/6, f268 · COMMAND: `bash scripts/cont21_family_sweep.sh anchors && bash scripts/cont21_build_probes.sh && python3 scripts/cont16_probe_run.py run/cont23/probes fcol f259 f259g f266 f268`
- [x] **Three fresh runs for important results**
  STATUS: DONE · EVIDENCE: dooz anchors ×3 + prefix ×2 + sweep + long-run all recorded separately (run/cont23/); anchor suite ×3 per target
- [x] **Per-target evidence table (binary/APK/execution/divergence/state/rendering/interaction/reproducibility/regression)**
  STATUS: DONE · FILE: `evidence/cont23/GRAPHICAL_PROGRESS.md`
- [x] **Screenshot SHA treated as reproducibility, not correctness**
  STATUS: DONE · EVIDENCE: d602648e8e401895 = reproducibility proof; compared against expected visual result = background-only (no app content) — recorded as NOT app-content · FILE: `evidence/cont23/GRAPHICAL_PROGRESS.md`
- [x] **CONT22_AUDIT.md created**
  STATUS: DONE · FILE: `evidence/cont23/CONT22_AUDIT.md` (10 claims: 9 TESTED, 1 SUPERSEDED)
- [x] **FIRST_DIVERGENCES.md created**
  STATUS: DONE · FILE: `evidence/cont23/FIRST_DIVERGENCES.md`
- [x] **GRAPHICAL_PROGRESS.md created**
  STATUS: DONE · FILE: `evidence/cont23/GRAPHICAL_PROGRESS.md`
- [x] **CONT23_REPORT.md created**
  STATUS: DONE · FILE: `evidence/cont23/CONT23_REPORT.md`
- [x] **Root registry updated (reuse IDs; new F-NEW only for genuinely new defects)**
  STATUS: DONE · EVIDENCE: registry 586 rows — F-NEW-277 registered CLASSIFIED P0 (genuinely new root, runtime-pinned); NO root registered for the falsified lifecycle hypothesis (no defect exists); F-NEW-265 verified_current extended (no duplicate) · COMMAND: `python3 scripts/cont23_registry.py` · FILE: `root_registry.json`, commit `26cf1b49`
- [x] **Worklog updated in established format**
  STATUS: DONE · FILE: `worklog.md` (CONT-23 section appended)
- [x] **Record unresolved/blocked honestly**
  STATUS: DONE · EVIDENCE: this checklist's PARTIAL/BLOCKED marks; report §8 blockers; no claim of graphical movement (all deltas 0, stated)
- [x] **Final questions answered with evidence**
  STATUS: DONE · FILE: `evidence/cont23/CONT23_REPORT.md` §10

## Answers to the mission's final questions (evidence-backed)

1. **Exact first semantic divergence at the dooz measure/layout frontier?** None remains inside measure/layout: `Lzs0.m` (MeasureAndLayoutDelegate.measureAndLayout) runs ×9 with zero exceptions; the decisive operation moved to the composition layer — the first-frame applyChanges executes `UiApplier.remove(0,1)` on the NavHost content subtree (runtime chain `Ls21.Y → Lg21.a → Lv02.j(0,1) → Lel0.Q → Lel0.M → Lel0.h`, faithful to upstream ui-1.11.4), and the destination-arriving recomposition never runs.
2. **Upstream source law?** ui-1.11.4 LayoutNode.removeAt/detach + UiApplier.remove (removal is upstream-legal); navigation-compose/runtime 2.9.8 NavHost.kt `visibleEntries.lastOrNull()` + `collectAsState()` produceState law; Recomposer.kt runRecomposeAndApplyChanges per-frame await; AndroidUiDispatcher.android.kt one-MessageQueue dispatch (whichever-path-wins must run the continuations); AOSP MessageQueue nativePollOnce wake law.
3. **What generic code changed and why is it not application-specific?** Nothing shipped: the single candidate patch was falsified by its own probe (the law already existed in the outer engine) and reverted to the byte-exact prior binary. The probe (app-agnostic, plain-Activity) ships as the law's regression lock.
4. **Did Dooz progress into placement/drawing/app-owned pixels?** Placement: yes for the chrome tree (2 place-writer executions, 3 nodes isPlaced=TRUE). Drawing/pixels: no (`Lgl0.c` CanvasDrawScope.draw = 0; frame truth DEFAULT_BACKGROUND_ONLY; anchor d602648e8e401895 unchanged ×5).
5. **Independent confirming target?** Not claimable for a fix (none landed). The lifecycle primitive itself was independently validated (probe = plain-Activity app vs dooz = ComponentActivity; both dispatch the full start/resume pairing).
6. **libGDX frame + input-driven state change?** No: tictactoe/bouncy remain blocked at GL/EGL native initialization (preserveEGLContextOnPause / GL20Renderer init faces) — a native-load prerequisite upstream of frame submission and input; not attacked this wave (no speculative fix; recorded honestly).
7. **Next shared root?** **F-NEW-277 (P0) — recomposition starvation at the frame-pump quiescence boundary.** Ranked by: direct causal pin to the F6 pixel frontier (pump-level traces, 3-tick stall reproduced at 120 s/60 frames); small bounded fix surface (re-arm parked AndroidUiDispatcher continuations at the quiescence boundary without breaking the F-115b frozen launch-frame law; 18/18 frozen anchors as the hard gate); everything downstream already proven healthy (lifecycle RESUMED, measure, placement, draw walk, canvas bridge); explicit cross-family fanout (all flow-collect/navigation Compose apps).
"""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers=HDRS, method="POST")
with urllib.request.urlopen(req) as r:
    res = json.load(r)
print("posted:", res.get("html_url"))
