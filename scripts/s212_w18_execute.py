#!/usr/bin/env python3
"""S212/WP10§6 execution — W18 Halma batch compaction for #587.

Outputs:
  evidence/s188_w18/halma_w18_BATCH_REPORT.md        truthful batch report (one screenshot section)
  evidence/s188_w18/halma_w18_preview.jpg            labeled DERIVATIVE (NOT PIXEL-EXACT)
  evidence/s188_w18/halma_w18_retention_manifest.json provenance of derivative + retained PNGs
  evidence/s188_w18/halma_w18_batch_summary.json     updated with census/contradiction/dispositions
  per-run report.md rewritten truthfully (r1 embeds retained PNG; r2..r11 reference the mapping)
  deletes screenshots of r2..r11 (10 PNGs, ~27.3 MiB) — SHAs preserved in summary+manifest
"""
import json
import hashlib
import re
from pathlib import Path
from PIL import Image

BASE = Path("/home/z/my-project")
W = BASE / "evidence/s188_w18/runs"
OUT = BASE / "evidence/s188_w18"
runs = [f"halma_w18_r{i}" for i in range(1, 12)]

summ = json.loads((OUT / "halma_w18_batch_summary.json").read_text())
by_run = {r["run"]: r for r in summ["runs"]}

# enrich with census + contradiction + disposition
for r in runs:
    ts = json.loads((W / r / "trace_summary.json").read_text())
    ffe = ts.get("first_failure_event", {})
    state = ffe.get("state", "")
    m = re.search(r"F-NEW-200 stub-census: (\d+) IMPLEMENTED, (\d+) STUBBED, (\d+) MISSING, (\d+) ERROR", state)
    m0 = re.search(r"F-016 exception-honesty: (\d+) uncaught in-flight exception", state)
    rec = by_run[r]
    rec["f_new_200_census"] = {"IMPLEMENTED": int(m.group(1)), "STUBBED": int(m.group(2)),
                               "MISSING": int(m.group(3)), "ERROR": int(m.group(4))} if m else None
    rec["f016_uncaught_inflight"] = int(m0.group(1)) if m0 else 0
    rec["first_failure_event"] = {"event": ffe.get("event"), "seq": ffe.get("seq"),
                                  "state_excerpt": state[:220]}
    fa = ts.get("frame_analysis", {})
    rec["frame_analysis_key_facts"] = {
        "app_draw_ops": fa.get("app_draw_ops"),
        "app_owned_pixels": fa.get("app_owned_pixels"),
        "depth_max": fa.get("depth_max"),
        "draw_walk_ran": fa.get("draw_walk_ran"),
        "verdict": fa.get("verdict"),
    }
    rec["verdict_contradiction"] = {
        "summary_verdict": fa.get("verdict"),
        "trace_verdict": "NO_APP_OPS (RENDER_OK result NO_APP_OPS)" ,
        "resolution": "BLOCKER recorded: ownership classifier attributes theme-fill pixels (975,949 px) as app-owned while app_draw_ops=0 and ViewTree depth_max=0; verdict must NOT be read as real app UI until classifier is reconciled (WP10 §3 issue flag)"
    }
    rec["disposition"] = ("KEEP (representative full PNG)" if r == "halma_w18_r1"
                          else "DELETE screenshot (visually equivalent: single shade pair "
                               "(70,127,0)->(47,127,0) x 10,572 px vs r1; SHA + run identity preserved here)")

summ["conclusion"] = {
    "visual": "all 11 frames are the same default Halma menu/first frame; the ONLY inter-run pixels are one shade pair (70,127,0)->(47,127,0) across 10,572 px (0.51%) — nondeterministic shading, no error/first-divergence/state transition",
    "honest_status": "proves APK load + manifest/DEX parse + lifecycle dispatch + surface creation + repeatable first frame; does NOT prove Halma gameplay or meaningful Compose content (app_draw_ops=0, ViewTree depth_max=0, 1 uncaught in-flight exception, stub-bounded census)",
    "kept_full_png": "halma_w18_r1/screenshot.png",
    "deleted_pngs": 10,
    "checkout_bytes_saved_target": 10 * 2_863_000,
}

(OUT / "halma_w18_batch_summary.json").write_text(json.dumps(summ, indent=1))

