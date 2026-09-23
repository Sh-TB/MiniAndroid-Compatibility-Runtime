# WS-C3 CORPUS — Corpus status in the Unified campaign

**Date:** 2026-08-27 · HEAD: `86bd646`

## New campaign entry

| Field | Value |
|-------|-------|
| App | Telegram |
| Version | 12.10.1 (versionCode 70389) |
| Package | org.telegram.messenger.web |
| Source | https://telegram.org/dl/android/apk (redirect → cdn4.telesco.pe) |
| APK SHA256 | `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` |
| Size | 73,028,244 bytes |
| DEX count | 5 (classes..classes5.dex) |
| Manifest entries | 11,576 |
| Depth reached | L4 (resources) — login/SMS-family execution + rendering; input was not tested on this build |
| First divergence | texts = R field names instead of values (per-version resource map) |
| First failure | — (0 errors) |
| Screenshot | run/uc_v12_run1/screenshot.png (3/3 identical SHA `06fb40da…`) |
| Manifest drift | the manifest expected 10.14.5 (`193ad551…`) → HASH MISMATCH recorded (§18) |

## Execution result

| Metric | Value |
|--------|-------|
| exit code | 0 |
| classes loaded | 12,544 (5 DEX) |
| non-white pixels | 41,233 / 2,073,600 (1.99%) |
| trace events | 12,582 |
| errors | 0 |
| determinism | 3/3 identical SHA |
| RLottie pending views | 7 identified |

## Suggested field structure for each corpus entry (per §7 charter)

```
name, version, package, source_url, source_repo, source_sha, apk_sha256,
size, dex_count, depth(L0-L10), first_divergence, first_failure,
screenshot_sha, run_count, deterministic(bool), notes
```

## Honest report of the previous status (per §18)

- The "100+ corpus" claim exists in previous documents but its full registry is not in the clone
  → the currently verifiable count: **limited manifest entries + 4 items**
  (`tests/corpus/apks.json`) + OA_API_MAP results (8 apps). Overall status:
  **UNKNOWN ≥ 8**, not PASS.
- Next priority: upload the full corpus results CSV/JSON to `tests/corpus/results/`.
