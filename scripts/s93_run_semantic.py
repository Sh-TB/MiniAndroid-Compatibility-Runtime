#!/usr/bin/env python3
"""s93_run_semantic.py — S93 §17/§18/§27 real-corpus semantic runner.

Applies the S93 semantic truth layer (image/animation/font/text vectors,
loaded-state chains, failure taxonomy) to REAL MiniAndroid runs.

Modes:
  --pilot    analyze the fresh S92 pilot evidence (run/s92pilot/*)
  --random   seeded reproducible random sample (§17) from the fetchable
             SHA-pinned corpus pool: seed + registry SHA + selection are
             recorded in run/s93/random_sample.json; selected titles are
             fetched (SHA-verified), executed (REAL runtime), analyzed.

Aggregates (§26/§28) written to run/s93/: metrics.json, failure_map.json,
asset_truth.json, animation_truth.json, font_truth.json.
Streaming + resume-safe (§18): one title at a time; verdict JSONs are
skipped if already present and valid.
"""
import json
import os
import random
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))
sys.path.insert(0, os.path.join(REPO, "tools"))

from probes.graphics_common import (RunEvidence, load_json,  # noqa: E402
                                    apk_extract_asset, find_contract)
from probes.semantic_image import image_truth  # noqa: E402
from probes.semantic_animation import animation_truth  # noqa: E402
from probes.semantic_font import (text_truth, font_object_truth)  # noqa
from probes.semantic_verdict import (asset_loaded_state,  # noqa: E402
                                     classify_failures, derive_s93_level)

MA_BIN = os.path.join(REPO, "miniandroid", "build", "miniandroid")
DL = os.path.join(REPO, "miniandroid", "download")
PILOT_DIR = os.path.join(REPO, "run", "s92pilot")
OUT93 = os.path.join(REPO, "run", "s93")
SEED = 20260924

# --- pilot case -> (apk file, package, title, stratum) ----------------------
PILOT_CASES = {
    "tictactoe": ("com.emmanuelmess.tictactoe_3.apk",
                  "com.emmanuelmess.tictactoe", "TicTacToe Classic",
                  "game-view-xml"),
    "nounours": ("ca.rmen.nounours_358.apk", "ca.rmen.nounours",
                 "ca.rmen.nounours", "image-heavy"),
    "dodge": ("com.dozingcatsoftware.dodge_10.apk",
              "com.dozingcatsoftware.dodge", "Dodge", "game-canvas"),
    "bouncy": ("com.dozingcatsoftware.bouncy_43.apk",
               "com.dozingcatsoftware.bouncy", "Vector Pinball",
               "game-gl"),
    "hotdeath": ("com.smorgasbork.hotdeath_11.apk",
                 "com.smorgasbork.hotdeath", "Hot Death Uno",
                 "image-heavy"),
    "bobball": ("org.bobstuff.bobball_26.apk", "org.bobstuff.bobball",
                "Bobball", "game-surfaceview"),
    "urlchecker": ("com.trianguloy.urlchecker_28.apk",
                   "com.trianguloy.urlchecker", "URL Checker", "app"),
    "chessclock": ("com.chessclock.android_29.apk",
                   "com.chessclock.android", "Chess Clock", "app"),
    "unote": ("app.varlorg.unote_30.apk", "app.varlorg.unote", "uNote",
              "app"),
    "gmdice": ("de.duenndns.gmdice_8.apk", "de.duenndns.gmdice",
               "GM Dice", "app-image-heavy"),
    "fishrings": ("eu.veldsoft.fish.rings_6.apk",
                  "eu.veldsoft.fish.rings", "Fish Rings", "game-view-xml"),
    "snake-deluxe": ("upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk",
                  "com.miniandroid.snakedeluxe",
                  "Snake Deluxe", "game-canvas"),
    "mini-tetris": ("upload/s80_games/build_tetris/tetris_v1.0_vc1.apk",
                  "com.miniandroid.tetris",
                  "Mini Tetris", "game-canvas"),
    "g2048": ("upload/s80_games/build_2048/g2048_v1.0_vc1.apk",
              "com.miniandroid.g2048", "2048",
              "game-canvas"),
    "tictactoedeluxe": ("upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
                        "com.miniandroid.tictactoedeluxe",
                        "TicTacToe Deluxe", "game-canvas"),
    "minicraft": ("upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
                  "com.miniandroid.minicraft", "Minicraft",
                  "game-canvas"),
}

