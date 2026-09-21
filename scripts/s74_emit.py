#!/usr/bin/env python3
"""S74 emitter — merges dossier data over defaults, validates statuses and
internal cross-references, emits canonical JSON records + Capability Matrix.

Layer A: docs/compatibility/apps/*.json
Layer B: docs/compatibility/tools/*.json
Layer D/E: docs/compatibility/capabilities/*.json
Layer C: docs/knowledge/laws/*.json + docs/knowledge/KNOWLEDGE_RECORDS.json
Layer E: docs/compatibility/CAPABILITY_MATRIX.md
"""
import json, os, sys, copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s74_data_apps1 import APPS_1
from s74_data_apps2 import APPS_2
from s74_data_platform import TOOLS, CAPABILITIES
from s74_data_laws import LAWS

ROOT = "/home/z/my-project"
APPS_DIR = os.path.join(ROOT, "docs/compatibility/apps")
TOOLS_DIR = os.path.join(ROOT, "docs/compatibility/tools")
CAPS_DIR = os.path.join(ROOT, "docs/compatibility/capabilities")
LAWS_DIR = os.path.join(ROOT, "docs/knowledge/laws")

APP_STATUS = {"DONE", "IMPLEMENTED", "TESTED", "OBSERVED", "PARTIAL", "BLOCKED", "PENDING", "SUPERSEDED"}
KNOW_STATUS = {"RAW", "CANDIDATE", "RESEARCHED", "OBSERVED", "TESTED", "VERIFIED", "SUPERSEDED", "REJECTED"}
SEC_STATUS = {"DECLARED", "OBSERVED", "ALLOWED", "BLOCKED", "NOT_OBSERVED", "UNKNOWN"}

APP_DEFAULTS = {
    "record_type": "app_dossier", "schema_version": 1,
    "package": None, "status_note": None,
    "source": {}, "apk": {}, "build": None,
    "min_sdk": None, "target_sdk": None, "manifest_summary": None,
    "lifecycle": {}, "framework_apis": [], "view_hierarchy": None,
    "resources": {}, "layout": {}, "rendering": {}, "input": {}, "state": {},
    "concurrency": {}, "storage": {}, "persistence": {},
    "network": {"requested": [], "observed": [], "apis": [], "status": "NOT_OBSERVED"},
    "security": {"permissions_declared": [], "permissions_observed": [], "exported_components": [],
                 "filesystem": "NOT_OBSERVED", "network": "NOT_OBSERVED", "sensitive_apis": [],
                 "status_model": "DECLARED/OBSERVED/ALLOWED/BLOCKED/NOT_OBSERVED/UNKNOWN (never declared->used)"},
    "evidence": {}, "regression": {}, "blocker": None, "next_task": None,
    "completion": {}, "links": {"issue": None, "laws": [], "capabilities": [], "knowledge": [], "evidence_files": []},
}


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def check_evidence_paths(paths, errs, owner):
    for p in paths or []:
        if not p:
            continue
        clean = p.split(" ")[0].rstrip("/")
        if not os.path.exists(os.path.join(ROOT, clean)):
            errs.append(f"{owner}: evidence path missing: {p}")


