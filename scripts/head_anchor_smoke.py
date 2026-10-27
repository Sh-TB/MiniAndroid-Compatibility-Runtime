#!/usr/bin/env python3
"""HEAD anchor smoke — run the golden anchor APKs at the freshly-built HEAD
binary and compare screenshot sha16 against the CONT-42 wall pins.

Honest scope: this is the PLUGINS-era re-execution evidence train. Any pin
mismatch is reported as-is (no fudging) — it means a regression OR a real
frontier advance; both are banked.
"""
import hashlib, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

FRESH = "/home/z/fresh-repo"
ENG = f"{FRESH}/miniandroid/build/miniandroid"
APKDIR = Path("/home/z/my-project/upload/canonical_apks")
OUT = Path(f"{FRESH}/run/head_smoke"); OUT.mkdir(parents=True, exist_ok=True)

# CONT-42 wall pins (evidence/cont42 + worklog): screenshot sha16 expectations
PINS = {
    "io.github.yamin8000.dooz": "851cc176",
    "dubrowgn.microtimer": "bbd350b6",
    "app.varlorg.unote": "7481e9b4",
    "stack.tower3d": "11a38a5a",
}

def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:16]

def png_metrics(p):
    try:
        from PIL import Image
        im = Image.open(p).convert("RGB")
        colors = im.getcolors(maxcolors=1 << 24)
        total = im.width * im.height
        # non-background pixels: treat the most common color as background
        content = sum(n for n, _ in colors) - max(n for n, _ in colors)
        return {"content_px": content, "distinct_colors": len(colors),
                "total_px": total}
    except Exception as e:
        return {"err": str(e)}

def rec_pkg(apk):
    r = subprocess.run([f"{FRESH}/tools/aapt2/aapt2", "dump", "badging", str(apk)],
                       capture_output=True, text=True)
    m = re.search(r"package: name='([^']+)'", r.stdout or "")
    return m.group(1) if m else None

def run_one(apk_path):
    label = apk_path.stem
    store = OUT / f"store_{label}"; run = OUT / f"r_{label}"
    for d in (store, run):
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True)
    rec = {"label": label, "apk": apk_path.name, "apk_sha16": sha16(apk_path)}
    t0 = time.time()
    try:
        ip = subprocess.run([ENG, "install", str(apk_path), "--data-root", str(store)],
                            capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        rec["install"] = "TIMEOUT"; return rec
    if ip.returncode != 0:
        rec["install"] = "FAIL"
        rec["sig"] = (ip.stderr or ip.stdout or "")[-220:]
        return rec
    rec["install"] = "OK"
    pkg = rec_pkg(apk_path)
    cmd = [ENG, "run", "--package", pkg, "--data-root", str(store),
           "--dump-view-tree", "--max-seconds", "90", "--frames", "6", "-o", str(run)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
    except subprocess.TimeoutExpired:
        rec["run_rc"] = "TIMEOUT"; rec["wall_s"] = round(time.time() - t0, 1); return rec
    rec["run_rc"] = r.returncode
    rec["wall_s"] = round(time.time() - t0, 1)
    logp = run / "run.log"
    if logp.exists():
        txt = open(logp, errors="replace").read()
        v = re.search(r"FINAL-STATUS: (\S+)", txt)
        rec["verdict"] = v.group(1) if v else None
        exc = re.findall(r"\[SYNTH-EXC\] (\S+) unwound", txt)
        rec["synth_exc_n"] = len(exc)
        rec["first_exc"] = exc[0] if exc else None
        rec["uncaught_n"] = txt.count("uncaught")
    shot = run / "screenshot.png"
    if shot.exists():
        rec["shot_sha16"] = sha16(shot)
        rec["png"] = png_metrics(str(shot))
    pin = next((v for k, v in PINS.items() if (pkg or "").startswith(k)), None)
    if pin:
        rec["pin"] = pin
        rec["pin_match"] = (rec.get("shot_sha16", "").startswith(pin))
    return rec

def main():
    apks = sorted(APKDIR.glob("*.apk"))
    want = sys.argv[1:] if len(sys.argv) > 1 else None
    if want:
        apks = [a for a in apks if any(w in a.name for w in want)]
    print("engine:", ENG, "exists:", os.path.exists(ENG), "| apks:", len(apks))
    results = []
    with ProcessPoolExecutor(max_workers=2) as ex:
        for rec in ex.map(run_one, apks):
            results.append(rec)
            px = rec.get("png", {}).get("content_px", "-")
            print(f"[{rec.get('wall_s','-'):>5}s] {rec['label'][:28]:28s} "
                  f"install={rec.get('install')} rc={rec.get('run_rc')} "
                  f"px={px} shot={rec.get('shot_sha16','-')} "
                  f"pin={rec.get('pin','-')} match={rec.get('pin_match','-')}")
            sys.stdout.flush()
    # merge with previous batches (script re-runs must not erase earlier rows)
    jp = OUT / "head_smoke.json"
    prev = {}
    if jp.exists():
        try:
            prev = {r["label"]: r for r in json.load(open(jp))}
        except Exception:
            prev = {}
    for r in results:
        prev[r["label"]] = r
    merged = [prev[k] for k in sorted(prev)]
    json.dump(merged, open(jp, "w"), indent=1)
    print("banked:", jp, "rows:", len(merged))

if __name__ == "__main__":
    main()
