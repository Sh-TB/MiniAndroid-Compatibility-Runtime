#!/usr/bin/env python3
"""Build complete per-issue evidence for all 108 batch issues."""
import json, os, re, collections

BASE = "/home/z/my-project"
B1 = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 17, 18, 68, 81, 121, 166, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 334, 335, 336, 337, 338, 340, 341, 342, 345, 347, 349, 350, 352]
B2 = [252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 273, 274, 275, 276, 277, 279, 280, 285, 286, 287, 289, 291, 292, 293, 294, 298, 299, 300, 301, 302, 303, 305, 306, 307, 308, 309, 310, 313, 314, 315, 316]
B3 = [317, 318, 319, 321, 323, 331, 332, 333]
BATCHES = {"1": B1, "2": B2, "3": B3}
ALL = set(B1 + B2 + B3)

def jl(p):
    recs = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try: recs.append(json.loads(line))
                except: pass
    return recs

fr = jl(f"{BASE}/docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl")
fr_by_issue = collections.defaultdict(list)
for r in fr:
    if r.get("issue") in ALL:
        fr_by_issue[r["issue"]].append(r)

mgr = json.load(open(f"{BASE}/docs/MICRO_GAP_REGISTRY.json"))["tickets"]
veg = json.load(open(f"{BASE}/docs/verified_executed_games.json"))
games = veg.get("games", [])
games_by_pkg = {g.get("package"): g for g in games}

titles = {}
for n in ALL:
    titles[n] = json.load(open(f"{BASE}/forensic_data/batch367/issue_{n}.json"))["title"]

out_rows = []
for n in sorted(ALL):
    t = titles[n]
    rows = fr_by_issue[n]
    mgm = re.match(r"\[(MG-\d+)\]", t)
    mg = mgr.get(mgm.group(1)) if mgm else None
    # games info
    ginfo = None
    for pkg, g in games_by_pkg.items():
        blob = json.dumps(g)
        # crude association: issue title contains game name fragments
    rec = {
        "issue": n,
        "title": t,
        "batch": ("1" if n in B1 else "2" if n in B2 else "3"),
        "fr_rows": [{"rid": r["request_id"], "vs": r.get("verified_status"), "lvl": r.get("evidence_level"),
                     "commits": r.get("commit_shas"), "expl": r.get("explanation"),
                     "superseded_by": r.get("superseded_by"), "blockers": r.get("blockers"),
                     "ss": r.get("screenshot_refs"), "rt": r.get("runtime_refs"), "tests": r.get("test_refs"),
                     "regr": r.get("regression_refs")} for r in rows],
        "mg_id": mgm.group(1) if mgm else None,
        "mg_status": mg.get("STATUS") if mg else None,
        "mg_evidence": mg.get("EVIDENCE") if mg else None,
        "mg_api": mg.get("API") if mg else None,
        "mg_domain": mg.get("DOMAIN") if mg else None,
        "mg_note": mg.get("NOTE") if mg else None,
    }
    out_rows.append(rec)

json.dump(out_rows, open(f"{BASE}/forensic_data/batch367/evidence_map_full.json", "w"), indent=1)

# Distribution summary
vs_all = collections.Counter()
for rec in out_rows:
    statuses = set(r["vs"] for r in rec["fr_rows"])
    vs_all["|".join(sorted(statuses))] += 1
print("FR verified_status combos across 108:")
for k, v in vs_all.most_common():
    print(f"  {v:3d}  {k}")

mg_ok = sum(1 for r in out_rows if r["mg_id"] and r["mg_status"])
print(f"\nMG rows resolved: {mg_ok}")
mg_status_dist = collections.Counter(r["mg_status"] for r in out_rows if r["mg_status"])
print("MG status dist:", dict(mg_status_dist))

# Non-MG issues list
nonmg = [r["issue"] for r in out_rows if not r["mg_id"]]
print(f"\nnon-MG issues ({len(nonmg)}):", nonmg)
for r in out_rows:
    if not r["mg_id"]:
        print(f"  #{r['issue']} [{r['batch']}] {r['title'][:70]}")
        for fr_row in r["fr_rows"]:
            print(f"      FR {fr_row['rid']} vs={fr_row['vs']} lvl={fr_row['lvl']} superseded_by={fr_row['superseded_by']!r}")
            print(f"      expl: {fr_row['expl'][:200] if fr_row['expl'] else ''}")
