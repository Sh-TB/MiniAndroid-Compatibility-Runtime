#!/usr/bin/env python3
"""Normalize ACHIEVEMENT_LEDGER.csv to canonical form.
- exactly one independently testable claim per row
- one canonical verdict per row: CONFIRMED / REJECTED / PARTIALLY CONFIRMED / BLOCKED / PENDING / SUPERSEDED
- evidence level + integration status in their own canonical columns
- split rows that carry multiple independent claims
- split tracker-state confirmation from runtime verification
"""
import csv, sys

SRC = "/home/z/my-project/miniandroid/evidence/audit/ACHIEVEMENT_LEDGER.csv"
DST = "/home/z/my-project/miniandroid/evidence/audit/ACHIEVEMENT_LEDGER.csv"  # overwrite in place
VERDICTS = {"CONFIRMED", "REJECTED", "PARTIALLY CONFIRMED", "BLOCKED", "PENDING", "SUPERSEDED"}
LEVELS = {"TRACKER-STATE", "SOURCE-INSPECTED", "BINARY-INSPECTED", "BUILD-GRAPH-MEASURED",
          "BUILD-MEASURED", "RUNTIME-EXECUTED", "UNIT-TESTED", "INTEGRATION-TESTED", "ENV-BLOCKED"}
INTEG = {"INTEGRATED", "NOT-INTEGRATED", "PARTIALLY-INTEGRATED", "REJECTED-EXPERIMENT",
         "DOCUMENTED-ONLY", "N/A", "OPEN-DEFECT"}

def lvl(*levels): return " + ".join(levels)

KEYMAP = {"verdict":"Verdict","level":"Evidence level","integ":"Integration status",
          "claim":"Exact claim","next":"Next action","source":"Source inspected",
          "test":"Test executed","runtime":"Runtime verified","evidence":"Evidence"}
LEGACY_LEVEL = {
 "Source-confirmed":"SOURCE-INSPECTED","Build-graph-confirmed":"BUILD-GRAPH-MEASURED",
 "Integration-test-confirmed":"INTEGRATION-TESTED","Runtime-observed":"RUNTIME-EXECUTED",
 "Tracker-confirmed":"TRACKER-STATE","Environment blocker":"ENV-BLOCKED","Environment":"ENV-BLOCKED",
 "Unit-test-confirmed + integration":"UNIT-TESTED","binary inspection":"BINARY-INSPECTED",
 "Not yet re-audited this session":"TRACKER-STATE","tracker state":"TRACKER-STATE",
 "API fetch":"TRACKER-STATE",
 "rule 44 disclosure: cmake not installed (tools/dl wiped)":"ENV-BLOCKED",
 "Missing exact APK":"ENV-BLOCKED","Missing APK — calculation-path claim untestable here":"ENV-BLOCKED",
 "APK corpus absent":"ENV-BLOCKED","source inspection":"SOURCE-INSPECTED",
 "measurement BLOCKED":"ENV-BLOCKED",
 "Source-confirmed + behavioral demo":"SOURCE-INSPECTED","Source-confirmed + battery":"SOURCE-INSPECTED",
 "Source-confirmed + runtime-observed":"SOURCE-INSPECTED",
 "Source-confirmed + build-graph-confirmed":"BUILD-GRAPH-MEASURED",
 "Source-confirmed; item-level re-verification PENDING":"SOURCE-INSPECTED",
 "Build-measured (rejection preserved)":"BUILD-MEASURED",
 "Build-measured":"BUILD-MEASURED","grep output 2026-11-20":"SOURCE-INSPECTED",
 "ls output":"SOURCE-INSPECTED","gitignore + ls inspection":"SOURCE-INSPECTED",
 "Makefile grep":"SOURCE-INSPECTED","W23 commit 68f4fe58 BUG-7 label":"SOURCE-INSPECTED",
 "registered evidence":"SOURCE-INSPECTED",
}
LEGACY_INTEG = {
 "n/a":"N/A","none":"N/A","unknown":"N/A",
 "UNKNOWN (claim untestable here)":"NOT-INTEGRATED","NOT verifiable locally":"NOT-INTEGRATED",
 "OPEN":"OPEN-DEFECT","OPEN — parity builds must pass the define":"OPEN-DEFECT",
 "REJECTED":"REJECTED-EXPERIMENT","REJECTED+REVERTED":"REJECTED-EXPERIMENT",
 "DOCUMENTED":"DOCUMENTED-ONLY","NOT INTEGRATED":"NOT-INTEGRATED",
 "NOT INTEGRATED (diagnostic/local-only)":"NOT-INTEGRATED",
 "NOT integrated as a build profile":"NOT-INTEGRATED",
 "Not applicable (CMake graph)":"N/A","none (integrated)":"INTEGRATED",
 "FIXED THIS AUDIT — added to Makefile":"INTEGRATED","Methodology lesson recorded":"DOCUMENTED-ONLY",
 "INTEGRATED (opt-in)":"INTEGRATED","INTEGRATED (via #606 wave)":"PARTIALLY-INTEGRATED",
 "INTEGRATED (FASTPROFILE=1 W24TIERS=1)":"INTEGRATED","INTEGRATED (#606 closed per tracker)":"INTEGRATED",
 "INTEGRATED per tracker":"INTEGRATED-PER-TRACKER","partially integrated":"PARTIALLY-INTEGRATED",
 "none needed at -j2":"N/A","INTEGRATED (split default)":"INTEGRATED",
 "none — do not resurrect without new evidence":"REJECTED-EXPERIMENT",
}
def canon_level(v):
    v = v.strip()
    if v in LEVELS: return v
    if v in LEGACY_LEVEL: return LEGACY_LEVEL[v]
    raise AssertionError(f"unknown evidence level: {v!r}")
