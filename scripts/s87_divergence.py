#!/usr/bin/env python3
"""s87_divergence.py — extract first divergence from fresh S87 probe logs."""
import glob, json, re

OUT = "/home/z/my-project/run/s87/probe"
man = json.load(open(f"{OUT}/manifest.json"))
res = json.load(open(f"{OUT}/EXEC_RESULTS.json"))

report = {}
for pkg in man:
    log = res[pkg]["obs"]["log"]
    try:
        text = open(log, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    lines = text.splitlines()
    info = {"pkg": pkg, "rc": res[pkg]["obs"]["rc"]}
    # first deferred/uncaught exception with full signature
    excs = []
    for l in lines:
        m = re.search(r"\[SYNTH-EXC\].*?L([\w/$]+);.*$", l)
        if m:
            excs.append(l.strip()[:220])
        elif re.match(r"\[UNCAUGHT\]|\[FATAL\]", l):
            excs.append(l.strip()[:220])
    info["first_exceptions"] = excs[:4]
    info["n_synth_exc"] = len(excs)
    # view tree dump (EXP092-RENDER nodes)
    nodes = [l for l in lines if "EXP092-RENDER" in l]
    info["n_render_nodes"] = len(nodes)
    info["root_nodes"] = [re.sub(r".*node=", "", n)[:120] for n in nodes[:6]]
    # last inflater/launch hints
    act = [l for l in lines if re.search(r"Activity.*onCreate|setContentView|inflate", l)]
    info["activity_hints"] = act[:3]
    # REC-MISS top methods
    miss = {}
    for l in lines:
        m = re.search(r"\[REC-MISS\] L([\w/$]+);\.(\w+)", l)
        if m:
            key = f"{m.group(1).split('/')[-1]}.{m.group(2)}"
            miss[key] = miss.get(key, 0) + 1
    info["rec_miss_top"] = sorted(miss.items(), key=lambda kv: -kv[1])[:8]
    report[pkg] = info

json.dump(report, open(f"{OUT}/DIVERGENCE.json", "w"), indent=1)
for pkg, i in report.items():
    print(f"===== {pkg} rc={i['rc']} nodes={i['n_render_nodes']} synth_exc={i['n_synth_exc']}")
    for e in i["first_exceptions"][:2]:
        print("  EXC:", e[:180])
    for n in i["root_nodes"][:2]:
        print("  NODE:", n[:120])
    if i["rec_miss_top"]:
        print("  MISS:", i["rec_miss_top"][:4])
