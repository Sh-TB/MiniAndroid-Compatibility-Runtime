#!/usr/bin/env python3
"""MEGA-W2 registration: F-NEW-232 (deferred-UI observability),
F-NEW-233 (unconditional frame-truth law), F-NEW-230 golden re-bank."""
import json, sys

REG = "/home/z/my-project/root_registry.json"

F232 = {
    "id": "F-NEW-232",
    "status": "IMPLEMENTED+TESTED",
    "priority": "P1",
    "layer": "evidence/deferred-ui-observability",
    "title": (
        "LAUNCH-FRAME DEFERRED-UI OBSERVABILITY: a plain run freezes at the "
        "launch frame (F-NEW-197/F-115b law — an idle Looper cannot observe "
        "its own future), so apps whose UI appears only after a deferred "
        "Timer/postDelayed/pending-activity-launch (fishrings splash Timer "
        "5000ms -> GameActivity; secuso sudoku splash -> TutorialActivity) "
        "were classified by a PROVISIONAL face (flat #303030 / white) with "
        "the census recording nothing — the blank verdict silently presented "
        "a launch-frame face as the app's state."
    ),
    "law": (
        "AOSP MessageQueue/Looper law: nativePollOnce(timeout) wakes for the "
        "next message when — future-dated work is legal and fires in real "
        "time; the launch frame predates it. Evidence law: a verdict computed "
        "at Looper-time ~0 with future-due queue entries or a pending "
        "activity launch is PROVISIONAL and must say so."
    ),
    "evidence": (
        "BEFORE: fishrings plain run = b5a7a35d5fe0564b (100% #303030), "
        "census silent; disasm proves SplashActivity.onResume Timer.schedule"
        "(task, 5000) -> startActivity(GameActivity). sudoku plain run = "
        "31ddd4d5b8e6d18e (100% white), G08-LAUNCH(TutorialActivity) executes "
        "AFTER capture. AFTER (same binary, time-driven capture "
        "--frames 14 --frame-delay 500): fishrings a341e3ad9092f640 x3 rc=0 — "
        "REAL GAME BOARD (6673 colors, ebingo logo + ring board + rotation "
        "arrows); sudoku 45962e018344e94d x3 — TutorialActivity layout + 2 "
        "buttons (text still missing — registered finding). Census now "
        "records deferred_ui_pending/queue_size/earliest_ready_ms and the "
        "quiescence log names DEFERRED-UI-PENDING."
    ),
    "fix": (
        "FrameRenderCensus gains deferred_ui_pending/deferred_queue_size/"
        "deferred_earliest_ready_ms; the F100 quiescence branch records them "
        "when the queue holds future-due entries; the capture stage takes a "
        "second snapshot covering PENDING INTENTS (IntentShadow.has_pending — "
        "G08 deferred launches); the run message carries the [F-NEW-232 "
        "deferred-UI pending] annotation post-final-status."
    ),
    "test": (
        "fishrings x3 + sudoku x3 byte-identical under time-driven capture; "
        "plain runs unchanged pixel-wise (launch-frame law frozen); goldens "
        "dooz/microtimer/unote/opencalc byte-identical x3 after the change."
    ),
    "fanout": (
        "every deferred-transition app (splash-Timer family: fishrings, "
        "klondike, sudoku, chess?; postDelayed menu family); the corpus "
        "blank-face classification layer."
    ),
    "aff": "evidence infrastructure; no rendering change.",
}

F233 = {
    "id": "F-NEW-233",
    "status": "IMPLEMENTED+TESTED",
    "priority": "P0",
    "layer": "evidence/frame-truth",
    "title": (
        "FRAME-TRUTH CENSUS WAS TRACE-GATED (false-SUCCESS family): the "
        "entire 21-P0 census + verdict + status-downgrade block ran only "
        "when boot trace was enabled. A PLAIN run (no --trace) reported "
        "SUCCESS for a 100%-white frame (secuso sudoku live: "
        "31ddd4d5b8e6d18e, rc=0, 'Status: SUCCESS') — the exact "
        "false-success the 21-P0 pixel-ownership law exists to forbid."
    ),
    "law": (
        "21-P0-6 pixel ownership + correlated proof: SUCCESS requires "
        "authoritative app content. The verdict is the product of the "
        "CAPTURE, not of the trace flag. CONSTITUTION V2 §17: silent wrong "
        "is more dangerous than crash."
    ),
    "evidence": (
        "BEFORE: sudoku plain run 'Status: SUCCESS' with a 1-unique-color "
        "white screenshot (the verdict block skipped; no [21-P0 frame truth] "
        "in the message). AFTER (same APK, same frame): 'Status: PARTIAL "
        "SUCCESS' + '[F-NEW-233 frame truth: verdict=NO_ROOT, "
        "first_missing_stage=WINDOW_ROOT — SUCCESS requires authoritative "
        "app content]' + '[F-NEW-232 deferred-UI pending ...]' in the "
        "message; census fields recorded. Goldens/gates byte-identical x3 "
        "after the change (dooz d602648e8e401895, microtimer "
        "da73010a37dd0189, unote 4f1a9e4e8f64fae8, opencalc e364b001ee7abd66)."
    ),
    "fix": (
        "Un-gate the census computation + verdict + 21-P0 downgrade "
        "(only the overlay composition stays trace-gated); persist "
        "verdict/first_missing_stage on the census; append the frame-truth "
        "annotation POST-final-status (the final-status block overwrites "
        "status_message — same placement law as F-016/F-NEW-200)."
    ),
    "test": (
        "Every plain run now carries verdict + first_missing_stage in its "
        "message when the frame is not REAL_APP_CONTENT; REAL_APP_CONTENT "
        "runs unchanged; regression battery x3 byte-identical."
    ),
    "fanout": "every run, every corpus title, every future golden gate.",
    "aff": "evidence infrastructure; no rendering change.",
}

