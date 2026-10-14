# R-NEW-368 — getFilesDir hard-coded path — sandbox/package-scope violation

**Status:** VERIFIED-FIXED · **Fix commit:** `c1f4d81c` · **Session:** S50

## Problem
Context.getFilesDir() returned the literal '/tmp/miniandroid/files' for every app: app files landed outside --data-root and outside any package dir (M3 F-012 one-root law + R-NEW-367 package-dir law violated). A second File.getAbsolutePath fallback stub answered the same literal for EVERY File object and shadowed the authoritative R-NEW-347 handler.

## Root Cause
two independent hard-coded path literals at different dispatch layers (get_or_create_singleton File default; bridge_to_api getAbsolutePath stub)

## Fix
getFilesDir bridge resolves <app_data_root>/<running-package>/files and creates it; the bogus getAbsolutePath stub was DELETED (R-NEW-347 name-component handler is the single source of truth); File singleton default made law-conformant

## Upstream Law
AOSP ContextImpl.getFilesDir -> /data/data/<pkg>/files; M3 F-012 one app-data root; R-NEW-367 package-dir; OpenJDK File.getAbsolutePath (R-NEW-347)

## Test
scripts/cleanup/s50_sandbox_test.sh — asserts <root>/<pkg>/files exists after run; FILE PATH LAW band renders blue (parent ends with '<package>/files') in all 4 runs

## Runtime Impact
app-private files are now genuinely package-scoped under the declared sandbox; cross-package file contamination surface eliminated

## Evidence
- Protocol `scripts/cleanup/s50_sandbox_test.sh`: **ALL PASS** (20/20 assertions, 4 runs)
- `evidence/cleanup/S50_SANDBOX_EVIDENCE.json` (SHA-256 `e871df64648dd928…`)
- Run screenshots SHA-pinned in `proof.json` (fresh-state determinism: run1 == run4;
  state transition: run1 != run2)
- Battery gate ALL PASS 94/94 at the fixes-included build
- Registry: `root_registry.json` → `R-NEW-368`
