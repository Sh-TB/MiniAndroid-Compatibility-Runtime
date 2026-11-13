#!/usr/bin/env python3
"""S212/WP10 §6 — W18 Halma 11-run batch analysis for #587.

1. Pixel/dimension/mode compare of the 11 screenshots + SHA + why they differ.
2. Trace/metric compare to detect any distinct divergence.
3. Keep ONE representative full PNG + compact 11-run JSON summary.
4. Delete the 10 non-representative PNGs with SHA+mapping (if only
   nondeterministic noise differences).
5. Emit corrected batch report facts (fix the known report defects).
"""
import json
import hashlib
import re
import subprocess
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image

BASE = Path("/home/z/my-project")
W = BASE / "evidence/s188_w18/runs"
OUT = BASE / "evidence/s188_w18"
runs = [f"halma_w18_r{i}" for i in range(1, 12)]

recs = []
imgs = {}
for r in runs:
    d = W / r
    shot = d / "screenshot.png"
    img = Image.open(shot)
    arr = np.asarray(img.convert("RGB"), dtype=np.int16)
    imgs[r] = (img, arr)
    ts = json.loads((d / "trace_summary.json").read_text())
    trace = (d / "trace.jsonl").read_text(errors="ignore")
    report = (d / "report.md").read_text(errors="ignore")
    recs.append({
        "run": r,
        "png_bytes": shot.stat().st_size,
        "sha256": hashlib.sha256(shot.read_bytes()).hexdigest(),
        "dims": list(img.size),
        "mode": img.mode,
        "app_draw_ops": ts.get("app_draw_ops"),
        "nodes_visited": ts.get("nodes_visited"),
        "verdict": (ts.get("frame_analysis") or {}).get("verdict"),
        "app_owned_px": ts.get("app_owned_pixels") or ts.get("app_owned_px"),
        "trace_events": trace.count("\n"),
        "render_ok": "RENDER_OK" in trace,
        "no_app_ops": "NO_APP_OPS" in trace,
        "uncaught": trace.count("uncaught"),
        "stubbed_calls": len(re.findall(r"STUBBED", trace)) if False else None,
    })

# stub census from trace
for rec in recs:
    trace = (W / rec["run"] / "trace.jsonl").read_text(errors="ignore")
    m_imp = sum(1 for line in trace.splitlines() if "IMPLEMENTED" in line)
    m_stub = sum(1 for line in trace.splitlines() if "STUBBED" in line)
    rec["census_implemented"] = m_imp
    rec["census_stubbed"] = m_stub

# pairwise pixel diffs vs r1
base_run = "halma_w18_r1"
_, base_arr = imgs[base_run]
for r in runs:
    _, arr = imgs[r]
    if arr.shape == base_arr.shape:
        dm = (arr != base_arr).any(axis=2)
        n = int(dm.sum())
        # characterise the differing colors
        pairs = Counter()
        if n:
            oc = base_arr[dm]
            nc = arr[dm]
            for a, b in list(zip(oc, nc))[:200000]:
                pairs[(int(a[0]), int(a[1]), int(a[2]), int(b[0]), int(b[1]), int(b[2]))] += 1
        rec = next(x for x in recs if x["run"] == r)
        rec["px_diff_vs_r1"] = n
        rec["px_diff_pct"] = round(100 * n / (arr.shape[0] * arr.shape[1]), 4)
        rec["top_color_pairs"] = [{"from": list(k[:3]), "to": list(k[3:]), "n": v}
                                  for k, v in pairs.most_common(6)]
    else:
        rec = next(x for x in recs if x["run"] == r)
        rec["px_diff_vs_r1"] = "dims differ"

summary = {
    "batch": "evidence/s188_w18/runs/halma_w18_r1..r11",
    "analysis": "S212/WP10§6 for #587",
    "runs": recs,
}
(OUT / "halma_w18_batch_summary.json").write_text(json.dumps(summary, indent=1))
for rec in recs:
    print(rec["run"], "sha", rec["sha256"][:12], "diff_vs_r1", rec.get("px_diff_vs_r1"),
          rec.get("px_diff_pct"), "verdict", rec.get("verdict"), "draw_ops", rec.get("app_draw_ops"),
          "uncaught", rec.get("uncaught"))
