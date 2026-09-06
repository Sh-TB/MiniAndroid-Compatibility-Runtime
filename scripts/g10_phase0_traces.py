#!/usr/bin/env python3
"""
g10_phase0_traces.py — G10 Phase 0: capture U007_LAYOUT_DEBUG measure/layout
traces for the selected 7-APK subset (NO code changes; env-gated trace).

For each APK: run with U007_LAYOUT_DEBUG=2, save console.log (contains
[U007-LAYOUT] per-view lines), then build a structured per-APK record:
  root ViewGroup -> child hierarchy -> lp (MeasureSpec proxy) -> measured dims
  -> layout bounds -> draw result (pixel audit from phase0_baseline.json).
Output: docs/evidence/g10_evidence/phase0_traces.json + per-APK trace logs.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
MA = REPO / "miniandroid"
BIN = MA / "build" / "miniandroid"
OUT = REPO / "docs" / "evidence" / "g10_evidence"

SUBSET = [
    ("microtimer", "download/exp076_corpus/dubrowgn.microtimer_8.apk"),
    ("billthefarmer_notes", "download/exp073_real_apps/org.billthefarmer.notes_139.apk"),
    ("headingcalculator", "download/exp073_real_apps/org.debian.eugen.headingcalculator_1.apk"),
    ("gmdice", "download/exp073_real_apps/de.duenndns.gmdice_8.apk"),
    ("simplestopwatch", "download/exp073_real_apps/omegacentauri.mobi.simplestopwatch_26.apk"),
    ("unote", "download/exp076_corpus/app.varlorg.unote_30.apk"),
    ("chessclock", "download/exp073_real_apps/com.chessclock.android_29.apk"),
]

LINE = re.compile(
    r"\[U007-LAYOUT\] (?P<indent>\s*)view (?P<vid>\d+) (?P<cls>\S+) "
    r"id_name=(?P<idn>\S*) lp=(?P<lpw>-?\d+)/(?P<lph>-?\d+) weight=(?P<w>-?[\d.]+) "
    r"(?:orient=(?P<orient>-?\d+) )?"
    r"measured=(?P<mw>\d+)x(?P<mh>\d+) text_size=(?P<ts>[\d.]+) lines=(?P<ln>-?\d+) "
    r"below='(?P<below>[^']*)' above='(?P<above>[^']*)' right_of='(?P<ro>[^']*)' "
    r"left_of='(?P<lo>[^']*)' cgrav=(?P<cg>0x[0-9a-fA-F]+|\d+) text='(?P<text>.*)'")


def parse_trace(log: str):
    rows = []
    for m in LINE.finditer(log):
        d = m.groupdict()
        rows.append({
            "depth": len(m.group("indent")) // 2,
            "vid": int(d["vid"]), "class": d["cls"].split("/")[-1].rstrip(";").lstrip("L"),
            "id_name": d["idn"], "lp": f"{d['lpw']}/{d['lph']}",
            "weight": float(d["w"]), "measured": f"{d['mw']}x{d['mh']}",
            "orient": int(d["orient"]) if d.get("orient") else None,
            "text": d["text"][:40],
        })
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base = json.loads((OUT / "phase0_baseline.json").read_text())
    baseline = {b["apk"]: b for b in base}
    results = []
    env = {"U007_LAYOUT_DEBUG": "2", "PATH": "/usr/bin:/bin:/usr/local/bin"}
    for name, rel in SUBSET:
        apk = MA / rel
        outdir = Path("/tmp/g10_runs") / name / "trace"
        outdir.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(outdir)],
                              capture_output=True, text=True, timeout=180, env=env)
        log = proc.stdout + proc.stderr
        rows = parse_trace(log)
        rec = {"apk": name, "trace_lines": len(rows)}
        if rows:
            rec["tree"] = rows
            # summary: the 6 shallowest-level interesting nodes
            rec["root"] = rows[0] if rows else None
            wide = [r for r in rows if r["depth"] <= 3]
            rec["shallow"] = wide[:30]
        (OUT / f"{name}_layout_trace.log").write_text(
            "\n".join(l for l in log.splitlines() if "U007-LAYOUT" in l) or "(no trace)")
        b = baseline.get(name, {})
        rec["pixel_audit"] = b.get("pixel_audit")
        rec["base_status"] = b.get("base", {}).get("status")
        results.append(rec)
        print(f"[{name}] trace_rows={len(rows)} "
              f"px={b.get('pixel_audit', {}).get('nonbg_pct')}% "
              f"bbox={b.get('pixel_audit', {}).get('content_bbox')}")
    (OUT / "phase0_traces.json").write_text(json.dumps(results, indent=1))
    print(f"\nwritten: {OUT / 'phase0_traces.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
