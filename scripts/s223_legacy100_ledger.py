#!/usr/bin/env python3
"""S223/#585: generate docs/compatibility/legacy_100_audit.{md,csv,json} from the fetched 100 oldest open issues."""
import json, re, os, csv
from collections import Counter, defaultdict

D = "/home/z/my-project/evidence/s223/legacy100"
data = json.load(open(f"{D}/oldest_open_100.json"))
OUT = "/home/z/my-project/docs/compatibility"
os.makedirs(OUT, exist_ok=True)

RUNTIME_HEAD = "62cd00f9+1 (S223 wave, binary 72628d05dbc8f8db)"

def classify(it):
    """Map one issue to the #585 state ladder + first-divergence signature."""
    b = it["body"] or ""
    n = it["number"]
    row = {
        "issue": n,
        "title": it["title"][:110],
        "labels": ",".join(it["labels"][:4]),
        "created": it["created_at"][:10],
        "updated": it["updated_at"][:10],
        "record_state": "",
        "stage_state": "",
        "signature": "",
        "shared_finding": "",
        "next_action": "",
        "closure": "OPEN",
    }
    is_game = "GAME-" in (it["title"] or "")

    # recorded state field from the body
    m = re.search(r"State: `?([A-Z-]+)`?", b)
    if m:
        row["record_state"] = m.group(1)

    if n == 9:
        row["stage_state"] = "CONTROL"
        row["signature"] = "n/a (roadmap issue)"
        row["shared_finding"] = "roadmap pointer; superseded per-wave by the #585 recovery ladder"
        row["next_action"] = "keep as index; wave statuses live in the per-family issues"
        row["closure"] = "OPEN (umbrella)"
        return row

    if n in (11, 12):
        row["stage_state"] = "DONE-PENDING-REVALIDATION"
        row["signature"] = "no open blocker (body: 'Current blocker: None')"
        row["shared_finding"] = "stale-closure bookkeeping (#585 finding 5)"
        row["next_action"] = ("revalidate vs current HEAD pin (ttt pin 7354c1b2 x3 cold runs; "
                              "ConnectFour equivalent pin) then close or state the remaining acceptance gap")
        row["closure"] = "CLOSURE-CANDIDATE"
        return row

    if n == 14:
        row["stage_state"] = "ACTIVE-EXECUTION"
        row["signature"] = "Compose post-NewGame blocker chain; S221/S222 decode wave landed; measure-bridge complete-render config proven (ISE storm 9,757-12,514 -> 0)"
        row["shared_finding"] = "Compose scheduling/measure frontier (#582 S221/S222 chain)"
        row["next_action"] = "complete-render run + pin a0fae907 BLOCKED->PASS transition"
        row["closure"] = "OPEN (active)"
        return row

    if n == 16:
        row["stage_state"] = "BLOCKED"
        row["signature"] = "ApplicationLoader + LifecycleRegistry reached; fragment-host frontier; 540s full-init budget"
        row["shared_finding"] = "Fragment/FragmentManager host family (S225 #16 row)"
        row["next_action"] = "fragment-commit pending-op drain wave (recorded next family in CAMPAIGN_STATE CONT-41)"
        row["closure"] = "OPEN"
        return row

    if n == 22:
        row["stage_state"] = "BLOCKED"
        row["signature"] = "Tile/Service launch contract mismatch (launch family, not Activity)"
        row["shared_finding"] = "Service-launch family"
        row["next_action"] = "reproduce + first-divergence trace of the Service launch path"
        row["closure"] = "OPEN"
        return row

    if n in (19, 20, 21, 23):
        row["stage_state"] = "EXEC-CANDIDATE"
        row["signature"] = ("historical: " + (re.search(r"Failure family: ([^\n]+)", b).group(1)[:90]
                          if re.search(r"Failure family: ([^\n]+)", b) else "layout/anchor or game-logic frontier"))
        row["shared_finding"] = "per-title reproduce -> Stage B first-divergence"
        row["next_action"] = "reproduce vs current HEAD; update first-divergence evidence (#585 immediate batch item 2)"
        row["closure"] = "OPEN"
        return row

    if n == 24:
        row["stage_state"] = "UMBRELLA"
        row["signature"] = "S81 wave: onCreate app-boundary unwind family 19/25 = dominant corpus frontier (F-NEW-156/F-NEW-159)"
        row["shared_finding"] = "onCreate APP-BOUNDARY-UNWIND family + image decode-vs-render (#229)"
        row["next_action"] = "shared-root closure propagation: map every fixed shared law back to affected app records"
        row["closure"] = "OPEN (umbrella)"
        return row

    # GAME-records
    if row["record_state"] == "STATE-NOT-LOADED":
        row["stage_state"] = "NOT-LOADED"
        # pull recorded frontier if present
        fr = re.search(r"(?:Frontier|frontier|Failure|failure)[:\s]+([^\n]+)", b)
        row["signature"] = ("NOT DIAGNOSED - no first failing method recorded"
                            + ("; recorded note: " + fr.group(1)[:80] if fr else ""))
        row["shared_finding"] = "untriaged population (#585 finding 2); Stage A+B required"
        row["next_action"] = "Stage A cold run x3 + Stage B first-divergence trace; cluster by identical signature"
        row["closure"] = "OPEN (triage population)"
    elif row["record_state"] == "STATE-NONBLANK":
        row["stage_state"] = "NONBLANK"
        fam = re.search(r"(F-NEW-\d+|FAIL-[A-Z]+)", b)
        row["signature"] = fam.group(1) if fam else "FAIL family not recorded"
        row["shared_finding"] = ("F-NEW-156 onCreate APP-BOUNDARY-UNWIND shared family"
                                 if (fam and fam.group(1) == "F-NEW-156")
                                 else ("F-NEW-003 shared family" if fam and fam.group(1) == "F-NEW-003" else "common-runtime"))
        row["next_action"] = ("cohort rerun after the shared F-NEW-156 wave (S222-A laws landed: contained-invoke "
                              "exception honesty, F-023b framework-object materialization defaults)")
        row["closure"] = "OPEN (shared-cluster)"
    elif row["record_state"] == "STATE-RENDERED":
        row["stage_state"] = "RENDERED"
        row["signature"] = "rendered frame; visual subchecks (layout/drawables/canvas) PENDING; no state proof"
        row["shared_finding"] = "evidence-threshold inconsistency (#585 finding 3/4)"
        row["next_action"] = "semantic state proof + interaction; do NOT count as complete (#76 rule)"
        row["closure"] = "OPEN (unproven)"
    elif row["record_state"] == "STATE-GRAPHICALLY-NONTRIVIAL":
        row["stage_state"] = "GRAPHICALLY-NONTRIVIAL"
        row["signature"] = "nontrivial graphics reached; interaction/state proof pending"
        row["shared_finding"] = "evidence threshold: render != interactive"
        row["next_action"] = "Stage A/B re-run + interaction proof"
        row["closure"] = "OPEN"
    else:
        row["stage_state"] = "UNCLASSIFIED"
        row["signature"] = "no state field parsed"
        row["next_action"] = "manual triage"
    return row

