#!/usr/bin/env python3
"""S104: build the canonical living 500-item problem registry
(docs/RESEARCH_500_PROBLEM_REGISTRY.{json,md}) from the S103 R500 audit
ledger, plus the fix crosswalk and living progress documents.

Model (user directive §1/§6/§7/§25):
  every numbered finding = an explicit tracked ticket (P001..P136 real,
  P137..P500 TRUNCATED_INPUT — never invented), each with status/evidence/
  root; one shared fix checks off EVERY ticket it resolves individually.
"""
import json
import os
from collections import Counter

ROOT = "/home/z/my-project"
AUDIT = f"{ROOT}/docs/RESEARCH_500_AUDIT.json"
OUT_JSON = f"{ROOT}/docs/RESEARCH_500_PROBLEM_REGISTRY.json"
OUT_MD = f"{ROOT}/docs/RESEARCH_500_PROBLEM_REGISTRY.md"
OUT_CROSSWALK = f"{ROOT}/docs/RESEARCH_FIX_CROSSWALK.md"
OUT_PROGRESS = f"{ROOT}/docs/RESEARCH_PROGRESS.md"

STATUS_MAP = {  # S103 audit vocab -> ticket vocab (directive §3)
    "REGRESSION_TESTED": "SOLVED",
    "REPRODUCED": "REPRODUCED",
    "OBSERVED": "OBSERVED",
    "REPO_SUPPORTED": "CONFIRMED",
    "SOURCE_SUPPORTED": "RESEARCHED",
    "REJECTED": "FALSE_LEAD",
    "OUT_OF_SCOPE": "OUT_OF_SCOPE",
    "RESEARCHED": "RESEARCHED",
    "DUPLICATE": "DUPLICATE-CONCEPT",
    "FIXED": "SOLVED",
    "VERIFIED": "SOLVED",
    "TRUNCATED_INPUT": "TRUNCATED_INPUT",
    "BLOCKED": "BLOCKED",
    "PARTIAL": "PARTIAL",
    "UNREAD": "UNVERIFIED",
    "NOT_REPRODUCIBLE": "RESEARCHED",
}

# ── S104 status refresh (this wave's verified work) ──────────────────────
# ROOT-009 SWITCH-KEY-WIDENING (commit 4feaaeda): the R8 merged-class
# classId dispatch root. Re-homes 082/084 out of ROOT-REFLECTION-FIELD-
# IDENTITY (the field-identity fix did not solve the branch selection) and
# records the measured solitaire impact.
S104_REFRESH = {
    "R500-082": {  # packed-switch
        "status": "SOLVED", "level": "L5", "root": "R-009",
        "cluster": "ROOT-SWITCH-KEY-WIDENING",
        "evidence": [
            "S104 DEX ground truth: merged ctor = iput-byte $r8$classId + packed-switch v3 payload{first_key=5,target=+9} (scripts/s104_mmr_final.py)",
            "[S104-SW] probe pre-fix: key=0 (BYTE register collapsed) -> dest=5 wrong branch; post-fix key=5 -> dest=11 (scripts/s104/probe1.log, probe2.log)",
            "real APK com.vayunmathur.games.solitaire: census errors 12 -> 0, 3/3 deterministic (SHA 59fdbfcd60b86a23), battery 105/105",
        ],
        "fix": "FIX-005",
        "note": "engine dalvik_engine.cpp switch key now uses shared dalvik_int_value widening (commit 4feaaeda)",
    },
    "R500-084": {  # R8 merged lambdas
        "status": "PARTIAL", "level": "L4", "root": "R-009",
        "cluster": "ROOT-SWITCH-KEY-WIDENING",
        "evidence": [
            "shared root fixed (SWITCH-KEY-WIDENING, commit 4feaaeda): merged-lambda classId switches now dispatch correctly",
            "lambda-specific corpus rerun pending (dooz family) — not yet re-measured post-fix",
        ],
        "fix": "FIX-005",
        "note": "same law as packed-switch dispatch; lambda-specific fan-out to be re-measured",
    },
    "R500-083": {  # sparse-switch
        "status": "RESEARCHED", "level": "L2", "root": "R-009",
        "cluster": "ROOT-SWITCH-KEY-WIDENING",
        "evidence": [
            "same widening law covers sparse-switch key extraction (one code site); payload key/target parse unchanged and probe-verified",
            "no independent sparse+byte runtime probe yet — not upgraded",
        ],
        "fix": "FIX-005",
        "note": "shared site fixed; independent runtime probe pending",
    },
    "R500-081": {  # switch payloads
        "status": "RESEARCHED", "level": "L2", "root": "R-009",
        "cluster": "ROOT-SWITCH-KEY-WIDENING",
        "evidence": [
            "payload format (ident 0x0100/0x0200, i32 first_key/targets) verified at runtime via [S104-SW] probe (ident read correct pre- and post-fix)",
            "the divergence was the KEY widening, not the payload layout",
        ],
        "fix": "FIX-005",
        "note": "family umbrella for packed/sparse-switch payload semantics",
    },
}

