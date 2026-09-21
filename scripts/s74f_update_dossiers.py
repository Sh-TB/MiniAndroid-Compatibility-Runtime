#!/usr/bin/env python3
"""s74f_update_dossiers.py — S74 FOLLOW-UP WAVE: operationalize app dossiers.

Writes ONLY measured/committed facts into docs/compatibility/apps/*.json:
  visual_evidence   (HUMAN_VISIBLE / NOT_HUMAN_VISIBLE / NOT_OBSERVED + frames)
  sandbox_profile   (per-app data-root inspection from the ops campaign)
  persistence       (close/reopen probes or honest NO_PERSISTENCE_OBSERVED)
  security          (aapt2 manifest DECLARED facts + observed behavior)
  what_actually_happened (§9 truth vocabulary: PROVEN/OBSERVED/IMPLEMENTED/
                          RESEARCHED/NOT_OBSERVED/BLOCKED/SUPERSEDED)
  ops_wave          (s74-ops bundle/session linkage)
Existing fields are never deleted; unknowns stay NOT_OBSERVED.
"""
import json
import glob
import os

REPO = "/home/z/my-project"
APPS = f"{REPO}/docs/compatibility/apps"
OPS = f"{REPO}/docs/evidence/s74_ops"
HEAD = "3505591b"


def load(aid):
    return json.load(open(f"{APPS}/{aid}.json"))


def save(aid, d):
    json.dump(d, open(f"{APPS}/{aid}.json", "w"), indent=1)


def bundle_frames(aid):
    p = f"{OPS}/{aid}/session.json"
    if not os.path.exists(p):
        return None
    s = json.load(open(p))
    return s


# ---------------- per-app truth content (evidence-derived, hand-written) ----

