#!/usr/bin/env python3
"""S200 — push the Target A (microtimer END-TO-END) result comments.
Golden rule: every result lands as a GitHub comment the moment it exists."""
import json, subprocess, sys, time
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


TOK = token()
HDRS = {"Authorization": f"token {TOK}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s200-main-integration-coder"}

MAIN = """## S200 P0 TARGET A — microtimer: **declared core feature 100% VERIFIED end-to-end** (first complete real application)

This is the S200 completion-rule claim, worded per mission law: **100% of declared core feature verified; optional features remain.**

**Identity.** APK `dubrowgn.microtimer_8.apk` (sha16 `79c6f730f64886e7`). Binary **`96329a7ad50819d0`** (HEAD `3da4f796`, built `make -j2`) — the same binary for every claim below.

**Declared core feature (from upstream source, not invented):** keypad duration entry → label; START → Room/SQLite INSERT + `TimerControl` row added to `layoutAlarms`; Handler-tick countdown; per-row PAUSE/RESUME (button swap); per-row DELETE; cold-restart restore via `loadAlarms()`.

**Verified chain (real Dalvik bytecode, real views, real taps, real SQLite):**
1. **Launch + real UI** — keypad 1-9/00/0 rendered white-on-blue, input row + dividers; 25-node view tree exactly matching the layout.
2. **Input reaches the correct components** — F117-TAP trace: `'1'→obj134`, `'0'→obj147`, `START→obj148`, `PAUSE→obj264`, **`RESUME→obj270` (the swapped-in button — the tap hit the re-parented view)**, `DELETE→obj253`.
3. **State changes → next frame correct** — label region +11350 px after digit taps (`00:00:10` rendered); countdown churn 3537 px across frames; **pause freezes the label to 0 changed px**; resume restarts the churn; delete removes the row (final tree: row absent, input cleared).
4. **Persistence (SQLite, cross-process)** — cold restart with ZERO taps restores the row from the Room DB; direct `sqlite3` on the store DB: tables `alarm`/`sqlite_sequence`/`room_master_table`, row `(duration=10, remaining=10, id=1, expires_ms=12290)`; restored label **`00:00:07`** and ticking.
5. **3+1 clean independent runs equivalent** — identical tap-target signature `[134,147,148,264,270,253]`, identical transition booleans (tick✓ / pause-frozen✓ / resume✓ / row-removed✓), **0 uncaught exceptions in every run**.

**First divergence found → shared fix (F-NEW-621 device-clock law).** The acceptance harness was written and its probe run on the UNMODIFIED S199 canonical `97628b00d237f9eb` BEFORE any runtime edit. Probe result: cold restart restored the row but the label instantly read `00:00:00` while the DB said `remaining_dec6=10`. Root cause: `SystemClock.elapsedRealtime()` returned the in-process virtual clock (rewinds to 0 each run), but AOSP defines it as monotonic since device boot, shared by all processes — the persisted `expires_ms` landed in the "future" of the rewound clock → `ceil((expiresMs-nowMs)/1000) > totalSeconds` → Kotlin UInt wrap → `remaining.zero()`. Fix (shared, no app-specific path): device == data-root; boot base persisted at `<data-root>/data/system/device_clock`, read at run start, accumulated clock written at run end (monotone guard); offset applied ONLY at the SystemClock boundary (`HandlerShadow::device_now_ms()`), Looper scheduling untouched. Fresh store = fresh boot (base 0) → deterministic reruns unchanged.

**Gates on the same binary (fresh stores):** goldens **3/3 ALL HOLD** (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `31ddd4d5`; dooz uncaught=6 = standing baseline, pin unchanged), floor **11/11 CLEAN**, **gmdice 5-tap PASS** (5 taps → 5 distinct result states, rerun identical — hash sequence equal across two fresh runs).

**Boundaries kept honest:** notifications/vibration/alarm-fire are documented in-run boundaries (AlarmManager records schedules; alarms do not fire in-run). They did not block the declared core loop and none were silently faked.

Evidence: `evidence/s200/S200_MICROTIMER_E2E.md` (gate table A–M), `evidence/s200/MICROTIMER_ACCEPTANCE.json`, acceptance harness `scripts/s200_microtimer_acceptance.py`, faces `evidence/s200/face_mtm_full_row.jpg` (row + 00:00:09 + pause) / `face_mtm_full_final.jpg`, screenshot sha16s `7913f6393e8051ff` / `bbd350b6c14fbd52` / `47ad887bf05c9c1d`. Commit `3da4f796`.

**Next:** P0 Target B tictactoe (GLES bridge: VBO attribute bind, glGetActiveAttrib dispatch, frame re-arm, board geometry) on this same binary; SQLite battery next; C2's next-10 ranking feeds the post-A cohort."""

CROSS = """## S200 wave update — Target A COMPLETE

microtimer (`dubrowgn.microtimer`) **declared core feature 100% VERIFIED end-to-end** on binary `96329a7ad50819d0` (commit `3da4f796`): real UI, real taps hitting the correct view objects (including the pause→resume swapped button), real state transitions with correct next frames, Room/SQLite persistence across a cold restart (direct sqlite3 row evidence), delete, **3+1 equivalent clean runs, 0 uncaught**. First divergence (SystemClock.elapsedRealtime rewinding across runs → UInt wrap → instant expiry on restore) fixed at the root as **F-NEW-621 device-clock law**; gates re-verified on the same binary: goldens 3/3, floor 11/11, gmdice 5-tap PASS. Full report: #536 (comment in thread) + `evidence/s200/S200_MICROTIMER_E2E.md`. Target B (tictactoe GLES bridge) is next on this same binary."""

posted = {}
import pathlib
IDS = pathlib.Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')
if IDS.exists():
    posted = json.loads(IDS.read_text())

for num, body, key in [(536, MAIN, '536_targetA'), (492, CROSS, '492_targetA')]:
    if posted.get(key):
        print(f"#{num} already posted: {posted[key]}")
        continue
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{num}/comments",
        data=json.dumps({"body": body}).encode(),
        headers=HDRS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        posted[key] = j.get("id")
        IDS.write_text(json.dumps(posted, indent=1))
        print(f"#{num}: POSTED {j.get('id')} -> {j.get('html_url')}")
    except Exception as e:
        print(f"#{num}: FAILED {e}")
    time.sleep(1)
