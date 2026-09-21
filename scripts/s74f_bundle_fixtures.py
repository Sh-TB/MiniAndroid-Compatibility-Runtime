#!/usr/bin/env python3
"""s74f_bundle_fixtures.py — assemble evidence bundles for the fixture-proven
apps (tictactoe_golden, connectfour_golden), the reused snake proof (§8: no
re-run), helloworld golden wire, and the improved TriPeaks lobby evidence.
Also runs manifest security inspection for every real APK (aapt2 badging).

Honesty rules:
  - fixture bundles are labeled scope=golden_fixture (NOT the real APK)
  - tictactoe real-APK bundle keeps its GL-blocker evidence (F-144)
  - snake bundle re-uses committed S73 frames (SHA-pinned), no new claims
"""
import hashlib
import json
import os
import shutil
import subprocess

REPO = "/home/z/my-project"
BIN = f"{REPO}/miniandroid/build/miniandroid"
OUT = f"{REPO}/docs/evidence/s74_ops"
AAPT2 = f"{REPO}/tools/aapt2/aapt2"
HEAD = subprocess.check_output(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], text=True).strip()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sums(bundle):
    with open(f"{bundle}/SHA256SUMS", "w") as f:
        for fn in sorted(os.listdir(bundle)):
            if fn == "SHA256SUMS":
                continue
            f.write(f"{sha256_file(os.path.join(bundle, fn))}  {fn}\n")


def manifest_security(apk):
    """Neutral manifest-derived security facts (§10: DECLARED facts only)."""
    out = {"tool": "aapt2 dump badging + permissions", "permissions_declared": [],
           "launchable_activities": [], "package": None}
    try:
        badging = subprocess.check_output([AAPT2, "dump", "badging", apk],
                                          text=True, timeout=60)
        for line in badging.splitlines():
            if line.startswith("package:"):
                out["package"] = line.split("name=")[1].split("'")[1] if "name='" in line else None
            if line.startswith("uses-permission:"):
                p = line.split("name=")[1].split("'")[1] if "name='" in line else line.strip()
                out["permissions_declared"].append(p)
            if line.startswith("launchable-activity:"):
                a = line.split("name=")[1].split("'")[1] if "name='" in line else line.strip()
                out["launchable_activities"].append(a)
    except Exception as e:  # aapt2 failure is recorded, never invented
        out["error"] = str(e)[:200]
    return out


def bundle_from_run(aid, run_dir, picks, session_extra, apk=None):
    bundle = f"{OUT}/{aid}"
    shutil.rmtree(bundle, ignore_errors=True)
    os.makedirs(bundle, exist_ok=True)
    metrics = {}
    for dest, src in picks:
        shutil.copy2(src, f"{bundle}/{dest}")
        metrics[dest] = {"png_sha256_16": sha256_file(src)[:16]}
    session = {
        "session_format": "s74-ops/1 (S74 FOLLOW-UP WAVE §6 execution checkpoint)",
        "runtime_commit": HEAD,
        "binary": "miniandroid/build/miniandroid (built at HEAD)",
        **session_extra,
        "representative_frames": list(metrics.keys()),
        "frame_metrics": metrics,
    }
    if apk:
        session["manifest_security"] = manifest_security(apk)
    with open(f"{bundle}/session.json", "w") as f:
        json.dump(session, f, indent=1)
    write_sums(bundle)
    print(f"[BUNDLED] {aid}: {list(metrics.keys())}")


