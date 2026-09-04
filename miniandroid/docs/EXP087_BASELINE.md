# EXP-087 — Forensic Baseline (Phase 0)

**Date:** 2026-08-23
**HEAD:** 0f7b743b5baa2cb34916e5f10dc94b5da71f3b5e
**Branch:** main

## Build/Test/Purity Status

- **Build:** miniandroid binary built (43.5 MB), all source compiles cleanly
- **Unit tests:** 4/4 PASS
- **Source purity:** PASS (0 violations)
- **Tracked APKs:** 0
- **Tracked run/ files:** 0
- **Tracked build/ files:** 0
- **Tracked file count:** 509

## APK Baseline Metrics

| APK | Status | PNG size | PPM size | api_trace | view_tree.json | PIL non-black (sampled) |
|---|---|---:|---:|---:|---|---:|
| gmdice | SUCCESS ✅ | 10535 B | 6.2 MB | 14 KB | NO | 848 |
| tictactoe | SUCCESS ✅ | 10535 B | 6.2 MB | 649 KB | NO | 848 |
| headingcalculator | SUCCESS ✅ | 10535 B | 6.2 MB | 15 KB | NO | 848 |
| telegram | SUCCESS ✅ | 10535 B | 6.2 MB | 3.8 MB | NO | 848 |
| unote | SUCCESS ✅ | 10535 B | 6.2 MB | 25 KB | NO | 848 |

## Critical Observation

**ALL 5 APKs produce IDENTICAL PNG output (10535 bytes, 848 non-black pixels).**

This confirms the B2 blocker: the renderer uses `create_view_from_dalvik_result()`
which creates a SYNTHETIC HelloWorld view for every APK, regardless of what
the APK's AXML layout actually contains. The PNG content is the same fallback
"HelloWorld" text rendered at the same position for every APK.

## Per-APK Entry-Point Verification (from EXP-086)

| APK | Launcher Activity | onCreate Entered |
|---|---|---|
| gmdice | de.duenndns.gmdice.GameMasterDice | YES |
| tictactoe | com.emmanuelmess.tictactoe.AndroidLauncher | YES |
| headingcalculator | org.debian.eugen.headingcalculator.MainActivity | YES |
| telegram | org.telegram.ui.LaunchActivity | YES (757 instructions) |
| unote | app.varlorg.unote.NoteMain | YES |

## B-Blocker Status (carried from EXP-086)

| ID | Title | Status |
|---|---|---|
| B1 | PNG Writer | ✅ FIXED (PIL-decodable) |
| B2 | AXML view inflation | ❌ BLOCKED — synthetic view used |
| B3 | SQLite | ❌ BLOCKED — no native bridge |
| B4 | Handler drain | ⚠️ WIRED — no trigger |
| B5 | Entry-point resolution | ✅ FIXED |
| B6 | Duplicate callback | ❌ BLOCKED — needs B2+B4 |

## Plan for Phase 1

Trace the setContentView chain to find where the runtime captures the
layout resource ID but fails to inflate AXML. The AXML parser exists
(`miniandroid/tools/exp075_layout_inflater.py`) but is a Python post-processor,
not integrated into the C++ runtime.