def canon_integ(v):
    v = v.strip()
    if v in INTEG or v in ("INTEGRATED-PER-TRACKER","SUPERSEDED-BY-SPLIT"): return v
    if v in LEGACY_INTEG: return LEGACY_INTEG[v]
    raise AssertionError(f"unknown integration status: {v!r}")

rows = list(csv.DictReader(open(SRC, newline="", encoding="utf-8")))
assert len(rows) == 50, f"expected 50 source rows, got {len(rows)}"

# split specs: id -> list of dicts with explicit fields for each new row
S = {
"AUD-10": [
 dict(id="AUD-10a", claim="Job pools / OOM guard needed at -j2 on 4 GB (claim #632 B9)",
      source="~40 full builds W22-W24 (make -j2)",
      test="zero OOM; peak RSS 1221 MB of 4 GB; wave-10 -O1 OOM was on the OLD 55k monolith only",
      runtime="full builds rc0", verdict="REJECTED", level="RUNTIME-EXECUTED",
      evidence="evidence/w24 build_bench.jsonl rss fields", integ="REJECTED-EXPERIMENT",
      next="never adopt at -j2; recorded so it is not retried"),
 dict(id="AUD-10b", claim="Job pools / OOM guard needed at -j4 and above",
      source="no -j4 build ever run in this environment", test="not executed (2 vCPU host)",
      runtime="n/a", verdict="PENDING", level="ENV-BLOCKED",
      evidence="host is 2 vCPU; -j4 unreachable here", integ="N/A",
      next="re-evaluate only on a >=4-vCPU host"),
],
"AUD-15": [
 dict(id="AUD-15a", claim="#612 Target1: candidate build <280 s",
      source="W24 combo A/B (4-build ABBA)", test="cand avg 289.85 s",
      runtime="battery 49/49 + gate 11/11 on candidate", verdict="REJECTED", level="BUILD-MEASURED",
      evidence="W24_FINAL_REPORT.md §6; commit d8b8fbb9", integ="DOCUMENTED-ONLY",
      next="MISS by ~10 s — at the effective-capacity floor (288.4 s)"),
 dict(id="AUD-15b", claim="#612 Target2: candidate build <250 s",
      source="CPU-work floor model 428.5/(2x0.743)", test="floor 288.4 s > 250 s",
      runtime="n/a", verdict="REJECTED", level="BUILD-MEASURED",
      evidence="W24_FINAL_REPORT.md §6 floor analysis", integ="DOCUMENTED-ONLY",
      next="needs CPU-work cuts or >=3 effective cores"),
],
"AUD-25": [
 dict(id="AUD-25a", claim="Monolith dalvik_engine.cpp ~94k lines kept as DALVIK_SPLIT=0 fallback",
      source="wc -l = 94305", test="split path default; battery rc0", runtime="builds rc0 W22-W24",
      verdict="CONFIRMED", level="SOURCE-INSPECTED",
      evidence="src/dex/dalvik_engine.cpp 94305 lines", integ="INTEGRATED", next="none"),
 dict(id="AUD-25b", claim="dalvik_engine.cpp contains one 5436-line function",
      source="pre-split measurement (#612 B1 era)", test="superseded by the W4 split machinery",
      runtime="n/a", verdict="SUPERSEDED", level="SOURCE-INSPECTED",
      evidence="W4 split commit lineage (DALVIK_SPLIT=1 default)", integ="SUPERSEDED-BY-SPLIT",
      next="historical count preserved; current per-TU ranking in evidence/w24/TU_COST_RANKING.csv"),
],
"AUD-36": [
 dict(id="AUD-36a", claim="#619 TicTacToe render parity (screenshot sha16 d55056a8928a26ff)",
      source="11-run gate on W24 candidate codegen", test="gate hash IDENTICAL to canonical set",
      runtime="render-level gate executed on SUBSTITUTE APK (itsfrz ttt_5 — original emmanuelmess APK absent)",
      verdict="CONFIRMED", level="RUNTIME-EXECUTED",
      evidence="evidence/w24/RAW_LOGS/w24_gate_hashes_cand.txt", integ="INTEGRATED",
      next="render parity only — see AUD-36b for the interactive surface"),
 dict(id="AUD-36b", claim="#619 TicTacToe interactive cell-level verification on the ORIGINAL APK",
      source="tracker #619 CLOSED 40 comments (tracker state only)", test="not executable — APK absent",
      runtime="n/a", verdict="BLOCKED", level="ENV-BLOCKED",
      evidence="AUD-35 run log: substitute app rc=1, 0 setGraph hits", integ="NOT-INTEGRATED",
      next="obtain emmanuelmess ttt APK; never substitute for the original"),
],
"AUD-37": [
 dict(id="AUD-37a", claim="#618 Android Counter issue closed (tracker state)",
      source="tracker: CLOSED 49 comments", test="API fetch 2026-11-20", runtime="n/a",
      verdict="CONFIRMED", level="TRACKER-STATE", evidence="API fetch 2026-11-20",
      integ="INTEGRATED-PER-TRACKER", next="tracker closure is NOT runtime proof"),
 dict(id="AUD-37b", claim="#618 Counter 0->1->2->1->0->-1->-2 across 3 runs (runtime claim)",
      source="issue body claim", test="not executable — APK absent", runtime="n/a",
      verdict="BLOCKED", level="ENV-BLOCKED", evidence="APK corpus absent from sandbox",
      integ="NOT-INTEGRATED", next="obtain the original APK; run the full interaction sequence"),
],
"AUD-38": [
 dict(id="AUD-38a", claim="#623 RNG issue closed (tracker state)",
      source="tracker: CLOSED 11 comments", test="API fetch", runtime="n/a",
      verdict="CONFIRMED", level="TRACKER-STATE", evidence="API fetch", integ="INTEGRATED-PER-TRACKER",
      next="tracker closure is NOT runtime proof"),
 dict(id="AUD-38b", claim="#623 RNG runtime behavior verified",
      source="issue body claim", test="not executable — APK absent", runtime="n/a",
      verdict="BLOCKED", level="ENV-BLOCKED", evidence="APK corpus absent",
      integ="NOT-INTEGRATED", next="obtain the original APK; verify identity + behavior"),
],
}

