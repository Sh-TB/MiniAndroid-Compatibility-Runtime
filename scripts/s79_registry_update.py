#!/usr/bin/env python3
"""s79_registry_update.py — S79 canonical-source updates (§24: script-driven,
never hand-patch derived output). Idempotent.

Adds to root_registry.json:
  F-155      fishrings: MediaPlayer.create REC-MISS stub → null player →
             GameActivity.sound() NPE aborted ring-rotation onClick (ROOT-CAUSED-FIXED)
  R-NEW-399  AOSP ViewGroup child-dispatch law (hit-test walk decoupled from
             ancestor bounds) + MINIANDROID_HITPROBE
  R-NEW-400  AOSP MediaPlayer object law (create → non-null PREPARED player;
             start/pause/stop/release/reset per the state table)
Adds LAW-R-NEW-399 / LAW-R-NEW-400 knowledge records (VERIFIED) and refreshes
the per-app dossier evidence fields touched this wave.
"""
import json
import os

ROOT = "/home/z/my-project"
REG = f"{ROOT}/root_registry.json"
KN = f"{ROOT}/docs/knowledge/KNOWLEDGE_RECORDS.json"

F155 = {
    "id": "F-155",
    "title": "fishrings: MediaPlayer.create REC-MISS stub returned null player → "
             "GameActivity.sound() NPE aborted ring-rotation onClick (input → "
             "state chain dead; the S10 interaction was invisible at HEAD)",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "evidence": "S79 PRODUCER TRACE: fishrings board taps (239,223)/(606,223)/"
                "(764,774) dispatched CLICK to real GameActivity$1/$2/$4 "
                "listeners, but every onClick died in GameActivity.sound() "
                "(pc=10/16) on MediaPlayer.start() of a NULL player — "
                "MediaPlayer.create was an unbridged framework call "
                "([REC-MISS] Landroid/media/MediaPlayer;.create) returning the "
                "typed default null; the deferred f141-null-recv NPE unwound "
                "the listener BEFORE any rotation ran (frames byte-identical, "
                "run/s79_reproofs/fishrings_r399b). Same §12 silent-propagation "
                "family as F-152 (doPrivileged null). FIX R-NEW-400 below. "
                "POST: 0 MediaPlayer NPEs; 3 taps → 3 rotations → 3 distinct "
                "board states (f8 cb9ef295be → f9 fd3319ff72 → f11 0c74b09a8b), "
                "deterministic x2 (run/s79_reproofs/fishrings_r400{,_run2}). "
                "REGRESSION: battery 26/26, verifier 26/26 SAME, snake fidelity "
                "BYTE-IDENTICAL 90/90, f152 6/6, f153 3/3.",
}
R399 = {
    "id": "R-NEW-399",
    "title": "AOSP ViewGroup child-dispatch law: touch targets are bounds-checked "
             "per CHILD; ancestor bounds never gate the descent (hit-test walk) "
             "+ MINIANDROID_HITPROBE",
    "status": "USED_BY_EXECUTION",
    "priority": "P1",
    "evidence": "UPSTREAM: ViewGroup.dispatchTouchEvent iterates children and "
                "asks isTransformedTouchPointInView(x,y,child) PER CHILD; the "
                "parent's own bounds are never a descent gate. OLD LAW: walk "
                "returned (pruned) when an ancestor's node geometry missed the "
                "point — any stale/unmeasured ancestor made whole subtrees "
                "tap-dead (target=0). PRODUCER: fishrings board taps → target=0 "
                "with all 43 board children holding REAL measured geometry "
                "([HITPROBE] logs, run/s79_reproofs/fishrings_r399) — the walk "
                "never reached them. NOTE (honest): the two corpus blockers "
                "first attributed to this family were REFUTED as stale tap "
                "coordinates (gmdice S78 tapped y=1714; the real button row is "
                "y=1776..1920 — multi-roll works on the old binary with "
                "correct coords; fishrings S65 coords predate the F-142 "
                "geometry). The law remains implemented because it is the "
                "upstream semantics, is consumer-independent, and the probe "
                "makes the walk inspectable. FIX: TouchDispatcher::dispatch "
                "DOWN walk descends unconditionally, bounds-check per node. "
                "REGRESSION: zero behavioral delta on all goldens (battery "
                "26/26 rc=0, verifier 26/26 SAME, snake fidelity BYTE-IDENTICAL "
                "90/90, f152 6/6, f153 3/3).",
}
R400 = {
    "id": "R-NEW-400",
    "title": "AOSP MediaPlayer object law: create() → non-null PREPARED player; "
             "start/pause/stop/release/reset per the state-machine table",
    "status": "USED_BY_EXECUTION",
    "priority": "P1",
    "evidence": "UPSTREAM: MediaPlayer.java — static create(Context,resid) = "
                "new + setDataSource + prepare (returns non-null PREPARED "
                "player; throws on failure, never returns null for a valid "
                "resource); state table: start() legal from {Prepared, Started, "
                "Paused, PlaybackCompleted}; pause() from {Started, Paused}; "
                "stop() from {Prepared, Started, Paused, Stopped}; release() "
                "any; reset() → Idle. IMPLEMENTATION (bridge_to_api): create "
                "allocates a REAL heap object with __mp_state__=PREPARED; "
                "instance methods transition per the table (illegal → ERROR + "
                "[R400-MEDIA] log). Audio OUTPUT is a no-op (software runtime, "
                "no speaker) — the OBJECT/STATE law is what app control flow "
                "depends on. CONSUMER-INDEPENDENT: single choke point (bridge "
                "fallthrough) — every app's sound path benefits. Test: "
                "fishrings S10 chain closed at HEAD (3 rotations, 3 states, "
                "x2 deterministic); MediaPlayer NPEs 1→0 per tap.",
}

