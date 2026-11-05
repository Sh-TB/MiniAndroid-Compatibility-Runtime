#!/usr/bin/env python3
"""s167_w6_gates.py — S167: W6 (stack+laws) verification gates.

REF = S166 final insurance 2a5464c2bf15f9ec (HEAD-tree product)
NEW = build/miniandroid 53fa8392640d1279 (HEAD + repaired w6_stack 53d234e1
      + w6_laws 65699ca9 — author-base CLEAN + 3-way clean on my tree)

Phases (argv[1]):
  anchors_mg   microtimer (pin) + g2048 delta
  anchors_oc   opencalc delta
  dooz_pair    dooz settle A/B (S156 fresh-store law, RSS monitor)
  tg_pair      Telegram boot A/B (seed+skip envs, pixels/api/uncaught)
  tb_pair      Thunderbird A/B (NDFE census, law-log census)
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

REF = BASE / ("upload/_ma_local_backup/"
              "miniandroid_s166_final_2a5464c2bf15f9ec.bin")
NEW = BASE / "miniandroid/build/miniandroid"
OUT = BASE / "run_s167_w6"
OUT.mkdir(parents=True, exist_ok=True)
EVID = BASE / "evidence/s167_w6"

APKS = {
    "microtimer": (BASE / "upload/canonical_apks/dubrowgn.microtimer_8.apk",
                   "dubrowgn.microtimer"),
    "g2048": (BASE / "upload/s80_games/build_2048/g2048_v1.0_vc1.apk",
              "com.miniandroid.g2048"),
    "opencalc": (BASE / "upload/opencalculator_53.apk",
                 "com.darkempire78.opencalculator"),
    "tb": (BASE / "upload/net.thunderbird.android_33.apk",
           "net.thunderbird.android"),
}
PINS = {"microtimer": "bbd350b6c14fbd52"}
CLEAN_ENVS = s166.CLEAN_ENVS + ("MINIANDROID_F261X_LAW",)


def save(name, row):
    out = EVID / name
    rows = {}
    if out.exists():
        try:
            rows = json.load(open(out))
        except Exception:
            rows = {}
    rows.update(row)
    json.dump(rows, open(out, "w"), indent=1, default=str)
    print("evidence ->", out)


def app_run(bin_path, tag, apk, store, pkg, max_seconds=75, frames=4):
    for k in CLEAN_ENVS:
        os.environ.pop(k, None)
    assert t.ensure_store(apk, store, bin_path, pkg), f"install fail {tag}"
    rundir = OUT / tag
    console = OUT / f"{tag}.err"
    cmd = [str(bin_path), "run", "--execution-mode", "real-dalvik",
           "--data-root", str(store), "-o", str(rundir),
           "--max-seconds", str(max_seconds), "--frames", str(frames),
           "--trace", "--package", pkg]
    t0 = time.time()
    with open(console, "w") as cf:
        subprocess.run(cmd, stdout=cf, stderr=subprocess.STDOUT,
                       timeout=max_seconds + 90)
    wall = round(time.time() - t0, 1)
    shot = rundir / "screenshot.png"
    text = console.read_text(errors="replace")
    row = {
        "tag": tag, "bin": t.sha16(bin_path), "wall_s": wall,
        "stderr_sha16": t.sha16(console) if console.exists() else None,
        "screenshot_face": t.sha16(shot) if shot.exists() else None,
        "uncaught": len(re.findall(r"UNCAUGHT", text)),
        "ndfe": len(re.findall(r"NoDefinitionFoundException", text)),
        "law_rows": len(re.findall(r"F-C4-5[6-7][0-9]|F-C4-261x", text)),
        "frames": re.findall(r"Frames Rendered: (\d+)", text)[-1:],
    }
    ts = rundir / "trace_summary.json"
    if ts.exists():
        try:
            s = json.load(open(ts))
            fa = s.get("frame_analysis") or {}
            row["app_owned_pixels"] = fa.get("app_owned_pixels")
            row["final_state"] = (s.get("lifecycle") or {}).get("final_state")
        except Exception:
            pass
    at = rundir / "api_trace.json"
    if at.exists():
        try:
            row["api_calls"] = json.load(open(at)).get("total_calls")
        except Exception:
            pass
    return row


def anchor_pair(name, max_seconds=75):
    apk, pkg = APKS[name]
    store = OUT / f"store_{name}"
    pair = {}
    for tag, b in ((f"{name}_ref", REF), (f"{name}_new", NEW)):
        pair[tag] = app_run(b, tag, apk, store, pkg,
                            max_seconds=max_seconds)
        print(f"[{tag}] face={pair[tag]['screenshot_face']} "
              f"wall={pair[tag]['wall_s']}s uncaught={pair[tag]['uncaught']}",
              flush=True)
    pair["delta_inert"] = (
        pair[f"{name}_ref"]["screenshot_face"] is not None and
        pair[f"{name}_ref"]["screenshot_face"] ==
        pair[f"{name}_new"]["screenshot_face"])
    if name in PINS:
        pair["pin_match"] = bool(
            pair[f"{name}_new"]["screenshot_face"] and
            pair[f"{name}_new"]["screenshot_face"].startswith(PINS[name]))
    return pair


def tb_pair():
    apk, pkg = APKS["tb"]
    store = OUT / "store_tb"
    pair = {}
    for tag, b in (("tb_ref", REF), ("tb_new", NEW)):
        pair[tag] = app_run(b, tag, apk, store, pkg, max_seconds=100,
                            frames=8)
        print(f"[{tag}] face={pair[tag]['screenshot_face']} "
              f"wall={pair[tag]['wall_s']}s uncaught={pair[tag]['uncaught']} "
              f"ndfe={pair[tag]['ndfe']} pixels="
              f"{pair[tag].get('app_owned_pixels')}", flush=True)
    return pair


SEED_SKIP = {"MINIANDROID_APP_DATA_SEED": "1",
             "MINIANDROID_PROVIDER_SKIP":
                 "FirebaseInitProvider,MlKitInitProvider"}


def tb_pair_env():
    """TB A/B under the TG-style fair baseline envs (seed+skip)."""
    apk, pkg = APKS["tb"]
    store = OUT / "store_tb"
    pair = {}
    for tag, b in (("tbseed_ref", REF), ("tbseed_new", NEW)):
        for k in CLEAN_ENVS:
            os.environ.pop(k, None)
        os.environ.update(SEED_SKIP)
        pair[tag] = app_run(b, tag, apk, store, pkg, max_seconds=100,
                            frames=8)
        print(f"[{tag}] face={pair[tag]['screenshot_face']} "
              f"wall={pair[tag]['wall_s']}s uncaught={pair[tag]['uncaught']} "
              f"ndfe={pair[tag]['ndfe']} "
              f"pixels={pair[tag].get('app_owned_pixels')}", flush=True)
    for k in SEED_SKIP:
        os.environ.pop(k, None)
    return pair


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "tbseed":
        pair = tb_pair_env()
        save("S167_W6_TB_SEED.json", pair)
    if phase == "anchors_mg":
        rows = {"microtimer": anchor_pair("microtimer"),
                "g2048": anchor_pair("g2048")}
        save("S167_W6_GATES.json", {"anchors": rows})
    elif phase == "anchors_oc":
        rows = {"opencalc": anchor_pair("opencalc")}
        save("S167_W6_GATES.json", {"anchors": rows})
    elif phase == "dooz_pair":
        ctl = s166.dooz_run("w6_dz_ctl", REF, store_root=OUT)
        print(json.dumps(ctl))
        save("S167_W6_TRAINS.json", {"w6_dz_ctl": ctl})
        fix = s166.dooz_run("w6_dz_fix", NEW, store_root=OUT)
        print(json.dumps(fix))
        save("S167_W6_TRAINS.json",
             {"w6_dz_fix": fix, "w6_dz_summary": s166.pair_summary(ctl, fix)})
    elif phase == "tg_pair":
        ctl = s166.tg_run("w6_tg_ctl", REF, store_name="s167_tg")
        print(json.dumps(ctl))
        save("S167_W6_TRAINS.json", {"w6_tg_ctl": ctl})
        fix = s166.tg_run("w6_tg_fix", NEW, store_name="s167_tg")
        print(json.dumps(fix))
        save("S167_W6_TRAINS.json",
             {"w6_tg_fix": fix, "w6_tg_summary": s166.pair_summary(ctl, fix)})
    elif phase == "tb_pair":
        pair = tb_pair()
        save("S167_W6_TB.json", pair)
    elif phase == "verdict":
        rows = json.load(open(EVID / "S167_W6_GATES.json"))
        anchors = rows["anchors"]
        all_inert = all(v.get("delta_inert") for v in anchors.values())
        pin_ok = all(v.get("pin_match") for v in anchors.values()
                     if "pin_match" in v)
        tr = json.load(open(EVID / "S167_W6_TRAINS.json"))
        tb = json.load(open(EVID / "S167_W6_TB.json"))
        dz = tr.get("w6_dz_summary", {})
        tg = tr.get("w6_tg_summary", {})
        verdict = {
            "ref_bin": t.sha16(REF), "new_bin": t.sha16(NEW),
            "stack_patch_sha16": "53d234e1db504568 (repaired)",
            "laws_patch_sha16": "65699ca9a235e915",
            "anchors_all_inert": all_inert, "microtimer_pin": pin_ok,
            "dooz": dz, "tg": tg,
            "tb_ref": {k: tb["tb_ref"].get(k) for k in
                       ("wall_s", "uncaught", "ndfe", "app_owned_pixels",
                        "final_state", "frames")},
            "tb_new": {k: tb["tb_new"].get(k) for k in
                       ("wall_s", "uncaught", "ndfe", "app_owned_pixels",
                        "final_state", "frames")},
        }
        save("S167_W6_VERDICT.json", verdict)
        print(json.dumps(verdict, indent=1, default=str)[:1200])