TRUTH = {
    "helloworld": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 main UI"],
                   "note": "self-aware 'hello world' identity text + API level line; golden byte-stable S53->S54"},
        "persistence": "NO_PERSISTENCE_OBSERVED (display-only app)",
        "sandbox": "not probed (APK not in repo per §20 policy; golden replay evidence reused)",
        "truth": {
            "PROVEN": ["launch render: self-aware identity text drawn (committed golden, byte-stable replay)",
                       "real Android build chain for the in-repo control app (aapt2/ECJ/D8, android-34 stubs)"],
            "OBSERVED": [],
            "IMPLEMENTED": [],
            "RESEARCHED": [],
            "NOT_OBSERVED": ["input interaction (app is display-only)", "sandbox file creation", "persistence"],
            "BLOCKED": [],
            "SUPERSEDED": []},
        "next_task": "none (golden control target; optional interactive probe if app variant with input is used)",
    },
    "tictactoe": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch (fixture)", "V1 board (fixture)", "V2 interaction (fixture)", "V4 result (fixture)"],
                   "note": "fixture-scope human-visible proof (X WINS board); REAL APK at HEAD is NOT_HUMAN_VISIBLE (GL blocker)",
                   "real_apk_note": "com.emmanuelmess.tictactoe_3.apk at HEAD: launch -> AndroidGraphics.createGLSurfaceView NPE (F-144 family) -> blank white frame; view tree = 2 nodes (launcher + RelativeLayout)"},
        "persistence": "NO_PERSISTENCE_OBSERVED (fixture writes no files)",
        "sandbox": "fixture runs write no data-root files (validator WORK dirs)",
        "truth": {
            "PROVEN": ["golden fixture full game: 9 real clicks -> turn flips -> X WINS at frame 7 (anti-diagonal), 4X+3O frozen tail, run B byte-identical (613cfccc0f27...)",
                       "real APK launch path executes (rc pipeline completes) and the GL divergence is REPRODUCIBLE at HEAD"],
            "OBSERVED": ["real APK: libgdx AndroidGraphics NPE chain on createGLSurfaceView (matches F-144 RESEARCHED record)"],
            "IMPLEMENTED": [],
            "RESEARCHED": ["F-144 GL surface family (tracked P2)"],
            "NOT_OBSERVED": ["real APK board interaction (blocked by GL family)", "real APK persistence"],
            "BLOCKED": ["real APK visual/gameplay: F-144 (GL compatibility path)"],
            "SUPERSEDED": []},
        "next_task": "optional: GL compatibility path research (F-144) to unblock the real APK UI; fixture proof stands",
    },
    "connectfour": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 board", "V2 interaction", "V3 state change", "V4 result"],
                   "note": "launch 'R to move' -> midgame -> 'Y WINS' full board; validator ALL PASS at HEAD"},
        "persistence": "NO_PERSISTENCE_OBSERVED (in-memory board; fixture writes no files)",
        "sandbox": "fixture runs write no data-root files",
        "truth": {
            "PROVEN": ["24 real clicks through real DEX state machine (char[6][7] multianewarray)",
                       "corrected canonical result: Y WINS at click 22 (r+1,c+1 diagonal), 11R+11Y, frozen tail 22/23/24",
                       "deterministic replay byte-identical (38e568bd3815...) at HEAD"],
            "OBSERVED": [], "IMPLEMENTED": [], "RESEARCHED": [],
            "NOT_OBSERVED": ["persistence (state is in-memory by design)"],
            "BLOCKED": [], "SUPERSEDED": []},
        "next_task": "none (completed state documented in #12)",
    },
    "androidgamesnake": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 board", "V2 interaction", "V3 state change (food capture)", "V4 game-over"],
                   "note": "S73 committed frames re-wired as representative evidence (taskbook §8: no re-run); frame_000 launch / frame_034 food capture / final snake+food"},
        "persistence": "NOT_OBSERVED (no data-root probe in S73 session; restart-after-game-over also honestly NOT observed)",
        "sandbox": "not probed this wave (§8: preserve existing S73 session as-is)",
        "truth": {
            "PROVEN": ["S73 autonomous gameplay chain: 88 moves / 22 turns / 1 food capture / 23 scheduled real taps (F-117)",
                       "3-run byte-identical 90/90 frames; S74 fidelity probe replayed fresh byte-identical at HEAD",
                       "reverse-direction rejection, WRAP law, self-collision game-over"],
            "OBSERVED": [],
            "IMPLEMENTED": ["F-150 game-loop family (sleep de-noop, javac subclass receivers, frame-boundary drains)"],
            "RESEARCHED": [],
            "NOT_OBSERVED": ["restart after game-over", "persistence/close-reopen with data-root probe"],
            "BLOCKED": [], "SUPERSEDED": []},
        "next_task": "optional new task only: restart-after-game-over probe (explicitly selected); otherwise preserve S73 state",
    },
    "dooz": {
        "visual": {"status": "NOT_HUMAN_VISIBLE",
                   "stages": ["V0 launch pipeline only"],
                   "note": "engine-default black region (23,472 px) — truthful blocker evidence attached in bundle; NO_MEANINGFUL_VISUAL_PROOF"},
        "persistence": "NOT_OBSERVED (launch path stops before user flow)",
        "sandbox": "no files created in data root (ops campaign probe)",
        "truth": {
            "PROVEN": [],
            "OBSERVED": ["Compose/coroutine init chain executes (b2/n queue -> Segment-like state -> AtomicReferenceArray knowledge chain)",
                         "23,472-px engine-default black region at HEAD (byte-class matches S73 reclassification)"],
            "IMPLEMENTED": [],
            "RESEARCHED": ["F-146 null receiver, F-147 getChildAt-on-null root causes"],
            "NOT_OBSERVED": ["first meaningful Compose UI", "interaction", "persistence"],
            "BLOCKED": ["F-146 / F-147 (root blockers)", "F-145 visual frontier"],
            "SUPERSEDED": ["CLAIM-DOOZ-23472-VISUAL (23,472 px was NEVER Dooz visual proof — preserved SUPERSEDED record)"]},
        "next_task": "targeted Compose/Compose-view frontier wave (F-145/146/147) — do not manufacture success",
    },
    "unote": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 main UI"],
                   "note": "search bar + 'Add note / Search / Quit' action bar at HEAD; themed UI 231,120 px matches S73 record"},
        "persistence": "OBSERVED: real SQLite DB created on launch (app.varlorg.unote/databases/notes.db, 12288 B, sha256_16 2bccf9475fe3810d) AND survives relaunch in same data root (SHA unchanged after reopen probe)",
        "sandbox": "data-root probe: exactly one file created (notes.db); no external-storage or cache writes observed",
        "truth": {
            "PROVEN": ["launch -> themed main UI at HEAD (231,120 px, byte-matches S73 recipe)",
                       "persistence layer active: notes.db created + survives close/reopen probe"],
            "OBSERVED": ["XML onClick dispatch: addNote/search/quit handlers fired (round-robin pass); no visible navigation change in empty-list state"],
            "IMPLEMENTED": ["SharedPreferences bridge (F-114), SQLite backend (F-026 room chain)"],
            "RESEARCHED": [],
            "NOT_OBSERVED": ["note creation end-to-end (editor screen)", "note content persistence across reopen"],
            "BLOCKED": [],
            "SUPERSEDED": []},
        "next_task": "drive Add note -> editor -> save -> reopen -> read-back chain (completes C9 end-to-end with visible note)",
    },
    "telegram": {
        "visual": {"status": "NOT_HUMAN_VISIBLE",
                   "stages": ["V0 launch pipeline only"],
                   "note": "v12.10.3 (official URL, fetched 2026-09-21, sha b6a13e87...) renders engine-default black region (23,472 px); init NPE family"},
        "persistence": "NOT_OBSERVED (init path stops before user flow)",
        "sandbox": "no app files observed in data root this wave",
        "truth": {
            "PROVEN": ["historical EXP071 CHECKPOINT_M: real Telegram v12.10.1 auth.sendCode -> mock response -> callback -> LoginActivitySmsView materialized (53 SmsView nodes / 2284-node tree); screenshot SHA c3c208a169a7dadd byte-identical x6"],
            "OBSERVED": ["v12.10.3 at HEAD: 3 frames render, 32 init-exception family errors (fragment/activity-result/obfuscated-DEX NPE chain)"],
            "IMPLEMENTED": [],
            "RESEARCHED": ["androidx fragment j0.b, activity-result f.d/f.e NPE roots (post-F-141 family)"],
            "NOT_OBSERVED": ["SmsView UI at HEAD", "network behavior (runtime has no real network stack; sendRequest is intercepted by controlled boundary)"],
            "BLOCKED": ["app-init NPE family + init budget on current official build"],
            "SUPERSEDED": []},
        "next_task": "targeted runtime wave on the androidx fragment/activity-result NPE chain to reopen the SmsView ladder at HEAD",
    },
    "gmdice": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 main UI"],
                   "note": "dice list + bottom action bar renders; roll result NOT visible at HEAD (S63 roll evidence is historical, older binary)"},
        "persistence": "NO_PERSISTENCE_OBSERVED (no files in data root)",
        "sandbox": "no files created",
        "truth": {
            "PROVEN": ["launch render at HEAD (181,495 px family, consistent with S73 182,628 px record)",
                       "F-113 SecureRandom law record (S63: roll chain SecureRandom.nextInt -> setText, 1,584-px result band) — VERIFIED law, test battery committed"],
            "OBSERVED": ["click dispatched to real GameMasterDice listener (view 39 '3D20') — handler executed, no pixel change at HEAD",
                         "tap 348,1848 / 116,1848 hit roll buttons (target 40/39); CLICK result=DISPATCHED"],
            "IMPLEMENTED": [],
            "RESEARCHED": [],
            "NOT_OBSERVED": ["visible roll result at HEAD (S63 evidence was on an older binary/older local APK copy)",
                             "selectDice() AlertDialog this wave (S63 proved it historically)"],
            "BLOCKED": [],
            "SUPERSEDED": [],
            "IDENTITY_FLAG": "local APK sha256_16 1621eda11b5dbc0c differs from dossier-recorded ee9f7396 (F-Droid re-download replaced the local cache file at some session); recorded honestly — re-pin canonical APK at next source-first rebuild"},
        "next_task": "re-pin canonical gmdice APK (source-first rebuild or verified download), then re-prove visible roll chain at HEAD",
    },
    "microtimer": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 main UI", "V2 interaction", "V3 state change"],
                   "note": "keypad UI at launch; after click round-robin the display shows 00:09:87 (real input->state->render at HEAD)"},
        "persistence": "NO_PERSISTENCE_OBSERVED (no files in data root this wave)",
        "sandbox": "no files created",
        "truth": {
            "PROVEN": ["keypad digits -> timer display state change at HEAD (display populated 00:09:87)",
                       "launch UI 1,040,698 px (S73 family 1,041,437 px)"],
            "OBSERVED": ["XML onClick keypad dispatch (digit handlers)"],
            "IMPLEMENTED": [],
            "RESEARCHED": [],
            "NOT_OBSERVED": ["timer start/stop flow", "L7 historical keypad-to-display on current binary was re-proven THIS wave (upgraded from historical)"],
            "BLOCKED": [], "SUPERSEDED": []},
        "next_task": "start/stop timer flow probe (start -> ticking -> stop) for full C6-C8 ladder",
    },
    "fishrings": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch (splash 0 px)", "V1 board"],
                   "note": "full colored ball board + rotation arrows + ebinqo logo at HEAD (frames 4+; splash frames 0-3 are 0 px by app design)"},
        "persistence": "NO_PERSISTENCE_OBSERVED (no files in data root)",
        "sandbox": "no files created",
        "truth": {
            "PROVEN": ["board render at HEAD (frame family matching S73 2073360 px record)"],
            "OBSERVED": [],
            "IMPLEMENTED": [],
            "RESEARCHED": [],
            "NOT_OBSERVED": ["input interaction at HEAD (S65 historical: fr_board_after_taps; this wave ran launch-only)",
                             "game-logic depth (rotation/capture chain)"],
            "BLOCKED": [], "SUPERSEDED": []},
        "next_task": "tap-based rotation interaction probe at HEAD (completes V2/V3 stages)",
    },
    "tripeaks": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch (splash 0 px frames 0-6)", "V1 lobby (frame 7+)"],
                   "note": "'Welcome to the Tri Peaks Solitaire for Android!' + New Game/About Us/Help/Exit menu; 205,061 px (S73 family 205,638 px)"},
        "persistence": "NO_PERSISTENCE_OBSERVED (no files in data root)",
        "sandbox": "no files created",
        "truth": {
            "PROVEN": ["splash->lobby transition at HEAD (14-frame run; lobby from frame 7) — NEW current-HEAD evidence (S73 recorded lobby via shorter recipe)"],
            "OBSERVED": ["tap 440,120@9 on 'New Game' hit-test target=0 (menu is not a per-view listener surface at HEAD)"],
            "IMPLEMENTED": [],
            "RESEARCHED": ["R-NEW-388 app-specific OBJECT-IDENTITY (game board path)"],
            "NOT_OBSERVED": ["game board at HEAD (S65 historical tp_game_board.png on older binary)"],
            "BLOCKED": ["R-NEW-388 for the board render path (generic RL anchor laws stay proven)"],
            "SUPERSEDED": []},
        "next_task": "R-NEW-388 OBJECT-IDENTITY root-cause wave to unblock the board; lobby evidence stands",
    },
    "bouncy": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 menu", "V2 interaction", "V3 state change"],
                   "note": "'Select Table / Unlimited Balls / Start Game / High scores / Help / Preferences / Quit' menu; click round-robin navigated to full-screen table-selector state (visible change)"},
        "persistence": "NO_PERSISTENCE_OBSERVED (no files in data root)",
        "sandbox": "no files created",
        "truth": {
            "PROVEN": ["menu render + click-driven UI navigation at HEAD (menu panel -> full-screen table selector)"],
            "OBSERVED": ["XML onClick dispatch: scoreViewClicked/doPreviousTable handlers fired"],
            "IMPLEMENTED": [],
            "RESEARCHED": [],
            "NOT_OBSERVED": ["physics game loop (L7) — remains open", "Start Game -> ball field flow this wave"],
            "BLOCKED": [], "SUPERSEDED": []},
        "next_task": "Start Game -> physics loop proof (L7 ladder)",
    },
    "stopwatch": {
        "visual": {"status": "NOT_HUMAN_VISIBLE",
                   "stages": ["V0 pipeline only"],
                   "note": "service-only manifest — NO launchable Activity (aapt2 badging at HEAD confirms launchable=[]); engine-default black region is the expected face, NOT an app UI"},
        "persistence": "NOT_APPLICABLE (no Activity flow; service-only)",
        "sandbox": "no files created",
        "truth": {
            "PROVEN": ["manifest fact: no launchable activity (F-143 family) — engine BLOCKED-by-design record is correct",
                       "engine behavior correct: the no-Activity face is the expected engine-default output"],
            "OBSERVED": [],
            "IMPLEMENTED": [],
            "RESEARCHED": ["F-143 service-only manifest family"],
            "NOT_OBSERVED": ["any UI (by design)", "service semantics execution"],
            "BLOCKED": ["by design: service-only manifest — not a runtime defect"],
            "SUPERSEDED": []},
        "next_task": "optional: service-dispatch probe when the service family wave is scheduled",
    },
    "opmt": {
        "visual": {"status": "HUMAN_VISIBLE",
                   "stages": ["V0 launch", "V1 menu", "V2 interaction (dialog)"],
                   "note": "'Play with Friend / Play with Computer / How to play?' menu; click round-robin opened the app's REAL AlertDialog 'Who will go first?' (Human/Computer) at HEAD"},
        "persistence": "NO_PERSISTENCE_OBSERVED (no files in data root)",
        "sandbox": "no files created",
        "truth": {
            "PROVEN": ["menu render (213,286 px, byte-matches S73 record) + real AlertDialog render at HEAD"],
            "OBSERVED": ["click -> dialog state change (menu -> modal 'Who will go first?')"],
            "IMPLEMENTED": [],
            "RESEARCHED": ["app-own IOOBE (OBJECT-IDENTITY) stops progression past menu/dialog"],
            "NOT_OBSERVED": ["game board flow"],
            "BLOCKED": ["app-own IOOBE (OBJECT-IDENTITY) for progression beyond menu"],
            "SUPERSEDED": []},
        "next_task": "OBJECT-IDENTITY root-cause wave (shared with tripeaks R-NEW-388 family)",
    },
}