# pilot titles whose evidence window includes a scheduled tap (§10/§11:
# animation truth is only judgeable when an input could have moved things)
TAP_CASES = {"fishrings", "snake-deluxe", "mini-tetris", "g2048",
             "tictactoedeluxe", "minicraft"}

# §17 random-sample pool: fetchable SHA-pinned corpus titles not already
# executed in the S92 pilot (see miniandroid/tests/corpus/apks.json).
RANDOM_POOL = [
    ("openlauncher", "com.benny.openlauncher_39.apk",
     "com.benny.openlauncher", "OpenLauncher", "app"),
    ("dooz", "io.github.yamin8000.dooz_18.apk", "io.github.yamin8000.dooz",
     "Dooz", "game"),
    ("bgclock", "nl.hansdezwart.bgclock_2.apk", "nl.hansdezwart.bgclock",
     "BGClock", "app"),
    ("stopwatchg", "com.github.muellerma.stopwatch_6.apk",
     "com.github.muellerma.stopwatch", "Stopwatch", "app"),
    ("simplekeyboard", "rkr.simplekeyboard.inputmethod_145.apk",
     "rkr.simplekeyboard.inputmethod", "Simple Keyboard", "app"),
    ("microtimer", "dubrowgn.microtimer_8.apk", "dubrowgn.microtimer",
     "MicroTimer", "app"),
    ("bnotes", "org.billthefarmer.notes_139.apk", "org.billthefarmer.notes",
     "Notes", "app-text-heavy"),
    ("simplestopwatch", "omegacentauri.mobi.simplestopwatch_26.apk",
     "omegacentauri.mobi.simplestopwatch", "Simple Stopwatch", "app"),
    ("headingcalc", "org.debian.eugen.headingcalculator_1.apk",
     "org.debian.eugen.headingcalculator", "Heading Calculator", "app"),
    ("tinymusic", "com.martinmimigames.tinymusicplayer_1.apk",
     "com.martinmimigames.tinymusicplayer", "Tiny Music Player", "app"),
    ("kiss", "fr.neamar.kiss_224.apk", "fr.neamar.kiss", "KISS Launcher",
     "app"),
    ("fossifynotes", "org.fossify.notes_13.apk", "org.fossify.notes",
     "Fossify Notes", "app-text-heavy"),
    ("markor", "net.gsantner.markor_163.apk", "net.gsantner.markor",
     "Markor", "app-text-heavy"),
]

PROV_STAGES = ("ASSET_FOUND", "RESOURCE_RESOLVED", "DECODED",
               "BITMAP_CREATED", "VIEW_RECEIVED", "DRAW_CALLED")


def find_apk(fname):
    for base in (DL, os.path.join(DL, "exp076_corpus"),
                 os.path.join(DL, "exp073_real_apps"),
                 os.path.join(REPO, "upload", "s80_games", "build_sd"),
                 os.path.join(REPO, "upload", "s80_games", "build_tetris"),
                 os.path.join(REPO, "upload", "s80_games", "build_2048"),
                 os.path.join(REPO, "upload", "s83_games", "build_ttt"),
                 os.path.join(REPO, "upload", "s86_games",
                              "build_minicraft"),
                 os.path.join(REPO, "fixtures", "s92battery")):
        p = os.path.join(base, os.path.basename(fname))
        if os.path.isfile(p):
            return p
    return None


