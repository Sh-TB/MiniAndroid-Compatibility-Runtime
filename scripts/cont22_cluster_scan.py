#!/usr/bin/env python3
"""CONT-22 — first-divergence harvester + shared-primitive clustering (wide).

Scans the FRESH post-CONT-21 family run logs (current binary) and clusters
semantic faces by the FRAMEWORK-side signature (framework class/method/field
involved), not by obfuscated app names. Emits run/cont22/cluster_scan.json.

Clustering law: a shared primitive is a face whose framework signature is
identical across targets from different execution families. Obfuscated app
classes (Lxx0;, Ly8;.) are NOT clustered across targets — only the framework
surface (Landroid/*, Ljava/*, Lkotlin/*, Landroidx/* std surfaces) is.
"""
import json, os, re
from collections import Counter, defaultdict

BASE = "/home/z/my-project"
OUTROOT = f"{BASE}/run/cont21/family"
OUTJSON = f"{BASE}/run/cont22/cluster_scan.json"

FAMILY = {
    "opencalc": "F1", "stopwatch": "F1", "chessclock": "F1",
    "unote": "F1", "microtimer": "F1",
    "tictactoe": "F2", "g2048": "F2",
    "fishrings": "F3", "flappycow": "F3", "bouncy": "F3",
    "forkgram": "F4", "telegram": "F4",
    "dooz": "F6", "minibrowser": "F7",
}

# face extractors -> (cluster_key, human_note)
RE_SYNTH_IGET = re.compile(
    r"\[SYNTH-EXC\] iget-null-recv: L([^;]+);\S* \(Attempt to read from field "
    r"'([^']+)' on a null object reference\) method=(\S+) pc=(\d+)")
RE_SYNTH_INVOKE = re.compile(
    r"\[SYNTH-EXC\] \S*-null-recv: L\S+ \((Attempt to invoke (?:virtual |interface |static )?method "
    r"'([^']+)' on a null object reference)\) method=(\S+) pc=(\d+)")
RE_RECMISS = re.compile(
    r"\[REC-MISS\] L([^;]+);\.(\S+) ?(\([^)]*\))? ?caller=(\S+)")
RE_UNCAUGHT = re.compile(
    r"\[SYNTH-EXC\] .*? method=(\S+) pc=(\d+) → uncaught")
RE_APPBOUNDARY = re.compile(r"APP BOUNDARY[^\n]*")
RE_STREAM = re.compile(r"STREAM-OPEN[^\n]*ENOENT[^\n]*")

def framework_side(sig):
    """Reduce a field/method signature to its framework-side identity.
    'Landroid/content/pm/ServiceInfo;.metaData' -> ServiceInfo.metaData.
    App-obfuscated declarers are kept but tagged app-side."""
    cls = sig.split(";")[0].lstrip("L").split("/")[-1] if ";" in sig else sig
    return cls

clusters = defaultdict(lambda: {"targets": {}, "count": 0, "families": set(),
                                "example": None})
uncaught_faces = {}

for t in sorted(os.listdir(OUTROOT)):
    logp = f"{OUTROOT}/{t}/run.log"
    if not os.path.exists(logp) or t not in FAMILY:
        continue
    log = open(logp, errors="replace").read()

    for m in RE_SYNTH_IGET.finditer(log):
        exc, field, caller, pc = m.groups()
        # field like 'Landroid/content/pm/ServiceInfo;.metaData'
        fcls, fname = (field.split(";")[0].lstrip("L"), field.split(".")[-1])
        key = f"IGET-NULL {fcls.split('/')[-1]}.{fname}"
        c = clusters[key]
        c["count"] += 1
        c["families"].add(FAMILY[t])
        c["targets"].setdefault(t, []).append(f"{caller} pc={pc}")
        if not c["example"]:
            c["example"] = m.group(0)[:200]

    for m in RE_SYNTH_INVOKE.finditer(log):
        _exc, meth, caller, pc = m.groups()
        mcls = meth.split(";")[0].lstrip("L").split("/")[-1] if ";" in meth else meth
        mname = meth.split(".")[-1].rstrip("'") if "." in meth else meth
        key = f"INVOKE-NULL {mcls}.{mname}"
        c = clusters[key]
        c["count"] += 1
        c["families"].add(FAMILY[t])
        c["targets"].setdefault(t, []).append(f"{caller} pc={pc}")
        if not c["example"]:
            c["example"] = m.group(0)[:200]

    for m in RE_RECMISS.finditer(log):
        cls, meth, _args, caller = m.groups()
        short = cls.split("/")[-1]
        key = f"REC-MISS {short}.{meth.split('(')[0]}"
        c = clusters[key]
        c["count"] += 1
        c["families"].add(FAMILY[t])
        c["targets"].setdefault(t, []).append(caller)
        if not c["example"]:
            c["example"] = m.group(0)[:200]

    us = RE_UNCAUGHT.findall(log)
    if us:
        uncaught_faces[t] = {"count": len(us), "faces": us[:5]}

    ab = RE_APPBOUNDARY.findall(log)
    if ab:
        clusters["APP-BOUNDARY"]["count"] += len(ab)
        clusters["APP-BOUNDARY"]["families"].add(FAMILY[t])
        clusters["APP-BOUNDARY"]["targets"].setdefault(t, []).append("n=1")
    st = RE_STREAM.findall(log)
    if st:
        clusters["STREAM-PATH-DUP"]["count"] += len(st)
        clusters["STREAM-PATH-DUP"]["families"].add(FAMILY[t])
        clusters["STREAM-PATH-DUP"]["targets"].setdefault(t, []).append(st[0][:120])

result = {
    "binary": "882b7cdf389aabc3 (CONT-21 post-fix, byte-verified this container)",
    "note": "fresh post-fix logs (run/cont21/family/*/run.log written by the CONT-22 harvester run)",
    "clusters": {
        k: {"count": v["count"],
            "targets": sorted(v["targets"]),
            "families": sorted(v["families"]),
            "example": v["example"]}
        for k, v in sorted(clusters.items(),
                           key=lambda kv: (-len(kv[1]["targets"]), kv[0]))
    },
    "uncaught_faces": uncaught_faces,
}
json.dump(result, open(OUTJSON, "w"), indent=1)

print(f"{'cluster':46s} {'targets':>7s} {'fam':>4s} {'count':>5s}")
for k, v in result["clusters"].items():
    print(f"{k:46s} {len(v['targets']):>7d} {','.join(v['families']):>4s} {v['count']:>5d}")
print("\nUNCAUGHT faces per target (post-fix):")
for t, u in sorted(uncaught_faces.items()):
    print(f"  {t:14s} n={u['count']} {u['faces'][:2]}")
