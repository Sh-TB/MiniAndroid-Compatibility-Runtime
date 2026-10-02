#!/usr/bin/env python3
"""SECONDARY CAMPAIGN PHASE V10 — FIVE-APP VISUAL GATE.

Corpus (user-mandated):
  1. Forkgram Classic (Telegram fork)   upload/forkgram_709208.apk
  2. 2048                               org.andstatus.game2048_47.apk
  3. Dame (blidraughts — draughts)      com.vovagorodok.blidraughts_3.apk
  4. Droidify                           corpus/droidify.apk
  5. OpenCalculator                     upload/opencalculator_53.apk

Per app: 3 deterministic runs. Record (per user directive):
  BOOT / ACTIVITY / CONTENT_ROOT / ATTACH / MEASURE / LAYOUT / DRAW /
  IMAGE-TEXT PROVENANCE / CAPTURE  — from --trace trace.jsonl, plus
  screenshot SHA256, nonwhite/content metrics (region-classified by the
  V1/V7 census), ViewTree metrics, first divergence, provenance chain.

Classification vocabulary: IMPLEMENTED / TESTED / OBSERVED / PARTIAL /
BLOCKED / PENDING / SUPERSEDED.
A white/black frame stays OPEN unless real app-content evidence exists.
"""
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ENG = "/home/z/my-project/miniandroid/build/miniandroid"
R = "/home/z/my-project"
OUT = Path("/tmp/v10")
OUT.mkdir(parents=True, exist_ok=True)

CORPUS = [
    ("forkgram",  f"{R}/upload/forkgram_709208.apk"),
    ("game2048",  "/tmp/my-project/apk_cache/s37new/org.andstatus.game2048_47.apk"),
    ("dame",      "/tmp/my-project/apk_cache/s82/com.vovagorodok.blidraughts_3.apk"),
    ("droidify",  "/tmp/my-project/apk_cache/corpus/droidify.apk"),
    ("opencalc",  f"{R}/upload/opencalculator_53.apk"),
]

STAGES = ["BOOT", "ACTIVITY", "CONTENT_ROOT", "ATTACH", "MEASURE",
          "LAYOUT", "DRAW", "CAPTURE"]


