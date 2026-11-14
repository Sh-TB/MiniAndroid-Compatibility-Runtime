#!/usr/bin/env python3
"""S236 audit deep verification (#595 follow-up).

Raw-log-first: every run's FULL console lands in evidence/s236/deep/ so the
markers are read from the REAL formats, not guessed strings.

1. chess_fresh      — clean root, 60 frames, no tap: the 2380-row frontier
                      (the onDraw-storm interrupt) + the RAW storm evidence.
2. chess_fresh_probe— SAME but MINIANDROID_S236_PROBE_DEFER_DRAW=1: the
                      custom-view onDraw storm is skipped -> the causality
                      measurement (insert count with vs without the storm).
3. chess_seeded     — the seeded root + tap 540,110@8: Practice list ->
                      rawQuery rows / adapter bind / FEN-into-model trace
                      (the REAL-app reachability for 655/657/658b/659/660).
4. sudoku_deep      — 40 frames + the folder tap: cursor -> adapter -> rows
                      bound AND rendered.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

BIN = Path("/tmp/s236_audit/miniandroid/build/miniandroid")
UPLOAD = Path("/home/z/my-project/upload")
OUT = Path("/tmp/s236_audit/evidence/s236/deep")
OUT.mkdir(parents=True, exist_ok=True)
CH = UPLOAD / "chess_jwtc_298.apk"
SU = UPLOAD / "opensudoku_v4113.apk"
results = {}

def run(cmd, env=None, timeout=900):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run([str(c) for c in cmd], capture_output=True,
                          text=True, timeout=timeout, env=e)

def install(apk, store):
    run([BIN, "install", apk, "--data-root", store])
    apps = store / "data" / "app"
    ds = [d.name for d in sorted(apps.iterdir())
          if d.is_dir() and not d.name.startswith(".")
          and not d.name.endswith(".staging")
          and (d / "base.apk").exists()]
    return ds[0] if ds else None

def run_app(store, pkg, out, frames, taps=None, env=None, delay=250):
    cmd = [BIN, "run", "--execution-mode", "real-dalvik",
           "--data-root", store, "-o", out, "--package", pkg,
           "--frames", str(frames), "--frame-delay", str(delay)]
    for t in (taps or []):
        cmd += ["--tap", t]
    r = run(cmd, env=env)
    log = Path(out) / "console.log"
    txt = log.read_text(errors="replace") if log.exists() else ""
    if not txt:
        # the console may land beside the frame dir
        for cand in Path(out).rglob("console.log"):
            txt = cand.read_text(errors="replace")
            break
    return txt

def census(store):
    rows = []
    for db in list(store.rglob("*.db")) + list(store.rglob("*.sqlite3")):
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            for (t,) in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"):
                try:
                    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    if n:
                        rows.append({"db": db.name, "table": t, "rows": n})
                except sqlite3.Error:
                    pass
            con.close()
        except sqlite3.Error:
            pass
    return rows

def markers(txt):
    hits = {}
    for m in ("SQLITE-SHADOW] insert", "SQLITE-INSERT", "CV-PUT",
              "_fieldColor", "loadPGN", "rawQuery rows=", "[FEN",
              "[F-NEW-659]", "[F-NEW-655]", "[F-NEW-657]", "[F-NEW-658",
              "C013-ONDRAW", "S191", "C102-ADAPTER", "getView",
              "NotFoundException", "F-016", "practice"):
        hits[m] = txt.count(m)
    return hits

# ── 1+2: the causality pair (fresh roots, probe OFF then ON) ────────────────
for tag, env in (("chess_fresh", None),
                 ("chess_fresh_probe",
                  {"MINIANDROID_S236_PROBE_DEFER_DRAW": "1"})):
    store = Path(tempfile.mkdtemp(prefix=f"s236_{tag}_"))
    out = Path(tempfile.mkdtemp(prefix=f"s236_{tag}_out_"))
    pkg = install(CH, store)
    txt = run_app(store, pkg, out, 60, env=env)
    (OUT / f"{tag}.console.log").write_text(txt)
    results[tag] = {"pkg": pkg, "census": census(store), "markers": markers(txt)}

# ── 3: the seeded Practice chain (REAL-app reachability) ───────────────────
store = Path(tempfile.mkdtemp(prefix="s236_chess_seeded_"))
out = Path(tempfile.mkdtemp(prefix="s236_chess_seeded_out_"))
pkg = install(CH, store)
txt0 = run_app(store, pkg, out, 60)          # the seeding boot
seeded_census = census(store)
txt1 = run_app(store, pkg, out, 16, taps=["540,110@8"])   # Practice tap
(OUT / "chess_seeded.console.log").write_text(txt1)
results["chess_seeded"] = {"pkg": pkg, "census_after_seed": seeded_census,
                           "markers": markers(txt1),
                           "tap": "540,110@8", "frames": 16}

# ── 4: OpenSudoku deep ──────────────────────────────────────────────────────
su_store = Path(tempfile.mkdtemp(prefix="s236_sudoku_deep_"))
su_out = Path(tempfile.mkdtemp(prefix="s236_sudoku_deep_out_"))
spkg = install(SU, su_store)
sutxt = run_app(su_store, spkg, su_out, 40)
(OUT / "sudoku_boot.console.log").write_text(sutxt)
results["sudoku_boot"] = {"pkg": spkg, "markers": markers(sutxt),
                          "census": census(su_store)}
sutxt2 = run_app(su_store, spkg, su_out, 16, taps=["540,250@30"])
(OUT / "sudoku_tapped.console.log").write_text(sutxt2)
results["sudoku_tapped"] = {"markers": markers(sutxt2), "tap": "540,250@30"}

(OUT / "deep_results.json").write_text(json.dumps(results, indent=1) + "\n")
print(json.dumps(results, indent=1))