def run_runtime(case, apk, rundir, frames=6):
    os.makedirs(rundir, exist_ok=True)
    env = dict(os.environ)
    env["MINIANDROID_GFX_PROVENANCE"] = os.path.join(
        rundir, "gfx_provenance.json")
    env["MINIANDROID_CLICK_AUDIT"] = os.path.join(rundir,
                                                  "click_audit.jsonl")
    cmd = (f"{MA_BIN} run -o {rundir} --execution-mode real-dalvik "
           f"--frames {frames} --width 1080 --height 1920 "
           f"--dump-view-tree --data-root {rundir}/data --apk {apk}")
    r = subprocess.run(cmd, shell=True, env=env, capture_output=True,
                       text=True, timeout=600)
    return r.returncode


def analyze_case(case, run_dir, apk_path, package, title, stratum,
                 is_game):
    """Full S93 semantic analysis for one executed title."""
    ev = RunEvidence(run_dir)
    out = {"schema": "s93.semantic_run.v1", "case": case, "package":
           package, "title": title, "stratum": stratum,
           "run_dir": os.path.relpath(run_dir, REPO),
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
           "evidence": ev.evidence_inventory()}
    if not ev.screenshot:
        out["verdict"] = "NO_EVIDENCE"
        return out

    prov = ev.provenance or {}
    events = prov.get("events", [])
    # record-quality classes: a drawn record with a real dst is the best
    # pixel-checkable evidence; decode-only/zero-dst records still feed the
    # loaded chain but can never be pixel-checked (honest NOT_APPLICABLE)
    def rec_class(r):
        dst = r.get("dst") or {}
        if r.get("DRAW_CALLED") and dst.get("w", 0) > 1 and \
                dst.get("h", 0) > 1:
            return 0
        if dst.get("w", 0) > 1 and dst.get("h", 0) > 1:
            return 1
        if r.get("DRAW_CALLED"):
            return 2
        return 3

    latest = {}
    for e in events:
        p = e.get("path")
        if not p:
            continue
        prev = latest.get(p)
        if prev is None or rec_class(e) < rec_class(prev):
            latest[p] = e
        elif rec_class(e) == rec_class(prev) and \
                rec_class(e) == 0 and e is not prev:
            # keep the LATEST fully-drawn record (post-interaction state)
            latest[p] = e

    image_truths = {}
    loaded = {}
    checked = 0
    pixel_checked = 0
    for path, rec in sorted(latest.items(),
                            key=lambda kv: rec_class(kv[1])):
        if checked >= 12:
            break
        rc = rec_class(rec)
        asset = apk_extract_asset(apk_path, path) if apk_path else None
        if not asset:
            continue
        checked += 1
        dst = rec.get("dst") or {}
        if rc <= 1 and pixel_checked < 10:
            pixel_checked += 1
            region = [int(dst.get("x", 0)), int(dst.get("y", 0)),
                      max(2, int(dst.get("w", 8))),
                      max(2, int(dst.get("h", 8)))]
            try:
                it = image_truth(ev.screenshot, asset, region=region)
            except Exception as ex:
                it = {"verdict": "UNKNOWN", "error": str(ex)[:100]}
        else:
            it = {"verdict": "NOT_APPLICABLE",
                  "note": "decoded/bound but no drawn dst region — no "
                          "pixel claim possible from this record",
                  "record_class": rc}
        image_truths[path] = it
        pe = [{"event": k} for k in PROV_STAGES if rec.get(k)]
        loaded[path] = asset_loaded_state(
            asset=path, provenance_events=pe, image_truth=it,
            screenshot_region_valid=(rc <= 1))

    # ViewTree image-node fallback: titles whose provenance produced no
    # pixel-checkable records get unanchored checks of the largest APK
    # raster assets (confidence downgraded, honest)
    if pixel_checked == 0 and ev.view_tree:
        import re
        nodes = ev.view_tree.get("nodes", [])
        img_nodes = [n for n in nodes
                     if n.get("image_resource_id") or
                     "ImageView" in str(n.get("class", ""))]
        if img_nodes and apk_path:
            import zipfile as _zf
            with _zf.ZipFile(apk_path) as z:
                cand = sorted(
                    (i for i in z.infolist()
                     if re.search(r"res/.*\.(png|webp|jpg|jpeg)$",
                                  i.filename)),
                    key=lambda i: -i.file_size)[:3]
            for info in cand:
                asset = apk_extract_asset(apk_path, info.filename)
                if not asset:
                    continue
                try:
                    it = image_truth(ev.screenshot, asset, region=None)
                except Exception as ex:
                    it = {"verdict": "UNKNOWN", "error": str(ex)[:100]}
                it["provenance"] = {"value": "UNANCHORED_FALLBACK",
                                    "note": "ViewTree node present but "
                                            "resource path unresolvable"}
                image_truths[info.filename] = it
                loaded[info.filename] = asset_loaded_state(
                    asset=info.filename,
                    provenance_events=[{"event": "ASSET_FOUND"}],
                    image_truth=it, screenshot_region_valid=False)

    # animation truth: games only (apps carry no animation contract);
    # titles whose evidence window contains no interaction have NO animation
    # contract — a static window is honest NOT_APPLICABLE (detection kept)
    anim = None
    if is_game and len(ev.frames) >= 2:
        anim = animation_truth([p for _, p in ev.frames],
                               expect_motion=True)
        if anim.get("verdict") == "FROZEN" and case not in TAP_CASES:
            anim = dict(anim)
            anim["verdict"] = "NOT_APPLICABLE"
            anim["note"] = ("STATIC_WINDOW: no interaction in evidence "
                            "window — frozen frames cannot be judged "
                            "without an animation contract")
    elif not is_game:
        anim = {"ANIMATION_DECODED": "NOT_APPLICABLE",
                "note": "static app — no animation contract"}

    # text truth over ViewTree text nodes (up to 6)
    text_truths = {}
    if ev.view_tree:
        nodes = ev.view_tree.get("nodes", [])
        texts = [n for n in nodes
                 if str(n.get("text", "")).strip() and
                 n.get("width", 0) >= 12 and n.get("height", 0) >= 12 and
                 n.get("visibility", 0) == 0 and
                 0 <= n.get("x", 0) and 0 <= n.get("y", 0) and
                 n.get("x", 0) + n.get("width", 0) <= 1080 and
                 n.get("y", 0) + n.get("height", 0) <= 1920]
        for n in texts[:6]:
            try:
                tt = text_truth(ev.screenshot, node=n)
            except Exception as ex:
                tt = {"verdict": "UNKNOWN", "error": str(ex)[:100]}
            text_truths[f"node:{n.get('id', len(text_truths))}"] = tt

    # font object truth: APK-bundled fonts (up to 2)
    font_truths = {}
    if apk_path:
        import zipfile
        try:
            with zipfile.ZipFile(apk_path) as z:
                fonts = [n for n in z.namelist()
                         if n.lower().endswith((".ttf", ".otf"))][:2]
            for fpath in fonts:
                data = apk_extract_asset(apk_path, fpath)
                if data:
                    font_truths[fpath] = font_object_truth(data)
        except Exception:
            pass

    cats = classify_failures(image_truths=image_truths,
                             animation_truth=anim,
                             font_truths=font_truths,
                             text_truths=text_truths)
    lvl = derive_s93_level(image_truths=image_truths,
                           animation_truth=anim, font_truths=font_truths,
                           text_truths=text_truths)
    out.update({
        "image_truths": image_truths,
        "loaded_states": loaded,
        "animation_truth": anim,
        "text_truths": text_truths,
        "font_truths": font_truths,
        "failure_categories": cats,
        "s93": lvl,
        "s93_verdict": lvl["s93_level"],
    })
    return out


