# S200 P0 TARGET A — microtimer (dubrowgn.microtimer) END-TO-END

Recorded: 2026-11-09. Verdict: **declared core feature 100% VERIFIED** —
launch → real UI → real input → real state transitions → correct next
frame → persistence → delete, with 3+1 equivalent clean runs and zero
uncaught exceptions.

## Identities
- APK: `upload/canonical_apks/dubrowgn.microtimer_8.apk`
  sha256 `79c6f730f64886e7…` (sha16 79c6f730f64886e7)
- Binary BEFORE fix: `97628b00d237f9eb` (S199 canonical)
- Binary AFTER F-NEW-621: **`96329a7ad50819d0`** (HEAD + dirty 3 files,
  `make -j2`; this is the S200 Target-A canonical identity)
- Package: `dubrowgn.microtimer` (launcher Activity → MainActivity)

## Declared core feature (from upstream source, not invented)
1. Keypad duration entry (0-9/00/backspace/clear) → `RoTimeControl` label
2. START → Room/SQLite INSERT (`alarm` table) + `TimerControl` row added
   to `layoutAlarms` (inside ScrollView)
3. Countdown via `Handler.postDelayed` ticks → row label decreases
4. Per-row PAUSE/RESUME → button swap + frozen/resumed countdown
5. Per-row DELETE → row removed + SQLite DELETE
6. Restart → `loadAlarms()` restores rows from SQLite

## Gates (S200 §4.1 A–M)
| Gate | Result | Evidence |
|---|---|---|
| A Launch | PASS | rc=0, 0 uncaught, setContentView dispatched, 26-node tree at boot |
| B Real UI | PASS | face: keypad 1-9/00/0 white-on-blue + input row + dividers (`face_probe_mtm_boot.jpg`, sha16 bbd350b6c14fbd52) |
| C ViewTree | PASS | boot tree 25 views exactly matching layout; post-start 31 views incl. TimerControl row [0,0 1080x126] with delete/label/pause children |
| D Text/controls | PASS | digit texts 1-9,00,0; hint `HH:MM:SS`; clickable flags true on all 12 keypad buttons |
| E Input→component | PASS | F117-TAP targets: '1'=134, '0'=147, START=148, PAUSE=264, RESUME=270 (the swapped-in button!), DELETE=253 |
| F State change | PASS | input-row label region +11350 px after digit taps (00:00:10 rendered); duration state drives label |
| G Next frame | PASS | per-tap frame diffs (changed=True each tap; bbox inside the correct regions) |
| H Core E2E | PASS | countdown live (3537 px churn, 00:00:10→09), pause FREEZES (0 px churn), resume restarts (2180 px churn), delete removes row (row_after_delete=False) |
| I Persistence | PASS | cold restart (no taps) restores row from Room DB; direct sqlite3: tables `alarm`/`sqlite_sequence`/`room_master_table`, row `(10,10,1,12290)`; label after fix = `00:00:07` (before fix = instant `00:00:00` — F-NEW-621 root cause) |
| J No fake output | PASS | structured content (text blobs, layout-consistent regions); not solid, not noise (center-patch law inverted) |
| K No uncaught | PASS | 0 FATAL / 0 uncaught / 0 APP BOUNDARY in every gate run |
| L 3 clean runs | PASS | rep1/rep2/rep3 (+f621_r1) identical: same tap-target signature [134,147,148,264,270,253], same transition booleans (T/F/T/False-row), 0 uncaught |
| M Artifacts | PASS | `MICROTIMER_ACCEPTANCE.json` + frames/ + view_tree.json + console logs + this file; screenshot sha16s: row frame 7913f6393e8051ff, final bbd350b6c14fbd52, restored 47ad887bf05c9c1d |

Wording (mission law): **100% of declared core feature verified; optional
features remain** (notifications/vibration/alarm-fire are documented
in-run boundaries — AlarmManager records schedules, alarms do not fire
in-run; those paths did not block the declared core loop).

## First divergence found and fixed (shared root cause)
F-NEW-621 DEVICE-CLOCK LAW: `SystemClock.elapsedRealtime()` returned the
in-process virtual clock (resets to 0 every run), but AOSP defines it as
monotonic since DEVICE BOOT, shared by every process. microtimer
persisted `expires_ms = ERT + 10s` in SQLite; on cold restart the
restored `expires_ms` (12290) sat in the FUTURE of the rewound clock →
`ceil((expiresMs-nowMs)/1000)=13 > totalSeconds=10` → Kotlin UInt
wraparound → `remaining.zero()` → timer instantly expired on restore.
Fix: device == data-root. Boot base persisted at
`<data-root>/data/system/device_clock`, read at run start, accumulated
clock written back at run end (monotone guard). Offset applied ONLY at
the SystemClock boundary (`HandlerShadow::device_now_ms()`); Looper
scheduling stays on the raw local clock (one authority, one offset).
Fresh store == fresh device boot (base 0) → deterministic reruns stay
byte-identical (goldens/floor re-verified).

## Gates after the fix (same binary 96329a7ad50819d0)
- Goldens 3/3 ALL HOLD: bouncy 8a6c24ac / unote 3b8dcb0a / dooz 31ddd4d5
  (dozz uncaught=6 = standing baseline, face pin unchanged)
- Floor 11/11 CLEAN
- gmdice 5-tap: PASS — 5 taps → 5 distinct result states, rerun identical
  (region hashes r1==r2: 8929ce63…, 40f4446a…, 33768519…, 5f3b1f65…, 4b066315…)

## Acceptance-test-first proof
The harness (`scripts/s200_microtimer_acceptance.py`) was written and its
probe phase run on the UNMODIFIED canonical binary 97628b00d237f9eb
before the F-NEW-621 edit; the probe surfaced the restore divergence
(restored label 00:00:00 vs DB remaining_dec6=10) which became the fix
target. Runtime diff: `miniandroid/src/framework/android_shadows.{h,cpp}`
+ `miniandroid/src/main.cpp` — no app-specific code path exists.
