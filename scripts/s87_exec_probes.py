#!/usr/bin/env python3
"""s87_exec_probes.py — PHASE 8: execute the S87 source-first probe corpus
at current HEAD (obs pass + click pass), audit final frames with the
S85-hardened visual gate, emit run/s87/probe/EXEC_RESULTS.json."""
import glob, hashlib, json, os, subprocess, sys

sys.path.insert(0, "/home/z/my-project/scripts")
from s81_visual_audit import audit_frame, level_of

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = f"{ROOT}/run/s87/probe"
MAN = json.load(open(f"{OUT}/manifest.json"))

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def engine_run(apk, out_dir, click=False, timeout=300):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [ENG, "run", "--execution-mode", "real-dalvik",
           "--frames", "8", "--frame-delay", "300", "--max-seconds", "240",
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
    api_calls = "?"
    for line in open(log, encoding="utf-8", errors="replace"):
        if line.startswith("Errors:"):
            errors = line.split(":", 1)[1].strip()
        if line.startswith("API Calls:"):
            api_calls = line.split(":", 1)[1].strip()
    frames = sorted(glob.glob(f"{out_dir}/frames/frame_*.png"))
    return {"rc": rc, "errors": errors, "api_calls": api_calls,
            "frames": frames, "log": log}

def uniq_colors(png):
    try:
        from PIL import Image
        im = Image.open(png).convert("RGB")
        return len(set(im.getdata()))
    except Exception:
        return -1

def main():
    results = {}
    for pkg, rec in MAN.items():
        apk = f"{OUT}/apks/{pkg}.apk"
        if not os.path.exists(apk):
            print(f"!! {pkg}: no apk"); continue
        print(f"== {pkg} (vc={rec.get('chosen_vc')})")
        r = {"apk_sha256": sha256(apk),
             "pin_match": rec.get("sha_matches_pin"),
             "vc": rec.get("chosen_vc")}
        obs = engine_run(apk, f"{OUT}/exec/{pkg}/obs")
        r["obs"] = {k: v for k, v in obs.items() if k != "frames"}
        r["obs"]["n_frames"] = len(obs["frames"])
        clk = engine_run(apk, f"{OUT}/exec/{pkg}/click", click=True)
        r["click"] = {k: v for k, v in clk.items() if k != "frames"}
        r["click"]["n_frames"] = len(clk["frames"])
        # visual audit of last obs + click frames
        for tag, fr in (("obs_final", obs["frames"][-1] if obs["frames"] else None),
                        ("click_final", clk["frames"][-1] if clk["frames"] else None)):
            if fr and os.path.exists(fr):
                a = audit_frame(fr)
                r[tag] = {"frame": fr, "uniq": uniq_colors(fr),
                          "level": level_of(a), "nonbg_ratio": a.get("nonbg_ratio")}
            else:
                r[tag] = {"frame": None, "uniq": 0, "level": "NO_FRAMES"}
        results[pkg] = r
        print(f"   obs rc={r['obs']['rc']} frames={r['obs']['n_frames']} "
              f"uniq={r['obs_final']['uniq']} level={r['obs_final']['level']} | "
              f"click rc={r['click']['rc']} frames={r['click']['n_frames']} "
              f"uniq={r['click_final']['uniq']}")
    json.dump(results, open(f"{OUT}/EXEC_RESULTS.json", "w"), indent=1)
    print("EXEC_RESULTS.json written")

if __name__ == "__main__":
    main()
