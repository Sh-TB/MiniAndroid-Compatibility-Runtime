#!/usr/bin/env python3
"""cont11_validator_repair.py — repair PRE-EXISTING validator data drift
(surfaced when the validator gate was run for CONT-11 W7; none of these are
caused by the F-NEW-264 fix, which touches no dossier/law data):

1. app dossiers: representative_frames pruned to files that actually exist in
   the bundle; bundles with NO surviving frames are downgraded honestly to
   NOT_OBSERVED with a note (truthfulness law — never claim HUMAN_VISIBLE
   without pixels).
2. SHA256SUMS in ops session bundles: entries for missing files removed.
3. dooz/gmdice/androidgamesnake evidence.primary: keep only paths that exist.
4. root_registry.json summary.total_roots re-synced to the real roots length.
5. laws with pseudo-app consumer refs: drop refs that are not real app ids.
"""
import glob
import json
import os

ROOT = "/home/z/my-project"
NOTE = ("pre-existing drift repaired CONT-11 W7: earlier frame files lost in "
        "container reset; no pixels -> honestly NOT_OBSERVED (no fabricated "
        "visual claim)")

# 1+2. visual evidence frames + SHA256SUMS pruning
for p in sorted(glob.glob(f"{ROOT}/docs/compatibility/apps/*.json")):
    d = json.load(open(p))
    vis = d.get("visual_evidence") or {}
    bundle = vis.get("bundle")
    changed = False
    if vis.get("status") == "HUMAN_VISIBLE" and bundle:
        bdir = os.path.join(ROOT, bundle)
        frames = [f for f in (vis.get("representative_frames") or [])
                  if os.path.exists(os.path.join(bdir, f))]
        if frames != (vis.get("representative_frames") or []):
            changed = True
            if frames:
                vis["representative_frames"] = frames
                vis["note"] = (vis.get("note") or "") + \
                    " [CONT-11 W7: pruned to surviving frames]"
            else:
                vis["status"] = "NOT_OBSERVED"
                vis["representative_frames"] = []
                vis["note"] = NOTE
        # SHA256SUMS entries for missing files
        sums = os.path.join(bdir, "SHA256SUMS")
        if os.path.exists(sums):
            lines = open(sums).read().splitlines()
            keep = []
            for ln in lines:
                fn = ln.split(maxsplit=1)[-1].strip() if ln.strip() else ""
                if fn and os.path.exists(os.path.join(bdir, fn)):
                    keep.append(ln)
            if len(keep) != len(lines):
                open(sums, "w").write("\n".join(keep) + ("\n" if keep else ""))
                changed = True
    if changed:
        json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
        print("repaired:", os.path.basename(p))

# 3. evidence.primary paths that exist
for name in ["dooz", "gmdice", "androidgamesnake"]:
    p = f"{ROOT}/docs/compatibility/apps/{name}.json"
    d = json.load(open(p))
    prim = (d.get("evidence") or {}).get("primary") or []
    good = []
    for s in prim:
        path = s.split(" (")[0].split(" + ")[0].strip()
        if os.path.exists(os.path.join(ROOT, path)):
            good.append(path)
    if good != prim:
        d["evidence"]["primary"] = good
        d["evidence"]["note"] = "CONT-11 W7: paths re-based to surviving artifacts"
        json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
        print("evidence re-based:", name, good)

# 4. registry summary re-sync
rp = f"{ROOT}/root_registry.json"
reg = json.load(open(rp))
if (reg.get("summary") or {}).get("total_roots") != len(reg["roots"]):
    reg["summary"]["total_roots"] = len(reg["roots"])
    json.dump(reg, open(rp, "w"), indent=1, ensure_ascii=False)
    print("registry summary.total_roots ->", len(reg["roots"]))

# 5. laws: drop pseudo-app consumer refs
for p in sorted(glob.glob(f"{ROOT}/docs/knowledge/laws/*.json")):
    d = json.load(open(p))
    cons = d.get("consumers") or []
    apps = {os.path.basename(f)[:-5]
            for f in glob.glob(f"{ROOT}/docs/compatibility/apps/*.json")}
    good = [c for c in cons if c in apps]
    if good != cons:
        d["consumers"] = good
        d["note"] = (d.get("note") or "") + \
            " [CONT-11 W7: pseudo-app consumer refs removed (validator gate)]"
        json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
        print("law consumers fixed:", os.path.basename(p))
