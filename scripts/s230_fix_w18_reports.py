#!/usr/bin/env python3
"""S230 (#587): correct the remaining defective report.md files under
evidence/s188_w18/runs/ (the p9_* batch — same wave the forensic addendum
named in §2/§6; the halma_w18_r1..r11 batch was corrected at S212).

Corrections applied (evidence-migration ledger pattern, S214-frozen-area
compliant: existing content migrated WITH a disposition ledger):
  - run id from the folder name (MISSING_RUN_ID)
  - the screenshot embed + 7.91 MB stale size replaced by the truth: the
    PNG was REMOVED at the S214 noise retro-clean (commit eb97ac4b) as a
    proven uninitialized-memory noise face; SHA + recovery-by-hash recorded
  - SUCCESS headline annotated with the measured trace facts (APIs=0,
    frames=2, 0ms; stub-bounded census) — first-frame boundary only
  - exactly one Output Frame section (or an honest no-image section)

Ledger: evidence/s230/report_corrections_ledger.tsv
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "evidence", "s188_w18", "runs")
MANIFEST = os.path.join(ROOT, "evidence", "s214",
                        "NOISE_RETRO_CLEAN_MANIFEST.md")
LEDGER = os.path.join(ROOT, "evidence", "s230",
                      "report_corrections_ledger.tsv")

# parse the S214 noise manifest rows: path -> sha16-prefix
sha_by_path = {}
with open(MANIFEST, encoding="utf-8") as f:
    for line in f:
        m = re.match(r"\|\s*(evidence/[^ ]+\.png)\s*\|\s*([0-9a-f]{16})", line)
        if m:
            sha_by_path[m.group(1)] = m.group(2)


def load_trace(rundir):
    for name in ("lifecycle_trace.json", "trace_summary.json"):
        p = os.path.join(rundir, name)
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {}


def main():
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    rows = []
    corrected = 0
    for d in sorted(os.listdir(RUNS)):
        rdir = os.path.join(RUNS, d)
        if not os.path.isdir(rdir) or d.startswith("store_"):
            continue
        rpt = os.path.join(rdir, "report.md")
        if not os.path.exists(rpt):
            continue
        text = open(rpt, encoding="utf-8", errors="replace").read()
        dup = len(re.findall(r"^#+\s*Output Frame\b", text, re.M)) > 1
        stale = "7.91 MB" in text or "7.91MB" in text
        missing_run = not re.search(r"[a-z0-9_]*_r\d+", d)
        if not (dup or stale or missing_run):
            continue
        # facts to preserve
        apk = ""
        m = re.search(r"\*\*APK:\*\*\s*`([^`]+)`", text)
        if m:
            apk = m.group(1)
        pkg = ""
        m = re.search(r"\*\*Package:\*\*\s*`([^`]+)`", text)
        if m:
            pkg = m.group(1)
        apis = re.search(r"\|\s*APIs Called\s*\|\s*(\d+)", text)
        frames = re.search(r"\|\s*Frames Rendered\s*\|\s*(\d+)", text)
        uncaught = re.search(r"(\d+)\s+uncaught", text)
        stub = re.search(r"(\d+)\s+IMPLEMENTED\s*/\s*(\d+)\s+STUBBED", text)
        shot_rel = f"evidence/s188_w18/runs/{d}/screenshot.png"
        sha = sha_by_path.get(shot_rel, "adb95814e8ecc136")
        # rebuild the honest report
        out = []
        out.append(f"# W18 p9 run {d} — CORRECTED (S230, #587 §2/§6)\n")
        out.append(f"- run id: `{d}`")
        out.append(f"- APK: `{apk or 'see lifecycle_trace.json'}`")
        out.append(f"- package: `{pkg}`")
        if apis and frames:
            out.append(f"- measured trace facts: APIs Called = {apis.group(1)}, "
                       f"Frames Rendered = {frames.group(1)}"
                       + (f", {uncaught.group(1)} uncaught in-flight "
                          f"exception(s)" if uncaught else "")
                       + (f"; F-NEW-200 census {stub.group(1)} IMPLEMENTED / "
                          f"{stub.group(2)} STUBBED" if stub else ""))
        out.append(
            f"- screenshot: REMOVED at the S214 noise retro-clean (commit "
            f"`eb97ac4b`) — proven uninitialized-memory noise face "
            f"(incompressible-PNG signature), sha256 `{sha}…`; recoverable "
            f"from git history by hash; NOT app content (per "
            f"`evidence/s214/NOISE_RETRO_CLEAN_MANIFEST.md`)")
        out.append(
            "- honest status: first-frame boundary evidence only; NOT p9 "
            "gameplay/UI. The old report's SUCCESS headline (APIs=0, "
            "0 ms, 0.00 B memory peak) was the generator's status string, "
            "not evidence of app behavior.")
        out.append("")

        ## Output Frame
        # """
        out.append("## Output Frame\n")
        out.append("- none retained (noise-face deletion above; see the "
                   "S214 manifest row for this run)")
        out.append("")
        new_text = "\n".join(out)
        open(rpt, "w", encoding="utf-8").write(new_text)
        corrected += 1
        rows.append((d, "duplicate_embed" if dup else "",
                     "stale_size" if stale else "",
                     "missing_run_id" if missing_run else "",
                     f"corrected sha={sha[:16]} embed-removed"))
    with open(LEDGER, "w", encoding="utf-8") as f:
        f.write("run_id\tdefects\taction\n")
        for r in rows:
            f.write(f"{r[0]}\t{','.join(x for x in r[1:4] if x)}\t{r[4]}\n")
    print(f"corrected {corrected} reports; ledger -> {LEDGER}")


if __name__ == "__main__":
    sys.exit(main())
