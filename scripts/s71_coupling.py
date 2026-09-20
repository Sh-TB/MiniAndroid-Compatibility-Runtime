#!/usr/bin/env python3
"""s71_coupling.py — S71 W8: dependency-depth & fan-out ranking of semantic
families, derived from the FRESH live traces (run/s71_live/*/api_calls.json).

Mandate: "260 call sites vs 20 call sites cannot be compared by count alone —
a low-level API may have 20 sites but hundreds of downstream dependents."

Metrics per semantic family (from docs/foundation/s71/forensic_classification.json):
  SITES   total static call sites (dex census)
  APKS    distinct APKs with static sites
  LIVE    live stubbed dispatches (fresh traces)
  WINDOW  downstream-coupling: distinct OTHER APIs invoked within ±8 trace
          events of a STUBBED event of this family (result-consumers)
  DEPTH   foundation layer (1 = deepest: interpreter/object-model, 7 = app)
  SW      silent-wrong records (poison downstream state invisibly)
  RANK    SITES×APKS + 40×LIVE + 25×WINDOW + 60×SW  (depth-weighted fan-out)

DEPTH table (foundation layer of the family ROOT):
  1 interpreter/object-model (enum law, class/object laws, boxing)
  2 java.lang core (String ctor, ThreadLocal, Thread state, Runtime)
  3 java.util collections & arrays
  4 io/nio streams & buffers
  5 framework data (Bundle/Uri/TypedValue/Json/properties)
  6 view/widget/window/layout (ancestry dispatch, listeners, textsize,
    window chrome, fragment tx, viewtree observer, drawable)
  7 app-level glue (pkg-feature, props, misc singletons)
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/z/my-project")

DEPTH = {
    "ENUM-LAW": 1, "OBJECT-CLASS-LAW": 1, "OBJECT-EQUALS-LAW": 1,
    "CLASS-LAW": 1, "BOXING-LAW": 1, "ISINSTANCE": 1,
    "STRING-CTOR-LAW": 2, "STRING-LAW": 2, "THREADLOCAL-LAW": 2,
    "THREAD-STATE-LAW": 2, "RUNTIME-LAW": 2, "PROPS-LAW": 2,
    "COLLECTION-ELEMENTS-LAW": 3, "ARRAYS-ORDER-LAW": 3, "BITSET-LAW": 3,
    "MAP-LAW": 3,
    "BAOS-LAW": 4, "NIO-LAW": 4, "IO-FILE-LAW": 4,
    "BUNDLE-LAW": 5, "URI-LAW": 5, "TYPEDVALUE-LAW": 5, "JSON-LAW": 5,
    "INTENTFILTER-LAW": 5, "FRAGMENT-TX-LAW": 6, "ANCESTRY-ROOT": 6,
    "WINDOW-CHROME": 6, "VIEWOBSERVER-LAW": 6, "WIDGET-LISTENER-LAW": 6,
    "TEXTSIZE-FAMILY": 6, "VIEW-RES-LAW": 6, "DRAWABLE-LAW": 6,
    "LAYOUT-LAW": 6, "THEME-LAW": 6, "RES-COLOR-LAW": 6,
    "PKG-FEATURE-LAW": 7, "DESUGAR-SHIM-LAW": 3, "CTX-SVC-LAW": 6,
    "RANDOM-LAW": 3, "SUPER-CALL-BOOKKEEPING": 2, "TRACE-RESOLUTION-ARTIFACT": 7,
}

# families treated as ancestry-dispatch (one root law)
def fam_key(f):
    return "ANCESTRY-ROOT" if (f or "").startswith("ANCESTRY-ROOT") else (f or "(NO-FAMILY)")


def main():
    cls = json.load(open(ROOT / "docs/foundation/s71/forensic_classification.json"))
    fams = defaultdict(list)
    for r in cls["records"]:
        if r["classification"] in ("INTRINSIC", "APP-SPECIFIC",
                                   "IMPLEMENTED-CORRECT"):
            continue
        fams[fam_key(r["family"])].append(r)

    # window coupling from fresh traces
    stub_api_fam = {}
    for f, rs in fams.items():
        for r in rs:
            stub_api_fam[r["api"]] = f
    traces = []
    for d in sorted((ROOT / "run/s71_live").glob("*/api_calls.json")):
        traces.append(json.loads(d.read_text()))
    coupling = defaultdict(set)
    window_events = defaultdict(int)
    for calls in traces:
        n = len(calls)
        for i, c in enumerate(calls):
            f = stub_api_fam.get(c.get("api", ""))
            if not f or c.get("status") != "STUBBED":
                continue
            window_events[f] += 1
            for j in range(max(0, i - 8), min(n, i + 9)):
                if j == i:
                    continue
                o = calls[j].get("api", "")
                if o and not o.startswith("<unknown>"):
                    coupling[f].add(o)

    rows = []
    for f, rs in fams.items():
        sites = sum(r["static_sites"] for r in rs)
        apks = max((r["static_apks"] for r in rs), default=0)
        live = sum(r["live_calls_s71"] for r in rs)
        sw = sum(1 for r in rs if r["silent_wrong"])
        win = len(coupling.get(f, ()))
        depth = DEPTH.get(f, 7)
        wdep = (8 - depth) / 7.0     # deeper layer → higher weight
        rank = round(sites * (1 + wdep) + 40 * live + 25 * win + 60 * sw)
        rows.append({"family": f, "n": len(rs), "sites": sites, "live": live,
                     "window_coupling": win, "silent_wrong": sw,
                     "depth_layer": depth, "rank": rank,
                     "sample_coupled": sorted(coupling.get(f, ()))[:10]})
    rows.sort(key=lambda r: -r["rank"])
    out = {"generated": "S71 W8 family ranking",
           "method": "depth-weighted fan-out + trace-window coupling",
           "families": rows}
    dest = ROOT / "docs/foundation/s71/family_ranking.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}\n")
    print(f"{'RANK':>5} {'family':<28} {'n':>3} {'sites':>6} {'live':>5} "
          f"{'win':>4} {'sw':>3} {'L':>2}")
    for r in rows:
        print(f"{r['rank']:>5} {r['family']:<28} {r['n']:>3} {r['sites']:>6} "
              f"{r['live']:>5} {r['window_coupling']:>4} "
              f"{r['silent_wrong']:>3} {r['depth_layer']:>2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
