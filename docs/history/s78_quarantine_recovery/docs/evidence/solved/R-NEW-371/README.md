# R-NEW-371 — String.startsWith/endsWith unimplemented — silent default-false

**Status:** VERIFIED-FIXED · **Fix commit:** `c1f4d81c` · **Session:** S50

## Problem
String.endsWith fell through the String bypass with a default-false result and no diagnostic (bypass path emits no REC-MISS), breaking app suffix checks.

## Root Cause
no bridge entry for the two methods

## Fix
OpenJDK law: endsWith(s) = startsWith(s, len-len(s)); startsWith(prefix[,toffset]); toffset bounds law -> false; null receiver -> deferred NPE

## Upstream Law
OpenJDK java.lang.String.startsWith/endsWith

## Test
band3 FILE PATH LAW blue in every run (endsWith check drives it)

## Runtime Impact
prefix/suffix string checks answer truthfully

## Evidence
- Protocol `scripts/cleanup/s50_sandbox_test.sh`: **ALL PASS** (20/20 assertions, 4 runs)
- `evidence/cleanup/S50_SANDBOX_EVIDENCE.json` (SHA-256 `e871df64648dd928…`)
- Run screenshots SHA-pinned in `proof.json` (fresh-state determinism: run1 == run4;
  state transition: run1 != run2)
- Battery gate ALL PASS 94/94 at the fixes-included build
- Registry: `root_registry.json` → `R-NEW-371`
