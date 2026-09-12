#!/usr/bin/env python3
"""Central root-verification fast path (brief §9/§10, speed-addendum §87).

  python3 tools/verify/verify.py --root R-NEW-246
  python3 tools/verify/verify.py --batch R-NEW-065,R-NEW-081,R-NEW-135
  python3 tools/verify/verify.py --list

FLOW (brief §46/§50): root → registry → cluster/probe plan → shared artifacts
→ probe (if implemented) → structured evidence record. Tool output is
EVIDENCE, never root-proof. Roots without an implemented probe return the
fast-path investigation package (registry row + artifact pointers + frontier
notes) so the agent does ONE tool call instead of thirty.
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.dirname(os.path.dirname(HERE))  # repo root (tools/verify is two levels below)
REG = os.path.join(REPO, "root_registry.json")
CORPUS = os.path.join(REPO, "miniandroid", "download", "exp076_corpus")
DOOZ = os.path.join(CORPUS, "io.github.yamin8000.dooz_18.apk")

# probe name -> (module callable spec, coverage note)
PROBES = {
    "apk-index": ("apk_artifacts", "APK/ZIP/manifest/ARSC structure (shared cache)"),
    "stub-radar": ("probes.stub_radar", "source stub/gap inventory (DISCOVERY ONLY)"),
    "screenshot-metrics": ("probes.screenshot_metrics", "pixel stats for run screenshots"),
    "symbol-index": ("probes.symbol_index", "C++ symbol index (discovery accelerator)"),
}

# root clusters -> probe plans (implemented framework subset)
CLUSTER_PLAN = {
    "apk": {"probe": "apk-index", "apk": DOOZ,
            "roots": ["033", "045", "064", "065", "067", "081", "082", "086", "087",
                      "122", "123", "124", "125", "135", "139", "089", "090", "170"]},
    "source": {"probe": "stub-radar", "roots": ["164", "165", "172"]},
    "shot": {"probe": "screenshot-metrics", "roots": ["077", "270", "271", "272", "273", "275", "276", "277", "278"]},
    "symbols": {"probe": "symbol-index", "roots": ["016", "027", "051", "127"]},
}

def load_registry():
    with open(REG) as f:
        return json.load(f)

def root_row(reg, rid):
    num = rid.replace("R-NEW-", "").lstrip("0") or "0"
    for r in reg["roots"]:
        if int(r["id"].split("-")[-1]) == int(num):
            return r
    return None

def run_probe(name, apk=None, run_dir=None):
    if name == "apk-index":
        import apk_artifacts
        d, info = apk_artifacts.build(apk or DOOZ)
        return info, d
    if name == "stub-radar":
        from probes import stub_radar
        return stub_radar.run(), None
    if name == "screenshot-metrics":
        from probes import screenshot_metrics
        return screenshot_metrics.run(run_dir), None
    if name == "symbol-index":
        from probes import symbol_index
        return symbol_index.run(), None

def fast_path(row):
    """One-call investigation package for a root (agent token reduction, §34)."""
    return {
        "id": row["id"], "status": row["status"], "priority": row["priority"],
        "floodgate": row["fg"], "evidence": row["evidence"],
        "missing_proof": row["missing"], "next_action": row["next"],
        "commit": row["commit"],
        "pointers": {
            "worklist": "docs/root-searchlight/ROOT_WORKLIST.md",
            "law_ledger": "docs/research/ROOT_LAW_GLOBAL_AUDIT.md",
            "failure_ledger": "docs/root-searchlight/FAILURE_LEDGER.md",
            "registry": "root_registry.json",
        },
    }

def main():
    reg = load_registry()
    args = sys.argv[1:]
    if "--list" in args:
        for k, (m, note) in PROBES.items():
            print(f"{k:20s} {m:26s} {note}")
        return 0
    results = []
    if "--batch" in args:
        i = args.index("--batch"); ids = args[i + 1].split(",")
    elif "--root" in args:
        i = args.index("--root"); ids = [args[i + 1]]
    elif "--cluster" in args:
        i = args.index("--cluster"); cname = args[i + 1]
        plan = CLUSTER_PLAN[cname]
        info, d = run_probe(plan["probe"], plan.get("apk"))
        print(json.dumps({"cluster": cname, "probe": plan["probe"],
                          "serves_roots": plan["roots"], "result": info,
                          "artifact_dir": d}, indent=1))
        return 0
    else:
        print(__doc__); return 1
    for rid in ids:
        row = root_row(reg, rid)
        if row is None:
            results.append({"id": rid, "error": "not in registry"}); continue
        num = rid.replace("R-NEW-", "").lstrip("0")
        plan = next(({"cluster": k, **{kk: vv for kk, vv in p.items() if kk != "roots"}}
                     for k, p in CLUSTER_PLAN.items() if num in p["roots"]), None)
        out = fast_path(row)
        if plan:
            try:
                info, d = run_probe(plan["probe"], plan.get("apk"))
                out["probe"] = {"name": plan["probe"], "cluster": plan["cluster"],
                                "result": info, "artifact_dir": d}
            except Exception as e:  # probe failure is evidence, not silence
                out["probe"] = {"name": plan["probe"], "error": str(e)}
        results.append(out)
    print(json.dumps({"results": results}, indent=1, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
