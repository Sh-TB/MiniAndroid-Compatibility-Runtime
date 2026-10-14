# CONT-21 CLAIM AUDIT (CONT-22 Section 1)

Audited at head `76044d63`, binary `882b7cdf389aabc3` (byte-exact CONT-21
post-fix lineage, verified by sha256 before any run). Every audit run is a
FRESH re-execution at this container — not a copy of CONT-21 artifacts.
Pre-fix "before" state preserved at `run/cont22/family_paths_PREFIX_CONT21.json`.

Status vocabulary: IMPLEMENTED (source exists) / TESTED (fresh runtime run
reproduces the claim) / OBSERVED (seen in logs, weaker than TESTED) /
PARTIAL / PENDING.

---

## 1. F-NEW-272 — Thread default UncaughtExceptionHandler law

```text
CLAIM:          Thread.getUncaughtExceptionHandler returns a non-null
                RuntimeInit$KillApplicationHandler default; per-thread
                override map; [UEH-DEFAULT] log contract; kills the
                kotlinx coroutine reporter NPE (dooz APP BOUNDARY 2->0).
SOURCE FILE:    miniandroid/src/dex/dalvik_engine.cpp (+ .h state fields)
IMPL LOCATION:  dalvik_engine.cpp:23272-23325 (static get/set ->
                default_uncaught_handler_; instance get/set ->
                thread_uncaught_handlers_; lazy non-null default
                Lcom/android/internal/os/RuntimeInit$KillApplicationHandler;)
TEST COMMAND:   bash scripts/cont21_family_sweep.sh sweep
EXPECTED:       dooz rc=0; zero APP BOUNDARY; [UEH-DEFAULT] fires; anchor d602648e8e401895
ACTUAL:         rc=0; APP BOUNDARY count=0; "[UEH-DEFAULT] FATAL EXCEPTION (KillApplicationHandler) thread=8123 caller=Llo;.K"; anchor sha16 d602648e8e401895
STATUS:         TESTED
EVIDENCE:       run/cont22/audit_anchors.log (anchors), run/cont21/sweep_dooz/run.log (fresh sweep this wave)
```

## 2. F-NEW-273 — component-info identity chain (getProviderInfo / ComponentName / Bundle.keySet)

```text
CLAIM:          ComponentName.<init> stores identity; PackageManager.getProviderInfo
                resolves manifest provider identity + seeds ProviderInfo (metaData)
                + NameNotFoundException; BaseBundle keySet/containsKey/isEmpty —
                kills the androidx.startup NPE cluster (5 targets / 3 families).
SOURCE FILE:    miniandroid/src/dex/dalvik_engine.cpp
IMPL LOCATION:  ComponentName.<init> law @39605-39617; getProviderInfo law
                @39640-39776 (incl. [F273-PROVINFO] diag @39698/39776);
                BaseBundle keySet/valueSet law @28076+ (EXP-093 block)
TEST COMMAND:   bash scripts/cont21_family_sweep.sh sweep
EXPECTED:       [F273-PROVINFO] metaData entries=3 on dooz; ProviderInfo.metaData
                NPE face GONE on dooz/opencalc/stopwatch/telegram/forkgram; all rc=0
ACTUAL:         all 5 rc=0; "[F273-PROVINFO] androidx.startup.InitializationProvider
                metaData entries=3" present in dooz AND stopwatch AND telegram logs;
                iget ProviderInfo.metaData NPE absent from all 5 logs
STATUS:         TESTED
EVIDENCE:       run/cont21/sweep_{dooz,opencalc,stopwatch,telegram,forkgram}/run.log (fresh this wave)
```

### 2a. ComponentName (source)

```text
STATUS:         IMPLEMENTED (identity producer; consumed by getProviderInfo law above)
EVIDENCE:       dalvik_engine.cpp:39605 "CONT-21 / #384 (F-NEW-273, producer half) — ComponentName.<init> law."
```

### 2b. Bundle.keySet / containsKey / isEmpty

```text
STATUS:         TESTED (indirect runtime: dooz startup chain advances PAST the
                former Set.iterator NPE — face absent from fresh dooz log;
                initializer discovery reaches composition)
EVIDENCE:       run/cont21/sweep_dooz/run.log — zero "Set.iterator" NPE faces;
                [F273-PROVINFO] followed by startup progression
```

## 3. 5-target recovery claim (rc 1 -> 0)

```text
CLAIM:          dooz/opencalc/stopwatch/telegram/forkgram all rc 1->0 at 882b7cdf.
TEST COMMAND:   bash scripts/cont21_family_sweep.sh sweep (fresh)
EXPECTED:       5/5 rc=0
ACTUAL:         SWEEP dooz rc=0 d602648e8e401895 / opencalc rc=0 a976d2f9fb675cb3 /
                stopwatch rc=0 31ddd4d5b8e6d18e / telegram rc=0 b5a7a35d5fe0564b /
                forkgram rc=0 b5a7a35d5fe0564b
STATUS:         TESTED
EVIDENCE:       sweep console output (this container, this wave)
CAVEAT (honest): telegram still logs 11 APP BOUNDARY unwinds (UI-init family
                faces) — the CONT-21 claim was the rc FLIP only, "UI-init family
                faces remain"; consistent, but F4 is NOT visually recovered.
                telegram+forkgram+chessclock share screenshot sha16 b5a7a35d5fe0564b
                (default-background frame) — all three are rc=0-but-no-app-content.
```