def main():
    # 1. Snake — REUSE committed S73 evidence (taskbook §8: no re-run, no
    #    reopen). Wire the human-visible representative frames already committed.
    s73 = f"{REPO}/docs/evidence/s73_snake_autoplay/run_01"
    bundle_from_run(
        "androidgamesnake", s73,
        [("01_launch.png", f"{s73}/frames/frame_000.png"),
         ("02_food_capture_frame034.png", f"{s73}/frames/frame_034.png"),
         ("03_final.png", f"{s73}/screenshot.png")],
        {"app_dossier": "docs/compatibility/apps/androidgamesnake.json",
         "evidence_scope": "REUSED_COMMITTED_S73_PROOF (taskbook §8 — historical truth preserved)",
         "apk": {"file": "snake_v1.0_vc1.apk", "sha256_16": "54cf48a947f9b690"[:16]},
         "execution_mode": "real-dalvik (bytecode interpretation)",
         "launch_run": {"source": "docs/evidence/s73_snake_autoplay/run_01",
                        "proven": "88 moves / 22 turns / 1 food capture / 23 scheduled real taps / 3-run byte-identical"},
         "interaction_run": {"source": "same committed run",
                             "state_changes": "START->run, 22 accepted turns, food capture at frame 34 (snake 3->4)"},
         "persistence": {"verdict": "NOT_OBSERVED (restart-after-game-over honestly open; no data-root probe in S73 session)"},
         "manifest_security": {"note": "see dossier security block; session run pre-dates the s74-ops sandbox probe"}})

    # 2. TicTacToe GOLDEN FIXTURE — frames from the validator run at HEAD.
    ttt = "/tmp/tmp.8zjFny0Vd3/runA"
    if os.path.isdir(f"{ttt}/frames"):
        bundle_from_run(
            "tictactoe_golden_fixture", ttt,
            [("01_launch.png", f"{ttt}/frames/frame_000.png"),
             ("02_first_move.png", f"{ttt}/frames/frame_001.png"),
             ("03_x_wins.png", f"{ttt}/frames/frame_007.png")],
            {"app_dossier": "docs/compatibility/apps/tictactoe.json",
             "evidence_scope": "GOLDEN_FIXTURE (com.miniandroid.tictactoegolden — NOT the real APK; real APK = GL-blocker evidence, see tictactoe bundle)",
             "apk": {"file": "tictactoe_golden.apk (built at HEAD by validate_tictactoe_golden.sh)",
                     "sha256_16": "9d1c2954c675813c"},
             "execution_mode": "real-dalvik (bytecode interpretation)",
             "launch_run": {"validator": "miniandroid/tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh",
                            "result": "ALL PASS at HEAD: 9/9 clicks, X to move -> O to move -> X WINS at frame 7, 4X+3O final, frozen tail, run B byte-identical (613cfccc0f27...)"},
             "interaction_run": {"clicks": 9, "dispatch": "real DEX Outer$Inner listeners"},
             "persistence": {"verdict": "NO_PERSISTENCE_OBSERVED (in-memory game state; fixture writes no files)"}})
    else:
        print("[SKIP] tictactoe fixture temp frames gone; re-run validator")

    # 3. ConnectFour GOLDEN FIXTURE
    c4 = "/tmp/tmp.jeEgdDXVzl/runA"
    if os.path.isdir(f"{c4}/frames"):
        bundle_from_run(
            "connectfour_golden_fixture", c4,
            [("01_launch.png", f"{c4}/frames/frame_000.png"),
             ("02_midgame.png", f"{c4}/frames/frame_011.png"),
             ("03_y_wins.png", f"{c4}/frames/frame_022.png")],
            {"app_dossier": "docs/compatibility/apps/connectfour.json",
             "evidence_scope": "GOLDEN_FIXTURE (in-repo ConnectFour golden; canonical corrected result Y WINS at click 22)",
             "apk": {"file": "connectfour_golden.apk (built at HEAD by validate_connectfour_golden.sh)",
                     "sha256_16": "see session build log"},
             "execution_mode": "real-dalvik (bytecode interpretation)",
             "launch_run": {"validator": "miniandroid/tests/fixtures/connectfour_golden/validate_connectfour_golden.sh",
                            "result": "ALL PASS at HEAD: 24 clicks, R/Y turn flips, Y WINS at click 22 (diagonal), 11R+11Y final, frozen tail 22/23/24, run B byte-identical (38e568bd3815...)"},
             "interaction_run": {"clicks": 24, "dispatch": "real DEX char[6][7] state machine"},
             "persistence": {"verdict": "NO_PERSISTENCE_OBSERVED (in-memory board; fixture writes no files)"}})
    else:
        print("[SKIP] connectfour fixture temp frames gone; re-run validator")

    # 4. HelloWorld — golden byte-stable replay evidence (APK not in repo per
    #    APK policy; committed evidence is the canonical proof)
    hw_png = f"{REPO}/docs/evidence/external_hello_golden/miniandroid_frame1.png"
    hw_jpg = f"{REPO}/docs/evidence/s54_frames/helloworld_ext01_base.jpg"
    picks = []
    if os.path.exists(hw_jpg):
        picks.append(("01_launch.jpg", hw_jpg))
    if os.path.exists(hw_png):
        picks.append(("02_frame1.png", hw_png))
    if picks:
        bundle_from_run(
            "helloworld", None, picks,
            {"app_dossier": "docs/compatibility/apps/helloworld.json",
             "evidence_scope": "REUSED_COMMITTED_GOLDEN (byte-stable S53->S54 replay proof; APK not committed per §20 APK policy, sha256_16 009b4671 pinned in dossier)",
             "execution_mode": "real-dalvik (bytecode interpretation)",
             "launch_run": {"source": "docs/evidence/s54_frames/helloworld_ext01_base.jpg + GOLDEN_HELLOWORLD.md",
                            "proven": "'hello world' self-aware identity text + API level line rendered; golden byte-stable"},
             "interaction_run": None,
             "persistence": {"verdict": "NO_PERSISTENCE_OBSERVED (display-only fixture app)"}})

    # 5. TriPeaks — replace bundle with the long-run lobby + honest tap note
    tp = f"{REPO}/run/s74f_ops/tripeaks_long"
    tpng = f"{REPO}/run/s74f_ops/tripeaks_ng"
    if os.path.isdir(f"{tp}/frames"):
        bundle_from_run(
            "tripeaks", None,
            [("01_splash_black.png", f"{tp}/frames/frame_003.png"),
             ("02_lobby.png", f"{tp}/frames/frame_009.png"),
             ("03_final_lobby.png", f"{tp}/frames/frame_013.png")],
            {"app_dossier": "docs/compatibility/apps/tripeaks.json",
             "evidence_scope": "REAL_APK at HEAD (14-frame run; splash->lobby transition at frame 7)",
             "apk": {"file": "tripeaks_v1.2.1_vc4.apk", "sha256_16": sha256_file(f"{REPO}/upload/canonical_apks/tripeaks_v1.2.1_vc4.apk")[:16]},
             "execution_mode": "real-dalvik (bytecode interpretation)",
             "launch_run": {"rc": 0, "frames": 14,
                            "state": "frames 0-6 splash (0 px — SplashActivity, no draw), frame 7 lobby 205,061 px"},
             "interaction_run": {"attempt": "tap 440,120@9 on 'New Game' — hit-test target=0 (menu is not a per-view listener surface)",
                                 "result": "board NOT reached at HEAD; R-NEW-388 (OBJECT-IDENTITY) remains the truthful blocker",
                                 "historical": "docs/evidence/s65_spotlight/tp_game_board.png (board render, older binary)"},
             "persistence": {"verdict": "NO_PERSISTENCE_OBSERVED (no files in data root)"},
             "manifest_security": manifest_security(f"{REPO}/upload/canonical_apks/tripeaks_v1.2.1_vc4.apk")})

    # 6. Manifest security facts for the real-APK bundles that lack them
    sec_apks = {
        "unote": "app.varlorg.unote_30.apk",
        "dooz": "io.github.yamin8000.dooz_23.apk",
        "gmdice": "de.duenndns.gmdice_8.apk",
        "microtimer": "dubrowgn.microtimer_8.apk",
        "fishrings": "fishrings_v1.23_vc6.apk",
        "bouncy": "bouncy.apk",
        "stopwatch": "com.github.muellerma.stopwatch_6.apk",
        "opmt": "opmt_v0.1.2_vc1.apk",
        "tictactoe": "com.emmanuelmess.tictactoe_3.apk",
    }
    for aid, fn in sec_apks.items():
        sj = f"{OUT}/{aid}/session.json"
        if not os.path.exists(sj):
            continue
        s = json.load(open(sj))
        s["manifest_security"] = manifest_security(f"{REPO}/upload/canonical_apks/{fn}")
        # attach the same facts to the dossier-level snapshot file
        with open(sj, "w") as f:
            json.dump(s, f, indent=1)
        write_sums(f"{OUT}/{aid}")
        ms = s["manifest_security"]
        print(f"[SEC] {aid}: pkg={ms.get('package')} perms={len(ms.get('permissions_declared', []))} launchable={ms.get('launchable_activities')}")


if __name__ == "__main__":
    main()