def sha256f(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def classify(rc, verdicts, shots, census_last):
    v = verdicts[-1] if verdicts else None
    if rc == -99:
        return "BLOCKED"          # budget timeout — never fake success
    if v == "REAL_APP_CONTENT":
        return "OBSERVED" if len(set(shots)) == 1 else "PARTIAL"
    if v in ("RESOURCE_INFLATION_FAILED", "RENDER_EXCEPTION",
             "NO_ROOT", "SYSTEM_CHROME_ONLY", "VIEWTREE_NO_APP_PIXELS",
             "DEFAULT_BACKGROUND_ONLY", "PARTIAL_RENDER_BUDGET"):
        return "PARTIAL" if v == "PARTIAL_RENDER_BUDGET" else "BLOCKED"
    return "PENDING"


report = {}
ONLY = sys.argv[1:] if len(sys.argv) > 1 else None
for tag, apk in CORPUS:
    if ONLY and tag not in ONLY:
        continue
    app = {"apk": apk, "apk_sha256": sha256f(apk), "runs": []}
    shas = []
    for i in (1, 2, 3):
        d = OUT / f"{tag}_run{i}"
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        cmd = [ENG, "run", "--execution-mode", "real-dalvik", "--frames", "2",
               "--frame-delay", "200", "--trace", "--data-root",
               str(d / "data"), "-o", str(d), apk]
        try:
            rc = subprocess.call(cmd, stdout=open(d / "run.log", "w"),
                                 stderr=subprocess.STDOUT, timeout=540)
        except subprocess.TimeoutExpired:
            rc = -99
        shot = d / "screenshot.png"
        rec = {"run": i, "rc": rc,
               "sha16": sha256f(shot)[:16] if shot.exists() else None}
        tj = d / "trace.jsonl"
        if tj.exists():
            lines = tj.read_text(errors="ignore").splitlines()
            evs = []
            for ln in lines:
                try:
                    evs.append(json.loads(ln))
                except Exception:
                    pass
            # stage presence map (user-mandated record set)
            stage_hits = {}
            for e in evs:
                et = str(e.get("event", "")).upper()
                st = str(e.get("stage", "")).upper()
                for s in STAGES:
                    if s in et or s == st or (s == "BOOT" and "boot" in et):
                        stage_hits.setdefault(s, 0)
                        stage_hits[s] += 1
            rec["stage_hits"] = stage_hits
            # census / verdict extraction
            cens = [e for e in evs if "frame_census" in json.dumps(e)[:80]
                    or e.get("event") == "FRAME_CENSUS"]
            rec["census_events"] = len(cens)
            if cens:
                rec["census_last"] = cens[-1]
            # first divergence
            div = [e for e in evs if "divergence" in json.dumps(e).lower()]
            rec["first_divergence"] = div[0] if div else None
            # provenance chain (gfx provenance json if produced)
        # run.log verdict + census mining (authoritative source)
        txt = (d / "run.log").read_text(errors="ignore") if (d / "run.log").exists() else ""
        rec["verdicts"] = re.findall(r"capture_verdict=([A-Z_]+)", txt) or \
            re.findall(r'"verdict"\s*:\s*"([A-Z_]+)"', txt)
        # trace_summary.frame_analysis carries the authoritative verdicts
        tsj = d / "trace_summary.json"
        if tsj.exists() and not rec["verdicts"]:
            try:
                summary = json.loads(tsj.read_text())
                fa = summary.get("frame_analysis") or []
                if isinstance(fa, dict) and fa.get("verdict"):
                    rec["verdicts"] = [fa.get("verdict")]
                    rec["census"] = fa
                elif isinstance(fa, list):
                    rec["verdicts"] = [f.get("verdict") for f in fa
                                       if isinstance(f, dict) and f.get("verdict")]
            except Exception as e:
                rec["ts_err"] = str(e)
        m = re.search(r"\[V1-CONTENT-BOUNDS\] root=(\d+) rect=\(([^)]*)\)", txt)
        if m:
            rec["content_bounds"] = m.group(2)
        rec["inflate_failed"] = "[V2-INFLATE-FAILED]" in txt
        rec["v4_tags"] = len(re.findall(r"\[V4-TAG\]", txt))
        rec["v6_fallbacks"] = len(re.findall(r"\[V6-CTX-FALLBACK\]", txt))
        # viewtree metrics from census json (trace_summary)
        ts = d / "trace_summary.json"
        if ts.exists():
            try:
                summary = json.loads(ts.read_text())
                fa = summary.get("frame_analysis") or summary.get("frames") or []
                if isinstance(fa, dict):
                    fa = fa.get("frames", [])
                rec["frame_analysis"] = fa[-3:] if isinstance(fa, list) else fa
            except Exception as e:
                rec["frame_analysis_err"] = str(e)
        # screenshot metrics (nonwhite/content, region-classified via census)
        if shot.exists():
            try:
                from PIL import Image
                im = Image.open(shot).convert("RGB")
                px = list(im.getdata())
                from collections import Counter
                c = Counter(px)
                dom, dn = c.most_common(1)[0]
                rec["px_total"] = len(px)
                rec["px_dominant"] = dom
                rec["px_dominant_pct"] = round(100.0 * dn / len(px), 2)
                rec["px_nonwhite"] = sum(n for col, n in c.items() if col != (255, 255, 255))
                rec["unique_colors"] = len(c)
            except Exception as e:
                rec["metrics_err"] = str(e)
        shas.append(rec["sha16"])
        app["runs"].append(rec)
        print(f"[V10] {tag} run{i}: rc={rc} sha={rec['sha16']} "
              f"verdict={rec['verdicts'][-1] if rec['verdicts'] else None}")
    app["deterministic"] = len(set(s for s in shas if s)) == 1 and shas[0] is not None
    verdicts = [r["verdicts"][-1] for r in app["runs"] if r["verdicts"]]
    app["verdicts"] = verdicts
    app["classification"] = classify(
        app["runs"][-1]["rc"], verdicts, shas,
        app["runs"][-1].get("census_last"))
    report[tag] = app
    print(f"[V10] == {tag}: classification={app['classification']} "
          f"deterministic={app['deterministic']}")

(OUT / "v10_results.json").write_text(json.dumps(report, indent=2, default=str))
print("V10 complete:", {k: v["classification"] for k, v in report.items()})