# per-id field corrections for non-split rows (non-canonical verdicts etc.)
FIX = {
"AUD-01": dict(verdict="CONFIRMED", level="BUILD-GRAPH-MEASURED", integ="N/A",
               next="MEASURED (AUD-52): battery loop at CMakeLists.txt:494 has no EXCLUDE_FROM_ALL — with -DBUILD_TESTS=ON all 49 test executables join default all (50 links measured); with the default BUILD_TESTS=OFF the default all contains 0 test exes; condition now documented"),
"AUD-02": dict(verdict="PARTIALLY CONFIRMED", level="BUILD-GRAPH-MEASURED", integ="N/A",
               claim="QuickJS sources compiled twice in CMake (298 + 459)",
               next="MEASURED (AUD-52): 2x compile CONFIRMED with -DBUILD_TESTS=ON (10 edges = 5 sources x 2 OBJECT libs); default graph compiles QuickJS ONCE (miniandroid_test_native lives behind the BUILD_TESTS guard); condition documented",
               evidence="CMakeLists.txt:298,459; evidence/audit/RAW_LOGS/cmake_graph_measurement.md"),
"AUD-03": dict(verdict="CONFIRMED", level="BUILD-GRAPH-MEASURED", integ="INTEGRATED"),
"AUD-04": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="INTEGRATED"),
"AUD-05": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="INTEGRATED"),
"AUD-06": dict(verdict="REJECTED", level="BUILD-GRAPH-MEASURED", integ="N/A",
               claim="~52 unnecessary link operations + OOM on 4GB host",
               next="SUPERSEDED BY MEASUREMENT (AUD-52, cmake 4.4.5 + ninja dry-run): default all = 99 edges, exactly 1 executable link, 0 test exes (test block behind option(BUILD_TESTS) OFF, CMakeLists.txt:395); the ~52-link scope exists only with -DBUILD_TESTS=ON (measured 50 links); OOM never observed; AUD-06's environment blocker is RESOLVED",
               source="evidence/audit/RAW_LOGS/cmake_graph_measurement.md"),
