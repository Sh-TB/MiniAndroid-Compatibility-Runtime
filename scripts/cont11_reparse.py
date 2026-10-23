#!/usr/bin/env python3
"""cont11_reparse.py — re-extract honest final-uncaught signatures from the
existing census run logs: pair the LAST 'EXC-PROPAGATE ... uncaught at caller'
(APP BOUNDARY) with the LAST SYNTH-EXC before it, plus verdict + REC-MISS set.
Then re-cluster by exception class + invoked-API anchor + crash site."""
import json, re, os, collections

OUT = "/home/z/my-project/run/cont11_census"
d = json.load(open(f"{OUT}/census.json"))

def extract(run_dir):
    p = f"{run_dir}/run.log"
    if not os.path.exists(p):
        return None
    txt = open(p, errors="replace").read()
    lines = txt.splitlines()
    # last uncaught site
    site_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if "EXC-PROPAGATE" in lines[i] and "uncaught at caller" in lines[i]:
            site_idx = i
            break
    # last SYNTH-EXC before site_idx (the actual final exception)
    exc_idx = None
    if site_idx is not None:
        for i in range(site_idx, -1, -1):
            if "[SYNTH-EXC]" in lines[i]:
                exc_idx = i
                break
    exc_line = lines[exc_idx] if exc_idx is not None else None
    site_line = lines[site_idx] if site_idx is not None else None
    v = None
    m = re.search(r"verdict=(\w+), first_missing_stage=(\w+)", txt)
    if m:
        v = f"verdict={m.group(1)} first_missing={m.group(2)}"
    elif re.search(r"Status: SUCCESS", txt):
        v = "verdict=SUCCESS"
    rms = []
    for m in re.finditer(r"\[REC-MISS\] (\S+)", txt):
        if m.group(1) not in rms:
            rms.append(m.group(1))
    fb = re.search(r"\[EXP092-COPY\] fb has (\d+) non-white pixels", txt)
    # view tree size
    vt = 0
    vp = f"{run_dir}/view_tree.json"
    if os.path.exists(vp):
        try:
            t = open(vp, errors="replace").read()
            vt = t.count('"text"') + t.count('"class"')
        except Exception:
            pass
    return {"exc": exc_line, "site": site_line, "verdict": v,
            "rec_miss": rms[:10], "fb": int(fb.group(1)) if fb else None}

def parse_exc(exc_line):
    if not exc_line:
        return None, None, None
    e = re.search(r"L([\w/$]+(?:Exception|Error));", exc_line)
    q = re.findall(r"'([^']+)'", exc_line)
    mth = re.search(r"method=(\S+) pc=", exc_line)
    return (e.group(1) if e else None), (q[0] if q else None), (mth.group(1) if mth else None)

fam_members = collections.defaultdict(list)
api_anchor = collections.Counter()
exc_classes = collections.Counter()
rows = []
for r in d:
    tag = r["apk"].replace(".apk", "")
    run_dir = f"{OUT}/r_{r['apk']}"
    ex = extract(run_dir)
    row = {"apk": r["apk"], "install": r["install"], "run": r["run"]}
    if ex:
        row.update(ex)
        cls, api, mth = parse_exc(ex["exc"])
        row["exc_class"], row["api"], row["method"] = cls, api, mth
        site = (ex["site"] or "")
        sm = re.search(r"uncaught at caller (\S+) invoke_pc=(\d+) → (APP BOUNDARY|deferred)", site)
        row["crash_site"] = sm.group(1) if sm else (site[:120] if site else None)
        row["boundary"] = sm.group(3) if sm else None
        if cls:
            exc_classes[cls] += 1
        if api:
            key = api if api not in ("X",) else None
            if key:
                api_anchor[key] += 1
        # family
        f = None
        if row["boundary"] != "APP BOUNDARY" and row["verdict"]:
            f = "NO-UNCAUGHT:" + (row["verdict"] or "").split()[0]
        elif cls and cls.endswith("NullPointerException"):
            f = "NPE:" + (api or "unknown-api")
        elif cls and "ClassNotFound" in cls:
            f = "CNF:" + (api or "unknown")
        elif cls and "NoSuchMethod" in cls:
            f = "NSM:" + (api or "unknown")
        elif cls:
            f = "EXC:" + cls
        else:
            f = "OTHER"
        row["family"] = f
        fam_members[f].append(r["apk"])
    else:
        row["family"] = "NO-LOG"
        fam_members["NO-LOG"].append(r["apk"])
    rows.append(row)

json.dump(rows, open(f"{OUT}/census_v2.json", "w"), indent=1)

print("=== final exception classes ===")
for k, c in exc_classes.most_common(12):
    print(f"  {c:3d}  {k}")
print("\n=== RECURRING FAMILIES (>=2 titles) ===")
for f, members in sorted(fam_members.items(), key=lambda kv: -len(kv[1])):
    if len(members) >= 2:
        print(f"  {len(members):3d}  {f}")
print("\n=== singles ===")
for f, members in sorted(fam_members.items(), key=lambda kv: -len(kv[1])):
    if len(members) == 1:
        print(f"    1  {f}   [{members[0]}]")
