#!/usr/bin/env python3
"""T279 P2 — TWO-INDEPENDENT-RUN campaign on the current engine build.

Per title: two independent S182-protocol runs (fresh store each, separate
rundirs, separate logs) + two identical --click-test interaction runs for
interactive candidates (games + clickable apps). Regressed-class titles
(Compose onMeasure frontier) get the two reproducibility runs only.

Incremental JSON: run_t279/T279_TWO_RUN_BATTERY.json (survives interruption).
Evidence copies (compact 500px screenshots) are produced by t279_publish.py.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/z/my-project")
sys.path.insert(0, str(BASE / "scripts"))
import s165_trains as t
import s166_trains as s166

BIN = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "run_t279"
OUT.mkdir(parents=True, exist_ok=True)
EJSON = OUT / "T279_TWO_RUN_BATTERY.json"

# tag: (apk_rel, secs, kind, interactive)
# interactive=True -> two extra --click-test runs (the same deterministic
# sequence in both interaction runs, per the T279 two-run law).
TITLES = {
    # ---- S182 REAL_APP_CONTENT 9 (all APKs on disk, SHAs pinned+verified) ----
    "gmdice": ("upload/canonical_apks/de.duenndns.gmdice_8.apk", 40, "game", True),
    "bouncy": ("upload/canonical_apks/com.dozingcatsoftware.bouncy_43.apk", 45, "game", True),
    "pfdicer": ("upload/fdroid_batch/org.secuso.privacyfriendlydicer_101.apk", 45, "game", True),
    "pfsolitaire": ("upload/fdroid_batch/org.secuso.privacyfriendlysolitaire_4.apk", 45, "game", True),
    "textpad": ("upload/fdroid_batch/com.maxistar.textpad_63.apk", 60, "app", True),
    "librecontactsbackup": ("upload/fdroid_batch/com.ashkanrafiee.librecontactsbackup_32.apk", 60, "app", True),
    "uturn": ("upload/fdroid_batch/ac.stresa.uturn_22.apk", 45, "game", False),   # regressed class
    "wocheneinkauf": ("upload/fdroid_batch/app.wocheneinkauf_199.apk", 60, "app", False),  # regressed class
    "peri": ("upload/fdroid_batch/app.simple.peri_983.apk", 60, "app", False),    # regressed class
    # ---- S182 PARTIAL titles whose APKs are on disk ----
    "stacktower3d": ("upload/canonical_apks/stack.tower3d_1.apk", 45, "game", True),
    "emmanuelttt": ("upload/canonical_apks/com.emmanuelmess.tictactoe_3.apk", 45, "game", True),
    # ---- S23-S27 easy-APK wave (registry-absent achievements; SHAs pinned in
    # miniandroid/evidence/s23/s23_apk_sha256.tsv, verified vs disk) ----
    "npuzzle": ("upload/handoff_apks/name.livitski.games.puzzle.android_2.apk", 45, "game", True),
    "ugaday": ("upload/handoff_apks/ru.zxalexis.ugaday_15.apk", 45, "game", True),
    "blockinger": ("upload/handoff_apks/org.blockinger.game_14.apk", 45, "game", True),
    "farmerbb": ("upload/handoff_apks/com.farmerbb.notepad_122.apk", 60, "app", False),
    "itsfrz": ("upload/handoff_apks/com.itsfrz.tictactoe_5.apk", 45, "game", False),
    "flip": ("upload/handoff_apks/org.ecos.logic.flip_a_coin_3.apk", 45, "app", False),
    "janken": ("upload/handoff_apks/com.attenomy.janken_1.apk", 45, "app", False),
    "diceroller": ("upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk", 45, "app", False),
    "authsrng": ("upload/handoff_apks/com.ivylopez.authsrng_6.apk", 45, "app", False),
    "minos": ("upload/handoff_apks/de.tcrass.minos_10004.apk", 45, "app", False),
    "randomix": ("upload/handoff_apks/com.minar.randomix_42.apk", 45, "game", True),
    "cocodechess": ("upload/handoff_apks/dk.cocode.chess_5022.apk", 45, "game", False),
}

SUBSYS = {
    "font": r"Typeface|TextShaper|font_family|createFromAsset|FontFamily",
    "graphics": r"Bitmap|BitmapFactory|Canvas|drawable|Drawable|decode|Surface|shader",
    "layout": r"Inflater|inflate|LayoutTras|setContentView|measure|layout_nodes|XMLLoader",
    "webview": r"WebView|webkit|loadUrl",
    "db": r"SQLite|sqlite|Room|Cursor|Database",
    "compose": r"Compose|Recomposer|Snapshot",
    "missing_class": r"NoDefinitionFoundException|ClassNotFoundException",
}


def discover_pkg(apk, store):
    store.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(BIN), "install", str(apk), "--data-root",
                        str(store)], capture_output=True, timeout=600)
    apps = store / "data" / "app"
    if apps.exists():
        ds = [d.name for d in apps.iterdir() if d.is_dir()
              and not d.name.startswith(".")]
        if ds:
            return ds[0]
    print("[discover] FAIL", (r.stderr or b"")[-160:].decode(
        errors="replace"))
    return None


def first_uncaught_block(text, span=6):
    m = re.search(r"UNCAUGHT", text)
    if not m:
        m = re.search(r"(?:Exception|Error)[:\s]", text)
    if not m:
        return None
    lines = text[max(0, m.start() - 80):m.start() + 900].splitlines()
    return " | ".join(lines[:span])[:500]


def census(text):
    out = {}
    for k, pat in SUBSYS.items():
        n = len(re.findall(pat, text))
        if n:
            out[k] = n
    return out


def parse_click_test(text):
    """--click-test summary lines: clicks dispatched, state changes, etc."""
    out = {"click_lines": []}
    for line in text.splitlines():
        if re.search(r"CLICK|click|CLICKABLE|statechang|state change", line,
                     re.I) and len(out["click_lines"]) < 12:
            out["click_lines"].append(line.strip()[:160])
    return out


def one_run(tag, apk_rel, secs, run_id, click_test):
    """One independent execution. Returns the row dict."""
    apk = BASE / apk_rel
    store = OUT / f"store_{tag}_{run_id}"
    pkg = discover_pkg(apk, store)
    if pkg is None or not t.ensure_store(apk, store, BIN, pkg):
        return {"tag": tag, "run_id": run_id, "class": "INSTALL_FAIL"}
    for k in s166.CLEAN_ENVS:
        os.environ.pop(k, None)
    rundir = OUT / f"{tag}_{run_id}"
    console = OUT / f"{tag}_{run_id}.err"
    cmd = [str(BIN), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(secs), "--frames", "5",
           "--trace", "--package", pkg]
    if click_test:
        cmd.append("--click-test")
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=secs + 150)
    wall = round(time.time() - t0, 1)
    shot = rundir / "screenshot.png"
    text = console.read_text(errors="replace")
    row = {"tag": tag, "run_id": run_id, "click_test": click_test,
           "pkg": pkg, "apk": apk_rel, "wall_s": wall,
           "face": t.sha16(shot) if shot.exists() else None,
           "shot_bytes": shot.stat().st_size if shot.exists() else 0,
           "uncaught": len(re.findall(r"UNCAUGHT", text)),
           "ndfe": len(re.findall(r"NoDefinitionFoundException", text))}
    ts = rundir / "trace_summary.json"
    if ts.exists():
        try:
            s = json.load(open(ts))
            fa = s.get("frame_analysis") or {}
            row["verdict"] = fa.get("verdict")
            row["app_owned_pixels"] = fa.get("app_owned_pixels")
            row["app_draw_ops"] = fa.get("app_draw_ops")
            row["unique_colors"] = fa.get("unique_colors")
            row["final_state"] = (s.get("lifecycle") or {}).get("final_state")
            row["first_failure_event"] = s.get("first_failure_event")
            row["last_exception"] = s.get("last_exception")
        except Exception as e:
            row["trace_err"] = str(e)[:120]
    row["first_stack"] = first_uncaught_block(text)
    row["subsys_census"] = census(text)
    if click_test:
        row["click_test_out"] = parse_click_test(text)
    if "REAL_APP_CONTENT" in str(row.get("verdict")):
        row["class"] = "REAL_APP_CONTENT"
    elif row.get("face") is None:
        row["class"] = "NO_FRAME"
    else:
        row["class"] = "PARTIAL"
    return row


def main():
    tags = sys.argv[1].split(",") if len(sys.argv) > 1 else list(TITLES)
    rows = json.load(open(EJSON)) if EJSON.exists() else {}
    bin_sha = t.sha16(BIN)
    print(f"[t279] binary sha16={bin_sha} titles={len(tags)}")
    for tag in tags:
        apk_rel, secs, kind, interactive = TITLES[tag]
        ent = rows.get(tag) or {"tag": tag, "kind": kind, "apk": apk_rel,
                                "bin_sha16": bin_sha, "runs": {}}
        # run 1 + run 2: the S182 reproducibility protocol
        for rid in ("r1", "r2"):
            key = f"run_{rid}"
            if key in ent["runs"] and ent["runs"][key].get("class") not in (
                    None, "INSTALL_FAIL"):
                continue
            print(f"[t279] {tag} {rid} (launch+census)", flush=True)
            ent["runs"][key] = one_run(tag, apk_rel, secs, rid, False)
            json.dump(rows, open(EJSON, "w"), indent=1, default=str)
        # interaction runs: identical deterministic click-test sequence, twice
        if interactive:
            for rid in ("ct1", "ct2"):
                key = f"run_{rid}"
                if key in ent["runs"] and ent["runs"][key].get("class") not in (
                        None, "INSTALL_FAIL"):
                    continue
                print(f"[t279] {tag} {rid} (click-test)", flush=True)
                ent["runs"][key] = one_run(tag, apk_rel, secs, rid, True)
                json.dump(rows, open(EJSON, "w"), indent=1, default=str)
        # reproducibility verdict for this tag
        r1, r2 = ent["runs"].get("run_r1", {}), ent["runs"].get("run_r2", {})
        same_face = (r1.get("face") and r1.get("face") == r2.get("face"))
        both_real = (r1.get("class") == "REAL_APP_CONTENT"
                     and r2.get("class") == "REAL_APP_CONTENT")
        ent["two_run_verdict"] = (
            "PASS-IDENTICAL" if same_face and both_real else
            "PASS-CONSISTENT" if both_real else
            "FAIL-NOT_REPRODUCIBLE" if r1.get("class") != r2.get("class")
            else "FAIL-CLASS_" + str(r1.get("class")))
        rows[tag] = ent
        json.dump(rows, open(EJSON, "w"), indent=1, default=str)
        print(f"[t279] == {tag}: {ent['two_run_verdict']} "
              f"faces {r1.get('face')}/{r2.get('face')}", flush=True)
    print("[t279] DONE ->", EJSON)


if __name__ == "__main__":
    main()
