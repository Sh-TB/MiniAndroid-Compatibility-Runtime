#!/usr/bin/env python3
"""Post the v2 cumulative audit update to Issue #635."""
import json, subprocess, urllib.request

TOKEN = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True,
                       cwd="/home/z/my-project").stdout.split("password=")[1].splitlines()[0]

body = """# AUDIT v2 — ledger normalized, #632 fully extracted (234 items), RC-12 closed-blocked, MG-011 recovered+integrated, CMake measured

Continuation per this issue's §1–§9 mission. Commits: 051af519 (AUD-51 S7 forensics) → 9d5714bb (AUDIT-v2 main) → 186cfe63/aef7a8d2 (gitignore completion). Nothing from v1 was replaced; everything was reconciled.

## §1 Ledger normalized — 63 rows, machine-validated
- 50 → **63 rows**: one independently testable claim per row; canonical verdicts only; separate evidence-level and integration-status columns.
- Splits: AUD-10a/b, 15a/b, 25a/b, 36a/b, 37a/b, 38a/b — tracker-state rows are now SEPARATE from runtime rows (AUD-36b/37b/38b runtime = BLOCKED; tracker closure is not runtime proof).
- AUD-36's `Original-APK-verified` level downgraded: the gate used the itsfrz SUBSTITUTE APK.
- Programmatic totals: **CONFIRMED 33 / REJECTED 11 / PARTIALLY CONFIRMED 6 / BLOCKED 8 / PENDING 4 / SUPERSEDED 1 = 63 == rows** (LEDGER_VALIDATION_REPORT.md, PASS; writer `scripts/normalize_ledger.py`, independent validator `scripts/validate_ledger.py`).

## §2 False-green corrections (source-checked this session)
| Was | Now | Proof |
|---|---|---|
| AUD-30 "GridLayout not implemented" | **REJECTED (falsified)** — Bellman-Ford arc solver IS present | layout_inflater.cpp:2899-2903, :4364-4380, :4494 (#606 wave); v1 grep was mis-scoped |
| AUD-32 "nine-patch npTc/npLb missing" | **PARTIALLY** — npTc parsing IS present | execution_engine.cpp:2876 (aapt2 8.13.2 payload); npLb path still absent |
| AUD-06 "~52 links + OOM (cmake)" | **REJECTED for the default graph** | measured (§4) |
| v1 verdict totals 30/4/5/4/3 | replaced by machine counts (v1's CONFIRMED bucket absorbed 3 REJECTED probes) | validator report |

## §3 #632 complete — all findings, one row each
- Body (42.6 KB, 140 items) + all 11 comments (137 KB) fetched authenticated (raw snapshot: RAW_LOGS/632_registry_snapshot_2026-11-20.json).
- **632_FINDINGS.csv = 234 rows**: 140 body (§A–§R) + 45 NEW + 24 BUILD-PERF (B1–B24, renamed 632-BP-* — the author's own ID collision with body §B documented) + 8 SQL + 10 S-sweep plans + 5 reuse (R-1..R-5) + SWEEP-S2 + REUSE-TOTAL.
- Statuses: **190 LIVE / 20 RETRACTED-BY-AUTHOR / 14 DEAD-CODE-RESCOPED / 10 PLAN-SWEEP**.
- Reconciliation: title says 194; delta = **+40, exactly the author's own retraction counter** (batch 3: "Running total of my own retracted/re-scoped claims: 40"). NEW-18/19/20 were never published (numbering gap). The 174-attribute sweep is preserved verbatim (632_BATCH8_174_ATTRIBUTES.md).
- Source checks: 25 file:line cites machine-verified against the active tree; the rest carry explicit status notes (no-cite items documented as such — per the registry's own `[C]` honesty rule).

## §4 CMake measured (AUD-06's blocker resolved)
cmake 4.4.5 + ninja dry-run, configure rc=0 both graphs (RAW_LOGS/cmake_graph_measurement.md):
- **Default `all`: 99 edges, exactly 1 executable link, QuickJS compiled ONCE, MINIANDROID_HAVE_WEBP = 0 refs, 0 test exes** (test block behind `option(BUILD_TESTS) OFF`).
- **BUILD_TESTS=ON: 204 edges, 50 executable links, QuickJS 2×** (10 edges = 5 sources × 2 OBJECT libs :298+:459).
- Verdicts: B19/B22 ("52 links") false for the default graph, true in scope with BUILD_TESTS=ON; AUD-01 CONFIRMED-with-condition; AUD-02 PARTIALLY CONFIRMED; WEBP parity gap (AUD-07) confirmed at generated-graph level. Peak memory of a full test-build remains honestly unmeasured.

## §5 Recovery outcomes (explicit, no hand-waving)
- **RC-12 (4 commits 46ca6258/73dcadb6/1439627a/d77edba6): BLOCKED-CLOSED.** Sources checked: cat-file ×4 (all missing), 26 remote refs, 2 PR refs, tags, 2 stashes, git fsck (0 dangling commits), prunable worktrees, upload/ coder artifacts. The owning branch **`layout-geometry-001` exists only in the original coder's environment** (#631 comment 7038260479 names it). Capability PARTIALLY SUPERSEDED in mainline by c48773a0 (scaleType raster at AOSP parity) + 7e5473be (s246 geometry laws). Still missing: verifier + probe app + 8/8 mutation battery + 3× determinism (AUD-53).
- **#630/#631 ten layout apps: BLOCKED** — built by the coder (visual evidence in comments 7021630435/7021636965/7021652138), coder-local only; no substitute apps generated per the mission rule (AUD-56).
- **MG-011 (#633): RECOVERED AND INTEGRATED (AUD-55).** Hole verified live first (vector_decode.cpp:942 ignored the :493 clip-path warning and reported success), then the fix applied verbatim: `out->ok = err.empty() && !paths.empty();`. Build rc=0; **battery 49/49 PASS rc=0** on binary 98b4ca24b62ba2cf (first battery run hit ENOSPC — rerun clean; both records logged). Direct-vs-referenced PathData parity queued as the follow-up test.
- **#634 MG-012 and #295/#296/#297 stroke laws: BLOCKED** — coder-local implementations documented in their issues; not re-implemented here, flagged as the top of NEXT_INTEGRATION_PLAN (§2/§3).

## §6 Remaining issue audits (state, not tracker-green)
- #597: the root-cause law (F-NEW-639 bounded append, the '777' face) is ALREADY INTEGRATED via s237-w27; the 7×3=21 real-UI re-check stays BLOCKED (OpenCalc APK absent from the corpus — identity census saved).
- #618/#623: tracker-closed rows split from runtime rows; runtime = BLOCKED (APKs absent).
- #628/#619: substitute-APK render parity only (11/11 gate hashes); interactive/--frames-12 claims BLOCKED on the emmanuelmess APK.
- #296/#297/#614/#610/#621/#622/#624/#626: bodies fetched and folded into the ledger/registry; APK-bound claims stay BLOCKED with the exact missing artifact named.
- APK identity census (S8): 15-corpus SHAs recorded; ru.zxalexis.ugaday_15 sha16 000ae2e5751f9a85 == the sha recorded in #612's body (EXACT match).

## §7 Beyond the 50 rows (S10 branch census, AUD-57)
- MERGED into main: s241-law-waves (S236–S240), s237-w27, s238-audit, s239-wave-stack, s240-generic-law-battery (merge-base == tip for each).
- ABSENT but preserved: wave10/dalvik-accel (15 commits — W16–W20 lineage incl. the P0 split evidence), audit/s236 (7, raw evidence for the selectively-merged laws), audit/m16-litehtml (3, flag-gated litehtml prototype, OFF by design), cont24/skeleton-light-experiment (2, measured branch-only experiment).
- 2 stashes preserved (62 files, +12,352 lines — w20 corpus evidence).

## §8 Commit 9b953ce1 forensics (S7) — FIXED
Root cause: root .gitignore covered build/, build-asan/, build_prof/, build_dev_so/ but **not build_w24_cand_a/**, so the auto-add committed the whole candidate tree (53 files: the executable binary + 5 test exes + stamps + generated header). Every rebuild then showed the tracked binary as modified. Fix (051af519 + 186cfe63/aef7a8d2): build_w24*/ + build_fast/ + build_dev/ + build_p2*/ + build/ + download/batch614_624_evidence/ gitignored; 53 build files + the violating APK untracked via `git rm --cached`; SHAs preserved (binary a3013295…, APK af769233…); batch614/617 run logs + screenshots moved to miniandroid/evidence/batch614_624_evidence/ (APK excluded — §20 zero-APK law). No history rewrite; nothing deleted without provenance.

## §9 Completion checklist (this issue's §9)
- [x] All 234 published #632 findings carry individual dispositions (including the 40 the registry itself retracted/re-scoped — preserved, not hidden).
- [x] All mandatory issues/comments inspected (bodies + 11 registry comments + #630/#631 threads + the 16-issue body batch).
- [x] Recovered coder work preserved (MG-011 integrated; RC-12/layout-apps/MG-012/stroke-laws documented with exact blocker = coder-local branch).
- [x] Every ledger row: one canonical verdict; counts reconcile automatically (sum==rows==63, PASS).
- [x] Runtime vs tracker-state vs source-only claims separated (evidence-level column; AUD-36b/37b/38b splits).
- [x] Shared execution chain updated (INTEGRATION_MAP v2 incl. MG-011 + AUD-51).
- [ ] Remaining blockers (explicit): coder-local branch layout-geometry-001 (RC-12 + 10 apps + MG-012 + stroke laws); missing APKs (#597 OpenCalc, #618 Counter, #623 RNG, emmanuelmess ttt); UBSAN profile (AUD-47); BUG-7 dedupe (AUD-49); cmake full-test-build memory measurement; #632 per-finding focused tests beyond the 25 machine-checked cites.
"""
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/635/comments",
    data=json.dumps({"body": body}).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
             "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as r:
    d = json.load(r)
    print("posted comment:", d["html_url"])
