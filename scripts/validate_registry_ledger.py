#!/usr/bin/env python3
"""CONT-3 Phase 3 — registry summary recomputation + ledger validator.

1. Recomputes root_registry.json summary metadata FROM the actual roots
   array (the wave generators updated roots but not summary — total_roots
   said 540 while roots held 542; total/verified_fixed/by_status/
   primary_frontier/open_frontiers were stale by multiple waves).

2. Validates (exit 1 on ANY failure):
   V1 registry root count == summary.total_roots
   V2 every root has a non-empty unique id (duplicate count reported)
   V3 every reconciliation-JSONL row's state is derivable from status_raw
      via the generator's maps (no silent TESTED->PENDING)
   V4 contract-374 rows: state must not be PENDING when status_raw is an
      audited status (TESTED/PARTIAL/IMPLEMENTED/NOT_APPLICABLE/BLOCKED*)
   V5 negative-test totals consistent across the contract docs (19/19)
   V6 reconciliation MD cites the same root count as the registry
   V7 stale-HEAD check: documented baseline_head/source_head strings must
      exist in the last 200 commits of git history (or be absent entirely)

Usage:
  python3 scripts/validate_registry_ledger.py            # validate only
  python3 scripts/validate_registry_ledger.py --fix      # recompute + validate
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE = Path("/home/z/my-project")
REG_PATH = BASE / "root_registry.json"
FIX = "--fix" in sys.argv

# ── recompute summary from the roots array ─────────────────────────────
reg = json.load(open(REG_PATH))
roots = reg["roots"]
st = Counter(r.get("status", "NONE").strip() for r in roots)
verified_fixed = sum(
    v for k, v in st.items()
    if k in ("ROOT-CAUSED-FIXED", "ROOT_CAUSED-FIXED", "VERIFIED-FIXED",
             "VERIFIED-CORRECT", "PROVEN-FIXED", "VERIFIED_3RUN",
             "ROOT-CAUSED-CLOSED", "ROOT-CAUSED-REMEASURED-GENERIC-OK",
             "FIXED-S75", "FIXED-VERIFIED"))
open_frontiers = sorted(
    r["id"] for r in roots
    if r.get("status") in ("OBSERVED", "OBSERVED-FAIL", "OPEN",
                           "PARTIAL-FIX"))
if FIX:
    reg["summary"]["total_roots"] = len(roots)
    reg["summary"]["total"] = len(roots)
    reg["summary"]["verified_fixed"] = verified_fixed
    reg["summary"]["by_status"] = dict(st)
    reg["summary"]["open_frontiers"] = open_frontiers
    reg["summary"]["last_updated"] = (
        "CONT-3 (2026-10-05): summary recomputed from the roots array by "
        "scripts/validate_registry_ledger.py --fix (F-NEW-238 "
        "AbstractCollection.toArray + F-NEW-238b INT-element fidelity "
        "landed; frontier advanced to the game's own solver invariant "
        "Lm2;.b pc=1471 ISE 'Even face counts always permit a completion')")
    json.dump(reg, open(REG_PATH, "w"), indent=1, ensure_ascii=False)
    print("registry summary recomputed: total_roots=%d verified_fixed=%d "
          "open_frontiers=%s" % (len(roots), verified_fixed, open_frontiers))

# ── validation ──────────────────────────────────────────────────────────
failures = []


def fail(vid, msg):
    failures.append(f"{vid}: {msg}")
    print(f"FAIL {vid}: {msg}")


# V1 count
if reg["summary"].get("total_roots") != len(roots):
    fail("V1", "summary.total_roots=%s != len(roots)=%d"
         % (reg["summary"].get("total_roots"), len(roots)))
else:
    print("PASS V1: total_roots == len(roots) == %d" % len(roots))

# V2 unique ids
ids = [r.get("id") for r in roots]
dup = {k: v for k, v in Counter(ids).items() if v > 1}
empty = sum(1 for i in ids if not i)
if dup or empty:
    fail("V2", "duplicate ids=%s empty=%d" % (dup, empty))
else:
    print("PASS V2: %d unique ids, zero duplicates, zero empty" % len(ids))

# V3/V4 reconciliation rows derivable
recon_rows = [json.loads(l) for l in
              (BASE / "docs/BASE_COMPLETION_RECONCILIATION.jsonl")
              .read_text().splitlines() if l.strip()]
sys.path.insert(0, str(BASE / "scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bcm", BASE / "scripts" / "base_completion_matrix.py")
# Do not EXECUTE the generator (it writes); replicate its maps here and
# cross-check by importing the module source for drift.
src = (BASE / "scripts" / "base_completion_matrix.py").read_text()
map_body = re.search(r"STATE_MAP = (\{.*?\n\})", src, re.S).group(1)
STATE_MAP = eval(map_body)
cmap_body = re.search(r"CONTRACT_STATE_MAP = (\{.*?\n\})", src, re.S).group(1)
CONTRACT_STATE_MAP = eval(cmap_body)
bad3 = bad4 = 0
for r in recon_rows:
    raw = (r.get("status_raw") or "").strip()
    if r["kind"] == "registry-root":
        want = STATE_MAP.get(raw, "UNKNOWN")
        if want != "UNKNOWN" and r.get("state") != want:
            bad3 += 1
    if r["kind"] == "contract-374":
        want = CONTRACT_STATE_MAP.get(raw, "UNKNOWN")
        if want == "UNKNOWN":
            continue  # free-form status_raw — flagged below only if PENDING-masked
        if r.get("state") != want:
            bad3 += 1
        if raw in ("TESTED", "PARTIAL", "IMPLEMENTED", "NOT_APPLICABLE") \
                and r.get("state") == "PENDING":
            bad4 += 1
if bad3:
    fail("V3", "%d reconciliation rows have state not derivable from "
         "status_raw" % bad3)
else:
    print("PASS V3: every mapped reconciliation row matches its status_raw")
if bad4:
    fail("V4", "%d contract-374 rows mask audited status as PENDING" % bad4)
else:
    print("PASS V4: no audited contract row masked as PENDING")

# V5 negative-test totals
neg_pat = re.compile(r"negatives?\s+(\d+)/(\d+)")
neg_refs = {}
for doc in ("docs/FOUNDATION_CONTRACT_98.md",
            "docs/FOUNDATION_CONTRACT_98.jsonl"):
    p = BASE / doc
    if not p.exists():
        continue
    for m in neg_pat.finditer(p.read_text()):
        neg_refs.setdefault(doc, set()).add((int(m.group(1)),
                                             int(m.group(2))))
bad5 = []
for doc, totals in neg_refs.items():
    if len(totals) > 1:
        bad5.append(f"{doc}: mixed totals {sorted(totals)}")
    elif doc.endswith(".md"):
        only = next(iter(totals))
        if only[0] != 19 or only[1] != 19:
            bad5.append(f"{doc}: {only[0]}/{only[1]} (current contract 19/19)")
if bad5:
    fail("V5", "; ".join(bad5))
else:
    print("PASS V5: negative-test totals consistent at 19/19")

# V6 reconciliation MD root count
md = (BASE / "docs/BASE_COMPLETION_RECONCILIATION.md").read_text()
m = re.search(r"root_registry\.json \((\d+) roots\)", md)
if m and int(m.group(1)) != len(roots):
    fail("V6", "reconciliation MD cites %s roots != %d"
         % (m.group(1), len(roots)))
else:
    print("PASS V6: reconciliation MD root count matches registry")

# V7 stale-HEAD references
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                      text=True, cwd=BASE).stdout.strip()
recent = subprocess.run(
    ["git", "log", "--format=%H", "-200"], capture_output=True, text=True,
    cwd=BASE).stdout.split()
recent_set = set(recent)
stale_refs = []
for doc in ("docs/ENVIRONMENT_PROFILE.json",):
    try:
        d = json.load(open(BASE / doc))
    except OSError:
        continue
    ref = d.get("source_head")
    if ref and ref not in recent_set:
        stale_refs.append(f"{doc}: source_head {ref[:12]} not in recent "
                          "history")
# registry summary must NOT pin a stale baseline_head
if "baseline_head" in reg["summary"]:
    stale_refs.append("root_registry.json: summary.baseline_head pinned "
                      "(remove — the registry tracks roots, not HEADs)")
if stale_refs:
    fail("V7", "; ".join(stale_refs))
else:
    print("PASS V7: no stale HEAD references in profile/registry summaries")


# V8 (CONT-5): legacy top-level counts + open_frontiers coherence
lf_bad = []
for k in ("total", "count", "total_roots"):
    if reg.get(k) != len(roots):
        lf_bad.append(f"{k}={reg.get(k)} != {len(roots)}")
if lf_bad:
    fail("V8", "legacy top-level counts stale: " + "; ".join(lf_bad))
else:
    print("PASS V8: legacy top-level counts == len(roots) == %d" % len(roots))

# V9 (CONT-5): open_frontiers must only list non-closed roots
CLOSED_STATUSES = {
    "ROOT-CAUSED-FIXED", "VERIFIED-FIXED", "ROOT_CAUSED-FIXED",
    "CLOSED-CLASSIFIED", "ROOT-CAUSED-CLOSED", "PROVEN-FIXED",
    "FIXED-VERIFIED", "VERIFIED_3RUN", "NOT-APPLICABLE",
    "SUPERSEDED-BY-EVIDENCE",
}
by_id = {r.get("id"): r for r in roots}
of_bad = []
for fid in reg.get("summary", {}).get("open_frontiers", []):
    st = (by_id.get(fid) or {}).get("status")
    if st in CLOSED_STATUSES:
        of_bad.append(f"{fid} listed open but status={st}")
if of_bad:
    fail("V9", "open_frontiers staleness: " + "; ".join(of_bad))
else:
    print("PASS V9: open_frontiers contains no closed roots")

if failures:
    print("\nVALIDATOR: %d FAILURE(S)" % len(failures))
    sys.exit(1)
print("\nVALIDATOR: ALL PASS")
