#!/usr/bin/env python3
"""Generate DELETE_CANDIDATES.csv + SOURCE_DEPENDENCY_PROTECTION.csv for the
deep-cleanup audit, from measured data (inventory CSV, noise analysis, git).
"""
import csv, hashlib, json, os, subprocess

ROOT = "/home/z/my-project"
OUT = os.path.join(ROOT, "evidence/audit/deep_cleanup")
AUD = os.path.join(ROOT, "download/repository_audit")
os.chdir(ROOT)

def git_ls(prefix):
    return subprocess.run(["git", "ls-files", prefix], capture_output=True,
                          text=True).stdout.splitlines()

def sha(p):
    h = hashlib.sha256()
    fp = os.path.join(ROOT, p)
    if not os.path.isfile(fp):
        return "UNTRACKED-REMOVED"
    with open(fp, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

# size lookup from inventory
inv = {}
with open(os.path.join(AUD, "FULL_FILE_INVENTORY.csv")) as f:
    for r in csv.DictReader(f):
        inv[r["path"]] = int(r["size_bytes"])

def grp(prefix):
    ps = git_ls(prefix)
    return ps, sum(inv.get(p, 0) for p in ps)

rows = []  # path, size, sha, classification, referenced_by, dup, regen, info_elsewhere, action, checkout_save, history_save, risk, justification

def add(path, size, sha256, cls, refs, dup, regen, elsewhere, action,
        csave, hsave, risk, why):
    rows.append([path, size, sha256, cls, refs, dup, regen, elsewhere,
                 action, csave, hsave, risk, why])

# ── EXECUTED (this commit) ──
e1ps, e1b = grp("upstream/s43/ui_android_src/")
add("upstream/s43/ui_android_src/ (379 files)", e1b,
    "per-file: evidence/audit/deep_cleanup/SHA256SUMS.txt (E1 rows)",
    "Duplicate (byte-identical twin)",
    "POLICY_ALLOWLIST.json (stale after removal), ARTIFACT_REGISTRY.json (record), "
    "DUPLICATE_AND_UNUSED_LEDGER.csv (verdict holder)",
    "yes — upstream/s43/ui_android/ 379/379 byte-identical (measured cmp)",
    "yes — unzip upstream/s43/ui-android-1.11.4-sources.jar (tracked)",
    "yes — DUPLICATE_AND_UNUSED_LEDGER verdict + S_SLIM_UNTRACK_SHAS sample rows",
    "DELETE (EXECUTED)", e1b, 0,
    "LOW",
    "S-SLIM ledger's own verdict (losers keep ui_android canonical) was "
    "recorded but the bulk untrack pass missed the tree; completing it "
    "executes documented policy. History blobs unaffected (no rewrite).")

noise_kept = "evidence/s195_audit/cohort/runs/tictactoe_s195fix_r1/screenshot.png"
for p in ["evidence/s195_audit/gates/runs/spot_halma/screenshot.png",
          "evidence/s200/runs/s202_625_forced/screenshot.png",
          "evidence/s207/runs/s207_ttt0/screenshot.png",
          "evidence/s188_w13/runs/app.halma/screenshot.png",
          "evidence/s188_w18/runs/halma_w18_r1/screenshot.png"]:
    add(p, inv.get(p, 0), "per-file: SHA256SUMS.txt (E2 rows)",
        "Historical failure evidence — NOISE face (≈1M unique colors, "
        "nonwhite≈0.9996, uninitialized framebuffer class)",
        "run report.md + trace.jsonl in the same run dir (tracked, kept)",
        "class-duplicate of " + noise_kept,
        "no (historical run)", "yes — face sha256 in SHA256SUMS.txt + "
        "NOISE_FACE_ANALYSIS.csv metrics; failure documented in report.md",
        "DELETE (EXECUTED, user-directed law)", inv.get(p, 0), 0,
        "LOW",
        "The noise pixels carry zero app information (measured ≈0.5-0.52 "
        "distinctness ratio, random RGB); the failure itself stays tracked "
        "via report.md/trace; user-named exhibit tictactoe_s195fix_r1 "
        "RETAINED as the family representative.")

add(noise_kept, inv.get(noise_kept, 0), sha(noise_kept),
    "Historical failure evidence — NOISE family EXHIBIT",
    "user directive (this audit), NOISE_FACE_ANALYSIS.csv",
    "yes (5 class members removed, hashes recorded)",
    "no", "this file IS the preserved exhibit", "KEEP (EXHIBIT)", 0, 0,
    "—", "the single retained sample of the noise class, per user directive")

# ── LEDGER-ONLY (owner decisions) ──
dbs = [p for p in git_ls("*") if p.endswith((".db", ".sqlite", ".wal", ".shm"))]
dbb = sum(inv.get(p, 0) for p in dbs)
add("; ".join(dbs[:5]) + f"; … ({len(dbs)} files)", dbb, "per-file in FULL_FILE_INVENTORY.csv",
    "Generated output — app run-store databases (untrack residue class)",
    "run reports of the same runs", "no", "yes (regenerable by re-running the apps)",
    "yes — run reports + traces carry the findings",
    "OWNER-DECISION (untrack with ledger)", dbb, 0, "LOW",
    "Same class the S-SLIM pass untracked (~450 files); these 10-14 DBs "
    "survived it; small total.")

for jar in ["upstream/s44/protobuf.jar", "upstream/s43/ui-android-1.11.4-sources.jar",
            "upstream/s43/ui-1.11.4-sources.jar", "upstream/s43/runtime-1.11.4-sources.jar"]:
    add(jar, inv.get(jar, 0), sha(jar), "Required dependency — pinned upstream sources",
        "ARTIFACT_REGISTRY.json / extraction lineage", "no", "no (external original)",
        "—", "KEEP", 0, 0, "—", "the regeneration source for the extracted s43 trees")

add("evidence/s182_mosaic/S182_MOSAIC.jpg", inv.get("evidence/s182_mosaic/S182_MOSAIC.jpg", 0),
    sha("evidence/s182_mosaic/S182_MOSAIC.jpg"),
    "Canonical evidence — web-optimized twin of the registered PNG",
    "ARTIFACT_REGISTRY.json, IMAGE_POLICY_BASELINE.json, POLICY_ALLOWLIST.json",
    "yes (S182_MOSAIC.png registered twin)", "no", "PNG twin retained",
    "KEEP", 0, 0, "—", "both twins are registered policy artifacts")

add("evidence/s182_mosaic/S182_MOSAIC.png", inv.get("evidence/s182_mosaic/S182_MOSAIC.png", 0),
    sha("evidence/s182_mosaic/S182_MOSAIC.png"),
    "Canonical evidence — the S182 20-title battery mosaic (user-cited)",
    "S182 audit + user directive 2026-11-27", "yes (JPG twin)", "no", "—",
    "KEEP", 0, 0, "—", "primary visual evidence of the S182 achievements")

add("miniandroid/database/source_first/ (8 files)",
    sum(inv.get(p, 0) for p in git_ls("miniandroid/database/source_first")),
    "per-file in FULL_FILE_INVENTORY.csv",
    "Canonical evidence — per-APK source-coverage inventories + gap_map",
    "coverage registries", "no", "no", "—", "KEEP", 0, 0, "—",
    "canonical achievement/coverage records (rule-8 protected)")

add("docs/history/ (139 files)",
    sum(inv.get(p, 0) for p in git_ls("docs/history")),
    "per-file in FULL_FILE_INVENTORY.csv",
    "Historical evidence — campaign worklogs", "worklog lineage", "partial",
    "no", "—", "KEEP", 0, 0, "—",
    "the project's own history record; rule 8")

add("miniandroid/make_err_b1..b5,c1..c3 + make_fg1 (8 files)",
    sum(inv.get(p, 0) for p in git_ls("miniandroid/make_err*")) +
    sum(inv.get(p, 0) for p in git_ls("miniandroid/make_fg*")),
    "per-file in FULL_FILE_INVENTORY.csv",
    "Historical evidence — build-failure receipts (blk609 finalize procedure)",
    "scripts/blk609_finalize.sh (the documented finalize)", "no", "no",
    "wave reports carry the summaries", "KEEP", 0, 0, "—",
    "intentionally committed receipts (51cc5bf17 lineage); 1.45MB total")

for t in ["miniandroid/build_w24b/", "miniandroid/build_fast/", "miniandroid/build_p2a/"]:
    add(t + " (history-only, absent at HEAD)", 0, "n/a (not at HEAD)",
        "Generated output — committed build trees (3 prod binaries + ~50×34MB test exes)",
        "REPOSITORY_SIZE_AUDIT.md (S-SLIM) — measured 4.77GB class",
        "no", "yes (rebuildable)", "build logs + SHAs in wave reports",
        "OWNER-AUTHORIZED-REWRITE-ONLY (rule 5)", 0, 4770000000, "HIGH",
        "the single dominant history-size class; removal requires history "
        "rewrite + external backup gate (currently user-blocked)")

with open(os.path.join(OUT, "DELETE_CANDIDATES.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["repo_path", "size_bytes", "sha256", "classification",
                "referenced_by", "duplicate_exists", "regenerable",
                "info_preserved_elsewhere", "proposed_action",
                "checkout_saving_bytes", "history_saving_bytes", "risk",
                "justification"])
    w.writerows(rows)

# ── SOURCE_DEPENDENCY_PROTECTION.csv ──
prot = []
def addp(path, cls, why, refs):
    prot.append([path, cls, why, refs])

manifest = os.path.join(ROOT, "miniandroid/core_sources.manifest")
core = []
if os.path.isfile(manifest):
    core = [l.strip() for l in open(manifest)
            if l.strip() and not l.startswith("#")]
for p in core:
    addp("miniandroid/" + p, "Essential production source",
         "core_sources.manifest + check-source-parity gate (88 sources)",
         "Makefile build graph; engine + tests")
tests = sorted({l.strip().replace("tests/", "").rstrip("\\ ")
                for l in open("miniandroid/Makefile")
                if "TEST_LAW" in l or "_test" in l})
addp("miniandroid/tests/* (TEST_LAW/TEST_CORE/TEST_HOSTILE registry)",
     "Canonical tests", "TEST_LAW battery 55 + core 4 + hostile 3 (Makefile-registered)",
     "make test-all; regression wall")
addp("miniandroid/fonts/ + renderer/font assets", "Runtime asset",
     "font-law incident (S-SLIM audit) — required at build+run",
     "text_shaper/font_family build graph")
addp("miniandroid/golden/ + fixtures", "Required fixture",
     "canonical test inputs", "law tests + parity gates")
addp("docs/evidence/canonical/", "Canonical evidence",
     "registry.json + canonical GIFs/PNGs (registered)", "docs/ACHIEVEMENTS.md")
addp("docs/POLICY_ALLOWLIST.json + ARTIFACT_REGISTRY.json",
     "Policy/registry", "the active artifact policy layer", "validator gates")
addp("miniandroid/database/source_first/", "Canonical evidence",
     "per-APK source-coverage records", "coverage registries")
addp("upload/canonical_apks/ + handoff_apks/ (untracked corpus)",
     "Required fixture (local-only)", "the APK corpus; S182 restore proved "
     "F-Droid reproducibility", "run harnesses")

with open(os.path.join(OUT, "SOURCE_DEPENDENCY_PROTECTION.csv"), "w",
          newline="") as f:
    w = csv.writer(f)
    w.writerow(["path", "classification", "protected_because", "referenced_by"])
    w.writerows(prot)

# copy the 4 inventory CSVs into the committed audit dir
import shutil
for fn in ["FULL_FILE_INVENTORY.csv", "DIRECTORY_REPORT.csv",
           "LARGE_FILES_TOP500.csv", "DUPLICATE_GROUPS.csv",
           "NOISE_FACE_ANALYSIS.csv"]:
    src = os.path.join(AUD, fn)
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(OUT, fn))
        print("copied", fn)

exec_sum = sum(r[9] for r in rows if "EXECUTED" in r[8] and r[0].startswith(("upstream", "evidence")))
print(f"DELETE_CANDIDATES rows: {len(rows)}; protection rows: {len(prot)}; executed checkout saving ≈ {exec_sum} bytes")
