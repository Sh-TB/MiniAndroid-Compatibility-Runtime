# WS-C3 PRIMARY TRANSFER

**To:** Primary Coder · **From:** WS-C3 (Unified Coder) · **Date:** 2026-08-27

## T1. Merge UC-CM-001 (ready)
- commit `86bd646` / attached patch file. Zero regression on Telegram 12.10.1 (3/3 SHA).
- Closes F012; STUBBED values become type-aware.
- CONFIDENCE: HIGH · RISK: LOW · EVIDENCE: `SOURCE_CHANGES.md`

## T2. Implement Uri (the biggest measured gap)
- `Landroid/net/Uri` **has no handler at all** (grep over the whole src = 0) while the
  charter assumed it 24/24 proven (probably it was the Python tests).
- ACTION: bridge handler for parse/Builder/scheme/authority/path/
  queryParameter/getQueryParameter/normalizeScheme + a simple object model.
- Reference source: AOSP `Uri.java` / libcore. EVIDENCE: WS-C3_KNOWLEDGE §UC3-001
- CONFIDENCE: HIGH (a definite gap) · BENEFIT: deep-link/content URIs in the corpus

## T3. Add SystemClock (F004 — easy and frequent)
- `uptimeMillis/elapsedRealtime*` → from `clock_gettime(CLOCK_MONOTONIC/BOOTTIME)`.
  Also add a deterministic-clock switch (for reproducibility).
- CONFIDENCE: HIGH · LOC: ~40

## T4. Minimal components (F010): BroadcastReceiver with internal dispatch only
- First goal: manifest-declared receivers with explicit intent filters.
  Keep the Google census separate (§31 census-only).

## T5. F015 (superclass-bridge retry)
- After UC-CM-001: on `try_recursive_invoke` path failure, before the bridge,
  try the superclass chain. Small and generic.

## T6. Put the real corpus registry in the repo
- The 100+ claim is not verifiable from the clone (only a few manifest entries).
  `WS-C3_CORPUS.md` has the field template.

## DO NOT
- Do not blindly take F012-AMPLIFIER (commit ab48fbc from an unmerged branch) —
  UC-CM-001 fulfilled its goal with less risk.
- Do not implement wide SQLite/Google support "just because it's there" (§31).