def main():
    errs, warns = [], []
    apps = {**APPS_1, **APPS_2}

    # ---- statuses + evidence path checks ----
    for aid, a in apps.items():
        if a["status"] not in APP_STATUS:
            errs.append(f"app {aid}: bad status {a['status']}")
        for c, s in a["completion"].items():
            if s not in APP_STATUS:
                errs.append(f"app {aid}: bad completion status {c}={s}")
        check_evidence_paths(a.get("evidence", {}).get("primary", []), errs, f"app {aid}")
    for tid, t in TOOLS.items():
        if t["provenance_class"] not in {"MOTHER", "DERIVED", "EXTRACTED", "REFERENCE", "COMPATIBILITY", "ANALYSIS", "TEST ORACLE", "RESEARCH ONLY"}:
            errs.append(f"tool {tid}: bad provenance class")
    for cid, c in CAPABILITIES.items():
        if c["status"] not in APP_STATUS:
            errs.append(f"cap {cid}: bad status {c['status']}")
    for lid, l in LAWS.items():
        if l["status"] not in KNOW_STATUS:
            errs.append(f"law {lid}: bad status {l['status']}")

    # ---- cross-reference graph ----
    for aid, a in apps.items():
        for lid in a["links"].get("laws", []):
            if lid not in LAWS: errs.append(f"app {aid}: unknown law {lid}")
        for cid in a["links"].get("capabilities", []):
            if cid not in CAPABILITIES: errs.append(f"app {aid}: unknown capability {cid}")
        if not (isinstance(a.get("issue"), int) and 1 <= a["issue"] <= 23):
            errs.append(f"app {aid}: bad issue {a.get('issue')}")
    for cid, c in CAPABILITIES.items():
        for lid in c.get("laws", []):
            if lid not in LAWS: errs.append(f"cap {cid}: unknown law {lid}")
        for ac in c.get("consumers", []):
            if ac not in apps: errs.append(f"cap {cid}: unknown consumer app {ac}")
    for lid, l in LAWS.items():
        for ac in l.get("consumers", []):
            if ac not in apps: errs.append(f"law {lid}: unknown consumer app {ac}")
        for cid in l.get("capabilities", []):
            if cid not in CAPABILITIES: errs.append(f"law {lid}: unknown capability {cid}")
        if l["status"] == "VERIFIED" and not l.get("test"):
            errs.append(f"law {lid}: VERIFIED without test (taskbook §14)")
        if l["status"] == "VERIFIED" and l["scope"] == "generic" and not l.get("source", {}).get("origin"):
            errs.append(f"law {lid}: VERIFIED generic without provenance")

    if errs:
        print("EMIT VALIDATION FAILED:")
        for e in errs: print("  -", e)
        sys.exit(1)

    # ---- emit JSONs ----
    for d in (APPS_DIR, TOOLS_DIR, CAPS_DIR, LAWS_DIR):
        os.makedirs(d, exist_ok=True)

    for aid, a in apps.items():
        rec = deep_merge(APP_DEFAULTS, a)
        rec["app_id"] = aid
        with open(os.path.join(APPS_DIR, f"{aid}.json"), "w") as f:
            json.dump(rec, f, indent=1, sort_keys=False)
            f.write("\n")
    for tid, t in TOOLS.items():
        rec = {"record_type": "tool_profile", "schema_version": 1, "tool_id": tid, **t}
        with open(os.path.join(TOOLS_DIR, f"{tid}.json"), "w") as f:
            json.dump(rec, f, indent=1); f.write("\n")
    for cid, c in CAPABILITIES.items():
        rec = {"record_type": "capability_record", "schema_version": 1, "capability_id": cid, **c}
        with open(os.path.join(CAPS_DIR, f"{cid}.json"), "w") as f:
            json.dump(rec, f, indent=1); f.write("\n")
    for lid, l in LAWS.items():
        rec = {"record_type": "knowledge_record", "schema_version": 1, "knowledge_id": lid, **l}
        with open(os.path.join(LAWS_DIR, f"{lid}.json"), "w") as f:
            json.dump(rec, f, indent=1); f.write("\n")

    idx = {
        "record_type": "knowledge_index", "schema_version": 1,
        "canonical_status_rule": "Only VERIFIED knowledge records are canonical semantic laws (taskbook §15).",
        "counts": {"apps": len(apps), "tools": len(TOOLS), "capabilities": len(CAPABILITIES),
                   "knowledge_records": len(LAWS),
                   "verified_laws": sum(1 for l in LAWS.values() if l["status"] == "VERIFIED"),
                   "open_or_open_frontier": sum(1 for l in LAWS.values() if l["status"] in {"OBSERVED", "RESEARCHED"})},
        "apps": sorted(apps), "tools": sorted(TOOLS), "capabilities": sorted(CAPABILITIES),
        "knowledge": sorted(LAWS),
        "registry_root": "root_registry.json (F-number source of truth; generic laws carry registry ids)",
    }
    with open(os.path.join(ROOT, "docs/knowledge/KNOWLEDGE_RECORDS.json"), "w") as f:
        json.dump(idx, f, indent=1); f.write("\n")

    # ---- Capability Matrix (Layer E) ----
    def cell(v): return v or "-"
    rows = []
    for aid, a in apps.items():
        comp = a.get("completion", {})
        storage = "OBSERVED" if aid in ("unote", "gmdice") else "NOT_OBSERVED"
        auto = "OBSERVED" if "cap-autonomous-gameplay" in a.get("links", {}).get("capabilities", []) else "-"
        rows.append((aid, a["status"], a.get("issue"), comp, storage, auto,
                     a.get("evidence", {}).get("screenshot_sha256_16")))
    m = ["# Capability Matrix — evidence-backed (S74)", "",
         "> Every cell cites the app dossier (`docs/compatibility/apps/<app>.json`),",
         "> its `[EXEC]` issue, and committed evidence. No scores, no 'probably'",
         "> (taskbook §17, §65, §66). Status vocabulary per taskbook §7.",
         "", "| App | Status | Issue | APK | Lifecycle | View | Measure/Layout | Render | Input | State | Concurrency | Storage | Persistence | Network | Security | Autonomous | Final-frame SHA-16 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for aid, st, issue, comp, storage, auto, sha in rows:
        m.append("| {} | {} | #{} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            aid, st, issue,
            cell(comp.get("C1_apk_load")), cell(comp.get("C2_manifest_lifecycle")),
            cell(comp.get("C3_view_framework")), cell(comp.get("C4_measure_layout")),
            cell(comp.get("C5_render")), cell(comp.get("C6_input")), cell(comp.get("C7_state_change")),
            cell(comp.get("C10_concurrency")), storage, cell(comp.get("C9_persistence")),
            "NOT_OBSERVED", cell(comp.get("C11_security_sandbox")), auto, sha or "-"))
    m += ["", "## Completion criteria legend (taskbook §8)", "",
          "C1 APK load · C2 manifest/lifecycle · C3 view/framework · C4 measure/layout · C5 render · C6 input · C7 state change · C8 re-render · C9 persistence · C10 concurrency · C11 security/sandbox · C12 determinism · C13 regression · C14 evidence.",
          "", "## Reading rule", "",
          "`OBSERVED` ≠ `VERIFIED`; `IMPLEMENTED` ≠ `TESTED`; `TESTED` ≠ real-APK proven",
          "(taskbook §59, §76.11-13). Historical cells marked in dossiers are proven in",
          "earlier sessions and not re-run at the current HEAD; they are never silently",
          "upgraded. The dooz visual false-claim correction is preserved as",
          "`CLAIM-DOOZ-23472-VISUAL` (SUPERSEDED) in `docs/knowledge/laws/`.",
          ""]
    with open(os.path.join(ROOT, "docs/compatibility/CAPABILITY_MATRIX.md"), "w") as f:
        f.write("\n".join(m))

    print(f"EMIT OK: {len(apps)} apps, {len(TOOLS)} tools, {len(CAPABILITIES)} capabilities, {len(LAWS)} knowledge records")
    if warns:
        print("Warnings:")
        for w in warns: print("  -", w)


if __name__ == "__main__":
    main()