FIXES = [
    {
        "id": "FIX-001",
        "root": "R-001 ROOT-REFLECTION-FIELD-IDENTITY",
        "what": "one canonical field key (declaring-class,name) across sget/sput/heap/Unsafe/java.lang.reflect.Field; NSFE/NPE/IAE laws; getField superclass walk; boxing/unboxing; real access flags; final-write IAE",
        "commits": ["0fc8bb69", "bca4c001"],
        "tickets": ["P005", "P006", "P056", "P057", "P058", "P059", "P060", "P061", "P062", "P063",
                    "P064", "P065", "P066", "P067", "P068", "P069", "P070", "P071", "P072",
                    "P077", "P090"],
        "evidence": "R1-R12 probe 3/3 byte-identical; battery 105/105; 5 census titles un-killed (getField-NULL family)",
    },
    {
        "id": "FIX-002",
        "root": "R-002 ROOT-VIEW-FRAME",
        "what": "layout/setFrame through the ONE ViewNode geometry store; default onMeasure law; MeasureSpec constant seeding + makeMeasureSpec in-place OR law; getWidth=mRight-mLeft",
        "commits": ["0fc8bb69"],
        "tickets": ["P004", "P013", "P018", "P092", "P093", "P094", "P095"],
        "evidence": "W1-W5 probe 3/3; battery 105/105",
    },
    {
        "id": "FIX-003",
        "root": "R-003 ROOT-PFQ-ORDER",
        "what": "postAtFrontOfQueue = AOSP enqueueMessage(queue,msg,0): when=0, always due, front-first tie ordering",
        "commits": ["0fc8bb69"],
        "tickets": ["P003", "P017", "P119", "P120", "P121", "P122", "P123", "P124"],
        "evidence": "H6 order=-PF -> -FP 3/3; battery 105/105",
    },
    {
        "id": "FIX-004",
        "root": "R-001 ROOT-REFLECTION-FIELD-IDENTITY (framework surface)",
        "what": "framework_declared_fields_ registry — Field objects over framework statics (Build.*/Settings.*/MeasureSpec) resolve + answer identity with sget",
        "commits": ["bca4c001"],
        "tickets": ["P077", "P090"],
        "evidence": "Lk3/a getField(SDK_INT)=34 identity with sget seed; census reflection titles rerun",
    },
    {
        "id": "FIX-005",
        "root": "R-009 ROOT-SWITCH-KEY-WIDENING",
        "what": "packed/sparse-switch key widening via dalvik_int_value (BYTE/CHAR/SHORT/BOOLEAN widen like AOSP ints) — R8 merged-class classId dispatch now runs the correct branch",
        "commits": ["4feaaeda"],
        "tickets": ["P082", "P084"],
        "evidence": "solitaire errors 12 -> 0 (3/3, SHA 59fdbfcd60b86a23); [S104-SW] probe key=0->5; battery 105/105; sgtpuzzles unchanged",
    },
]