"AUD-07": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="OPEN-DEFECT"),
"AUD-08": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="DOCUMENTED-ONLY"),
"AUD-09": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="INTEGRATED"),
"AUD-11": dict(verdict="CONFIRMED", level="INTEGRATION-TESTED", integ="INTEGRATED"),
"AUD-12": dict(verdict="CONFIRMED", level="INTEGRATION-TESTED", integ="INTEGRATED"),
"AUD-13": dict(verdict="CONFIRMED", level="BUILD-GRAPH-MEASURED", integ="INTEGRATED"),
"AUD-14": dict(verdict="CONFIRMED", level="BUILD-MEASURED", integ="DOCUMENTED-ONLY"),
"AUD-16": dict(verdict="CONFIRMED", level="INTEGRATION-TESTED", integ="INTEGRATED"),
"AUD-17": dict(verdict="REJECTED", level="BUILD-MEASURED", integ="REJECTED-EXPERIMENT"),
"AUD-18": dict(verdict="REJECTED", level="BUILD-MEASURED", integ="REJECTED-EXPERIMENT"),
"AUD-19": dict(verdict="REJECTED", level="BUILD-MEASURED", integ="REJECTED-EXPERIMENT"),
"AUD-20": dict(verdict="REJECTED", level="BUILD-MEASURED", integ="REJECTED-EXPERIMENT"),
"AUD-21": dict(verdict="REJECTED", level="BUILD-MEASURED", integ="REJECTED-EXPERIMENT",
               claim="PCH 36.4 s gives no useful win (claim itself preserved as rejected)"),
"AUD-22": dict(verdict="CONFIRMED", level="BUILD-MEASURED", integ="REJECTED-EXPERIMENT"),
"AUD-23": dict(verdict="CONFIRMED", level="BUILD-MEASURED", integ="DOCUMENTED-ONLY"),
"AUD-24": dict(verdict="REJECTED", level="BUILD-MEASURED", integ="REJECTED-EXPERIMENT"),
"AUD-26": dict(verdict="BLOCKED", level="ENV-BLOCKED", integ="NOT-INTEGRATED",
               next="4 commits not in any checked source (cat-file x4, 26 remote branches, 2 PR refs, 2 stashes, 0 dangling commits, upload/ artifacts); capability PARTIALLY SUPERSEDED by mainline c48773a0 (scaleType raster AOSP parity) + 7e5473be (s246 scaleType geometry laws); still missing: scaletype_oracle.py + probe_scaletype + 8/8 mutation battery + 3x determinism"),
"AUD-27": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="INTEGRATED"),
"AUD-28": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="INTEGRATED"),
"AUD-29": dict(verdict="PARTIALLY CONFIRMED", level="SOURCE-INSPECTED", integ="PARTIALLY-INTEGRATED"),
"AUD-30": dict(verdict="REJECTED", level="SOURCE-INSPECTED", integ="N/A",
               claim="GridLayout not implemented (no solver in runtime)",
               next="FALSIFIED by source check 2026-11-20: Bellman-Ford arc solver IS present (layout_inflater.cpp:2899-2903 computeLinks+solve port, :4364-4380 AOSP track, :4494 cell resolution, #606 wave); prior grep was scoped to wrong directory; remaining surface = full span-tracks + RTL row mirror (#606 record)",
               source="grep src/resources/layout_inflater.cpp (full-tree grep, not src/resources-only)"),
