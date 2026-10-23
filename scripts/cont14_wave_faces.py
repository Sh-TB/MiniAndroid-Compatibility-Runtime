#!/usr/bin/env python3
"""CONT-14 wave — batch-4 of the 20-by-20 directive (user: "ادامه", GitHub check+push).

Wave target: the two recurring census faces named by the CONT-13 ledger:
  - ColorStateList.getDefaultColor NPE (fossify_notes + batterymonitor, ×2)
Runs the face apps at the CURRENT binary, captures the full evidence chain
(log signature, draw ops, screenshot metrics) into evidence/cont14/.
"""
import hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = "/home/z/my-project"
ENG = f"{ROOT}/miniandroid/build/miniandroid"
OUT = Path(f"{ROOT}/run/cont14_waves")
OUT.mkdir(parents=True, exist_ok=True)
EV = Path(f"{ROOT}/evidence/cont14")
EV.mkdir(parents=True, exist_ok=True)

APPS = [
    ("fossify_notes", "upload/fdroid_batch/org.fossify.notes_13.apk"),
    ("batterymonitor", "upload/fdroid_batch/codes.swistak.batterymonitor_1007003.apk"),
]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def rec_pkg(apk):
    r = subprocess.run([f"{ROOT}/tools/aapt2/aapt2", "dump", "badging", str(apk)],
                       capture_output=True, text=True, timeout=60)
    m = re.search(r"^package: name='([^']+)'", r.stdout, re.M)
    return m.group(1) if m else None


def png_metrics(p):
    from PIL import Image
    try:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        px = list(im.resize((min(w, 270), min(h, 480))).getdata())
        colors = {}
        for q in px:
            colors[q] = colors.get(q, 0) + 1
        bg = max(colors.values()) if colors else len(px)
        return {"w": w, "h": h, "distinct_colors": len(colors),
                "content_px": len(px) - bg}
    except Exception as e:
        return {"error": str(e)}


def run_one(label, rel, budget=90):
    apk = Path(ROOT) / rel
    store = OUT / f"store_{label}"
    run = OUT / f"r_{label}"
    for d in (store, run):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    rec = {"label": label, "apk": os.path.basename(rel), "apk_sha16": sha16(apk),
           "binary": sha16(ENG)}
    ip = subprocess.run([ENG, "install", str(apk), "--data-root", str(store)],
                        capture_output=True, text=True, timeout=300)
    if ip.returncode != 0:
        rec["install"] = "FAIL"
        rec["sig"] = (ip.stderr or ip.stdout or "")[-300:]
        return rec
    rec["install"] = "OK"
    cmd = [ENG, "run", "--package", rec_pkg(apk), "--data-root", str(store),
           "--dump-view-tree", "--max-seconds", str(budget), "--frames", "6",
           "-o", str(run)]
    t0 = time.time()
    with open(run / "run.log", "w") as lf:
        try:
            rc = subprocess.call(cmd, stdout=lf, stderr=subprocess.STDOUT,
                                 timeout=budget + 240)
        except subprocess.TimeoutExpired:
            rc = -99
            lf.write("\nTIMEOUT\n")
    rec["run_rc"] = rc
    rec["wall_s"] = round(time.time() - t0, 1)
    log_path = run / "run.log"
    log = open(log_path, errors="replace").read() if log_path.exists() else ""
    # uncaught signature (last 2)
    rec["synth_exc"] = [s[:300] for s in
                        re.findall(r"\[SYNTH-EXC\][^\n]*", log)[-2:]]
    rec["uncaught"] = [s[:300] for s in
                       re.findall(r"\[EXC-PROPAGATE\][^\n]*uncaught[^\n]*", log)[-2:]]
    m = re.search(r"app_draw_ops[=:]?\s*(\d+)", log)
    rec["app_draw_ops"] = int(m.group(1)) if m else None
    fbn = re.search(r"\[EXP092-COPY\] fb has (\d+) non-white pixels", log)
    rec["fb_nonwhite"] = int(fbn.group(1)) if fbn else None
    ss = run / "screenshot.png"
    if ss.exists():
        rec["screenshot_sha16"] = sha16(ss)
        rec["png"] = png_metrics(ss)
    rec["loading_screen"] = bool(
        (rec.get("app_draw_ops") or 0) > 0 or (rec.get("fb_nonwhite") or 0) > 2000
        or (rec.get("png", {}).get("content_px") or 0) > 2000)
    rec["verdict"] = (re.findall(r"verdict=(\w+), first_missing_stage=(\w+)", log)
                      or [None])[-1]
    return rec


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "prefix"
    sel = sys.argv[2:] if len(sys.argv) > 2 else None
    results = []
    for label, rel in APPS:
        if sel and label not in sel:
            continue
        print(f"=== {tag}: {label} ===", flush=True)
        r = run_one(label, rel)
        print(json.dumps(r, indent=1)[:1200], flush=True)
        results.append(r)
    outp = EV / f"wave_faces_{tag}.json"
    json.dump(results, open(outp, "w"), indent=1)
    print("wrote", outp)
