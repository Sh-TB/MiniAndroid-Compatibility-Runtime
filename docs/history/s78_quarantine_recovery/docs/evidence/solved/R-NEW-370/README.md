# R-NEW-370 — static WRITE skipped class init — later first init destroyed written statics (state loss)

**Status:** VERIFIED-FIXED · **Fix commit:** `c1f4d81c` · **Session:** S50

## Problem
Static fields written by app code BEFORE the class's first initialization were silently overwritten when init ran later and re-materialized defaults (observed: onCreate wrote b1Persisted=true; render-time first SGET ran <clinit>, zeroed the slot, screen showed fresh state).

## Root Cause
ensure_class_initialized missing in execute_sput/execute_sput_object (execute_sget had it since EXP-053); ensure_class_initialized re-materializes static defaults

## Fix
ensure_class_initialized(field_res.class_descriptor) added to both static-write handlers — putstatic is an active use (JLS 12.4.1); re-entrancy safe

## Upstream Law
JLS 12.4.1 class-initialization triggers; ART ClassLinker::EnsureInitialized

## Test
s50_sandbox_test.sh run2 GREEN-band assertions (persisted state visible on screen); SGET trace value=1 at draw; battery 94/94

## Runtime Impact
statics written during onCreate are visible to draw/callback paths — a whole state-loss class removed

## Evidence
- Protocol `scripts/cleanup/s50_sandbox_test.sh`: **ALL PASS** (20/20 assertions, 4 runs)
- `evidence/cleanup/S50_SANDBOX_EVIDENCE.json` (SHA-256 `e871df64648dd928…`)
- Run screenshots SHA-pinned in `proof.json` (fresh-state determinism: run1 == run4;
  state transition: run1 != run2)
- Battery gate ALL PASS 94/94 at the fixes-included build
- Registry: `root_registry.json` → `R-NEW-370`