"AUD-31": dict(verdict="PARTIALLY CONFIRMED", level="SOURCE-INSPECTED", integ="PARTIALLY-INTEGRATED"),
"AUD-32": dict(verdict="PARTIALLY CONFIRMED", level="SOURCE-INSPECTED", integ="PARTIALLY-INTEGRATED",
               claim="Nine-patch npTc/npLb support missing",
               next="npTc chunk parsing IS implemented (execution_engine.cpp:2876, aapt2 8.13.2 payload layout) — prior grep scoped to src/resources only missed it; npLb (legacy aapt chunk) path not found — that half of the claim stands",
               source="grep src/runtime/execution_engine.cpp + full-tree npTc/npLb"),
"AUD-33": dict(verdict="PARTIALLY CONFIRMED", level="SOURCE-INSPECTED", integ="PARTIALLY-INTEGRATED"),
"AUD-34": dict(verdict="CONFIRMED", level="BINARY-INSPECTED", integ="OPEN-DEFECT"),
"AUD-35": dict(verdict="BLOCKED", level="ENV-BLOCKED", integ="NOT-INTEGRATED"),
"AUD-39": dict(verdict="BLOCKED", level="ENV-BLOCKED", integ="NOT-INTEGRATED"),
"AUD-40": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="NOT-INTEGRATED"),
"AUD-41": dict(verdict="PARTIALLY CONFIRMED", level="SOURCE-INSPECTED", integ="PARTIALLY-INTEGRATED"),
"AUD-42": dict(verdict="PENDING", level="TRACKER-STATE", integ="N/A"),
"AUD-43": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="NOT-INTEGRATED"),
"AUD-44": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="INTEGRATED"),
"AUD-45": dict(verdict="CONFIRMED", level="SOURCE-INSPECTED", integ="OPEN-DEFECT",
               claim="R5 -Werror + clang-tidy CI is ABSENT (no .github/workflows in mainline — live gap, not a feature)"),
"AUD-46": dict(verdict="CONFIRMED", level="UNIT-TESTED", integ="INTEGRATED"),
"AUD-47": dict(verdict="PENDING", level="ENV-BLOCKED", integ="NOT-INTEGRATED"),
"AUD-48": dict(verdict="CONFIRMED", level="INTEGRATION-TESTED", integ="INTEGRATED"),
"AUD-49": dict(verdict="PENDING", level="SOURCE-INSPECTED", integ="OPEN-DEFECT"),
"AUD-50": dict(verdict="CONFIRMED", level="BUILD-GRAPH-MEASURED", integ="INTEGRATED"),
}