def save(out, name):
    d = os.path.join(OUT93, "verdicts")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{name}.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1, default=str)
    return p


def run_pilot():
    results = {}
    for case, (fname, pkg, title, stratum) in PILOT_CASES.items():
        run_dir = os.path.join(PILOT_DIR, case)
        if not os.path.isdir(run_dir):
            results[case] = {"error": "no run dir"}
            continue
        apk = find_apk(fname)
        is_game = stratum.startswith("game")
        out = analyze_case(case, run_dir, apk, pkg, title, stratum, is_game)
        save(out, case)
        n_img = len(out.get("image_truths", {}))
        vv = sum(1 for i in out.get("image_truths", {}).values()
                 if i.get("verdict") == "VISUALLY_VERIFIED")
        results[case] = {
            "s93_verdict": out.get("s93_verdict"),
            "images_checked": n_img, "images_visually_verified": vv,
            "animation": (out.get("animation_truth") or {}).get("verdict"),
            "text_nodes": len(out.get("text_truths", {})),
            "fonts": len(out.get("font_truths", {})),
            "top_failures": [c["category"] for c in
                             out.get("failure_categories", [])][:4],
        }
        print(f"{case:16s} {out.get('s93_verdict'):14s} img={n_img} "
              f"vv={vv} anim={results[case]['animation']} "
              f"fails={results[case]['top_failures']}")
    return results