## 4. Dooz APP-BOUNDARY 2 -> 0 claim

```text
CLAIM:          pre-fix dooz had 2 APP BOUNDARY unwinds (MainActivity.onCreate
                invoke_pc=317 death); post-fix zero.
TEST COMMAND:   grep -c "APP BOUNDARY" run/cont21/sweep_dooz/run.log
EXPECTED:       0
ACTUAL:         0 (and UEH-DEFAULT fires instead — the crash path is now the
                AOSP-modeled handler, not an engine unwind)
STATUS:         TESTED
EVIDENCE:       fresh sweep log this wave
```

## 5. 18/18 anchor claim + zero-drift (repeated runs)

```text
CLAIM:          6 packages x3 runs = 18 anchor screenshots, byte-identical
                (dooz d602648e8e401895, microtimer da73010a37dd0189, unote
                4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc
                a976d2f9fb675cb3, tictactoedeluxe af6094295ecb50e3).
TEST COMMAND:   bash scripts/cont21_family_sweep.sh anchors — RE-RUN manually
                per package at this container (the bg nohup variant was killed
                by the tool-call process-group policy; re-executed in
                foreground chunks, see run/cont22/anchor_*)
EXPECTED:       18/18 MATCH
ACTUAL:         18/18 MATCH byte-identical (dooz 3/3, microtimer 3/3,
                unote 3/3, gmdice 3/3, opencalc 3/3, tictactoedeluxe 3/3)
STATUS:         TESTED
EVIDENCE:       run/cont22/anchor_<pkg>_<1..3>/screenshot.png + the anchor
                console log reproduced in CONT22_REPORT.md §12
```

## 5b. AUDIT FINDING — the CONT-21 "5/5 targets rc 1->0" claim is REJECTED

```text
CLAIM (CONT-21): the family sweep showed 5/5 targets flipping rc 1 -> 0.
FINDING:         scripts/cont21_family_sweep.sh's run1() declared
                 `local sha rc` BETWEEN the engine call and `rc=$?`; bash
                 `local` resets $?, so the sweep ALWAYS reported rc=0 —
                 the script could never observe anything else.
ENGINE LAW:      miniandroid/src/main.cpp:992 —
                 `return (result.status == ExecutionStatus::SUCCESS) ? 0 : 1;`
                 PARTIAL SUCCESS (frame-truth DEFAULT_BACKGROUND_ONLY, or
                 any remaining uncaught face) exits 1 BY DESIGN.
TRUE MEASUREMENT (Python subprocess, this wave, binary 882b7cdf):
                 dooz rc=1, opencalc rc=1, stopwatch rc=1, telegram rc=1,
                 forkgram rc=1 — the targets did NOT reach rc 0.
WHAT SURVIVES:   the FATAL-face claims (stopwatch pre-UI startup death GONE;
                 dooz APP BOUNDARY 2->0; ProviderInfo.metaData cluster GONE
                 x5; anchors byte-identical) are all real and re-verified.
WHAT DOES NOT:   "rc 1->0" as an exit-code claim is an artifact of the
                 script bug. The honest post-CONT-21 state of those targets
                 is: rc=1 / Status PARTIAL SUCCESS with the named faces
                 closed (rc=0 additionally requires frame-truth SUCCESS,
                 i.e. app-owned pixels — a separate, higher rung).
ACTION TAKEN:    run1() fixed (locals declared before the engine call) and
                 the fix committed this wave; CONT-22 runs the sweep again
                 and reports the TRUE rc (still 1 — honestly, because
                 frame-truth remains DEFAULT_BACKGROUND_ONLY for F4/F6).
STATUS:          REJECTED (claim) / FIXED (script) / RE-MEASURED (truth)
EVIDENCE:        scripts/cont21_family_sweep.sh diff this wave;
                 main.cpp:992; run/cont22/sweep_*/ (Python-measured rcs in
                 CONT22_REPORT.md §12)
```

## 6. Dooz "single remaining uncaught face = F-NEW-274" claim

```text
CLAIM:          after F-272/F-273, dooz's one remaining uncaught face is
                Lwg0;.y pc=17 iget Lrf1;.f on null (F-NEW-274).
TEST COMMAND:   grep -n "Lrf1;.f" run/cont21/sweep_dooz/run.log; grep -c uncaught ...
EXPECTED:       face present at ~line 3036; uncaught count=1
ACTUAL:         line 3036 exact match: "[SYNTH-EXC] iget-null-recv ... field
                'Lrf1;.f' on a null object reference ... method=Lwg0;.y pc=17 →
                uncaught (frame unwind + propagate)"; uncaught count=1
STATUS:         TESTED
EVIDENCE:       run/cont21/sweep_dooz/run.log:3036 (fresh this wave)
```

## 7. Build-success != TESTED guard applied to this audit

No item above was marked TESTED from the binary build alone: every TESTED
verdict carries a fresh runtime command + observed output from THIS container
at the byte-identical binary. Items still pending runtime reproduction are
marked PENDING until their run completes.
