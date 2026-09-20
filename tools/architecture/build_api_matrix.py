#!/usr/bin/env python3
"""build_api_matrix.py — §13 API COVERAGE MATRIX builder.

Merges three REAL data sources (no hand annotation):
  1. DEX census (tools/architecture/dex_census.py): static fan-out — how many
     call sites in the corpus DEX consume each framework API
  2. Live dispatch traces (run/s69_live/*/api_calls.json, summarized in
     docs/foundation/live_runs.json): observed at runtime + per-call status
     IMPLEMENTED / STUBBED / MISSING / ERROR
  3. Static served surface (docs/foundation/graph/served_api.json): string-
     guard extraction of the dispatcher (over-approximation, flagged)

Output: docs/foundation/api_matrix.json — queryable, machine-readable (§23).
"""
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/z/my-project")
OUT = ROOT / "docs" / "foundation" / "api_matrix.json"
CENSUS = ROOT / "docs" / "foundation" / "dex_census" / "_aggregate.json"
LIVE = ROOT / "docs" / "foundation" / "live_runs.json"
SERVED = ROOT / "docs" / "foundation" / "graph" / "served_api.json"


def main():
    census = json.loads(CENSUS.read_text())
    live = json.loads(LIVE.read_text())
    served = json.loads(SERVED.read_text())

    # static served surface: (class, method) → dispatch sites (over-approx)
    served_map = defaultdict(set)
    for p in served.get("pairs", []):
        # served class guard "Lcom/x;" + method guard; normalize to "Lcls;.meth"
        served_map[f"{p['class']}.{p['method']}"].add(f"{p['tu']}:{p['function']}:{p['line']}")

    # live observed: (class, method) → status counts + per-apk
    live_map = defaultdict(lambda: {"status": Counter(), "apks": set()})
    for run in live.get("runs", []):
        ap = Path(run["dir"]) / "api_calls.json"
        if not ap.exists():
            continue
        calls = json.loads(ap.read_text())
        for c in calls:
            key = f"{c.get('class')}.{c.get('method')}"
            live_map[key]["status"][c.get("status", "UNKNOWN")] += 1
            live_map[key]["apks"].add(run["apk"])

    rows = []
    fanout = census.get("corpus_api_fanout", [])
    byapk = census.get("corpus_api_fanout_by_apk", {})
    for api, sites in fanout:
        # api = "Landroid/os/Handler;.post"
        cls, _, meth = api.rpartition(".")
        status = "UNSERVED-STATIC"
        served_where = []
        if api in served_map:
            status = "SERVED-STATIC"
            served_where = sorted(served_map[api])
        lv = live_map.get(api)
        live_status = None
        observed_apks = []
        if lv:
            live_status = dict(lv["status"])
            observed_apks = sorted(lv["apks"])
        # semantic status law (§25 anti-false-success):
        #   LIVE-IMPL   — observed at runtime with IMPLEMENTED status
        #   LIVE-STUB   — observed, only STUBBED returns
        #   SERVED-STATIC — dispatcher has a guard, not yet observed live
        #   UNSERVED    — consumed by corpus DEX, no dispatch guard found
        if live_status:
            impl = live_status.get("IMPLEMENTED", 0)
            stub = live_status.get("STUBBED", 0) + live_status.get("MISSING", 0)
            if impl and impl >= stub:
                status = "LIVE-IMPL"
            elif impl:
                status = "LIVE-PARTIAL"
            else:
                status = "LIVE-STUB"
        elif status == "SERVED-STATIC":
            status = "SERVED-STATIC"
        else:
            status = "UNSERVED"
        rows.append({
            "api": api,
            "dex_call_sites": sites,
            "apks_using": byapk.get(api, {}),
            "status": status,
            "live_status_counts": live_status,
            "live_observed_apks": observed_apks,
            "static_dispatch_sites": served_where[:6],
        })

    # priority: fan-out × unserved first (FAN-OUT FIRST — §14)
    def prio(r):
        rank = {"UNSERVED": 0, "LIVE-STUB": 1, "LIVE-PARTIAL": 2,
                "SERVED-STATIC": 3, "LIVE-IMPL": 4}.get(r["status"], 5)
        return (rank, -r["dex_call_sites"])

    rows.sort(key=prio)
    summary = Counter(r["status"] for r in rows)
    result = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "data_sources": {
            "static_fanout": "docs/foundation/dex_census/_aggregate.json",
            "live_traces": "docs/foundation/live_runs.json (run/s69_live/*/api_calls.json)",
            "static_served": "docs/foundation/graph/served_api.json",
        },
        "note": "status law: LIVE-IMPL > LIVE-PARTIAL > LIVE-STUB > "
                "SERVED-STATIC > UNSERVED; fan-out = corpus DEX call sites. "
                "UNSERVED with high fan-out = highest-priority foundation gap.",
        "summary": dict(summary),
        "total_distinct_apis": len(rows),
        "apis": rows,
    }
    OUT.write_text(json.dumps(result, indent=1))
    print("summary:", dict(summary))
    print("top UNSERVED by fan-out:")
    for r in rows[:15]:
        if r["status"] in ("UNSERVED", "LIVE-STUB"):
            print(f'  {r["dex_call_sites"]:5} sites  {r["status"]:13} {r["api"]}')


if __name__ == "__main__":
    main()
