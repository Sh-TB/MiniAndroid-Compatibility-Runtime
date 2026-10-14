# R-NEW-369 — Color.rgb(III)I unimplemented — transparent paints (silent blank)

**Status:** VERIFIED-FIXED · **Fix commit:** `c1f4d81c` · **Session:** S50

## Problem
Color.rgb REC-MISSed and returned 0 (alpha 0). Every surface painted with Color.rgb rendered invisible — a silent-blank failure class with no error signal.

## Root Cause
no bridge entry for Landroid/graphics/Color;.rgb

## Fix
AOSP Color.java law: rgb(r,g,b) = 0xFF000000 | (r<<16) | (g<<8) | b (opaque)

## Upstream Law
AOSP android.graphics.Color.rgb

## Test
s50_sandbox_probe pixel assertions: exact hex colors (c8:8c:00 amber / 00:a0:00 green / 1e:50:c8 blue) sampled from rendered frames

## Runtime Impact
custom-drawn UIs using Color.rgb render visibly; removes a silent-blank class

## Evidence
- Protocol `scripts/cleanup/s50_sandbox_test.sh`: **ALL PASS** (20/20 assertions, 4 runs)
- `evidence/cleanup/S50_SANDBOX_EVIDENCE.json` (SHA-256 `e871df64648dd928…`)
- Run screenshots SHA-pinned in `proof.json` (fresh-state determinism: run1 == run4;
  state transition: run1 != run2)
- Battery gate ALL PASS 94/94 at the fixes-included build
- Registry: `root_registry.json` → `R-NEW-369`
