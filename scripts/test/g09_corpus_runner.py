#!/usr/bin/env python3
"""
scripts/test/g09_corpus_runner.py — G09 Phases 2/3/4 batch harness.

For every corpus APK:
  1. BASE run   : ./miniandroid run <apk> -o <out>/base
                  → Status, screenshot.png, lifecycle_trace.json (G07 evidence)
  2. CLICK run  : ./miniandroid run <apk> -o <out>/click --click-test
                  → click_test_report.json (G06 evidence: real View → real
                    dispatcher → real DEX callback → state change → frame)
  3. G08 signals: scan run.log + api_trace.json for Intent/startActivity/
                  second-Activity instantiation evidence.

Writes docs/evidence/g09_corpus/results/<pkg>.result.json per APK and a
combined g09_results_summary.json. Screenshot/click-frame PNGs are left in
the (gitignored) output tree; selected visual evidence is copied out by the
caller.

No fixture logic, no package-name branches: everything runs through the ONE
canonical runtime entry point with default device configuration.
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MA = REPO / "miniandroid"
BIN = MA / "build" / "miniandroid"
RESULTS = REPO / "docs" / "evidence" / "g09_corpus" / "results"
WORK = Path("/tmp/g09_runs")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run_apk(apk: Path, outdir: Path, extra: list[str]) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run([str(BIN), "run", str(apk), "-o", str(outdir)] + extra,
                          capture_output=True, text=True, timeout=180)
    dt = time.time() - t0
    log = proc.stdout + proc.stderr
    (outdir / "console.log").write_text(log)
    status = "SUCCESS" if "Status: SUCCESS" in log else (
        "PARTIAL" if "Status:" in log else "CRASH")
    return {
        "rc": proc.returncode, "status": status, "seconds": round(dt, 2),
        "has_screenshot": (outdir / "screenshot.png").exists(),
        "screenshot_sha256": sha256(outdir / "screenshot.png")
        if (outdir / "screenshot.png").exists() else None,
        "log_path": str(outdir / "console.log"),
        "log_tail": log[-2000:],
    }


def lifecycle_evidence(outdir: Path) -> dict:
    lt = outdir / "lifecycle_trace.json"
    if not lt.exists():
        return {"present": False}
    try:
        d = json.loads(lt.read_text())
    except Exception as e:  # noqa: BLE001
        return {"present": True, "error": str(e)}
    return {
        "present": True,
        "final_state": d.get("final_state"),
        "transitions": [(t.get("from"), t.get("to"), t.get("success"))
                        for t in d.get("transitions", [])],
        "finish_cascade": d.get("finish_cascade"),
        "activity_launch": d.get("activity_launch"),
    }


def click_evidence(outdir: Path) -> dict:
    ct = outdir / "click_test_report.json"
    if not ct.exists():
        return {"present": False}
    try:
        d = json.loads(ct.read_text())
    except Exception as e:  # noqa: BLE001
        return {"present": True, "error": str(e)}
    return {
        "present": True,
        "views_probed": d.get("views_probed"),
        "xml_onclick_views": d.get("xml_onclick_views"),
        "views_changed_second_frame": d.get("views_changed_second_frame"),
        "per_view": [
            {"class": v.get("class"), "handler": v.get("handler"),
             "kind": v.get("kind"), "dispatched": v.get("click_dispatched"),
             "state_changed": v.get("state_changed"),
             "changed_px": v.get("changed_px")}
            for v in d.get("per_view", [])],
    }


def g08_signals(outdir: Path, log: str) -> dict:
    sig = {"startActivity_in_dex_trace": False,
           "startActivityForResult_in_dex_trace": False,
           "intent_apis_seen": [],
           "second_activity_instantiated": None,
           "activity_not_found": False}
    hay = log
    api = outdir / "api_trace.json"
    if api.exists():
        try:
            d = json.loads(api.read_text())
            hay += "\n".join(json.dumps(c) for c in d.get("calls", []))
        except Exception:  # noqa: BLE001
            pass
    if re.search(r"startActivity\b", hay):
        sig["startActivity_in_dex_trace"] = True
    if "startActivityForResult" in hay:
        sig["startActivityForResult_in_dex_trace"] = True
    if "ACTIVITY_NOT_FOUND" in hay:
        sig["activity_not_found"] = True
    for pat in ["putExtra", "getStringExtra", "getIntExtra", "setResult",
                "getIntent", "setClassName", "Intent("]:
        if pat in hay:
            sig["intent_apis_seen"].append(pat)
    m = re.findall(r"[Ee]xecut\w* (?:second |new )?[Aa]ctivity|"
                   r"performLaunchActivity[^\\n]*?L([\w/$]+);", hay)
    if m:
        sig["second_activity_instantiated"] = m[:4]
    return sig


def main() -> int:
    registry = json.loads(
        (REPO / "docs/evidence/g09_corpus/g09_corpus_registry.json").read_text())
    RESULTS.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    only = sys.argv[1:] or None
    summary = []
    for entry in registry:
        rel = entry.get("corpus_rel")
        apk = (MA / rel) if rel else None
        if apk is None or not apk or not apk.exists():
            apk = Path(entry.get("apk_abs", ""))
        if not apk.exists():
            print(f"SKIP {entry['package']} — apk missing")
            continue
        if only and not any(o in entry["package"] for o in only):
            continue
        stem = entry["package"]
        out = WORK / stem
        print(f"=== {stem} ===", flush=True)
        base = run_apk(apk, out / "base", [])
        if base["status"] != "CRASH":
            run_apk(apk, out / "click", ["--click-test"])
        cev = click_evidence(out / "click")
        click_log = ""
        cl = out / "click/console.log"
        if cl.exists():
            click_log = cl.read_text()
        g08ev = g08_signals(out / "click", click_log)
        rec = {
            "package": entry["package"],
            "apk_file": entry["apk_file"],
            "sha256": entry["sha256"],
            "minSdk": entry.get("minSdk"),
            "targetSdk": entry.get("targetSdk"),
            "uses_appcompat": entry.get("uses_appcompat"),
            "uses_compose": entry.get("uses_compose"),
            "n_activities": entry.get("n_activities"),
            "interactive_surface": entry.get("interactive_surface"),
            "base": {k: v for k, v in base.items() if k != "log_tail"},
            "click_run_status": cev.get("present"),
            "click": cev,
            "lifecycle": lifecycle_evidence(out / "base"),
            "g08": g08ev,
        }
        (RESULTS / f"{stem}.result.json").write_text(json.dumps(rec, indent=2) + "\n")
        summary.append({
            "package": stem, "status": base["status"],
            "screenshot": base["has_screenshot"],
            "lifecycle_final": rec["lifecycle"].get("final_state"),
            "probed": rec["click"].get("views_probed", 0) if rec["click"] else 0,
            "changed": rec["click"].get("views_changed_second_frame", 0) if rec["click"] else 0,
        })
        print(f"  base={base['status']} shot={base['has_screenshot']} "
              f"lifecycle={rec['lifecycle'].get('final_state')} "
              f"probed={summary[-1]['probed']} changed={summary[-1]['changed']}",
              flush=True)
    (RESULTS / "g09_results_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    print(f"summary: {len(summary)} APKs → {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
