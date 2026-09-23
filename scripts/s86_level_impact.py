#!/usr/bin/env python3
"""s86_level_impact.py — stratified re-execution campaign (user directive:
"From each, level 0 to the latest level, pick up to 5 and show how much impact the progress has had").

Deterministic sample: up to 5 titles per registered level (L0..L10),
sorted by package. Every sampled title re-executes at the current HEAD
(obs pass + click pass, same evidence protocol as S84/S85), the final
frame re-audits through the S85-hardened visual gate, and the result is
compared against the registered level: rc, exceptions, unique colors,
level delta. Progress proof = titles advancing or holding under the
HARSHER gate; regressions recorded honestly.
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "/home/z/my-project/scripts")
from s81_visual_audit import audit_frame, level_of

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s86/impact"
REG = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))
S82 = json.load(open(f"{ROOT}/docs/corpus/s82/title_registry.json"))

VC_MAP = {}
for t in S82.get("TITLES", []):
    VC_MAP[t.get("PACKAGE", "")] = (t.get("VERSION_CODE", ""),
                                    t.get("APK_SHA256", ""))
# older corpus registries (S80/S81 waves) also pinned version codes
for extra in ["docs/corpus/s81/corpus_index.json"]:
    try:
        d = json.load(open(f"{ROOT}/{extra}"))
        for t in d.get("items", d.get("titles", [])):
            p = t.get("package", "")
            if p and p not in VC_MAP:
                VC_MAP[p] = (str(t.get("versionCode", "")),
                             t.get("sha256", ""))
    except Exception:
        pass


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch(url, dst, timeout=180):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dst)
        return True
    except Exception:
        return False


def resolve_apk(t):
    """Return local APK path (downloading when needed) + provenance note."""
    pkg = t["package"]
    local = f"{OUT}/apks/{pkg}.apk"
    if os.path.exists(local):
        return local, "cached"
    # 1) evidence-pinned canonical cache (exact versions the canonical
    #    JPGs/GIFs were captured from — the honest comparison baseline)
    canon = {
        "com.miniandroid.snakedeluxe": "upload/s80_games/build_sd/snake_deluxe_v1.0_vc1.apk",
        "com.miniandroid.g2048": "upload/s80_games/build_2048/g2048_v1.0_vc1.apk",
        "com.miniandroid.tetris": "upload/s80_games/build_tetris/tetris_v1.0_vc1.apk",
        "com.miniandroid.minicraft": "upload/s86_games/build_minicraft/minicraft_v1.0_vc1.apk",
        "com.miniandroid.tictactoedeluxe": "upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
        "eu.veldsoft.fish.rings": "upload/canonical_apks/fishrings_v1.23_vc6.apk",
        "eu.veldsoft.tri.peaks": "upload/canonical_apks/tripeaks_v1.2.1_vc4.apk",
        "org.miniandroid.helloworld": None,  # fixture — rebuilt on demand
    }
    if pkg in canon:
        if canon[pkg] and os.path.exists(f"{ROOT}/{canon[pkg]}"):
            return f"{ROOT}/{canon[pkg]}", "evidence-pinned in-house/canonical"
        return None, "in-house build missing"
    if pkg == "org.miniandroid.helloworld":
        return None, "fixture (ladder covers it)"
    # canonical-cache fuzzy match (e.g. klondike/opmt/anuto when present)
    for p in glob.glob(f"{ROOT}/upload/canonical_apks/*.apk"):
        base = os.path.basename(p)
        if pkg.split(".")[-1] in base:
            return p, f"evidence-pinned cache ({base})"
    # 2) F-Droid: try the pinned versionCode first, then suggested
    vc_pin, sha_pin = VC_MAP.get(pkg, ("", ""))
    api = f"https://f-droid.org/api/v1/packages/{pkg}"
    cands = []
    try:
        d = json.load(urllib.request.urlopen(api, timeout=30))
        cands = [p["versionCode"] for p in d.get("packages", [])[::-1]]
    except Exception:
        pass
    if vc_pin:
        cands = [int(vc_pin)] + [c for c in cands if str(c) != str(vc_pin)]
    elif cands:
        cands = cands[:3]
    for vc in cands:
        for base in ("https://f-droid.org/repo/", "https://f-droid.org/archive/"):
            url = f"{base}{pkg}_{vc}.apk"
            if fetch(url, local):
                got = sha256(local)
                if sha_pin and got == sha_pin:
                    return local, f"pinned vc{vc} SHA-match"
                if not sha_pin:
                    return local, f"f-droid vc{vc} (re-pinned)"
                os.remove(local)  # hash mismatch → try next candidate
    return None, "download failed"


def engine_run(apk, out_dir, click=False, timeout=240):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "6", "--frame-delay", "300", "--max-seconds", "180",
           "-o", out_dir, apk]
    if click:
        cmd.append("--click-test")
    log = out_dir + ("_click.log" if click else "_obs.log")
    with open(log, "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=lf, timeout=timeout)
        except subprocess.TimeoutExpired:
            rc = -1
    errors = "?"
    for line in open(log, encoding="utf-8", errors="replace"):
        if line.startswith("Errors:"):
            errors = line.split(":", 1)[1].strip()
    frames = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    return {"rc": rc, "errors": errors, "frames": frames}


def uniq_colors(png):
    try:
        from PIL import Image
        im = Image.open(png).convert("RGB")
        return len(im.getcolors(200000))
    except Exception:
        return 0


def run_title(t):
    pkg = t["package"]
    apk, note = resolve_apk(t)
    rec = {"package": pkg, "title": t["title"], "old_level": t.get("level"),
           "old_status": t.get("status"), "apk_note": note}
    if not apk:
        rec.update({"status": "APK-UNAVAILABLE", "rc": -2})
        return rec
    rec["apk_sha256"] = sha256(apk)
    obs = engine_run(apk, f"{OUT}/{pkg}/obs")
    rec["rc_obs"] = obs["rc"]
    rec["errors_obs"] = obs["errors"]
    if obs["frames"]:
        fin = obs["frames"][-1]
        rec["uniq_obs"] = uniq_colors(fin)
        try:
            rec["audit_obs"] = audit_frame(fin)
            rec["level_obs"] = level_of(rec["audit_obs"])
        except Exception as e:
            rec["level_obs"] = f"audit-error: {e}"
    clk = engine_run(apk, f"{OUT}/{pkg}/click", click=True)
    rec["rc_click"] = clk["rc"]
    if clk["frames"]:
        rec["uniq_click"] = uniq_colors(clk["frames"][-1])
        try:
            a = audit_frame(clk["frames"][-1])
            rec["level_click"] = level_of(a)
            rec["state_changed"] = (
                rec.get("uniq_obs") != rec.get("uniq_click"))
        except Exception as e:
            rec["level_click"] = f"audit-error: {e}"
    return rec


def main():
    from collections import defaultdict
    by = defaultdict(list)
    for t in REG["titles"]:
        by[t.get("level", -1)].append(t)
    sample = []
    for lvl in sorted(by):
        ts = sorted(by[lvl], key=lambda t: t["package"])
        sample.extend(ts[:5])
    print(f"sampled {len(sample)} titles across levels "
          f"{sorted(by)}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    report_path = f"{OUT}/report.json"
    done = []
    if os.path.exists(report_path):
        done = json.load(open(report_path))
    seen = {r["package"] for r in done}
    todo = [t for t in sample if t["package"] not in seen]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for rec in ex.map(run_title, todo):
            done.append(rec)
            json.dump(done, open(report_path, "w"), indent=1)
            lv = rec.get("level_obs", rec.get("level_click", "?"))
            print(f"  {rec['package'][:40]:40} L{rec['old_level']}→{lv} "
                  f"rc={rec.get('rc_obs')} uniq={rec.get('uniq_obs')}",
                  flush=True)
    print("DONE", len(done))


if __name__ == "__main__":
    main()