F230_UPDATE = {
    "valid_x3_with_repro": [
        {"name": "dooz",
         "apk": "/tmp/my-project/apk_cache/corpus/dooz.apk",
         "sha": "d602648e8e401895",
         "repro": "./build/miniandroid run <apk> -o <out> (defaults 1080x1920) x3"},
        {"name": "microtimer",
         "apk": "/tmp/my-project/apk_cache/dubrowgn.microtimer_8.apk",
         "sha": "da73010a37dd0189",
         "repro": "./build/miniandroid run <apk> -o <out> x3"},
        {"name": "unote",
         "apk": "/tmp/my-project/apk_cache/app.varlorg.unote_30.apk",
         "sha": "4f1a9e4e8f64fae8",
         "repro": "./build/miniandroid run <apk> -o <out> x3"},
        {"name": "opencalc",
         "apk": "/home/z/my-project/upload/opencalculator_53.apk",
         "sha": "e364b001ee7abd66",
         "repro": "./build/miniandroid run <apk> -o <out> x3 (F-NEW-228 "
                  "weight-pass frame; also reproduced FROM THE INSTALLED "
                  "PACKAGE via 'run --package com.darkempire78.opencalculator' — F-NEW-231)"},
    ],
    "stale_remeasured_2026_10_02": [
        {"name": "forkgram", "old": "cf4c41e62ceb6557",
         "now": "bbb6cd10a834963d",
         "note": "REAL_APP_CONTENT verdict; frame drifted from the V10 bank "
                 "(F-NEW-226/227 text-identity + measureText laws changed "
                 "text pixels globally); current face = real Telegram menu "
                 "with DOUBLE-DRAWN 'LowPowerEnabledTitle' (overlap bug "
                 "registered); re-bank needed"},
        {"name": "ssw", "old": "f48ae6d467d1e746", "note": "STALE per F-NEW-228 session"},
        {"name": "headingcalc", "old": "be1cea9cf994b26a", "note": "STALE per F-NEW-228 session"},
        {"name": "secuso", "old": "eb5ebd559cad1028", "note": "STALE per F-NEW-228 session"},
        {"name": "whatsapp", "old": "31ddd4d5b8e6d18e",
         "note": "INVALID — the golden itself is a 100% white frame; "
                 "rejected as a gate per the blank-frame law"},
    ],
}


def main():
    with open(REG) as f:
        reg = json.load(f)
    if not any(r["id"] == "F-NEW-232" for r in reg["roots"]):
        reg["roots"].append(F232)
    else:
        for r in reg["roots"]:
            if r["id"] == "F-NEW-232":
                r.update(F232)
    if not any(r["id"] == "F-NEW-233" for r in reg["roots"]):
        reg["roots"].append(F233)
    else:
        for r in reg["roots"]:
            if r["id"] == "F-NEW-233":
                r.update(F233)
    for r in reg["roots"]:
        if r["id"] == "F-NEW-230":
            r["status"] = "PARTIAL"
            r["evidence"] = (
                r.get("evidence", "") + " | 2026-10-02 mega-campaign re-bank: "
                + json.dumps(F230_UPDATE))
    reg["count"] = len(reg["roots"])
    reg["status_counts"] = {}
    for r in reg["roots"]:
        reg["status_counts"][r.get("status", "?")] = (
            reg["status_counts"].get(r.get("status", "?"), 0) + 1)
    with open(REG, "w") as f:
        json.dump(reg, f, indent=1)
    print(f"F-NEW-232/233 registered, F-NEW-230 updated; count={reg['count']}")


if __name__ == "__main__":
    sys.exit(main())