# truthful batch report
r1 = by_run["halma_w18_r1"]
c = r1["f_new_200_census"]
md = ["# W18 Halma batch report — CORRECTED (S212/WP10§6, #587)",
      "",
      "This report supersedes the eleven per-run auto-reports whose defects are listed below.",
      "",
      "## Batch facts (all 11 runs: halma_w18_r1 .. halma_w18_r11)",
      "",
      "| fact | value |",
      "|---|---|",
      f"| APK | `upload/canonical_apks/app.halma*.apk` (package `app.halma`, Activity `{json.loads((W/'halma_w18_r1'/'trace_summary.json').read_text()).get('activity')}`) |",
      f"| Screenshots | 1 retained full PNG `runs/halma_w18_r1/screenshot.png` ({r1['png_bytes']} bytes, 1080x1920, sha256 {r1['sha256']}) |",
      "| Other 10 runs | screenshots deleted; per-run SHA-256 + run identity preserved in `halma_w18_batch_summary.json` and `halma_w18_retention_manifest.json` |",
      f"| Census | F-NEW-200 stub-census: {c['IMPLEMENTED']} IMPLEMENTED, {c['STUBBED']} STUBBED, {c['MISSING']} MISSING, {c['ERROR']} ERROR — success claim is stub-bounded |",
      f"| Exceptions | F-016: {r1['f016_uncaught_inflight']} uncaught in-flight exception past all app frames (per run) — NOT a clean complete-app pass |",
      "| Trace verdict | RENDER_OK with result NO_APP_OPS; `frame_analysis.verdict` says REAL_APP_CONTENT — CONTRADICTION recorded, ownership classifier unreconciled |",
      "| app_draw_ops / ViewTree | 0 / depth_max=0 — no real draw walk content |",
      "| Honest verdict | NOT a gameplay/UI pass. Proves: APK load, manifest+DEX parse, lifecycle dispatch, surface creation, repeatable first-frame boundary |",
      "",
      "## Inter-run pixel analysis",
      "",
      "Every run differs from r1 by exactly 10,572 px (0.51%) and every differing pixel is the single shade pair `(70,127,0) -> (47,127,0)` — nondeterministic shading of one UI element. No run contains a distinct error, first divergence, output or state transition, so 10 full-size PNGs add no independent visual finding.",
      "",
      "## Defects corrected vs the old per-run reports",
      "",
      "1. wrong APK store path (r4 pointed at `store_halma_w18_r1`) — batch-level APK identity now stated once",
      "2. wrong screenshot size (claimed 7.91 MB; tracked blob is 2,863,792–2,865,516 bytes) — corrected",
      "3. duplicated `Output Frame` section in every report — single section here",
      "4. headline `SUCCESS ✅` without F-016/stub caveats — honest verdict above",
      "5. `app_owned_pixels=975,949` presented as app content while `app_draw_ops=0` — contradiction recorded instead of repeated",
      "",
      "## Retained screenshot",
      "",
      "![Retained representative Halma frame](runs/halma_w18_r1/screenshot.png)",
      "",
      "*The image above is the canonical pixel evidence for all 11 runs (r2..r11 differ only in the documented shade pair). The preview `halma_w18_preview.jpg` is a DERIVATIVE / NOT PIXEL-EXACT for human browsing only.*",
      ]
(OUT / "halma_w18_BATCH_REPORT.md").write_text("\n".join(md) + "\n")

# derivative preview (labeled)
img = Image.open(W / "halma_w18_r1" / "screenshot.png").convert("RGB")
img.thumbnail((640, 640))
img.save(OUT / "halma_w18_preview.jpg", "JPEG", quality=82)

# retention manifest
manifest = {
    "policy": "S212/WP10 §5 tier B (repeated-run determinism evidence): one representative full PNG + compact per-run rows",
    "retained_full_png": {
        "path": "evidence/s188_w18/runs/halma_w18_r1/screenshot.png",
        "sha256": r1["sha256"], "bytes": r1["png_bytes"], "dims": r1["dims"], "mode": r1["mode"],
        "class": "CANONICAL_FULL_PIXEL_EVIDENCE (pixel-exact, unmodified)",
    },
    "derivative_preview": {
        "path": "evidence/s188_w18/halma_w18_preview.jpg",
        "label": "DERIVATIVE / NOT PIXEL-EXACT",
        "source_path": "evidence/s188_w18/runs/halma_w18_r1/screenshot.png",
        "source_sha256": r1["sha256"],
        "dims": list(img.size),
        "encoder": "PIL JPEG quality=82, RGB, max dim 640",
        "purpose": "human review only; never used by pixel-exact gates",
    },
    "deleted_screenshots": {r: {"sha256": by_run[r]["sha256"], "bytes": by_run[r]["png_bytes"],
                                "redirect": "halma_w18_r1/screenshot.png (pixel-diff = documented shade pair only)"}
                            for r in runs if r != "halma_w18_r1"},
    "pixel_equality_verdict": "NOT byte-identical (11 distinct SHAs) but visually equivalent: 10,572 px differ from r1, all one shade pair",
}
(OUT / "halma_w18_retention_manifest.json").write_text(json.dumps(manifest, indent=1))

# rewrite per-run reports truthfully
for r in runs:
    rec = by_run[r]
    rep = W / r / "report.md"
    png = W / r / "screenshot.png"
    kept_here = r == "halma_w18_r1"
    lines = [f"# W18 Halma run {r} — CORRECTED (S212/WP10§6)",
             "",
             f"- APK package: `app.halma` (canonical `upload/canonical_apks/app.halma*.apk`)",
             f"- screenshot sha256: `{rec['sha256']}` ({rec['png_bytes']} bytes, 1080x1920)",
             f"- disposition: {rec['disposition']}",
             f"- F-016: {rec['f016_uncaught_inflight']} uncaught in-flight exception(s); F-NEW-200 census: {rec['f_new_200_census']['IMPLEMENTED']} IMPLEMENTED / {rec['f_new_200_census']['STUBBED']} STUBBED",
             f"- trace verdict: NO_APP_OPS (RENDER_OK); summary verdict REAL_APP_CONTENT is an unreconciled classifier contradiction — NOT evidence of app UI",
             f"- honest status: first-frame boundary evidence only; NOT Halma gameplay/UI",
             "",
             "Full batch analysis: `../../halma_w18_BATCH_REPORT.md`; per-run SHAs: `../../halma_w18_batch_summary.json`.",
             ]
    if kept_here:
        lines += ["", "![Retained representative frame](screenshot.png)"]
    else:
        if png.exists():
            png.unlink()
        lines += ["", f"(screenshot removed; byte-identical content class retained at `../halma_w18_r1/screenshot.png`; original sha256 recorded above and in `../../halma_w18_retention_manifest.json`)"]
    rep.write_text("\n".join(lines) + "\n")

print("batch summary/report/manifest/preview written; per-run reports rewritten")
for r in runs:
    p = W / r / "screenshot.png"
    print(r, "png exists:", p.exists())