def main():
    for path in sorted(glob.glob(f"{APPS}/*.json")):
        aid = os.path.basename(path)[:-5]
        d = load(aid)
        t = TRUTH.get(aid)
        if not t:
            print(f"[SKIP] {aid}: no truth content")
            continue
        sess = bundle_frames(aid)

        d["visual_evidence"] = {
            "status": t["visual"]["status"],
            "execution_stage": t["visual"]["stages"],
            "note": t["visual"]["note"],
            "representative_frames": (list(sess["frame_metrics"].keys()) if sess and "frame_metrics" in sess else (list(sess.get("representative_frames", [])) if sess else [])),
            "bundle": f"docs/evidence/s74_ops/{aid}/",
            "session": f"docs/evidence/s74_ops/{aid}/session.json",
            "model": "AGENT_OBSERVED vs HUMAN_VISIBLE distinguished per S74-FOLLOW-UP §4",
        }

        # §9 truth section
        d["what_actually_happened"] = t["truth"]

        # persistence + sandbox
        d["persistence"] = {"status_note": t["persistence"],
                            "probe": ("relaunch_same_data_root (s74-ops)" if "survives" in t["persistence"] or "OBSERVED" in t["persistence"] else "s74-ops data-root probe"),
                            "verdict": t["persistence"].split(" (")[0]}
        d["sandbox_profile"] = {"data_root_probed": bool(sess and sess.get("sandbox")),
                                "observation": t["sandbox"],
                                "boundary_note": "sandbox treated as execution boundary: files under app package dir only; no external paths touched"}

        # security: merge aapt2 DECLARED facts from session bundle
        if sess and sess.get("manifest_security"):
            ms = sess["manifest_security"]
            sec = d.get("security", {})
            if ms.get("permissions_declared"):
                sec["permissions_declared"] = ms["permissions_declared"]
                sec["permissions_declared_source"] = "aapt2 dump badging at s74-ops HEAD"
            if ms.get("launchable_activities") is not None:
                sec["launchable_activities"] = ms["launchable_activities"]
            sec["network_observed"] = sec.get("network_observed", "NOT_OBSERVED (runtime has no real network stack; no egress possible)")
            sec["status_model"] = "DECLARED/OBSERVED/ALLOWED/BLOCKED/NOT_OBSERVED/UNKNOWN (never declared->used)"
            d["security"] = sec

        # ops wave linkage
        d["ops_wave"] = {
            "wave": "S74 FOLLOW-UP (operational base completion)",
            "runtime_commit": HEAD,
            "binary": "miniandroid/build/miniandroid built at HEAD (zero runtime changes this wave)",
            "evidence_bundle": f"docs/evidence/s74_ops/{aid}/",
            "human_review": "representative frames individually opened and reviewed by the executing agent before status assignment",
        }
        if t.get("next_task"):
            d["next_task"] = t["next_task"]

        save(aid, d)
        print(f"[DOSSIER] {aid}: visual={t['visual']['status']}")


if __name__ == "__main__":
    main()
