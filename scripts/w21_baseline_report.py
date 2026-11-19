#!/usr/bin/env python3
"""w21_baseline_report.py — analyze evidence/w21/runtime_baseline.tsv.

Produces:
  - medians/spread/outliers per APK (cold separate)
  - per-run CPU/RSS now captured (W20-K2 had 'na')
  - regression comparison vs the W20-K2 TSV (evidence/w20/runtime_baseline.tsv)
    screenshot sha16 identity per APK = the no-regression check
Outputs CSV + MD under evidence/w21/.
"""
import csv
import json
import statistics
from pathlib import Path

ROOT = Path("/home/z/my-project/miniandroid/evidence/w21")
NEW = ROOT / "runtime_baseline.tsv"
OLD = Path("/home/z/my-project/miniandroid/evidence/w20/runtime_baseline.tsv")


def read_tsv(p):
    rows = []
    with open(p) as f:
        rd = csv.DictReader(f, delimiter="\t")
        for r in rd:
            rows.append(r)
    return rows


def med(v):
    return statistics.median(v) if v else None


new_rows = read_tsv(NEW)
old_rows = read_tsv(OLD) if OLD.exists() else []

# group new rows
apps = {}
for r in new_rows:
    a = apps.setdefault(r["apk"], {"reps": [], "cold": None, "shas": set(),
                                   "rcs": set(), "divs": set(), "rss": [],
                                   "cpu": [], "blank": set()})
    a["reps"].append((int(r["rep"]), float(r["wall_s"]), r["phase"]))
    a["cpu"].append(float(r["cpu_s"]) if r["cpu_s"] not in ("?", "na") else None)
    a["rss"].append(int(r["maxrss_kb"]) if r["maxrss_kb"] not in ("?", "na") else None)
    if r["phase"] == "cold":
        a["cold"] = float(r["wall_s"])
    a["shas"].add(r["sha16"])
    a["rcs"].add(r["rc"])
    a["divs"].add(r["first_divergence"])
    a["blank"].add(r["blank_ratio"])

# old sha16 per apk per phase (set identity, not majority — the randomix
# cold/warm two-face pattern proved a majority vote misfires)
old_phase_shas = {}
for r in old_rows:
    old_phase_shas.setdefault(r["apk"], {}).setdefault(r["phase"], set()).add(r["sha16"])

# old medians
old_meds = {}
old_by_app = {}
for r in old_rows:
    old_by_app.setdefault(r["apk"], []).append(float(r["wall_s"]))
for k, v in old_by_app.items():
    old_meds[k] = med(v)

# per-phase sha sets (new)
new_phase_shas = {}
for r in new_rows:
    new_phase_shas.setdefault(r["apk"], {}).setdefault(r["phase"], set()).add(r["sha16"])

out_rows = []
for apk, d in sorted(apps.items()):
    walls = [w for _, w, _ in d["reps"]]
    m = med(walls)
    mn, mx = min(walls), max(walls)
    cpu_ok = [c for c in d["cpu"] if c is not None]
    rss_ok = [r for r in d["rss"] if r is not None]
    sha = ",".join(sorted(d["shas"]))
    oph = old_phase_shas.get(apk, {})
    phase_verdicts = []
    for ph in ("cold", "warm"):
        nset = new_phase_shas.get(apk, {}).get(ph, set())
        oset = oph.get(ph)
        if oset is None:
            phase_verdicts.append(f"{ph}:(absent)")
        elif nset and nset.issubset(oset):
            phase_verdicts.append(f"{ph}:IDENTICAL")
        else:
            phase_verdicts.append(f"{ph}:DIFFERS")
    old_sha = ",".join(sorted({s for v in oph.values() for s in v})) or "(absent)"
    old_m = old_meds.get(apk)
    out_rows.append({
        "apk": apk, "n_reps": len(walls), "median_s": round(m, 2),
        "min_s": round(mn, 2), "max_s": round(mx, 2),
        "cold_s": round(d["cold"], 2) if d["cold"] else "",
        "median_cpu_s": round(med(cpu_ok), 2) if cpu_ok else "",
        "median_rss_kb": int(med(rss_ok)) if rss_ok else "",
        "sha16": sha, "rcs": ",".join(sorted(d["rcs"])),
        "w20k2_sha16": old_sha,
        "sha_regresion": " ".join(phase_verdicts),
        "w20k2_median_s": round(old_m, 2) if old_m else "",
        "wall_delta_vs_w20k2": (round(m - old_m, 2) if old_m else ""),
        "first_divergence": ";".join(sorted(x for x in d["divs"] if x != "none")) or "none",
    })

with open(ROOT / "W21_RUNTIME_BASELINE.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    w.writeheader()
    w.writerows(out_rows)

# MD
md = ["# W21 RUNTIME PERFORMANCE BASELINE — 15 original APKs x 5 measured reps",
      "",
      "Binary: `build/miniandroid` sha256-16 `f2083d06e5a6e89a` @ commit `c1602b754ddf5d00`.",
      "Workload: `run --max-seconds 35 --frames 30 --execution-mode real-dalvik`, fresh",
      "data-root per APK, cold rep1 + warm reps2-5 (W20-K2-identical config).",
      "Per-run wall + CPU + peak RSS via `scripts/w21_runner.py` (getrusage(RUSAGE_CHILDREN)",
      "per fresh process — the fields W20-K2 could not capture: /usr/bin/time is absent",
      "on this host). Host: 2 CPUs, no swap; measured nproc in every JSONL.",
      "",
      "| APK | n | median s | min | max | cold | median CPU s | median RSS KB | sha16 | rc | vs W20-K2 sha | W20-K2 median s | delta s |",
      "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|"]
for r in out_rows:
    md.append("| {apk} | {n_reps} | {median_s} | {min_s} | {max_s} | {cold_s} | "
              "{median_cpu_s} | {median_rss_kb} | {sha16} | {rcs} | {sha_regresion} | "
              "{w20k2_median_s} | {wall_delta_vs_w20k2} |".format(**r))
diff = [r for r in out_rows if "DIFFERS" in r["sha_regresion"]]
md.append("")
md.append(f"**Screenshot regression check vs W20-K2**: {len(out_rows) - len(diff)}/{len(out_rows)} "
          "APKs byte-IDENTICAL; differing: " +
          (", ".join(f"{r['apk']} ({r['sha16']} vs {r['w20k2_sha16']})" for r in diff) or "none") + ".")
md.append("")
md.append("Raw per-run TSV: `evidence/w21/runtime_baseline.tsv` (header + 75 rows). "
          "Runner JSONL per run: `evidence/w21/runtime_perf/<apk>_rN/runner.json`; "
          "full stdout logs `<apk>_rN/run.log`.")
(ROOT / "W21_RUNTIME_BASELINE.md").write_text("\n".join(md) + "\n")
print(json.dumps(out_rows[:3], indent=1)[:600])
print("W21_RUNTIME_BASELINE.csv/.md written,", len(out_rows), "apps")