# ---------------------------------------------------------------- registry
reg = json.load(open(REG))
ids = {x["id"] for x in reg["roots"]}
if reg["total"] == 409:
    assert "F-155" not in ids and "R-NEW-399" not in ids and "R-NEW-400" not in ids
    reg["roots"] += [F155, R399, R400]
    reg["total"] = 412
    reg["summary"]["total_roots"] = 412
    reg["summary"]["last_updated"] = (
        "S79 (2026-09-22): F-155 ROOT-CAUSED-FIXED via R-NEW-400 (MediaPlayer "
        "object law; fishrings input->state chain closed at HEAD, det x2); "
        "R-NEW-399 implemented (AOSP per-child hit-test walk law + HITPROBE; "
        "corpus blockers refuted as stale coordinates — honest note); gmdice "
        "multi-roll closed (580,1848 x2 rolls '6'->'5'); microtimer/unote/"
        "bouncy/opmt re-proven at HEAD; snake gameplay GIF published to "
        "gh-pages site")
    json.dump(reg, open(REG, "w"), indent=1, ensure_ascii=False)
    print("registry: 409 -> 412 (F-155, R-NEW-399, R-NEW-400)")
else:
    assert reg["total"] == 412, f"unexpected registry total {reg['total']}"
    assert "F-155" in ids and "R-NEW-399" in ids and "R-NEW-400" in ids
    print("registry: already at 412 (idempotent no-op)")

# ---------------------------------------------------------------- knowledge
k = json.load(open(KN))
if "LAW-R-NEW-399" not in set(k["knowledge"]):
    k["knowledge"] += ["LAW-R-NEW-399", "LAW-R-NEW-400"]
    k["counts"]["knowledge_records"] = len(k["knowledge"])
    k["counts"]["verified_laws"] = 24 + 2
    json.dump(k, open(KN, "w"), indent=1, ensure_ascii=False)
    print("knowledge: -> 37 record ids")
else:
    print("knowledge: already updated (idempotent no-op)")

LAW_399 = {
    "record_type": "knowledge_record",
    "schema_version": 1,
    "knowledge_id": "LAW-R-NEW-399",
    "title": "Touch targets are bounds-checked per child; ancestor bounds "
             "never gate the descent",
    "domain": "input-semantics",
    "scope": "engine",
    "statement": "ViewGroup.dispatchTouchEvent bounds-checks each CHILD "
                 "independently (isTransformedTouchPointInView); a parent's own "
                 "bounds are not a descent gate. The engine walk now descends "
                 "unconditionally and bounds-checks per node; "
                 "MINIANDROID_HITPROBE=1 logs the walk (render-neutral probe). "
                 "Honest scope note: no current corpus app is blocked by the "
                 "old walk — both suspects (gmdice multi-roll, fishrings S65 "
                 "coords) were refuted as stale tap coordinates; the law is "
                 "upstream-alignment with a measurable no-regression gate.",
    "status": "VERIFIED",
    "source": {
        "origin": "AOSP ViewGroup.dispatchTouchEvent / "
                  "isTransformedTouchPointInView (android-14)",
        "file": "miniandroid/src/framework/touch_dispatcher.cpp (DOWN walk)",
    },
    "test": "battery 26/26 + verifier 26/26 SAME + snake fidelity "
            "BYTE-IDENTICAL 90/90 + f152 6/6 + f153 3/3 (zero behavioral "
            "delta on goldens); probe logs "
            "run/s79_reproofs/fishrings_r399/engine.log",
    "consumers": ["fishrings", "gmdice", "all-input-driven-apps"],
    "issues": [],
    "capabilities": [],
    "first_discovered": "S79",
    "last_verified": "S79",
    "utilization": {"verdict": "USED_BY_EXECUTION",
                    "consumer_apps": ["fishrings", "gmdice"]},
}
LAW_400 = {
    "record_type": "knowledge_record",
    "schema_version": 1,
    "knowledge_id": "LAW-R-NEW-400",
    "title": "MediaPlayer.create returns a non-null PREPARED player; instance "
             "methods follow the AOSP state table",
    "domain": "framework-object-semantics",
    "scope": "engine",
    "statement": "MediaPlayer.create(Context, resid) never returns null for a "
                 "valid resource (it throws on failure) — it returns a player "
                 "in the PREPARED state. start/pause/stop/release/reset "
                 "transition per the class-doc state table; illegal "
                 "transitions log and enter ERROR (mirrors the C++ "
                 "audio::MediaPlayer table). The engine allocates a real heap "
                 "object with __mp_state__; audio OUTPUT is a no-op in a "
                 "software runtime. Without this object law, every app whose "
                 "onClick plays a sound before acting dies silently on a "
                 "deferred null-receiver NPE (F-155).",
    "status": "VERIFIED",
    "source": {
        "origin": "AOSP android.media.MediaPlayer "
                  "(frameworks/base/media/java/android/media/MediaPlayer.java)",
        "file": "src/dex/dalvik_engine.cpp bridge_to_api (R-NEW-400 branch)",
    },
    "test": "fishrings S10 chain at HEAD: 3 taps → 3 CLICK dispatches → 3 "
            "rotations → 3 distinct board states, deterministic x2; "
            "MediaPlayer NPE count 1/tap → 0",
    "consumers": ["fishrings", "any-app-with-sound-on-click"],
    "issues": ["#19"],
    "capabilities": [],
    "first_discovered": "S79",
    "last_verified": "S79",
    "utilization": {"verdict": "USED_BY_EXECUTION",
                    "consumer_apps": ["fishrings"]},
}
law_dir = f"{ROOT}/docs/knowledge/laws"
os.makedirs(law_dir, exist_ok=True)
json.dump(LAW_399, open(f"{law_dir}/LAW-R-NEW-399.json", "w"), indent=1,
          ensure_ascii=False)
