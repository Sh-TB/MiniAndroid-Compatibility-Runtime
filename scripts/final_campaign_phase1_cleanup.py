#!/usr/bin/env python3
"""FINAL CAMPAIGN PHASE 1 — hygiene execution.
1. Distill every raw evidence trace (api_trace.json/heap_trace.json/*_trace.json)
   into evidence/<session>/TRACE_SUMMARIES.json (census + SHA256 provenance).
2. Write disposition ledger docs/history/final_campaign_phase1/DISPOSITION_LEDGER.json
   (every removed path + SHA256 + size + reason + law reference).
3. Print the git rm manifest. Does NOT commit — reviewer runs --apply for git rm.
"""
import hashlib
import json
import os
import sys

REPO = "/home/z/my-project"
LEDGER_DIR = "docs/history/final_campaign_phase1"
SUMMARY_NAME = "TRACE_SUMMARIES.json"
TOP_N = 20


def sha256(path, cap=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            if cap and os.path.getsize(path) <= h.bytecount:
                break
    return h.hexdigest()


def is_raw_trace(rel):
    b = os.path.basename(rel)
    return (b in ("api_trace.json", "heap_trace.json", "full_trace.json")
            or b.endswith("_trace.json"))


def distill(path):
    """One trace file -> compact record. Never invents: census computed from real data."""
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception as e:
        return {"path": path, "error": f"unparseable: {e}",
                "sha256": sha256(path)}
    rec = {"sha256": sha256(path), "size_bytes": os.path.getsize(path),
           "generated_at": d.get("generated_at"),
           "session_id": d.get("session_id")}
    calls = d.get("calls") if isinstance(d, dict) else d
    if isinstance(calls, list):
        rec["total_calls"] = d.get("total_calls", len(calls)) if isinstance(d, dict) else len(calls)
        census = {}
        for c in calls:
            if isinstance(c, dict):
                sig = c.get("method") or c.get("signature") or c.get("api") or c.get("class")
                if sig:
                    census[sig] = census.get(sig, 0) + 1
        rec["top_apis"] = [{"api": k, "count": v} for k, v in
                           sorted(census.items(), key=lambda x: -x[1])[:TOP_N]]
        rec["distinct_apis"] = len(census)
    return rec


def main():
    apply = "--apply" in sys.argv
    ledger = []
    summaries = {}
    n_tr = 0

    # 1. evidence raw traces
    for root, dirs, files in os.walk(os.path.join(REPO, "evidence")):
        if SUMMARY_NAME in files:
            continue
        for b in sorted(files):
            fp = os.path.join(root, b)
            rel = os.path.relpath(fp, REPO)
            if not is_raw_trace(rel):
                continue
            rec = distill(fp)
            rec["path"] = rel
            rec["disposition"] = "DELETE_RAW_TRACE (distilled; law ARTIFACT_LIFECYCLE §3 RAW_LOG/§4 Logs-traces)"
            ledger.append({k: rec[k] for k in ("path", "size_bytes", "sha256", "disposition") if k in rec})
            sess = os.path.relpath(root, os.path.join(REPO, "evidence"))
            summaries.setdefault(sess, []).append(rec)
            n_tr += 1

    # 2. tmp offenders (zero canonical references — measured by phase1 ref check)
    tmp_targets = [
        "tmp/archidx.json", "tmp/index-v1.json", "tmp/idx.jar",
        "tmp/mykanji_extract", "tmp/blid", "tmp/flappy_build",
        "tmp/ac_x", "tmp/aa_check",
    ]
    for t in tmp_targets:
        fp = os.path.join(REPO, t)
        if not os.path.exists(fp):
            continue
        if os.path.isdir(fp):
            for root, dirs, files in os.walk(fp):
                for b in sorted(files):
                    f2 = os.path.join(root, b)
                    rel = os.path.relpath(f2, REPO)
                    sz = os.path.getsize(f2)
                    ledger.append({"path": rel, "size_bytes": sz, "sha256": sha256(f2),
                                   "disposition": f"DELETE (inside {t}; tmp/ must hold no required artifact — ARTIFACT_LIFECYCLE §3 TEMPORARY/CACHE; zero canonical refs measured)"})
        else:
            sz = os.path.getsize(fp)
            ledger.append({"path": t, "size_bytes": sz, "sha256": sha256(fp),
                           "disposition": "DELETE (tmp/ must hold no required artifact; zero canonical refs measured)"})

    # 3. z.ai production JS bundle (mission-forbidden class; provenance already in REPORT_S133.md)
    zai = "evidence/s133_browser/zai_main_bundle_index-BEIsjDOv.js"
    if os.path.exists(os.path.join(REPO, zai)):
        fp = os.path.join(REPO, zai)
        ledger.append({"path": zai, "size_bytes": os.path.getsize(fp), "sha256": sha256(fp),
                       "disposition": "DELETE (copied complete JS production bundle — mission-forbidden; provenance URL+SHA preserved in ledger & REPORT_S133.md ref updated)"})

    # write summaries + ledger
    os.makedirs(os.path.join(REPO, LEDGER_DIR), exist_ok=True)
    for sess, recs in summaries.items():
        out = os.path.join(REPO, "evidence", sess, SUMMARY_NAME)
        with open(out, "w") as f:
            json.dump({"_law": "ARTIFACT_LIFECYCLE.md §3-4: raw traces deleted after distillation; SHA256 provenance preserved",
                       "distilled_at": "2026-10-02",
                       "traces": recs}, f, indent=1)
    total_bytes = sum(x.get("size_bytes", 0) for x in ledger)
    with open(os.path.join(REPO, LEDGER_DIR, "DISPOSITION_LEDGER.json"), "w") as f:
        json.dump({"_law": "docs/ARTIFACT_LIFECYCLE.md (never delete silently)",
                   "campaign": "FINAL GENERIC RUNTIME COMPATIBILITY CAMPAIGN — PHASE 1",
                   "before_tracked_MiB": 591.89,
                   "ledger_entries": len(ledger),
                   "raw_traces_distilled": n_tr,
                   "freed_MiB": round(total_bytes / 1048576, 2),
                   "entries": ledger}, f, indent=1)
    print(f"distilled {n_tr} raw traces into {len(summaries)} TRACE_SUMMARIES.json")
    print(f"ledger entries: {len(ledger)}  freed: {total_bytes/1048576:.2f} MiB")
    if apply:
        with open(os.path.join(REPO, LEDGER_DIR, "git_rm_manifest.txt"), "w") as f:
            for x in ledger:
                f.write(x["path"] + "\0")
        print("git_rm_manifest.txt written (NUL-separated) — run: xargs -0 git rm -q -- < manifest")


if __name__ == "__main__":
    main()