# rows registered by THIS continuation session (2026-11-20, post-56ba5842)
NEW_ROWS = [
 dict(ID="AUD-51", **{"Issue/Coder": "S7/9b953ce1", "Exact claim": "build_w24_cand_a/ binary tracked + 1 APK in repo (S7 anomaly)",
   "Source inspected": "git ls-files: 53 build files + download/batch614_624_evidence/de.tcrass.minos_10004.apk; root .gitignore lacked build_w24*/ rule",
   "Test executed": "git rm --cached 53+7 files; gitignore rules added; SHAs recorded (binary a3013295..., APK af769233...)",
   "Runtime verified": "n/a", "Verdict": "CONFIRMED", "Evidence level": "SOURCE-INSPECTED",
   "Evidence": "commit 051af519; miniandroid/evidence/audit/RAW_LOGS/untrack_evidence_shas.txt",
   "Integration status": "INTEGRATED", "Next action": "root cause: auto-add session committed the untracked candidate tree; binary churned per rebuild",
   "Split-from": ""}),
 dict(ID="AUD-52", **{"Issue/Coder": "S9/cmake", "Exact claim": "CMake graph measured (AUD-06 blocker resolved)",
   "Source inspected": "cmake 4.4.5 configure + ninja -n (default and BUILD_TESTS=ON)",
   "Test executed": "default all: 99 edges / 1 link / QuickJS 1x / WEBP 0 refs; BUILD_TESTS=ON: 204 edges / 50 links / QuickJS 2x (10 edges)",
   "Runtime verified": "graph facts via ninja dry-run (no full test-build run)", "Verdict": "CONFIRMED", "Evidence level": "BUILD-GRAPH-MEASURED",
   "Evidence": "evidence/audit/RAW_LOGS/cmake_graph_measurement.md",
   "Integration status": "DOCUMENTED-ONLY", "Next action": "peak memory during a full BUILD_TESTS=ON build remains unmeasured",
   "Split-from": ""}),
 dict(ID="AUD-53", **{"Issue/Coder": "S4/RC-12", "Exact claim": "RC-12 commits 46ca6258/73dcadb6/1439627a/d77edba6 recoverable",
   "Source inspected": "cat-file x4 MISSING; 26 remote refs; 2 PR refs; tags; 2 stashes; 0 dangling commits; worktrees prunable; upload/ artifacts; branch layout-geometry-001 named in #631 comments is coder-local only",
   "Test executed": "full source sweep executed; capability partially superseded by mainline c48773a0 (scaleType raster AOSP parity) + 7e5473be (s246 scaleType geometry laws)",
   "Runtime verified": "n/a", "Verdict": "BLOCKED", "Evidence level": "ENV-BLOCKED",
   "Evidence": "#631 comments 7038260479 (RC-12 record) + 7021652138 (mission complete); git ls-remote",
   "Integration status": "NOT-INTEGRATED", "Next action": "recovery requires the original coder environment (branch layout-geometry-001); verifier + probe + mutation battery still absent",
   "Split-from": ""}),
 dict(ID="AUD-54", **{"Issue/Coder": "S3/#632", "Exact claim": "194-item registry fully extracted with per-item disposition",
   "Source inspected": "issue body (42.6KB, 140 items) + all 11 comments (137KB) fetched authenticated",
   "Test executed": "234 rows extracted (140 body + 45 NEW + 24 BP + 8 SQL + 10 S-plans + 5 reuse + SWEEP-S2 + REUSE-TOTAL); statuses: 190 LIVE / 20 RETRACTED-BY-AUTHOR / 14 DEAD-CODE-RESCOPED / 10 PLAN-SWEEP; delta 234-194=40 = the author's own retracted/re-scoped counter (batch 3: 'Running total: 40')",
   "Runtime verified": "source checks on 25 file:line cites; 199 no-cite items documented as such", "Verdict": "CONFIRMED", "Evidence level": "SOURCE-INSPECTED",
   "Evidence": "evidence/audit/632_FINDINGS.csv; 632_BATCH8_174_ATTRIBUTES.md; RAW_LOGS/632_registry_snapshot_2026-11-20.json",
   "Integration status": "DOCUMENTED-ONLY", "Next action": "NEW-18/19/20 never published (numbering gap in the source registry)",
   "Split-from": ""}),
 dict(ID="AUD-56", **{"Issue/Coder": "S6/#630-#631", "Exact claim": "10 layout test apps recoverable from coder artifacts",
   "Source inspected": "apps/ empty in mainline; #631 comments: 'All 10 original apps are built' on branch layout-geometry-001 (coder-local); no APKs or app sources on origin (26 refs checked)",
   "Test executed": "recovery sweep executed; apps not found in any accessible source",
   "Runtime verified": "n/a", "Verdict": "BLOCKED", "Evidence level": "ENV-BLOCKED",
   "Evidence": "#631 comments 7021630435/7021636965 (visual evidence) + 7021652138 (mission complete)",
   "Integration status": "NOT-INTEGRATED", "Next action": "no substitute apps may be generated (mission §D rule); original apps need the coder environment",
   "Split-from": ""}),
 dict(ID="AUD-57", **{"Issue/Coder": "S10/branches", "Exact claim": "all coder contributions audited beyond the 50-row ledger",
   "Source inspected": "merge-base census of every local+remote branch",
   "Test executed": "MERGED into main: s241-law-waves (S236-S240), s237-w27, s238-audit, s239, s240; ABSENT from main: wave10/dalvik-accel (15 commits), audit/s236 (7), audit/m16-litehtml (3), cont24/skeleton-light-experiment (2); 2 stashes preserved (62 files, +12,352 lines)",
   "Runtime verified": "n/a", "Verdict": "CONFIRMED", "Evidence level": "SOURCE-INSPECTED",
   "Evidence": "git merge-base census 2026-11-20; PRESERVED_WORK_MANIFEST.md updated",
   "Integration status": "DOCUMENTED-ONLY", "Next action": "wave10/dalvik-accel 15 commits are the largest unmerged coder line (dev-so profiles, PR #626)",
   "Split-from": ""}),
 dict(ID="AUD-55", **{"Issue/Coder": "S5/#633", "Exact claim": "MG-011 ok-fix recoverable and integrable",
   "Source inspected": "vector_decode.cpp:942 (hole verified live: clip-path warning :493 still reported ok=true)",
   "Test executed": "fix applied verbatim from #633; FASTPROFILE build rc=0; battery 49/49 PASS rc=0 on binary 98b4ca24b62ba2cf (first battery run hit ENOSPC — rerun clean)",
   "Runtime verified": "battery executed on the fix-included binary", "Verdict": "CONFIRMED", "Evidence level": "INTEGRATION-TESTED",
   "Evidence": "evidence/audit/RAW_LOGS/mg011_build_testall.log",
   "Integration status": "INTEGRATED", "Next action": "direct-vs-referenced PathData parity test as battery extension (NEXT_INTEGRATION_PLAN #1)",
   "Split-from": ""}),
]