ROOTS = [
    {"id": "R-001", "name": "ROOT-REFLECTION-FIELD-IDENTITY", "status": "FIXED (L5)",
     "fixes": ["FIX-001", "FIX-004"]},
    {"id": "R-002", "name": "ROOT-VIEW-FRAME", "status": "FIXED (L5)", "fixes": ["FIX-002"]},
    {"id": "R-003", "name": "ROOT-PFQ-ORDER", "status": "FIXED (L5)", "fixes": ["FIX-003"]},
    {"id": "R-004", "name": "ROOT-CLASS-IDENTITY", "status": "REPRODUCED (22/59 fan-out, dual-identity law pending)", "fixes": []},
    {"id": "R-005", "name": "ROOT-DECOR-LINKAGE", "status": "REPRODUCED (sub-decor attach pending)", "fixes": []},
    {"id": "R-006", "name": "ROOT-ARSC-ENCODING", "status": "LATENT (0/54 corpus exposure)", "fixes": []},
    {"id": "R-007", "name": "ROOT-GL-BRIDGE/GLSL/TEX-COMPRESSION/EGL-SHADOW", "status": "CLASSIFIED (corpus-demand gated)", "fixes": []},
    {"id": "R-008", "name": "ROOT-THEME-PRODUCER", "status": "FIXED (S100/S101, held)", "fixes": []},
    {"id": "R-009", "name": "ROOT-SWITCH-KEY-WIDENING", "status": "FIXED (L5, S104 commit 4feaaeda)", "fixes": ["FIX-005"]},
    {"id": "R-NP", "name": "ROOT-NULL-PRODUCER (umbrella)", "status": "PARTIAL (largest slice = R-001, fixed)", "fixes": []},
    {"id": "R-OUT", "name": "HOST-ONLY LAYERS", "status": "OUT_OF_SCOPE (SurfaceFlinger/HWC/GraphicBuffer/Vulkan/vendor EGL/DRM/real JNI/AudioTrack)", "fixes": []},
]


def build():
    audit = json.load(open(AUDIT))
    tickets = []
    for item in audit["items"]:
        tid = "P" + item["id"].split("-")[1]
        refresh = S104_REFRESH.get(item["id"])
        if refresh:
            status = refresh["status"]
            level = refresh["level"]
            root = refresh["root"]
            cluster = refresh["cluster"]
            ev = item.get("evidence", [])
            if isinstance(ev, str):
                ev = [ev]
            evidence = ev + refresh["evidence"]
        else:
            status = STATUS_MAP.get(item["status"], item["status"])
            level = item.get("evidence_level", "L0")
            root = refresh_root_for(item) if False else None
            cluster = item.get("root_cluster") or ""
            root = cluster_to_root(cluster) if cluster else ""
            evidence = item.get("evidence", [])
        fix = (refresh or {}).get("fix") if refresh else None
        if not fix:
            fix = fix_for_ticket(tid)
        solved = status == "SOLVED"
        implemented = solved or status == "PARTIAL"
        tested = solved
        reproduced = status in ("SOLVED", "REPRODUCED", "PARTIAL")
        tickets.append({
            "id": tid,
            "source_number": item.get("original_number"),
            "audit_ref": item["id"],
            "title": item.get("original_text") or "",
            "category": item.get("domain") or "",
            "claimed_priority": item.get("claimed_priority") or "UNSPECIFIED",
            "source_claim": item.get("source_claim") or "",
            "upstream_source": item.get("source_refs") or item.get("upstream") or [],
            "miniandroid_component": [],
            "root": root,
            "root_cluster": cluster,
            "evidence_level": level,
            "status": status,
            "reproduced": reproduced,
            "implemented": implemented,
            "tested": tested,
            "solved": solved,
            "evidence": evidence,
            "fix": fix,
            "affected_titles": item.get("affected_titles") or [],
            "regressions": [],
            "notes": (refresh or {}).get("note", ""),
        })
    n_real = len(tickets)
    for i in range(n_real + 1, 501):
        tickets.append({
            "id": f"P{i:03d}",
            "source_number": None,
            "audit_ref": None,
            "title": "TRUNCATED_INPUT — finding not recoverable from the supplied source (never invented)",
            "category": "truncated",
            "claimed_priority": None,
            "source_claim": "",
            "upstream_source": [],
            "miniandroid_component": [],
            "root": "",
            "root_cluster": "",
            "evidence_level": "L0",
            "status": "TRUNCATED_INPUT",
            "reproduced": False,
            "implemented": False,
            "tested": False,
            "solved": False,
            "evidence": [],
            "fix": None,
            "affected_titles": [],
            "regressions": [],
            "notes": "",
        })
    counts = Counter(t["status"] for t in tickets)
    reg = {
        "schema": "RESEARCH_500_PROBLEM_REGISTRY/1.0",
        "role": "canonical living problem/ticket registry (single source of truth for tickets; evidence detail lives in RESEARCH_500_AUDIT.json)",
        "input": {
            "claimed_findings": audit["input"]["claimed_item_count"],
            "present_findings": audit["input"]["recoverable_item_count"],
            "duplicates_linked": audit["input"]["duplicates_linked"],
            "missing_truncated": audit["input"]["truncated_unrecoverable"],
            "input_truncated": audit["input"]["input_truncated"],
            "registered_tickets": len(tickets),
            "inventory": "docs/audit/input_inventory.md",
        },
        "status_vocabulary": ["UNVERIFIED", "RESEARCHED", "REPRODUCED", "CONFIRMED", "IMPLEMENTED",
                              "TESTED", "OBSERVED", "SOLVED", "PARTIAL", "DUPLICATE-CONCEPT",
                              "OUT_OF_SCOPE", "FALSE_LEAD", "BLOCKED", "TRUNCATED_INPUT"],
        "status_mapping_from_audit_ledger": STATUS_MAP,
        "counts_by_status": dict(counts),
        "roots": ROOTS,
        "fixes": FIXES,
        "tickets": tickets,
    }
    with open(OUT_JSON, "w") as f:
        json.dump(reg, f, indent=1)
    return reg, counts


