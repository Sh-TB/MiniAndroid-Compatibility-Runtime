#!/usr/bin/env python3
"""validate_compatibility_graph.py — S74 integrity gate for the compatibility
platform (taskbook §62/§63). Fails on broken references, duplicate IDs,
invalid statuses, missing provenance/tests for VERIFIED laws, missing evidence
paths, registry drift, and index/file mismatches.

Usage: python3 tools/validate_compatibility_graph.py [--root /path/to/repo]
Exit 0 = PASS, 1 = FAIL. Run before every platform commit.
"""
import argparse, glob, json, os, re, sys

APP_STATUS = {"DONE", "IMPLEMENTED", "TESTED", "OBSERVED", "PARTIAL", "BLOCKED", "PENDING", "SUPERSEDED"}
KNOW_STATUS = {"RAW", "CANDIDATE", "RESEARCHED", "OBSERVED", "TESTED", "VERIFIED", "SUPERSEDED", "REJECTED"}
SEC_STATUS = {"DECLARED", "OBSERVED", "ALLOWED", "BLOCKED", "NOT_OBSERVED", "UNKNOWN"}
C_KEYS = [f"C{i}" for i in range(1, 15)]


def load_dir(d, kind, errs):
    recs = {}
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            rec = json.load(open(p))
        except Exception as e:
            errs.append(f"[{kind}] unparseable JSON {os.path.basename(p)}: {e}")
            continue
        rid = rec.get(f"{kind}_id")
        if not rid:
            errs.append(f"[{kind}] missing {kind}_id in {os.path.basename(p)}")
            continue
        if rid in recs:
            errs.append(f"[{kind}] DUPLICATE id {rid} ({os.path.basename(p)})")
        rec["__file__"] = os.path.basename(p)
        recs[rid] = rec
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    errs, oks = [], []

    apps = load_dir(os.path.join(root, "docs/compatibility/apps"), "app", errs)
    tools = load_dir(os.path.join(root, "docs/compatibility/tools"), "tool", errs)
    caps = load_dir(os.path.join(root, "docs/compatibility/capabilities"), "capability", errs)
    laws = load_dir(os.path.join(root, "docs/knowledge/laws"), "knowledge", errs)

    for rid, r in apps.items():
        if r.get("record_type") != "app_dossier": errs.append(f"[app] {rid}: record_type != app_dossier")
        if r.get("status") not in APP_STATUS: errs.append(f"[app] {rid}: invalid status {r.get('status')}")
        if not isinstance(r.get("issue"), int): errs.append(f"[app] {rid}: missing/invalid issue")
        comp = r.get("completion", {})
        for i in range(1, 15):
            ck = next((k for k in comp if k.split("_")[0] == f"C{i}"), None)
            if ck is None:
                errs.append(f"[app] {rid}: completion criteria C{i} missing")
            elif comp[ck] not in APP_STATUS:
                errs.append(f"[app] {rid}: C{i} invalid status {comp[ck]}")
        for p in (r.get("evidence", {}).get("primary", []) or []) + (r.get("links", {}).get("evidence_files", []) or []):
            clean = str(p).split(" ")[0].rstrip("/")
            if not os.path.exists(os.path.join(root, clean)):
                errs.append(f"[app] {rid}: evidence path missing: {p}")
        sec = r.get("security", {})
        for k in ("filesystem", "network"):
            if sec.get(k) not in SEC_STATUS | {None}:
                errs.append(f"[app] {rid}: security.{k} invalid: {sec.get(k)}")
        for law in r.get("links", {}).get("laws", []):
            if law not in laws: errs.append(f"[app] {rid}: broken law ref {law}")
        for c in r.get("links", {}).get("capabilities", []):
            if c not in caps: errs.append(f"[app] {rid}: broken capability ref {c}")
        oks.append(f"[app] {rid}: issue #{r['issue']} status={r['status']} C1..C14 ok")

    seen_pkg = {}
    for rid, r in apps.items():
        pkg = r.get("package")
        if pkg:
            if pkg in seen_pkg:
                errs.append(f"[app] DUPLICATE package {pkg}: {rid} vs {seen_pkg[pkg]}")
            seen_pkg[pkg] = rid

    for rid, r in caps.items():
        if r.get("record_type") != "capability_record": errs.append(f"[cap] {rid}: record_type != capability_record")
        if r.get("status") not in APP_STATUS: errs.append(f"[cap] {rid}: invalid status {r.get('status')}")
        for f in ("name", "implemented", "tests", "consumers", "laws"):
            if f not in r: errs.append(f"[cap] {rid}: missing field {f} (taskbook §64)")
        if r.get("status") in {"DONE", "TESTED", "VERIFIED"} and not r.get("consumers"):
            errs.append(f"[cap] {rid}: status {r['status']} without consumers")
        for law in r.get("laws", []):
            if law not in laws: errs.append(f"[cap] {rid}: broken law ref {law}")
        for c in r.get("consumers", []):
            if c not in apps: errs.append(f"[cap] {rid}: broken consumer app ref {c}")

    registry_path = os.path.join(root, "root_registry.json")
    registry_text = ""
    registry_roots = None
    if os.path.exists(registry_path):
        try:
            reg = json.load(open(registry_path))
            registry_text = json.dumps(reg)
            registry_roots = len(reg.get("roots", []))
            summary_roots = (reg.get("summary") or {}).get("total_roots")
            if summary_roots is not None and registry_roots != summary_roots:
                errs.append(f"[registry] drift: roots list has {registry_roots} entries but summary.total_roots says {summary_roots}")
        except Exception as e:
            errs.append(f"[registry] unparseable root_registry.json: {e}")
    else:
        errs.append("[registry] root_registry.json missing")

    for rid, r in laws.items():
        if r.get("record_type") != "knowledge_record": errs.append(f"[law] {rid}: record_type != knowledge_record")
        if r.get("status") not in KNOW_STATUS: errs.append(f"[law] {rid}: invalid status {r.get('status')}")
        st = r["status"]
        if st == "VERIFIED":
            if not r.get("test"): errs.append(f"[law] {rid}: VERIFIED without test (taskbook §14.5)")
            if not (r.get("source") or {}).get("origin"): errs.append(f"[law] {rid}: VERIFIED without provenance (taskbook §14.1)")
        m = re.match(r"^LAW-F(\d+)$", rid)
        if m and r.get("scope") == "generic" and registry_text:
            if f"F-{m.group(1)}" not in registry_text:
                errs.append(f"[law] {rid}: registry id F-{m.group(1)} not found in root_registry.json")
        if r.get("superseded_by") and st != "SUPERSEDED":
            errs.append(f"[law] {rid}: has superseded_by but status != SUPERSEDED")
        for c in r.get("consumers", []):
            if c not in apps: errs.append(f"[law] {rid}: broken consumer app ref {c}")
        for c in r.get("capabilities", []):
            if c not in caps: errs.append(f"[law] {rid}: broken capability ref {c}")

    for rid, r in tools.items():
        if r.get("record_type") != "tool_profile": errs.append(f"[tool] {rid}: record_type != tool_profile")
        for f in ("name", "url", "provenance_class", "provides"):
            if not r.get(f): errs.append(f"[tool] {rid}: missing field {f}")

    idx_path = os.path.join(root, "docs/knowledge/KNOWLEDGE_RECORDS.json")
    if os.path.exists(idx_path):
        idx = json.load(open(idx_path))
        for key, recs in (("apps", apps), ("tools", tools), ("capabilities", caps), ("knowledge", laws)):
            listed, actual = set(idx.get(key, [])), set(recs)
            if listed != actual:
                miss = (actual - listed) | (listed - actual)
                errs.append(f"[index] KNOWLEDGE_RECORDS.json {key} mismatch: {sorted(miss)}")
        c = idx.get("counts", {})
        if c.get("apps") != len(apps) or c.get("knowledge_records") != len(laws):
            errs.append(f"[index] counts stale: {c} vs apps={len(apps)} laws={len(laws)}")
    else:
        errs.append("[index] docs/knowledge/KNOWLEDGE_RECORDS.json missing")

    matrix_path = os.path.join(root, "docs/compatibility/CAPABILITY_MATRIX.md")
    if os.path.exists(matrix_path):
        mtext = open(matrix_path).read()
        for aid in apps:
            if aid not in mtext:
                errs.append(f"[matrix] app {aid} absent from CAPABILITY_MATRIX.md")
    else:
        errs.append("[matrix] docs/compatibility/CAPABILITY_MATRIX.md missing")

    # ------------------------------------------------------------------
    # S74 FOLLOW-UP WAVE §35 extensions — operational evidence gates.
    # These verify STRUCTURE + METADATA CONSISTENCY + FILE EXISTENCE only.
    # They deliberately do NOT infer execution from file existence (§36):
    # a PNG existing is never treated as "the app executed"; the claim and
    # the evidence label must simply be consistent with each other.
    # ------------------------------------------------------------------
    ops_root = os.path.join(root, "docs/evidence/s74_ops")
    for rid, r in apps.items():
        vis = r.get("visual_evidence") or {}
        status = vis.get("status")
        if not status:
            errs.append(f"[app] {rid}: visual_evidence.status missing (§35: every app needs an explicit visual-evidence state)")
            continue
        if status not in {"HUMAN_VISIBLE", "NOT_HUMAN_VISIBLE", "NOT_OBSERVED"}:
            errs.append(f"[app] {rid}: visual_evidence.status invalid: {status}")
        frames = vis.get("representative_frames", []) or []
        bundle = vis.get("bundle")
        if bundle and not os.path.isdir(os.path.join(root, bundle)):
            errs.append(f"[app] {rid}: visual evidence bundle missing: {bundle}")
        if status == "HUMAN_VISIBLE":
            if not frames:
                errs.append(f"[app] {rid}: claims HUMAN_VISIBLE with no representative frames (§35)")
            for fr in frames:
                fp = os.path.join(root, str(bundle or ""), str(fr))
                if not os.path.exists(fp):
                    errs.append(f"[app] {rid}: HUMAN_VISIBLE frame file missing: {fr}")
        if status == "NOT_HUMAN_VISIBLE" and not vis.get("note"):
            errs.append(f"[app] {rid}: NOT_HUMAN_VISIBLE without an explanatory note (truthfulness law)")
        # execution claims require an ops session bundle or committed evidence
        if r.get("status") in {"DONE", "TESTED", "OBSERVED"}:
            has_session = False
            for cand in (rid, f"{rid}_golden_fixture"):
                sp = os.path.join(ops_root, cand, "session.json")
                if os.path.exists(sp):
                    has_session = True
                    sess = json.load(open(sp))
                    shas = []
                    for m in (sess.get("frame_metrics") or {}).values():
                        if m.get("png_sha256_16"):
                            shas.append(m["png_sha256_16"])
                    if sess.get("screenshot_sha256_16"):
                        shas.append(sess["screenshot_sha256_16"])
                    if not shas:
                        errs.append(f"[app] {rid}: session bundle has no SHA evidence (§35: evidence with missing SHA)")
                    sums = os.path.join(ops_root, cand, "SHA256SUMS")
                    if os.path.exists(sums):
                        for line in open(sums):
                            if line.strip():
                                fn = line.split("  ")[-1].strip()
                                if not os.path.exists(os.path.join(ops_root, cand, fn)):
                                    errs.append(f"[app] {rid}: broken evidence link in SHA256SUMS: {fn}")
                    break
            if not has_session:
                prim = r.get("evidence", {}).get("primary", []) or []
                if not prim:
                    errs.append(f"[app] {rid}: status {r['status']} but no execution session and no evidence path (§35)")

        # persistence truthfulness
        pv = str((r.get("persistence") or {}).get("verdict", ""))
        if "PASS" in pv.upper() and "relaunch" not in str((r.get("persistence") or {}).get("probe", "")).lower():
            errs.append(f"[app] {rid}: persistence PASS without close/reopen probe (§35)")
        # blocked claims must name the blocker somewhere
        wa = r.get("what_actually_happened") or {}
        if wa.get("BLOCKED") and not r.get("blocker"):
            if "blocker" not in str(r.get("next_task", "")).lower():
                errs.append(f"[app] {rid}: BLOCKED truth section present but blocker field empty (§35)")

    for tid, t in tools.items():
        u = t.get("utilization") or {}
        v = u.get("verdict")
        if v not in {"USED", "RESEARCHED_ONLY", "AVAILABLE_NOT_USED"}:
            errs.append(f"[tool] {tid}: utilization.verdict missing/invalid (§35): {v}")
        if v == "USED" and not (t.get("consumers") or t.get("laws_learned")):
            errs.append(f"[tool] {tid}: marked USED without consumer/law evidence (§35)")

    for lid, l in laws.items():
        u = l.get("utilization") or {}
        v = u.get("verdict")
        if not v:
            errs.append(f"[law] {lid}: utilization block missing (§15/§35)")
            continue
        if v == "USED_BY_EXECUTION" and not u.get("consumer_apps"):
            errs.append(f"[law] {lid}: USED_BY_EXECUTION without consumer apps (§35)")
        if l.get("status") == "VERIFIED" and v == "UNUSED_VERIFIED_LAW" and u.get("consumer_apps"):
            errs.append(f"[law] {lid}: UNUSED_VERIFIED_LAW but consumers recorded — inconsistent (§35)")

    print(f"Compatibility graph validation: {len(apps)} apps, {len(tools)} tools, "
          f"{len(caps)} capabilities, {len(laws)} knowledge records, "
          f"registry roots={registry_roots}")
    if errs:
        print(f"FAIL — {len(errs)} error(s):")
        for e in errs:
            print("  ✗", e)
        sys.exit(1)
    print("PASS — all references, statuses, provenance, evidence paths, registry and index consistency checks green.")
    try:
        for o in oks:
            print("  ·", o)
    except BrokenPipeError:
        pass


if __name__ == "__main__":
    main()