FIELDS = ["ID","Issue/Coder","Exact claim","Source inspected","Test executed","Runtime verified",
          "Verdict","Evidence level","Evidence","Integration status","Next action","Split-from"]

out = []
for r in rows:
    rid = r["ID"]
    if rid in S:
        for spec in S[rid]:
            out.append({
                "ID": spec["id"],
                "Issue/Coder": r["Issue/Coder"],
                "Exact claim": spec["claim"],
                "Source inspected": spec["source"],
                "Test executed": spec["test"],
                "Runtime verified": spec["runtime"],
                "Verdict": spec["verdict"],
                "Evidence level": spec["level"],
                "Evidence": spec["evidence"],
                "Integration status": spec["integ"],
                "Next action": spec["next"],
                "Split-from": rid,
            })
    else:
        f = dict(r)
        f["Split-from"] = ""
        f["ID"] = rid
        f["Evidence level"] = r.get("Level", "")  # source column is named "Level"
        for k in ("Source inspected","Test executed","Runtime verified","Verdict",
                  "Evidence","Integration status","Next action","Issue/Coder","Exact claim"):
            f[k] = r[k]
        if rid in FIX:
            for k, v in FIX[rid].items():
                f[KEYMAP[k]] = v
        f["Verdict"] = f["Verdict"].strip()
        f["Evidence level"] = canon_level(f["Evidence level"])
        f["Integration status"] = canon_integ(f["Integration status"])
        # rename Verdict column handled below
        out.append(f)

# append this session's new rows
for nr in NEW_ROWS:
    f = {k: nr.get(k, "") for k in FIELDS}
    f["Evidence level"] = canon_level(f["Evidence level"])
    f["Integration status"] = canon_integ(f["Integration status"])
    out.append(f)

final = []
for f in out:
    # remap from the source key "Level" if present
    final.append({k: f.get(k, "") for k in FIELDS})

# validation before write
ids = [f["ID"] for f in final]
assert len(ids) == len(set(ids)), "duplicate IDs"
for f in final:
    assert f["Verdict"] in VERDICTS, (f["ID"], f["Verdict"])
    assert f["Evidence level"] in LEVELS, (f["ID"], f["Evidence level"])
    isv = f["Integration status"]
    assert isv in INTEG or isv.startswith("INTEGRATED") or isv in ("SUPERSEDED-BY-SPLIT",), (f["ID"], isv)
    assert f["Evidence"].strip(), (f["ID"], "empty evidence")

with open(DST, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    w.writerows(final)

from collections import Counter
c = Counter(f["Verdict"] for f in final)
print("rows:", len(final))
for k in ["CONFIRMED","REJECTED","PARTIALLY CONFIRMED","BLOCKED","PENDING","SUPERSEDED"]:
    print(f"  {k}: {c.get(k,0)}")
print("sum:", sum(c.get(k,0) for k in VERDICTS))
