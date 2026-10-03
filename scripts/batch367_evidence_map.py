#!/usr/bin/env python3
"""Build per-issue evidence map for the 108 batch issues from all authoritative ledgers."""
import json, os, re, collections

BASE = "/home/z/my-project"
B1 = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 17, 18, 68, 81, 121, 166, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 334, 335, 336, 337, 338, 340, 341, 342, 345, 347, 349, 350, 352]
B2 = [252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 273, 274, 275, 276, 277, 279, 280, 285, 286, 287, 289, 291, 292, 293, 294, 298, 299, 300, 301, 302, 303, 305, 306, 307, 308, 309, 310, 313, 314, 315, 316]
B3 = [317, 318, 319, 321, 323, 331, 332, 333]
ALL = set(B1 + B2 + B3)

def jl(p):
    recs = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                try: recs.append(json.loads(line))
                except Exception as e: print("BADLINE", p, e)
    return recs

# 1. FORENSIC_ALL_REQUESTS_LEDGER
fr = jl(f"{BASE}/docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl")
fr_by_issue = collections.defaultdict(list)
for r in fr:
    iss = r.get("issue")
    if iss in ALL:
        fr_by_issue[iss].append(r)

# 2. FORENSIC_MISSING_EVIDENCE
me = jl(f"{BASE}/docs/FORENSIC_MISSING_EVIDENCE.jsonl")
me_by_issue = collections.defaultdict(list)
for r in me:
    iss = r.get("issue")
    if iss in ALL:
        me_by_issue[iss].append(r)

# 3. MICRO_GAP_REGISTRY (MG-### keyed)
mgr = json.load(open(f"{BASE}/docs/MICRO_GAP_REGISTRY.json"))
if isinstance(mgr, dict):
    print("MICRO_GAP_REGISTRY top keys:", list(mgr.keys())[:10])
    items = mgr.get("gaps") or mgr.get("items") or mgr.get("records") or []
else:
    items = mgr
mg_by_id = {}
for r in (items if isinstance(items, list) else []):
    gid = r.get("gap_id") or r.get("id") or ""
    mg_by_id[gid] = r
print("micro-gap registry records:", len(mg_by_id), "sample ids:", list(mg_by_id.keys())[:8])

# 4. VERIFIED_EXECUTED_GAMES
veg = json.load(open(f"{BASE}/docs/verified_executed_games.json"))
print("verified_executed_games type:", type(veg).__name__, "len:", len(veg) if hasattr(veg,'__len__') else '?')
print(json.dumps(veg, indent=0)[:600] if not isinstance(veg, list) else json.dumps(veg[:2], indent=0)[:600])

# 5. map issue -> MG id via title from fetched issues
iss_title = {}
for n in ALL:
    p = f"{BASE}/forensic_data/batch367/issue_{n}.json"
    if os.path.exists(p):
        iss_title[n] = json.load(open(p))["title"]

mg_from_title = {}
for n, t in iss_title.items():
    m = re.match(r"\[(MG-\d+)\]", t)
    if m:
        mg_from_title[n] = m.group(1)

# stats
have_fr = sorted(n for n in ALL if fr_by_issue[n])
no_fr = sorted(n for n in ALL if not fr_by_issue[n])
print(f"\nissues with FR ledger rows: {len(have_fr)}/108; without: {len(no_fr)}")
print("without FR rows:", no_fr)
print("\nMG ids resolved from titles:", len(mg_from_title), "; found in registry:", sum(1 for v in mg_from_title.values() if v in mg_by_id))

# verified_status distribution
vs = collections.Counter()
for n in ALL:
    for r in fr_by_issue[n]:
        vs[r.get("verified_status","?")] += 1
print("\nFR verified_status distribution:", dict(vs))

# save intermediate map
out = {
  "fr_by_issue": {str(k): [ {kk: vv for kk, vv in r.items()} for r in v] for k, v in fr_by_issue.items()},
  "me_by_issue": {str(k): v for k, v in me_by_issue.items()},
  "titles": {str(k): v for k, v in iss_title.items()},
}
json.dump(out, open(f"{BASE}/forensic_data/batch367/evidence_map_raw.json", "w"), indent=1)
print("\nsaved evidence_map_raw.json")