json.dump(LAW_400, open(f"{law_dir}/LAW-R-NEW-400.json", "w"), indent=1,
          ensure_ascii=False)
print("law files written: LAW-R-NEW-399.json, LAW-R-NEW-400.json")

# ---------------------------------------------------------------- dossiers
def patch_dossier(path, updates):
    d = json.load(open(path))
    d.update(updates)
    json.dump(d, open(path, "w"), indent=1, ensure_ascii=False)
    print("dossier updated:", os.path.basename(path))

APPS = f"{ROOT}/docs/compatibility/apps"
patch_dossier(f"{APPS}/fishrings.json", {
    "last_error": "S79: taps dispatched but board static — GameActivity.sound() "
                  "NPE on null MediaPlayer (F-155, create REC-MISS stub)",
    "root_cause": "F-155 ROOT-CAUSED (MediaPlayer object law gap) — FIXED "
                  "R-NEW-400",
    "last_fix": "R-NEW-400: create → non-null PREPARED player; state table "
                "enforced; 0 NPEs post-fix",
    "regression": "battery 26/26 + verifier 26/26 + fidelity 90/90 + det x2 "
                  "board states (cb9ef295be/fd3319ff72/0c74b09a8b)",
    "next_probe": "catch-the-fish full gameplay loop to game end (win/"
                  "completion condition) — interaction chain now open at HEAD",
    "session": "S79 (run/s79_reproofs/fishrings_r400{,_run2})",
    "issue_state": "open (S10 interaction chain CLOSED at HEAD; game-end loop "
                   "open)",
})
patch_dossier(f"{APPS}/gmdice.json", {
    "last_error": "S78: multi-roll taps at (540,1714) → target=0 (STALE "
                  "coordinates — button row is y=1776..1920; NOT a decor law)",
    "root_cause": "refuted S78 decor-offset hypothesis: hit-test works on the "
                  "row; the tap y was above the buttons",
    "last_fix": "S79: taps at real button center (580,1848) → target=41 → "
                "results '6' then '5' across frames (multi-roll closed)",
    "regression": "battery 26/26; click-test 5/5 dispatched + results rendered "
                  "(SETTEXT view_37) on the S79 binary",
    "next_probe": "Random.nextInt REC-MISS (F-114 family) — result distribution "
                  "honesty frontier",
    "session": "S79 (run/s79_reproofs/gmdice_multiroll{,2})",
    "issue_state": "closed (ladder complete at HEAD)",
})
patch_dossier(f"{APPS}/microtimer.json", {
    "last_fix": "S79 re-proof at HEAD: clicks → 00:00:00 → 00:00:09 → 00:00:98 "
                "(timer running; 11/12 views changed; det x2)",
    "session": "S79 (run/s79_reproofs/microtimer_run{1,2})",
    "issue_state": "closed (state change re-proven at HEAD)",
})
patch_dossier(f"{APPS}/unote.json", {
    "last_fix": "S79 re-proof at HEAD: 'Add note' tap → real editor screen "
                "(Title/Note fields + Save/Return) — 13,032 sampled-px state "
                "change; notes.db SQLite chain live",
    "session": "S79 (run/s79_reproofs/unote_run{1,2})",
    "issue_state": "closed (input → state change visible at HEAD)",
})
print("S79 canonical updates complete")