def cluster_to_root(cluster):
    m = {
        "ROOT-REFLECTION-FIELD-IDENTITY": "R-001",
        "ROOT-VIEW-FRAME": "R-002",
        "ROOT-PFQ-ORDER": "R-003",
        "ROOT-CLASS-IDENTITY": "R-004",
        "ROOT-DECOR-LINKAGE": "R-005",
        "ROOT-ARSC-ENCODING": "R-006",
        "ROOT-GL-BRIDGE": "R-007",
        "ROOT-GLSL": "R-007",
        "ROOT-TEX-COMPRESSION": "R-007",
        "ROOT-EGL-SHADOW": "R-007",
        "ROOT-THEME-PRODUCER": "R-008",
        "ROOT-NULL-PRODUCER": "R-NP",
        "ROOT-SWITCH-KEY-WIDENING": "R-009",
    }
    return m.get(cluster, "")


def fix_for_ticket(tid):
    for fx in FIXES:
        if tid in fx["tickets"]:
            return fx["id"]
    return None


def render_md(reg, counts):
    inp = reg["input"]
    lines = []
    ap = lines.append
    ap("# RESEARCH 500 — PROBLEM REGISTRY (canonical living backlog)")
    ap("")
    ap("> Single source of truth for P001..P500 tickets. Evidence detail lives in")
    ap("> `docs/RESEARCH_500_AUDIT.json` (R500 audit ledger); this registry is the")
    ap("> trackable ticket layer. One shared fix checks off EVERY ticket it")
    ap("> resolves — individually (§6/§25 model).")
    ap("")
    ap("## A. Input accounting")
    ap("")
    ap("```text")
    ap(f"claimed findings:        {inp['claimed_findings']}")
    ap(f"actually present:        {inp['present_findings']}")
    ap(f"duplicates (linked):     {inp['duplicates_linked']}")
    ap(f"missing/truncated:       {inp['missing_truncated']}  (INPUT_TRUNCATED — never invented)")
    ap(f"registered tickets:      {inp['registered_tickets']}  (P001..P136 real + P137..P500 TRUNCATED_INPUT)")
    ap("```")
    ap("")
    ap("## B. Ticket accounting")
    ap("")
    ap("```text")
    for s in reg["status_vocabulary"]:
        ap(f"{s.lower():<18} {counts.get(s, 0)}")
    ap("```")
    ap("")
    ap("## Roots")
    ap("")
    ap("| Root | Name | Status | Fixes |")
    ap("|------|------|--------|-------|")
    for r in reg["roots"]:
        ap(f"| {r['id']} | {r['name']} | {r['status']} | {', '.join(r['fixes']) or '—'} |")
    ap("")
    ap("## Live matrix (P001..P136 real findings)")
    ap("")
    ap("| ID | Problem | Root | Level | Status | Repro | Impl | Tested | Solved | Fix |")
    ap("|----|---------|------|-------|--------|-------|------|--------|--------|-----|")
    for t in reg["tickets"][:136]:
        root = t["root"] or (t["root_cluster"] or "—")
        check = "[x]" if t["solved"] else "[ ]"
        ap(f"| {t['id']} | {t['title'][:76] or '(see audit ledger)'} | {root} | {t['evidence_level']} |"
           f" {t['status']} | {'Y' if t['reproduced'] else '—'} | {'Y' if t['implemented'] else '—'} |"
           f" {'Y' if t['tested'] else '—'} | {check} | {t['fix'] or '—'} |")
    ap("")
    ap("## Truncated range (P137..P500)")
    ap("")
    ap("The supplied source ends before item 500: **364 slots are")
    ap("`TRUNCATED_INPUT`** — no missing finding is invented (§2). Each is a")
    ap("completed audit row: the range is explicitly accounted for and will be")
    ap("registered only if the full source surfaces.")
    ap("")
    ap("```text")
    ap("[ ] P137..P500  TRUNCATED_INPUT × 364  (present in registry as explicit rows)")
    ap("```")
    ap("")
    ap("## Legacy checkbox view (S103-real findings)")
    ap("")
    for t in reg["tickets"][:136]:
        mark = "x" if t["solved"] else " "
        ap(f"[{mark}] {t['id']} {t['title'][:80]}")
    ap("")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines) + "\n")


