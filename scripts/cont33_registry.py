#!/usr/bin/env python3
"""CONT-33 registry update:
- F-NEW-524 ROOT-CAUSED-FIXED (heap-map representation lever: the three hot
  string/uint-keyed maps swap std::map -> std::unordered_map with the
  frozen ordered consumers preserved by explicit sorted iteration)
- F-NEW-381 evidence refresh (phase-2 lever landed: iget-object
  1.112us -> 1.038us/call on the 90s dooz PERF census; wall remains)
Registry stays id-unique; mirror sync."""
import json

BASE = "/home/z/my-project"
REG = f"{BASE}/canonical/root_cause_registry.json"
MIRROR = f"{BASE}/root_registry.json"

r = json.load(open(REG))
ids = {row["id"] for row in r}
print("registry rows:", len(r))

def append(row):
    if row["id"] in ids:
        print("SKIP (exists):", row["id"])
        return
    r.append(row)
    ids.add(row["id"])
    print("APPENDED:", row["id"], row["status"])

append({
    "id": "F-NEW-524",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "layer": "dalvik/interpreter-throughput (heap field-map representation; F-NEW-381 phase 2)",
    "date": "2026-10-26",
    "title": "Heap representation wall (the named F-NEW-381 phase-2 lever): HeapObject.fields, DalvikHeap.objects_ and static_field_storage_ were std::map (RB-tree) — every iget/iput/sget paid O(log n) pointer-chasing walks with string compares on qualified keys, on top of the memoized resolution",
    "root_cause": "The CONT-32 ledger named the remaining iget-object constant: after the CowStr register lever, the per-access cost is the map lookups — objects_.find(uint32) tree walk + fields.find(qualified string) tree walk + static_field_storage_.find(string) on the sget path. Hot path is find/operator[] only (order-independent); ~35 fields-iteration sites and 4 static-iteration sites exist but are cold (bounded diagnostics, collect-then-sort, collect-then-erase, name-priority scans).",
    "evidence": {
        "wave": "CONT-33",
        "fix": "std::map -> std::unordered_map for the three hot maps (dalvik_engine.h). Frozen ordered consumers keep the historical std::map iteration contract by explicit sorted keys: DalvikHeap::dump()/get_all_ids() (id-ascending), the view-tree fallback full-heap scan (id-ascending), and the R$string resource-id scan (first-match IS semantic — D8 shrinker ordinal collisions). all_objects() signature updated. Bounded diagnostic stderr dumps may print in hash order — zero semantic surface (ledger-noted). Patch: scripts/cont33_heap_unordered.py (anchor-verified, idempotent).",
        "ab_measurement": "dooz 90s PERF-PHASES A/B at identical HEAD 733bcbe3 lineage — op=0x54 (iget-object): PRE 3,929,077 calls / 13.11G ticks / 1.112 us-per-call; POST 3,697,908 calls / 11.52G ticks / 1.038 us-per-call (-6.6%). sget-object (op=0x62): 0.891 -> 0.773 est_ms. Wall clock: the 90s window still ends in the F084 budget halt mid-composition — the F-NEW-381 wall REMAINS (structural per-instruction cost, next named lever = the per-call method-invocation machinery: try_recursive_invoke 4.64M calls dominates the phase mass).",
        "regression": "FULL GATE at the lever binary (sha16 3a3961d63697483d, HEAD 733bcbe3): dooz 90s x4 byte-identical 851cc1761a1dfcdf; anchors opencalc 63020bc7334048fe x2, chess 3f7e670759b7c6a8 x2, microtimer bbd350b6c14fbd52 x2, unote 7481e9b468eaa376, tower3d 11a38a5aeeff45a6 — 6/6 byte-identical; user goldens 4/4 PASS (2048/snakedeluxe/minicraft REAL_APP_UI pixel gates + helloworld 83720c1028f832d0); gate-A probe 98 PASS / 1 INFO / 0 FAIL; negatives 19/19 PASS (after run/gatea/probe_store regeneration at the new binary — the initial 9/19 was the stale-store artifact, same as the CONT-158/CONT-32 records); skill selftest 13/13; telegram 60s face 774075b428f53791 byte-identical; batch-20 census re-run byte-exact retention across all 20 rows (5/20 content rows same px + same sha; 15 blanks same blank)."
    },
    "verified_current": True,
})

for row in r:
    if row["id"] == "F-NEW-381":
        ev = row.get("evidence") or {}
        if isinstance(ev, dict):
            ev["cont33_update"] = ("CONT-33 landed the ledger's NAMED phase-2 lever (heap-map "
                "representation -> F-NEW-524): iget-object per-call 1.112us -> 1.038us (-6.6%) on "
                "the dooz 90s PERF census, sget-object 0.891 -> 0.773 est_ms, zero semantic drift "
                "(full gate: anchors 6/6 byte-identical, goldens 4/4, negatives 19/19, skill 13/13, "
                "telegram face byte-identical, batch-20 byte-exact retention). The wall REMAINS: "
                "the 90s window still ends in the F084 budget halt mid-first-composition. Next "
                "named lever: per-call method-invocation machinery (try_recursive_invoke 4.64M "
                "calls / 74.7T ticks dominates the phase mass; frame setup/register marshaling "
                "per nested call).")
        print("F-NEW-381 evidence refreshed")

json.dump(r, open(REG, "w"), indent=1, ensure_ascii=False)
try:
    json.dump(r, open(MIRROR, "w"), indent=1, ensure_ascii=False)
    print("mirror synced")
except Exception as e:
    print("mirror sync skipped:", e)
print("registry rows after:", len(r))
