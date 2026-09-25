#!/usr/bin/env python3
"""s101_api_need_ledger.py — S101 API-NEED LEDGER (permanent registry).

Owner mandate: "every app/game must be registered with WHICH classes and
WHICH APIs it needs, so fixing them flips more titles to loaded."

Inputs  : run/s101/full_load_report.json (fresh census, S101 re-run)
          run/s101/full_load/<pkg>/{obs,click}/crash.log + *_obs.log
Output  : docs/API_NEED_LEDGER.json  (machine-readable, per-title needs)
          docs/API_NEED_LEDGER.md    (fanout-ranked family table)

Extraction is evidence-first: every recorded need carries the exact log
line (trimmed) as evidence. Family classification uses keyword rules on
the exception sites; families are ranked by distinct-title fan-out so the
next fix batch attacks the highest-leverage roots first.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
from collections import defaultdict

ROOT = "/home/z/my-project"
REPORT = f"{ROOT}/run/s101/full_load_report.json"
OUT_JSON = f"{ROOT}/docs/API_NEED_LEDGER.json"
OUT_MD = f"{ROOT}/docs/API_NEED_LEDGER.md"

FAMILY_RULES = [
    ("appcompat-decor-toolbar", r"WindowDecorActionBar|getDecorToolbar|Can't make a decor toolbar|ActionBarOverlayLayout"),
    ("theme-gate", r"Theme\.AppCompat theme|ThemeUtils|theme-gate"),
    ("constraint-layout", r"constraintlayout|ConstraintWidget|ConstraintWidgetContainer"),
    ("compose-runtime", r"compose/ui/platform|ensureCompositionCreated|ComposeView|snapshot was taken"),
    ("lifecycle-adapter", r"Recreator_LifecycleAdapter|Lifecycling|LifecycleAdapter|lifecycle/Lifecycle"),
    ("libgdx-glsurfaceview", r"badlogic/gdx|GdxRuntimeException|AndroidGraphics"),
    ("capacitor-bridge", r"getcapacitor|CapacitorBridge"),
    ("multidex-family", r"multidex|MultiDex"),
    ("handler-null", r"Landroid/os/Handler;->getLooper|Landroid/os/Handler;-><init>.*null"),
    ("typedarray-null", r"Landroid/content/res/TypedArray;.*null object reference"),
    ("coordinatorlayout", r"coordinatorlayout|CoordinatorLayout\$LayoutParams|findAn"),
    ("savedstate-registry", r"savedstate|SavedStateRegistry"),
    ("material-speeddial", r"SpeedDialView|leinardi"),
    ("gl-native", r"UnsatisfiedLink|libGL|EGL|GLThread"),
]


def fam_of(sig):
    fams = []
    for fam, pat in FAMILY_RULES:
        if re.search(pat, sig):
            fams.append(fam)
    return fams or ["unclassified"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except FileNotFoundError:
        return ""


def extract_title(pkg, status, visual_level):
    logs = ""
    crash = ""
    base = f"{ROOT}/run/s101/full_load/{pkg}"
    for p in (f"{base}/obs/crash.log", f"{base}/click/crash.log",
              f"{base}/obs_obs.log", f"{base}/obs_click.log"):
        if p.endswith("crash.log"):
            crash += read(p)
        logs += read(p)
    needs = {
        "missing_classes": {},   # class -> evidence
        "exceptions": {},        # (type|site|msg) -> evidence
        "inflate_unresolved_max": 0,
        "textshaper_missing": [],
    }
    for m in re.finditer(r"(?:ClassNotFoundException|NoClassDefFoundError)[^\n]{0,160}", crash + logs):
        line = m.group(0).strip()
        cls = re.search(r"L([\w/$]+);", line)
        key = "L" + cls.group(1) + ";" if cls else re.sub(r"[^\w/.]", "?", line[:60])
        if key not in needs["missing_classes"]:
            needs["missing_classes"][key] = {"evidence": line[:200], "count": 0}
        needs["missing_classes"][key]["count"] += 1
    for m in re.finditer(
            r"(NullPointerException|ClassCastException|IllegalStateException|RuntimeException|"
            r"IndexOutOfBoundsException|ArrayStoreException|UnsatisfiedLinkError|Exception)[^\n]{0,200}", crash):
        line = m.group(0).strip()
        site = ""
        sm = re.search(r"(?:in|at|caller=|unwound) L([\w/$]+);\.\w+", line)
        if sm:
            site = sm.group(0)
        key = (m.group(1) + "|" + site)[:120]
        if key not in needs["exceptions"]:
            needs["exceptions"][key] = {"evidence": line[:240], "count": 0}
        needs["exceptions"][key]["count"] += 1
    for m in re.finditer(r"\[U007-INFLATE\][^\n]*unresolved=(\d+)", logs):
        needs["inflate_unresolved_max"] = max(needs["inflate_unresolved_max"], int(m.group(1)))
    for m in re.finditer(r"\[TEXTSHAPER\][^\n]*MISSING[^\n]{0,120}", logs):
        tok = m.group(0)
        if tok not in needs["textshaper_missing"]:
            needs["textshaper_missing"].append(tok)
    families = set()
    blob = crash + logs
    for fam, pat in FAMILY_RULES:
        if re.search(pat, blob):
            families.add(fam)
    for d in needs["missing_classes"]:
        for f in fam_of(d):
            families.add(f)
    for k in needs["exceptions"]:
        for f in fam_of(k):
            families.add(f)
    return {
        "package": pkg,
        "s101_status": status,
        "visual_level": visual_level,
        "missing_classes": [{"class": k, **v} for k, v in needs["missing_classes"].items()],
        "exceptions": [{"sig": k, **v} for k, v in needs["exceptions"].items()],
        "inflate_unresolved_max": needs["inflate_unresolved_max"],
        "textshaper_missing": needs["textshaper_missing"],
        "families": sorted(families),
    }


def main():
    rep = json.load(open(REPORT))
    titles = []
    for r in rep:
        lvl = r.get("visual", {}).get("LEVEL", -1)
        titles.append(extract_title(r["package"], r.get("status", "?"), lvl))

    fam_titles = defaultdict(set)
    for t in titles:
        if t["s101_status"] in ("PARTIAL", "FAIL"):
            for f in t["families"]:
                fam_titles[f].add(t["package"])

    rank = {"FAIL": 0, "PARTIAL": 1, "RENDERED-L2+": 2, "INTERACTIVE-EVIDENCE": 3}
    titles.sort(key=lambda t: (rank.get(t["s101_status"], 9), t["package"]))

    fams_ranked = sorted(fam_titles.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    doc = {
        "generated_at": os.environ.get("S101_TS", ""),
        "engine_head": head,
        "engine_sha256": sha256(f"{ROOT}/miniandroid/build/miniandroid"),
        "protocol": "S99 full-load protocol re-run on S101 tree (identical obs+click+visual audit)",
        "census": {s: sum(1 for t in titles if t["s101_status"] == s)
                   for s in ("INTERACTIVE-EVIDENCE", "RENDERED-L2+", "PARTIAL", "FAIL")},
        "families_ranked_by_fanout": [
            {"family": f, "fanout": len(ps), "titles": sorted(ps)} for f, ps in fams_ranked
        ],
        "titles": titles,
    }
    json.dump(doc, open(OUT_JSON, "w"), indent=1)

    # ---- markdown ----
    lines = [
        "# API-NEED LEDGER (S101 RECALL SWEEP)",
        "",
        f"Engine head: `{head}` — census: {doc['census']}",
        "",
        "Every PARTIAL/FAIL title with the classes/APIs it needs, extracted from",
        "crash forensics logs (evidence-first: each need carries its log line).",
        "Families ranked by distinct-title fan-out — the next fix batch attacks",
        "the top of this table first.",
        "",
        "## Families by fan-out",
        "",
        "| # | family | titles needing it | example titles |",
        "|---|--------|------------------:|----------------|",
    ]
    for i, (f, ps) in enumerate(fams_ranked, 1):
        ex = ", ".join(sorted(ps)[:3])
        lines.append(f"| {i} | `{f}` | {len(ps)} | {ex} |")
    lines += ["", "## Per-title needs (PARTIAL/FAIL only)", ""]
    for t in titles:
        if t["s101_status"] not in ("PARTIAL", "FAIL"):
            continue
        lines.append(f"### {t['package']} — {t['s101_status']} (L{t['visual_level']})")
        if t["missing_classes"]:
            lines.append("- missing classes:")
            for d in t["missing_classes"][:8]:
                lines.append(f"  - `{d['class']}` x{d['count']}: `{d['evidence'][:120]}`")
        if t["exceptions"]:
            lines.append("- exceptions:")
            for d in t["exceptions"][:6]:
                lines.append(f"  - `{d['sig']}` x{d['count']}")
        if t["textshaper_missing"]:
            lines.append(f"- textshaper: {t['textshaper_missing']}")
        if t["families"]:
            lines.append(f"- families: {', '.join(t['families'])}")
        lines.append("")
    open(OUT_MD, "w").write("\n".join(lines))
    print(f"wrote {OUT_JSON} ({len(titles)} titles, {len(fams_ranked)} families)")
    print(f"wrote {OUT_MD}")
    for f, ps in fams_ranked[:12]:
        print(f"  {len(ps):2d}  {f}")


if __name__ == "__main__":
    main()
