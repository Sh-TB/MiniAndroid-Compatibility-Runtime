# RELEASE v0.0.3 — Chantecler (draft — final SHA256SUMS at packaging)

**Release chain (provenance policy):** source commit == tag commit ==
binary build commit. Fill the three hashes in the checklist below at
packaging time; the release notes must never describe assets built from a
different commit than the tag (the v0.0.2 gap, closed by policy).

- [ ] source/tag commit: `<hash>`
- [ ] linux-x64 artifact: `MiniAndroid-v0.0.3-Chantecler-linux-x64.tar.gz` — SHA256 `<hash>`
- [ ] windows-x64 artifact: `MiniAndroid-v0.0.3-Chantecler-windows-x64.zip` — SHA256 `<hash>`
- [ ] `SHA256SUMS_v0.0.3.txt` covering all assets
- [ ] battery: ALL PASS (88 stages) at the tag commit

## The three levels (§26)

### PROVEN

- **F-044 — per-frame return-descriptor law.** The recursive-frame
  save/restore now covers `current_method_descriptor_`. Pre-fix, an int
  return from any method whose last callee returned boolean collapsed to
  BOOLEAN(0/1) — a whole class of silent corruption. Micro-proof:
  `f044_return_descriptor_law` (ECJ+D8 real DEX) 7/7 bands GREEN,
  3-run byte-identical (`32b8a456…`). Real APK: dooz rc 1→0; the
  app-boundary NullPointerException (Intrinsics checkNotNull on
  `getViewTreeOwners()`) is eliminated; `onAttachedToWindow` executes to
  its last DEX instruction; 3-run deterministic.
- **F-045 — System.identityHashCode law** (OpenJDK System.java):
  lifetime-stable identity hash, 0 for null. Was a silent REC-MISS → 0
  for every object. Reached live in the dooz version scan.
- **F-040 — Arrays.fill family** (all primitives + Object, 2- and 4-arg)
  — 7/7 golden bands, 3-run byte-identical (`b3610c68…`).
- **F-041 — encoded_catch_handler negative-size law** (`|size|` typed
  pairs + catch-all; spec cross-checked against androguard).
- **F-042 — VALUE_LONG static-default 64-bit law.**
- **F-043 — Double/Float IEEE bit-conversion family** (NaN
  canonicalization for the non-Raw variants).
- Battery: 88 stages ALL PASS (85 + the F-044 build/run/golden stages).

### IMPROVED (execution advanced; full app success NOT claimed)

- **dooz (Compose lighthouse)**: rc 1→0; `onAttachedToWindow` completes;
  AndroidUiDispatcher (`J;.O`) + `J$c` runnables + MonotonicFrameClock
  context chain execute post-attach; framebuffer still 0 non-white —
  **"DOOZ: EXECUTION FRONTIER ADVANCED — FINAL UI NOT YET PROVEN"**.
- Derived-state dependency-change detection now works (the version-hash
  law) — the pre-condition for Compose recomposition correctness.

### REMAINING BOUNDARY

- Compose first-frame pump: Recomposer frame → measure/layout/draw via the
  AndroidUiDispatcher/MonotonicFrameClock delayed dispatch — root-located,
  PENDING (the next P0 battle).
- GLES dispatch hook (K-25), layout weight exactness, BitmapFont long
  strings, Telegram golden re-acquisition (K-26), obfuscated AXML safe
  abort — unchanged from v0.0.2, see README Known Limitations.

## Root-law ledger (status per §46)

| Root | Status |
|---|---|
| F-028 / F-028h | REAL-APK-PROVEN (M4) |
| F-029 | REAL-APK-PROVEN (M4) |
| F-030..F-033 | REAL-APK-PROVEN (M5) |
| F-035/F-035b | REAL-APK-PROVEN (M5) |
| F-036/F-039 | REAL-APK-PROVEN (M5) |
| F-040/F-041/F-042 | REAL-APK-PROVEN (M6) |
| F-043 | IMPLEMENTED / REAL-APK-REACHED (M6) |
| **F-044** | **REAL-APK-PROVEN (C4)** |
| **F-045** | **IMPLEMENTED / REAL-APK-REACHED (C4)** |

## Release package policy (§47)

The artifact contains the runtime binary, the demo APK + proof frames, and
SHA256SUMS. It never contains: compilers, toolchains, temporary logs,
build directories, source dependency dumps, credentials, or test APKs from
the SHA-pinned corpus (fetched by the reproducibility script instead).