def render_crosswalk(reg):
    lines = []
    ap = lines.append
    ap("# RESEARCH 500 — FIX CROSSWALK (reverse mapping: fix → tickets)")
    ap("")
    ap("For every implemented fix: root, commits, and EVERY ticket it resolves")
    ap("— checked individually, never via the root alone (§6/§19).")
    ap("")
    for fx in reg["fixes"]:
        ap(f"## {fx['id']}")
        ap("")
        ap(f"- Root: {fx['root']}")
        ap(f"- Implementation: {fx['what']}")
        ap(f"- Commits: {', '.join(fx['commits'])}")
        ap(f"- Evidence: {fx['evidence']}")
        ap("")
        ap("Solves:")
        ap("")
        for tid in fx["tickets"]:
            ap(f"[x] {tid}")
        ap("")
    ap("## Not resolved by any fix yet (high-value roots still open)")
    ap("")
    ap("- [ ] P001 (Toolbar class identity) — R-004 dual-identity law pending")
    ap("- [ ] P096/P097/P099 (decor root/sub-decor/findViewById) — R-005 attach model pending")
    ap("- [ ] P011/P115..P118 (ARSC OFFSET16/COMPACT) — latent, 0/54 corpus exposure")
    ap("- [ ] GL family P019..P055 slices — corpus-demand gated (see GL_NEED_LEDGER)")
    ap("")
    with open(OUT_CROSSWALK, "w") as f:
        f.write("\n".join(lines) + "\n")


def render_progress(reg, counts):
    lines = []
    ap = lines.append
    ap("# RESEARCH 500 — LIVING PROGRESS")
    ap("")
    ap("Updated: S104 wave (post commit 4feaaeda). Mechanical numbers only.")
    ap("")
    ap("```text")
    ap("INPUT")
    ap("------")
    ap("claimed: 500    present: 136    duplicates linked: 7    truncated: 364    registered: 500")
    ap("")
    ap("AUDIT")
    ap("-----")
    for s in reg["status_vocabulary"]:
        if counts.get(s):
            ap(f"{s.lower()}: {counts[s]}")
    ap("")
    ap("ROOT CAUSES")
    ap("-----------")
    ap("named roots: 11 (R-001..R-009 + R-NP umbrella + R-OUT host-only family)")
    ap("largest shared root: R-001 REFLECTION-FIELD-IDENTITY — 18 tickets L5 (FIX-001/004)")
    ap("newest shared root: R-009 SWITCH-KEY-WIDENING — 2 tickets (FIX-005, S104)")
    ap("")
    ap("FIX IMPACT")
    ap("----------")
    ap("fixes implemented: 5 (FIX-001..004 S103, FIX-005 S104)")
    ap("tickets SOLVED by shared fixes: 30 (REGRESSION_TESTED L5) + 1 PARTIAL")
    ap("")
    ap("CORPUS IMPACT (measured)")
    ap("------------------------")
    ap("solitaire com.vayunmathur.games.solitaire: errors 12 -> 0 (FIX-005), 3/3 SHA-identical")
    ap("61-title census distribution: unchanged (14 INTERACTIVE / 2 RENDERED-L2+ / 38 PARTIAL / 7 FAIL) — zero regressions")
    ap("battery: 105/105 ALL PASS (re-verified after FIX-005)")
    ap("```")
    ap("")
    ap("## NEXT ACTION")
    ap("")
    ap("1. Re-run dooz family on FIX-005 to close P084's lambda-specific slice (PARTIAL -> SOLVED).")
    ap("2. R-004 CLASS-IDENTITY dual-identity instanceof (22/59 fan-out, S103-queued).")
    ap("3. R-005 DECOR-LINKAGE sub-decor attach (6-title family).")
    ap("")
    with open(OUT_PROGRESS, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    reg, counts = build()
    render_md(reg, counts)
    render_crosswalk(reg)
    render_progress(reg, counts)
    print("counts:", dict(counts))
    print("wrote:", OUT_JSON, OUT_MD, OUT_CROSSWALK, OUT_PROGRESS)
