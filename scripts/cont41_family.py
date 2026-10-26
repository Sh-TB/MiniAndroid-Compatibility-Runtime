#!/usr/bin/env python3
"""CONT-41 — targeted re-run of the 4 capacitor-family titles at the
post-R-NEW-550/551 binary, then any subset of the batch-50.
Usage: cont41_family.py <n> [label,label,...]"""
import json, sys, time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, "/home/z/my-project/scripts")
import importlib.util
spec = importlib.util.spec_from_file_location(
    "c40", "/home/z/my-project/scripts/cont40_batch50.py")
c40 = importlib.util.module_from_spec(spec)
spec.loader.exec_module.__self__ if False else None

# import without running main
import types
src = open("/home/z/my-project/scripts/cont40_batch50.py").read()
src = src.replace('if __name__ == "__main__":\n    main()', "")
c40 = types.ModuleType("c40")
exec(compile(src, "cont40_batch50.py", "exec"), c40.__dict__)

OUT = Path("/home/z/my-project/run/cont41_family")
EV = Path("/home/z/my-project/evidence/cont41")
OUT.mkdir(parents=True, exist_ok=True)
EV.mkdir(parents=True, exist_ok=True)


def run_one(job):
    label, rel = job
    t0 = time.time()
    apk = Path(c40.ROOT) / rel
    store = OUT / f"store_{label}"
    run = OUT / f"r_{label}"
    import shutil
    for d in (store, run):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    rec = {"label": label, "apk": apk.name, "apk_sha16": c40.sha16(apk)}
    ip = c40.subprocess.run(
        [c40.ENG, "install", str(apk), "--data-root", str(store)],
        capture_output=True, text=True, timeout=300)
    if ip.returncode != 0:
        rec["install"] = "FAIL"
        return rec
    rec["install"] = "OK"
    cmd = [c40.ENG, "run", "--package", c40.rec_pkg(apk), "--data-root", str(store),
           "--dump-view-tree", "--max-seconds", "90", "--frames", "6", "-o", str(run)]
    try:
        r = c40.subprocess.run(cmd, capture_output=True, text=True, timeout=420)
    except c40.subprocess.TimeoutExpired:
        rec["run_rc"] = "TIMEOUT"
        return rec
    rec["run_rc"] = r.returncode
    rec["wall_s"] = round(time.time() - t0, 1)
    sig, v, verdict, unc = c40.signature(str(run / "run.log"))
    rec["verdict_line"] = verdict
    shot = run / "screenshot.png"
    if shot.exists():
        rec["screenshot_sha16"] = c40.sha16(shot)
        rec["png"] = c40.png_metrics(str(shot))
    return rec


FAMILY = ["subster", "voyager", "how2vote", "leradar"]

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    jobs = [(lbl, rel) for lbl, rel in c40.BATCH
            if (only is None or lbl in only)][:limit]
    with Pool(2) as pool:
        for rec in pool.imap_unordered(run_one, jobs):
            png = rec.get("png") or {}
            print(f"{rec['label']:14s} rc={rec.get('run_rc')} "
                  f"px={png.get('content_px', '-'):>7} colors={png.get('distinct_colors', '-'):>5} "
                  f"wall={rec.get('wall_s', '-')}s", flush=True)
            json.dump(rec, open(EV / f"cont41_{rec['label']}.json", "w"), indent=1)
