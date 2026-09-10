# ROOT DISCOVERY EVIDENCE — the F-044 worked example
# (MASTER CAMPAIGN 4; every claim below is traceable to a log line or a
#  probe output from runs c4_dooz_run1..9)

## The chain, from symptom to root

```text
ROOT_DISCOVERY
APK=dooz_18.apk (sha d81292cd, EXACT registry pin)
CLASS=LF/F$a; (DerivedSnapshotState record)
METHOD=d (dependency-version scan, 276 bytes)
CALLS=LP/l;.r (SnapshotKt.readable), LP/j;.q (SnapshotIdSet.contains),
      Ljava/lang/System;.identityHashCode
LAW = version hash = ((7*31 + ihc)*31 + recordId), compared against the
      cached record.g to decide whether the derived value must recompute
ROOT = F-044 (see below)
```

## Before (M6 HEAD, honest baseline)

| Metric | Value |
|---|---|
| rc | 1 |
| final exception | NullPointerException via Intrinsics (LM1/i.c) from AndroidComposeView.onAttachedToWindow @0x0112 (checkNotNull(getViewTreeOwners())) |
| APP BOUNDARY unwinds | 1 |
| ComposeView children | 1 (AndroidComposeView attached, 0x105 tall) |
| non-white pixels | 0 / 2073600 |
| framebuffer SHA | 31ddd4d5b8e6d18e… (deterministic BLANK) |

## The investigation (evidence-first, no guessing)

1. **DEX ground truth** (androguard, per-instruction):
   - `AndroidComposeView.<init>`: `c0 = LF/w.e(…) = mutableStateOf(null)`;
     `d0 = LF/w.d(AndroidComposeView$o) = derivedStateOf(calculation)`.
   - `getViewTreeOwners()` = `d0.getValue()` — a DERIVED read.
   - `LF/F.getValue` → `r(record, snapshot, validate, policy)`:
     validity via `LF/F$a.c` (watermark c/d vs snapshot d()/h()), then a
     dependency re-scan via `LF/F$a.d` (SWAR walk of the record's Lh/u
     dependency table; per dependency `P/l.r(firstRecord, snapshotId,
     invalidSet)` then a rolling hash incl. `System.identityHashCode`).
2. **Live field traces** (`MINIANDROID_FIELD_TRACE`): the write to c0
   commits correctly (new record obj#1166, snapshotId=4, value=owners,
   prepended, recordModified, notifyWrite) — the WRITE side is clean.
3. **Probe round 1** (`MINIANDROID_F044_DIAG` at law-method returns):
   `LF/F$a.d()` returned **type=9 (BOOLEAN) int_val=1** on EVERY call —
   while the DEX says it returns the version hash (an int).
4. **Probe round 2** (register-file dump at .d's return, capped at 3):
   `v4 = INT32(6729)` — **the version hash was computed correctly in the
   register** — yet the RETURN was BOOLEAN(1).
5. **Root located**: `execute_return`'s CHAR-PROBE signature-aware
   retyping reads `current_method_descriptor_`. That field is set at
   frame entry but was **never saved/restored across recursive frames** —
   .d's last callee (`LP/j.q`, descriptor ")Z") left it stale, so .d's
   `)I` return was retyped `make_bool(6729 != 0)` → BOOLEAN(1). Cache-time
   and re-scan versions therefore ALWAYS compared equal (1 == 1); the
   dependency-change law was dead; the derived state was permanently
   stale; `getViewTreeOwners()` returned the pre-write null; the
   Intrinsics checkNotNull NPE crossed the app boundary.
6. **F-044 fix** (generic, no special-casing): save/restore
   `current_method_descriptor_` at the recursive-frame boundary — the
   same discipline `current_class_`/`current_method_` already obeyed.
7. **F-045** (§19 fail-soft sweep hit found in the same trace):
   `System.identityHashCode` was a silent REC-MISS → 0 for EVERY object —
   implemented per OpenJDK System.java law (lifetime-stable identity
   hash, 0 for null; engine: Fibonacci-mixed heap id, deterministic).

## After (F-044+F-045 at working tree, commit pending)

| Metric | Before | After | Delta |
|---|---|---|---|
| rc | 1 | 0 | NPE chain eliminated |
| APP BOUNDARY unwinds | 1 | 0 | attach completes through the LAST DEX instruction (setViewTranslationCallback) |
| dooz 3-run determinism | deterministic BLANK | deterministic (byte-identical SHA) | stable |
| non-white pixels | 0 | 0 (HONEST — no visual claim) | unchanged |
| Compose dispatch depth | attach killed at 0x0112 | AndroidUiDispatcher (J;.O) + J$c runnables + frame-clock context chain execute | frontier moved to the first-frame pump |
| micro-proof | — | f044_return_descriptor_law 7/7 GREEN, 3-run byte-identical (32b8a456…) | new |
| battery | 85 stages | 88 stages (F-044 build/run/golden) | +3 |

## Classification (§15 loading-impact taxonomy)

```text
F-044: LOAD-BLOCKING = NO; POST-LOAD EXECUTION = YES;
       FRAMEWORK = INDIRECT; COMPOSE-BLOCKING = WAS (now resolved);
       UI-BLOCKING = still yes via the remaining first-frame pump
F-045: POST-LOAD EXECUTION = YES; COMPOSE = YES (version-hash term);
       cross-app value: every hash-table/identity-hash consumer
```

## Honest frontier statement

DOOZ: EXECUTION FRONTIER ADVANCED — FINAL UI NOT YET PROVEN.
The remaining blocker is the Compose first-frame pipeline
(Recomposer frame → measure/layout/draw through the AndroidUiDispatcher /
MonotonicFrameClock delayed dispatch — the "scheduler pump" spotlight,
root-located but PENDING).