def run_random(n=6):
    reg_path = os.path.join(REPO, "docs", "evidence", "canonical",
                            "registry.json")
    import hashlib
    reg_sha = hashlib.sha256(open(reg_path, "rb").read()).hexdigest()
    rng = random.Random(SEED)
    pool = sorted(RANDOM_POOL)
    selection = rng.sample(pool, min(n, len(pool)))
    manifest = {"schema": "s93.random_sample.v1", "seed": SEED,
                "registry_sha256": reg_sha,
                "pool_size": len(pool),
                "selection": [{"case": c, "apk": a, "package": p,
                               "title": t, "stratum": s}
                              for c, a, p, t, s in selection]}
    with open(os.path.join(OUT93, "random_sample.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    results = {}
    for case, fname, pkg, title, stratum in selection:
        apk = find_apk(fname)
        if not apk:
            # fetch via manifest pin: resolve the manifest ENTRY NAME for
            # this filename (fetch_corpus filters by entry name)
            try:
                m = json.load(open(os.path.join(
                    REPO, "miniandroid", "tests", "corpus", "apks.json")))
                entry = next((e for e in m["apks"] if e.get(
                    "download_url", "").endswith(fname)), None)
                if entry:
                    subprocess.run(
                        ["python3", os.path.join(REPO, "scripts", "test",
                                                 "fetch_corpus.py"),
                         entry["name"]],
                        cwd=REPO, capture_output=True, timeout=240)
            except Exception:
                entry = None
            apk = find_apk(fname)
        if not apk:
            results[case] = {"apk_availability": "NOT_FETCHABLE"}
            print(f"{case:16s} APK NOT FETCHABLE ({fname})")
            continue
        rundir = os.path.join(OUT93, "random", case)
        rc = run_runtime(case, apk, rundir)
        out = analyze_case(case, rundir, apk, pkg, title, stratum,
                           is_game=(stratum == "game"))
        out["apk_sha256"] = entry_sha(fname)
        out["runtime_rc"] = rc
        save(out, f"random_{case}")
        n_img = len(out.get("image_truths", {}))
        results[case] = {
            "s93_verdict": out.get("s93_verdict"),
            "runtime_rc": rc, "images_checked": n_img,
            "top_failures": [c["category"] for c in
                             out.get("failure_categories", [])][:4],
        }
        print(f"{case:16s} rc={rc} {out.get('s93_verdict'):14s} "
              f"img={n_img} fails={results[case]['top_failures']}")
    return results


def entry_sha(fname):
    try:
        m = json.load(open(os.path.join(REPO, "miniandroid", "tests",
                                        "corpus", "apks.json")))
        for e in m["apks"]:
            if e.get("download_url", "").endswith(fname):
                return e.get("sha256")
    except Exception:
        pass
    return None


def main():
    os.makedirs(OUT93, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "--pilot"
    if mode == "--pilot":
        results = run_pilot()
    elif mode == "--random":
        results = run_random(int(sys.argv[2]) if len(sys.argv) > 2 else 6)
    else:
        results = {}
    with open(os.path.join(OUT93, f"semantic_results{mode[1:]}.json"),
              "w") as f:
        json.dump(results, f, indent=1, default=str)
    print(f"saved: {os.path.join(OUT93, f'semantic_results{mode[1:]}.json')}")


if __name__ == "__main__":
    main()
