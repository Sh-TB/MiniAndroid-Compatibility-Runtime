#!/usr/bin/env python3
"""S188 Phase A: snapshot named issues + seed the adoption ledger from current HEAD state."""
import subprocess, json, urllib.request, sys, os, collections

REPO_DIR = "/home/z/my-project"
out = subprocess.run(["git", "credential", "fill"],
    input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, cwd=REPO_DIR).stdout
token = None
for line in out.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]
if not token:
    sys.exit("NO TOKEN")
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "s188-phase-a"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HDRS)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

NAMED = {
    536: "S185 SQLITE RULE (governing law)", 529: "Coder D source audit", 530: "Coder D related",
    472: "Achievement Ledger", 519: "Coder 8 concurrency", 533: "Coder 8 concurrency (2)",
    520: "Coder 7 PM/SQLite", 521: "Coder 9 resources/images", 528: "Coder 4 framework/Java",
    534: "Coder 4 W13", 538: "Coder 4 W13 results", 537: "Coder 3 image pipeline/ListView",
    540: "Coder 3 libGDX AssetManager laws", 539: "main integration & frontier inventory",
    475: "TicTacToe tracker", 441: "Mindustry", 470: "Mindustry (2)", 492: "Main dashboard",
}
snapshot = {}
for num, role in NAMED.items():
    try:
        it = api(f"/repos/{REPO}/issues/{num}")
        snapshot[num] = {"role": role, "title": it["title"], "state": it["state"],
                         "comments": it["comments"], "updated_at": it["updated_at"],
                         "url": it["html_url"]}
        print(f"#{num} [{it['state']}] {it['comments']:>4} comments | {it['title'][:60]}")
    except Exception as e:
        snapshot[num] = {"role": role, "error": str(e)}
        print(f"#{num} ERROR {e}")

os.makedirs(f"{REPO_DIR}/reports/s188", exist_ok=True)
with open(f"{REPO_DIR}/reports/s188/phase_a_issue_snapshot.json", "w") as f:
    json.dump({"generated": "2026-11-07", "purpose": "S188 Phase A reconciliation input",
               "issues": snapshot}, f, indent=1)

# battery state from S186i evidence
battery_path = f"{REPO_DIR}/evidence/s186_s107/S186I_BATTERY.json"
battery_summary = None
if os.path.exists(battery_path):
    b = json.load(open(battery_path))
    rows = b if isinstance(b, list) else b.get("titles", b.get("results", []))
    if isinstance(rows, dict):
        rows = list(rows.values())
    tiers = collections.Counter(t.get("tier", "?") for t in rows)
    battery_summary = {"titles": len(rows),
        "zero_uncaught_total": sum(1 for t in rows if t.get("uncaught_total") == 0),
        "tiers": dict(tiers),
        "rich_faces": [t.get("pkg") for t in rows if str(t.get("tier", "")).upper().startswith("A_RICH")]}
    print("battery:", battery_summary)

# infrastructure state (what S188 phases must build vs extend)
infra = {
    "tools/fdt": os.path.isdir(f"{REPO_DIR}/tools/fdt"),
    "library_ecosystem": sorted(os.listdir(f"{REPO_DIR}/library_ecosystem")) if os.path.isdir(f"{REPO_DIR}/library_ecosystem") else [],
    "reports/apk_routes": os.path.isdir(f"{REPO_DIR}/reports/apk_routes"),
    "runtime_capabilities.json": os.path.exists(f"{REPO_DIR}/library_ecosystem/runtime_capabilities.json"),
    "docs/S188_DIRECTIVE.md": os.path.exists(f"{REPO_DIR}/docs/S188_DIRECTIVE.md"),
}

ledger = {
    "generated": "2026-11-07",
    "directive": "docs/S188_DIRECTIVE.md (commit 7edaa2b6)",
    "master_issue": 541,
    "status_vocabulary": ["DISCOVERED", "EVIDENCE_VERIFIED", "REVIEWED", "ACCEPTED",
        "SOURCE_INTEGRATED", "BINARY_INTEGRATED", "BLOCKED", "REJECTED", "SUPERSEDED"],
    "impact_vocabulary": ["UNOBSERVED", "NO_CHANGE", "LOCAL_CONTRACT_VERIFIED", "CHAIN_ADVANCED",
        "PARTIAL_CHAIN", "CROSS_APP_VERIFIED", "VISUAL_VERIFIED", "INTERACTIVE_VERIFIED",
        "REGRESSION_VERIFIED"],
    "infrastructure": infra,
    "s186i_baseline": {
        "battery_json": "evidence/s186_s107/S186I_BATTERY.json",
        "engines_compared": ["de_engine", "head_s186i"],
        "summary": battery_summary,
        "adoption_status": "EVIDENCE_VERIFIED",
        "impact_status": "UNOBSERVED",
        "note": "Claims (29 zero-uncaught, 2 A_RICH) require Phase I reproduction on one identified binary before VISUAL_VERIFIED credit.",
    },
    "goldens": {
        "bouncy": "8a6c24ac", "unote": "3b8dcb0a", "dooz": "d602648e",
        "note": "Re-verify hashes against current HEAD test definitions before use (Phase L).",
    },
    "contributions": [],
}
with open(f"{REPO_DIR}/reports/s188/adoption_ledger.json", "w") as f:
    json.dump(ledger, f, indent=1)
print("WROTE reports/s188/phase_a_issue_snapshot.json + adoption_ledger.json")
print("INFRA:", json.dumps(infra, indent=1))