rows = [classify(it) for it in data]

# ---- ranked shared blocker clusters ----
clusters = Counter(r["shared_finding"] for r in rows if r["shared_finding"])
ranked = sorted(clusters.items(), key=lambda kv: -kv[1])

sig_members = defaultdict(list)
for r in rows:
    sig_members[r["shared_finding"]].append(r["issue"])

CSV_FIELDS = ["issue", "title", "labels", "created", "updated", "record_state",
              "stage_state", "signature", "shared_finding", "next_action", "closure"]

with open(f"{OUT}/legacy_100_audit.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    w.writeheader()
    w.writerows(rows)
json.dump({"runtime_head": RUNTIME_HEAD,
           "generated": "2026-11-12",
           "rows": rows,
           "clusters": [{"finding": k, "count": v, "members": sig_members[k]} for k, v in ranked]},
          open(f"{OUT}/legacy_100_audit.json", "w"), indent=1)

# ---- markdown ----
md = []
md.append("# LEGACY-100 — the 100 oldest open compatibility issues: audit ledger")
md.append("")
md.append(f"*Generated 2026-11-12 for issue **#585**; runtime HEAD `{RUNTIME_HEAD}` (audit data fetched via the GitHub API the same day; states are record states, NOT fresh execution claims).*")
md.append("")
md.append("## Method")
md.append("")
md.append("1. The 100 currently-open issues sorted by `created:asc` were retrieved from the GitHub API (`#9` through `#115`).")
md.append("2. Each record's body/labels/updated-at were parsed for its recorded compatibility state (the `State:` field of the GAME-series reports), failure-family markers, and evidence dates.")
md.append("3. Each record was mapped to the #585 Stage-E state ladder and clustered by SHARED first-divergence finding, not by app title.")
md.append("4. **A record state is historical bookkeeping.** Per the #585 audit rule, a label or historical screenshot is not proof of current compatibility; the `next_action` column defines the work that turns a record into evidence.")
md.append("")
md.append("## Distribution (the one-line summary)")
md.append("")
md.append("| Stage state | Count | Meaning |")
md.append("|---|---|---|")
cnt = Counter(r["stage_state"] for r in rows)
meaning = {
    "NOT-LOADED": "no app content proven; NOT diagnosed (Stage A+B pending)",
    "NONBLANK": "pixels differ from background; FAIL family recorded (lower-level milestone only)",
    "RENDERED": "app-owned content visible; visual subchecks + state proof pending",
    "GRAPHICALLY-NONTRIVIAL": "graphics advanced; interaction/state proof pending",
    "DONE-PENDING-REVALIDATION": "body says blockers resolved; current-HEAD revalidation pending before closure",
    "ACTIVE-EXECUTION": "active decode/fix wave (dooz)",
    "BLOCKED": "exact blocker recorded",
    "EXEC-CANDIDATE": "older EXEC records; reproduce vs current HEAD pending",
    "UMBRELLA": "wave-tracking record",
    "CONTROL": "roadmap index",
    "UNCLASSIFIED": "no state field parsed — manual triage",
}
for k, v in cnt.most_common():
    md.append(f"| {k} | {v} | {meaning.get(k, '')} |")
md.append("")
md.append("## Ranked shared-blocker clusters (fix once, propagate to the cohort)")
md.append("")
md.append("| Rank | Shared finding | Records | Member issues |")
md.append("|---|---|---|---|")
for i, (k, v) in enumerate(ranked, 1):
    members = sig_members[k]
    mtxt = ", ".join(f"#{m}" for m in members[:14])
    if len(members) > 14:
        mtxt += f", … ({len(members)} total)"
    md.append(f"| {i} | {k} | {v} | {mtxt} |")
md.append("")
md.append("**Cluster 1 — F-NEW-156 (onCreate APP-BOUNDARY-UNWIND), %d records — the largest cluster.**" % clusters.get("F-NEW-156 onCreate APP-BOUNDARY-UNWIND shared family", 0))
md.append("")
md.append("This is the same family the #585 body cites via #24 (`19/25 in that wave`). The shared runtime work is ALREADY in flight and must be propagated, not re-invented:")
md.append("")
md.append("* **S222-A laws landed** (commit `eff78882`, gate ALL HOLD): contained nested-invoke exception honesty (APP-BOUNDARY process-death records 54→0 for runtime-injected unwinds), F-023b framework-object materialization defaults (`Configuration.setToDefaults()` face on EVERY `new-instance` path — fontScale/densityDpi/orientation), S221 measure-bridge cadence law (`MINIANDROID_S222_FRAME_BRIDGE=1` = complete-render config).")
md.append("* **S223 wave landed** (this audit's session, binary `72628d05dbc8f8db`, gate ALL HOLD byte-exact, test-all 27/27): NATIVE-001/JNI-001/JNI-002/BITMAP-001/ELF-001 memory+JNI laws, F-NEW-283 stale-cache removal + constructor-failure propagation (inflation honesty — the poisoned-View path the GAME-NONBLANK cohort dies through), LOG-001/003/004/005/007 stage-truth laws, CALL-001..004 trace enrichment.")
md.append("* **Next:** cohort rerun of the F-NEW-156 members after the wave lands; each affected GAME record then gets its before/after delta per Stage D.")
md.append("")
md.append("## The per-record ledger (100 rows)")
md.append("")
md.append("| # | Title | Record state | Stage state | First-divergence signature | Shared finding | Next action |")
md.append("|---|---|---|---|---|---|---|")
for r in rows:
    md.append(f"| #{r['issue']} | {r['title'][:46]} | {r['record_state'] or '—'} | {r['stage_state']} | {r['signature'][:60]} | {r['shared_finding'][:40]} | {r['next_action'][:60]} |")
md.append("")
md.append("## Closure candidates (the #585 immediate batch, item 1)")
md.append("")
md.append("* **#11 TicTacToe / #12 ConnectFour** — both bodies state the previous blockers are resolved (`Current blocker: None`). The runtime side keeps byte-exact HOLD pins for the family (`ttt 7354c1b2` ×3 cold runs on binary `72628d05dbc8f8db`, 0 uncaught exceptions — same-day evidence). Closure rule per #585 Stage E: a fresh current-HEAD acceptance run against each issue's own checklist, then close with the run linked — the ledger marks both `CLOSURE-CANDIDATE`.")
md.append("")
md.append("## What this ledger does NOT claim")
md.append("")
md.append("* No fresh APK execution happened for the 100 records in this audit pass (the audit is record triage, exactly as #585 allows: `This is a triage/audit of GitHub records, not a claim that all 100 APKs were freshly executed`).")
md.append("* The 64 `NOT-LOADED` records are a TRIAGE POPULATION with no first-divergence evidence; they are not 64 individual bugs.")
md.append("* The same-day S223 wave evidence (gate pins, 27/27 tests) covers the shared runtime laws, not per-record app acceptance.")
open(f"{OUT}/legacy_100_audit.md", "w").write("\n".join(md))
print("written:", OUT)
print("cluster ranking:", [(k[:50], v) for k, v in ranked[:6]])
