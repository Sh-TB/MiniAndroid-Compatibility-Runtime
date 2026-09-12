# EXP-086 — Baseline Capture (Phase 0)

**Date:** 2026-08-22
**HEAD:** bec6efc851e2a8a32c909d02f5957da043004230
**Branch:** main

---

## Build State

- **Compiler:** g++ (Debian 14.2.0-19) 14.2.0
- **Architecture:** x86_64
- **Binary size:** 43,478,744 bytes (42 MB)
- **Binary path:** `miniandroid/build/miniandroid` (untracked, gitignored)
- **Source size:** 11.03 MB tracked

## Unit Test Result

```
[TEST] Testing API Stubs...
  [PASS] Bundle operations
  [PASS] TextView operations
  [PASS] Activity operations
[TEST] Testing Trace Engine...
  [PASS] Trace Engine operations
[TEST] Testing Paint & Canvas...
  [PASS] Paint & Canvas operations
[TEST] Testing View Hierarchy...
  [PASS] View hierarchy operations

Test Results: 4 passed, 0 failed
```

## Source Tree Purity

```
OK: source tree is pure (no violations).
```

## Tracked Artifact Counts

| Category | Count |
|---|---:|
| Tracked files | 495 |
| Tracked APKs | 0 |
| Tracked run/ files | 0 |
| Tracked build/ files | 0 |

## APK Corpus Status

All 15 APKs in `tests/corpus/apks.json` report `APK_FOUND` with matching SHA256:

| Name | Local Path |
|---|---|
| Telegram | `miniandroid/download/exp038_telegram/Telegram.apk` |
| gmdice | `miniandroid/download/exp073_real_apps/de.duenndns.gmdice_8.apk` |
| TicTacToe | `miniandroid/download/tictactoe.apk` |
| OpenLauncher | `miniandroid/download/exp076_corpus/com.benny.openlauncher_39.apk` (corrupted ZIP) |
| Dooz | `miniandroid/download/exp076_corpus/io.github.yamin8000.dooz_18.apk` |
| BGClock | `miniandroid/download/exp076_corpus/nl.hansdezwart.bgclock_2.apk` |
| Stopwatch | `miniandroid/download/exp076_corpus/com.github.muellerma.stopwatch_6.apk` |
| Simple Keyboard | `miniandroid/download/exp076_corpus/rkr.simplekeyboard.inputmethod_145.apk` |
| MicroTimer | `miniandroid/download/exp076_corpus/dubrowgn.microtimer_8.apk` |
| uNote | `miniandroid/download/exp076_corpus/app.varlorg.unote_30.apk` |
| Notes | `miniandroid/download/exp073_real_apps/org.billthefarmer.notes_139.apk` |
| Simple Stopwatch | `miniandroid/download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk` |
| Chess Clock | `miniandroid/download/exp073_real_apps/com.chessclock.android_29.apk` |
| Heading Calculator | `miniandroid/download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk` |
| Tiny Music Player | `miniandroid/download/exp037_real_apks/TinyMusicPlayer.apk` |

## B1–B6 Status (carried over from EXP-085)

| ID | Title | Status | Evidence |
|---|---|---|---|
| B1 | Renderer PNG output broken | BLOCKED | gmdice/Telegram produce 6.2 MB PPM, no PNG; PNGWriter IDAT zlib invalid |
| B2 | AXML view inflation incomplete | BLOCKED | APKs execute onCreate but no view_tree.json produced |
| B3 | SQLite not implemented | BLOCKED | No native bridge; `miniandroid/src/storage/` only has file_sandbox.cpp |
| B4 | Handler/Looper drain incomplete | BLOCKED | HandlerShadow::drain_ready() only called for Telegram-specific paths |
| B5 | Telegram entry-point detection broken | BLOCKED | Manifest parser picks `org.telegram.messenger.web` instead of `org.telegram.messenger` |
| B6 | Duplicate callback/event dispatch | BLOCKED | onNextPressed observed multiple times in Telegram run |

## Real APK Baseline Results

Saved to local (gitignored) `run/exp086_baseline/`.

### gmdice (`run/exp086_baseline/gmdice/`)
- Package: `de.duenndns.gmdice` ✅ correct
- Exit code: 0
- Status: FAILURE (per report.md)
- view_tree.json: NOT produced (B2)
- screenshot.png: NOT produced (B1)
- screenshot.ppm: 6,220,817 bytes (1080×1920 raw)
- api_trace.json: 14 KB, 51 ExecutionEngine calls
- Crash log: empty (no runtime crash)

### tictactoe (`run/exp086_baseline/tictactoe/`)
- Similar to gmdice: bytecode executes, no view_tree, PPM-only screenshot

### Telegram (`run/exp086_baseline/telegram/`)
- Package: `org.telegram.messenger.web` ❌ (B5 bug confirmed)
- Exit code: 0
- Status: FAILURE (per report.md)
- view_tree.json: NOT produced (B2)
- screenshot.png: NOT produced (B1)
- screenshot.ppm: 6,220,817 bytes
- api_trace.json: 3.85 MB (12,549 ExecutionEngine calls — heavy class loading)
- The runtime picked fallback entry `Landroid/media/MediaDrmThrowable;.<clinit>`
  because the manifest-provided `org.telegram.messenger.web.LaunchActivity`
  didn't exist in any DEX file.

## uNote Result

uNote (`app.varlorg.unote_30.apk`) not in this baseline run; will be tested in Phase 11.

## Calculator Result

No dedicated small calculator APK in current corpus (headingcalculator is the closest match). Will be tested in Phase 6.

## Run Directory Policy

`run/exp086_baseline/` is LOCAL ONLY — gitignored under the existing
`.gitignore` rule `miniandroid/run/`. Will not be committed.

## Plan for Phase 1

Phase 1 will fix B5 by building a **generic** Android manifest resolver
that understands `<intent-filter>` with `<action android:name="android.intent.action.MAIN" />`
and `<category android:name="android.intent.category.LAUNCHER" />`.
The resolver will be tested against 10 synthetic manifest cases before
any real APK is run.
