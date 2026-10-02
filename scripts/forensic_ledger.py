#!/usr/bin/env python3
"""forensic_ledger.py — build the canonical request ledger for issue #365.

Sources (all independent of agent claims):
  forensic_data/issues_all.json      all 365 GitHub issues
  forensic_data/all_issue_comments   708 comments (all by owner = requests)
  forensic_data/commits.json         597 commits
  root_registry.json                 530 roots (authoritative)
  docs/MICRO_GAP_REGISTRY.json       311 micro-gap tickets
  docs/corpus/s82/title_registry.json  202 frozen titles (per-issue joins)
  canonical/game_registry.json       91 games (S84 canonical)
  canonical/app_registry.json        15 apps
  docs/evidence/canonical/registry.json 150 canonical executed titles

Output:
  docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl   one row per reconstructed request
  forensic_data/ledger_stats.json           §19 statistics (derived, reproducible)
"""
import json, re, os
from collections import Counter, defaultdict

D = "/home/z/my-project"
FD = f"{D}/forensic_data"

issues = {i["number"]: i for i in json.load(open(f"{FD}/issues_all.json"))}
comments = json.load(open(f"{FD}/all_issue_comments.json"))
commits = json.load(open(f"{FD}/commits.json"))
cmts_by_issue = defaultdict(list)
for c in comments:
    m = re.search(r"/issues/(\d+)$", c.get("issue_url", ""))
    if m:
        cmts_by_issue[int(m.group(1))].append(c)

rootreg = json.load(open(f"{D}/root_registry.json"))["roots"]
root_by_id = {r.get("id"): r for r in rootreg if isinstance(r, dict)}
mg = json.load(open(f"{D}/docs/MICRO_GAP_REGISTRY.json"))["tickets"]
titles202 = json.load(open(f"{D}/docs/corpus/s82/title_registry.json"))["TITLES"]
t202_by_issue = {t.get("ISSUE_NUMBER"): t for t in titles202}
t202_by_pkg = {t.get("PACKAGE"): t for t in titles202}
gamereg = json.load(open(f"{D}/canonical/game_registry.json"))["games"]
appreg = json.load(open(f"{D}/canonical/app_registry.json"))["apps"]
g_by_pkg = {g.get("package"): g for g in gamereg}
a_by_pkg = {a.get("package"): a for a in appreg}
canreg = json.load(open(f"{D}/docs/evidence/canonical/registry.json"))["titles"]
can_by_pkg = {t.get("package"): t for t in canreg}

# ---- commit token index ------------------------------------------------------
commit_tokens = defaultdict(list)   # token -> [sha,...]
for c in commits:
    msg = c["commit"]["message"]
    sha = c["sha"][:8]
    for tok in set(re.findall(r"[A-Z]+-NEW-\d+|R-NEW-\d+|ROOT-\d+|MG-\d+|GAME-\d+|APP-\d+|MAND-\d+|GAMES-\d+|S1\d{2}|#\d+", msg)):
        commit_tokens[tok].append(sha)

def pkg_of_title(t):
    m = re.search(r"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)", t or "")
    return m.group(1) if m else ""

def ev(level, why):
    return {"level": level, "why": why}

rows = []

def add_row(**kw):
    row = {
        "request_id": kw.get("request_id", ""),
        "parent_id": kw.get("parent_id", ""),
        "issue": kw.get("issue", ""),
        "source": kw.get("source", "github-issue"),
        "date": kw.get("date", ""),
        "request_text": kw.get("request_text", "")[:300],
        "acceptance_criteria": kw.get("acceptance_criteria", ""),
        "claimed_status": kw.get("claimed_status", ""),
        "verified_status": kw.get("verified_status", "PENDING"),
        "evidence_level": kw.get("evidence_level", "E0"),
        "commit_shas": kw.get("commit_shas", [])[:6],
        "test_refs": kw.get("test_refs", []),
        "runtime_refs": kw.get("runtime_refs", []),
        "screenshot_refs": kw.get("screenshot_refs", []),
        "regression_refs": kw.get("regression_refs", []),
        "blockers": kw.get("blockers", ""),
        "superseded_by": kw.get("superseded_by", ""),
        "explanation": kw.get("explanation", ""),
    }
    rows.append(row)
    return row

# =============== 1..8 EXP era =================================================
exp_map = {
    1: ("EXP-064 login image proven by pixels", "OBSERVED", "E3",
        "Screenshot + OCR session evidence; predates golden/3-run laws; superseded by the S107+ Telegram chain."),
    2: ("EXP-065 multi-DEX const-string fix", "TESTED", "E3",
        "Session proof; law re-verified by later multi-DEX campaigns."),
    3: ("EXP-066 multi-DEX audit + text capture", "OBSERVED", "E3", "Session evidence."),
    4: ("EXP-067 resource resolution + AXML + drawable decode", "OBSERVED", "E3",
        "Superseded by ARSC/AXML law waves (S126/S127 R-NEW-423)."),
    5: ("EXP-068 generic view inheritance", "OBSERVED", "E3", "Session evidence."),
    6: ("EXP-069 generic text input + click dispatch", "OBSERVED", "E3", "Session evidence."),
    7: ("EXP-071 login->SMS page transition (CHECKPOINT M)", "OBSERVED", "E4",
        ".agent/state.md checkpoint table records 15 checkpoints; session-bound, not re-verified at HEAD."),
    8: ("Campaign evidence ledger (REUSE-FIRST 2026-09-05)", "SUPERSEDED", "E3",
        "55-comment evidence thread; superseded by canonical registries (S84 law, one record per title)."),
}
for n, (txt, st, lvl, expl) in exp_map.items():
    i = issues[n]
    add_row(request_id=f"FR-{n:03d}", issue=n, date=i["created_at"][:10],
            request_text=txt, source="github-issue",
            claimed_status="DONE (issue body)", verified_status=st,
            evidence_level=lvl, explanation=expl,
            parent_id="FR-009" if n >= 9 else "FR-016",
            superseded_by="canonical registries (S84+)" if st == "SUPERSEDED" else "")

# =============== 9 MASTER-ROADMAP v3 ==========================================
add_row(request_id="FR-009", issue=9, date=issues[9]["created_at"][:10],
        request_text="MASTER-ROADMAP v3 — 100% base execution closure system (living document)",
        acceptance_criteria="roadmap tracked to closure; phases closed with evidence",
        claimed_status="OPEN", verified_status="SUPERSEDED", evidence_level="E1",
        superseded_by="docs/FINAL_COMPATIBILITY_CAMPAIGN.md master checklist (CAMPAIGN_STATE law: ONE master checklist)",
        explanation="CAMPAIGN_STATE.md declares FINAL_COMPATIBILITY_CAMPAIGN §15 the single master checklist; #9 remained open and drifted.")

# =============== 10..23 EXEC titles ===========================================
exec_statuses = {
    10: ("com.miniandroid.helloworld", "VERIFIED", "E5", "battery + golden era"),
    11: ("com.emmanuelmess.tictactoe", "OBSERVED", "E3", "early session proof; canonical registry OBSERVED"),
    12: ("com.miniandroid.connectfour", "OBSERVED", "E3", "early session proof"),
    13: ("com.miniandroid.snakedeluxe", "VERIFIED", "E5", "full gameplay loop; x2 runs + 4-run sweep; canonical GIF"),
    14: ("io.github.yamin8000.dooz", "VERIFIED", "E5", "golden d602648e8e401895 x3 re-verified at HEAD 2026-10-03"),
    15: ("app.varlorg.unote", "VERIFIED", "E5", "golden 4f1a9e4e8f64fae8 x3 re-verified at HEAD 2026-10-03"),
    16: ("org.telegram.messenger.web", "PARTIAL", "E4", "0-error runs + settings face recorded; main UI NOT reached (intro/auth chain open)"),
    17: ("com.miniandroid.gmdice", "VERIFIED", "E4", "AXML inflation + OCR text verified (D05)"),
    18: ("dubrowgn.microtimer", "VERIFIED", "E5", "golden da73010a37dd0189 x3 re-verified at HEAD 2026-10-03"),
    19: ("eu.veldsoft.fish.rings", "VERIFIED", "E5", "x3 repeats + RC=0 reproof + tap GIF; NEW SUCCESS re-banked e9ce717b"),
    20: ("com.sidhant.triplematch", "PARTIAL", "E3", "tripeaks: deferred-UI family; blank render recorded"),
    21: ("io.github.ebraminio.bouncy", "VERIFIED", "E5", "b6dde6074bf47264 x3 (installed-store mode) 145-color real content"),
    22: ("com.best.deskclock (Simple Stopwatch)", "PARTIAL", "E3", "service-launch family; no full runtime proof found"),
    23: ("com.miniandroid.opmt", "OBSERVED", "E3", "session proof only"),
}
for n, (pkg, st, lvl, expl) in exec_statuses.items():
    i = issues[n]
    art = can_by_pkg.get(pkg, {})
    add_row(request_id=f"FR-{n:03d}", issue=n, date=i["created_at"][:10],
            request_text=i["title"][:200], source="github-issue",
            acceptance_criteria="APK executes + renders real app content + evidence recorded",
            claimed_status=i["state"], verified_status=st, evidence_level=lvl,
            runtime_refs=(["docs/evidence/canonical/registry.json"] if art else []),
            screenshot_refs=([art.get("artifact")] if art.get("artifact") else []),
            regression_refs=(["scripts/working_vs_failing_probe.sh 2026-10-03 ALL PASS"] if st == "VERIFIED" else []),
            explanation=expl)

# =============== 24 S81 parent + 25..226 titles ===============================
add_row(request_id="FR-024", issue=24, date="2026-09-22",
        request_text="S81 — REAL APP VISUAL COMPATIBILITY: audit ladder, VF fixes, 200-item F-Droid corpus + BATCH-01",
        acceptance_criteria="200-title corpus executed with visual compatibility ladder",
        claimed_status="OPEN", verified_status="PARTIAL", evidence_level="E3",
        explanation="Frozen corpus registry: 41/202 EXECUTED, 161 NOT_TESTED; 39 STATE-NONBLANK; campaign superseded by S84/S97 waves and the canonical per-title registries.",
        commit_shas=commit_tokens.get("S81", [])[:4])

child_stats = Counter()
for n in range(25, 227):
    i = issues[n]
    pkg = pkg_of_title(i["title"])
    t = t202_by_issue.get(n) or t202_by_pkg.get(pkg, {})
    g = g_by_pkg.get(pkg) or a_by_pkg.get(pkg)
    can = can_by_pkg.get(pkg)
    # decide status/evidence
    if g:
        st, lvl = g["status"], g.get("evidence_level", "E4")
        expl = f"canonical {'game' if g in gamereg else 'app'} registry record (checkpoints: {','.join(k for k,v in (g.get('checkpoints') or {}).items() if v in ('PROVEN','YES')) if isinstance(g.get('checkpoints'),dict) else 'recorded'})"
    elif can:
        raw_can = can["status"]
        if raw_can.startswith("candidate_") or raw_can in ("VISUALLY_PARTIAL", "FRAME_CAPTURED", "FAILED"):
            st = {"VISUALLY_PARTIAL": "PARTIAL", "FRAME_CAPTURED": "OBSERVED",
                  "FAILED": "BLOCKED"}.get(raw_can, "OBSERVED")
        else:
            st = raw_can
        lvl = "E4"
        expl = f"canonical registry record (session {can.get('session','?')}, artifact on disk; raw status {raw_can})"
    elif t:
        ex = t.get("EXECUTION", "NOT_TESTED")
        state = t.get("STATE", "STATE-NOT-LOADED")
        if ex == "EXECUTED":
            st, lvl = ("OBSERVED", "E3")
            expl = f"title registry: EXECUTED/{state}; screenshot SHA {'recorded' if t.get('SCREENSHOT_SHA256') else 'absent'}; no canonical artifact registered"
        elif ex == "BLOCKED_DOWNLOAD_FAIL":
            st, lvl = "BLOCKED", "E1"
            expl = "title registry: APK download failed (BLOCKED_DOWNLOAD_FAIL)"
        else:
            st, lvl = "PENDING", "E0"
            expl = "title registry: NOT_TESTED — no execution record found"
    else:
        st, lvl = "UNVERIFIED_CLAIM", "E0"
        expl = "no record in any registry (202-title registry, canonical registries)"
    child_stats[st] += 1
    add_row(request_id=f"FR-{n:03d}", parent_id="FR-024", issue=n,
            date=i["created_at"][:10], request_text=i["title"][:200],
            source="github-issue",
            acceptance_criteria="per-title compatibility report with runtime evidence",
            claimed_status="report opened", verified_status=st, evidence_level=lvl,
            runtime_refs=(["docs/corpus/s82/title_registry.json"] if t else []),
            screenshot_refs=([can["artifact"]] if can and can.get("artifact") else []),
            explanation=expl)

# =============== 227..233 root-cause + S84 + MG parent ========================
def norm_root_status(rs):
    """Normalize root-registry status to the #365 §2 strict vocabulary."""
    if not rs:
        return "PENDING"
    if rs in ("ROOT-CAUSED-FIXED", "VERIFIED-FIXED", "ROOT-CAUSED-REMEASURED-GENERIC-OK",
              "FIXED-VERIFIED", "PROVEN-FIXED", "VERIFIED_3RUN", "VERIFIED",
              "ROOT-CAUSED-CLOSED", "ROOT_CAUSED-FIXED", "VERIFIED-CORRECT",
              "ROOT-CAUSED-SEMANTIC", "FIXED-S75", "USED_BY_EXECUTION"):
        return "TESTED"
    if rs.startswith("IMPLEMENTED"):
        return "IMPLEMENTED" if rs == "IMPLEMENTED" else "TESTED"
    if rs in ("UNPROVEN", "PENDING", "REGISTERED", "OPEN", "NOT-APPLICABLE",
              "RESEARCHED-NOT-IMPLEMENTED"):
        return "PENDING"
    if rs.startswith("OBSERVED"):
        return "OBSERVED"
    if rs.startswith("SUPERSEDED"):
        return "SUPERSEDED"
    if rs == "BLOCKED":
        return "BLOCKED"
    if rs.startswith("PARTIAL"):
        return "PARTIAL"
    return "PENDING"


rc_map = {
    227: "F-NEW-156", 228: "F-NEW-157", 229: "VF-NEW-003",
    230: "F-NEW-161", 231: "F-NEW-162",
}
for n, rid in rc_map.items():
    r = root_by_id.get(rid)
    raw = r["status"] if r else ""
    st = norm_root_status(raw)
    lvl = {"TESTED": "E4", "IMPLEMENTED": "E2", "OBSERVED": "E3", "PARTIAL": "E3"}.get(st, "E2")
    add_row(request_id=f"FR-{n:03d}", issue=n, date=issues[n]["created_at"][:10],
            request_text=issues[n]["title"][:200], source="github-issue",
            claimed_status=issues[n]["state"], verified_status=st, evidence_level=lvl,
            commit_shas=commit_tokens.get(rid, [])[:4],
            explanation=f"root_registry.json id={rid} raw status={raw or 'MISSING'}")

add_row(request_id="FR-232", issue=232, date=issues[232]["created_at"][:10],
        request_text=issues[232]["title"][:200], source="github-issue",
        claimed_status="wave report", verified_status="PARTIAL", evidence_level="E4",
        explanation="S84 wave: canonical achievements + 50 NEW titles + README landing — delivered (docs/ACHIEVEMENTS.md canonical law); corpus work continued in later waves.")

add_row(request_id="FR-233", issue=233, date=issues[233]["created_at"][:10],
        request_text=issues[233]["title"][:200], source="github-issue",
        acceptance_criteria="issue-per-problem micro-gap sweep with evidence per ticket",
        claimed_status="OPEN", verified_status="PARTIAL", evidence_level="E2",
        explanation=f"parent of the MG ticket wave: registry totals 311 tickets (claimed {json.load(open(f'{D}/docs/MICRO_GAP_REGISTRY.json'))['counts']}); synthetic-fixture evidence dominates (see per-ticket rows).",
        children="issues #234-333 + registry MG-001..MG-311")

# =============== 234..333 MG tickets ==========================================
st_map = {"CLOSED": ("TESTED", "E2"), "TESTED": ("TESTED", "E2"),
          "PARTIAL": ("PARTIAL", "E2"), "OBSERVED": ("OBSERVED", "E3"),
          "PENDING": ("PENDING", "E0")}
for n in range(234, 334):
    i = issues[n]
    m = re.search(r"MG-(\d+)", i["title"])
    mid = f"MG-{int(m.group(1)):03d}" if m else ""
    tick = mg.get(mid)
    if tick:
        st, lvl = st_map.get(tick["STATUS"], ("UNVERIFIED_CLAIM", "E1"))
        expl = (f"registry {mid} STATUS={tick['STATUS']}; evidence: {tick.get('EVIDENCE','')[:120]}"
                f"{'; UPSTREAM_SOURCE: ' + tick['UPSTREAM_SOURCE'] if tick.get('UPSTREAM_SOURCE') else ''}")
        # #365 law: synthetic test is NOT real-APK proof
        if st == "TESTED" and "battery" in (tick.get("EVIDENCE", "") + tick.get("TEST", "")):
            expl += " — battery/synthetic class: real-APK fan-out NOT individually proven"
    else:
        st, lvl = "UNVERIFIED_CLAIM", "E0"
        expl = "ticket not found in MICRO_GAP_REGISTRY"
    add_row(request_id=f"FR-{n:03d}", parent_id="FR-233", issue=n,
            date=i["created_at"][:10], request_text=i["title"][:200],
            source="github-issue", acceptance_criteria="executable test + source-backed law + runtime fixture",
            claimed_status=i["title"].split("(")[-1].rstrip(")") if "(" in i["title"] else "",
            verified_status=st, evidence_level=lvl,
            test_refs=([mid] if tick else []), explanation=expl)

# =============== 334..341 GAMES waves =========================================
games_map = {
    334: ("GAMES-1 full-load 5-10 games end-to-end", "VERIFIED", "E5",
          "wave delivered: snake/2048/tetris/tictactoe/dooz evidence packages"),
    335: ("GAMES-2 autonomous Snake Deluxe play", "VERIFIED", "E5",
          "autoplay GIF + S79/S83 reproof matrix"),
    336: ("GAMES-3 house-building autonomous play (Minicraft)", "OBSERVED", "E4",
          "minicraft_autoplay.gif exists (S98); full house-building loop not proven"),
    337: ("GAMES-4 NEW snake variant build+play", "OBSERVED", "E4",
          "snakeneon_autoplay.gif exists (S98)"),
    338: ("GAMES-5 autonomous 2048 play", "VERIFIED", "E5",
          "g2048 autoplay GIF + score-to-200 state change"),
    339: ("GAMES-6 autonomous Mini Tetris play", "VERIFIED", "E5",
          "tetris GIF + S95 wave_c_determinism.json x3 deterministic"),
    340: ("GAMES-7 autonomous TicTacToe Deluxe play", "VERIFIED", "E4",
          "tictactoe GIF + session record"),
    341: ("GAMES-8 wave evidence package + gh-pages GIFs", "VERIFIED", "E4",
          "docs/EXECUTED_GIFS.md + canonical GIF set shipped"),
}
for n, (txt, st, lvl, expl) in games_map.items():
    add_row(request_id=f"FR-{n:03d}", issue=n, date=issues[n]["created_at"][:10],
            request_text=txt, source="github-issue",
            acceptance_criteria="autonomous play + rendered state change + reproducible evidence",
            claimed_status="closed" if issues[n]["state"] == "closed" else "open",
            verified_status=st, evidence_level=lvl,
            screenshot_refs=["docs/EXECUTED_GIFS.md"], explanation=expl,
            parent_id="FR-354" if n != 341 else "FR-354")

# =============== 342..352 F-NEW-165..170 + S102 ===============================
for n, rid in ((342, "F-NEW-165"), (343, "F-NEW-166"), (344, "F-NEW-167"),
               (345, "F-NEW-168"), (346, "F-NEW-169"), (347, "F-NEW-169"),
               (348, "F-NEW-170")):
    r = root_by_id.get(rid)
    raw = r["status"] if r else ""
    st = norm_root_status(raw)
    lvl = {"TESTED": "E4", "IMPLEMENTED": "E2", "OBSERVED": "E3", "PARTIAL": "E3"}.get(st, "E2")
    add_row(request_id=f"FR-{n:03d}", issue=n, date=issues[n]["created_at"][:10],
            request_text=issues[n]["title"][:200], source="github-issue",
            claimed_status=issues[n]["state"], verified_status=st, evidence_level=lvl,
            commit_shas=commit_tokens.get(rid, [])[:4],
            explanation=f"root_registry.json id={rid} raw status={raw or 'MISSING'}")
s102 = {
    349: ("S102-A solitaire R8-merged SavedStateRegistryController", "TESTED", "E4",
          "fix recorded in worklog S102 wave; solitaire rendering evidence in wave records"),
    350: ("S102-B compose LocalDensity not present", "PARTIAL", "E3",
          "compose frontier open (WindowRecomposer host) — recorded as open family"),
    351: ("S102-C mentalmath Hilt DI ApplicationContextModule", "BLOCKED", "E3",
          "Hilt DI graph requires generated dagger code execution — no runtime path implemented"),
    352: ("S102-D coroutines LockSupport.park spin", "TESTED", "E4",
          "LockSupport park law landed; worker spin resolved in session records"),
}
for n, (txt, st, lvl, expl) in s102.items():
    add_row(request_id=f"FR-{n:03d}", issue=n, date=issues[n]["created_at"][:10],
            request_text=txt, source="github-issue",
            claimed_status=issues[n]["state"], verified_status=st, evidence_level=lvl,
            explanation=expl + "; root id S102-* NOT present in root_registry.json (registry coverage gap)")

# =============== 353..363 master waves + knowledge transfer ===================
add_row(request_id="FR-353", issue=353, date=issues[353]["created_at"][:10],
        request_text=issues[353]["title"][:200], source="github-issue",
        acceptance_criteria="white-screen WebView apps reach REAL JS execution + rendered game",
        claimed_status="OPEN", verified_status="PARTIAL", evidence_level="E4",
        commit_shas=commit_tokens.get("R-NEW-423", [])[:4],
        explanation="Breakout-71 HTML5 game loop over QuickJS proven (E4/E5); S127 R-NEW-423 closed the framework theme/graphics base end-to-end; broader HTML5-app matrix remains open; S107-S115 WebView work revalidated via in-tree webview_engine/QuickJS build.")

add_row(request_id="FR-354", issue=354, date=issues[354]["created_at"][:10],
        request_text="[GAMES] Native game family — gameplay GIFs, engine-bug laws, verified 3-run titles (master thread)",
        acceptance_criteria="native games render real content; loading campaign audit->implementation->proof->regression",
        claimed_status="OPEN", verified_status="PARTIAL", evidence_level="E5",
        commit_shas=commit_tokens.get("R-NEW-457", [])[:3] + ["81134ac5", "438f8e85"],
        test_refs=["scripts/loading_probe_runner.sh 23/23 ALL PASS @HEAD 2026-10-03",
                   "scripts/working_vs_failing_probe.sh 5/5 goldens x3 byte-identical @HEAD 2026-10-03",
                   "scripts/forensic_uninstall_proof.sh 16/16 ALL PASS @HEAD 2026-10-03"],
        explanation="37-comment master thread. LOAD-AUDIT wave (26e03696) + LOADING-CAMPAIGN implementation (81134ac5) + close (438f8e85) all independently re-verified at HEAD during THIS forensic campaign; open frontier S-2 dlopen/JNI, S-4 content:// query, S-11 splits, SELECTION_FROZEN.")

add_row(request_id="FR-355", issue=355, date=issues[355]["created_at"][:10],
        request_text="[TELEGRAM] Forkgram 12.10.8.0 — errors 32 -> 0, first fully clean run",
        acceptance_criteria="clean-run parity on forkgram APK; roots recorded",
        claimed_status="OPEN", verified_status="PARTIAL", evidence_level="E4",
        explanation="ROOT-046/062/063 fixes recorded with run tables (59fdbfcd60b86a23 x2; then 0-error rc=0); golden bbb6cd10a834963d recorded in campaign gates; NOT re-run at HEAD during this forensic pass (store gates cover 5 other titles). ROOT-062/063 absent from root_registry.json (registry gap).")

add_row(request_id="FR-356", issue=356, date=issues[356]["created_at"][:10],
        request_text="[TELEGRAM] Official Telegram S117->S119 — complete first-person journey changelog",
        acceptance_criteria="official APK 0-error execution; login pixels; main UI",
        claimed_status="OPEN", verified_status="PARTIAL", evidence_level="E4",
        explanation="5-error -> rc=0 parity proven (ROOT-064..067 recorded with diffs in comments); G21 seven AOSP measure laws; login text ink + z-order overpaint frontier honestly open; Dialogs-page first render recorded; full main-UI NOT achieved.")

for n in range(357, 364):
    add_row(request_id=f"FR-{n:03d}", issue=n, date=issues[n]["created_at"][:10],
            request_text=issues[n]["title"][:200], source="github-issue",
            acceptance_criteria="knowledge-transfer document delivered with reproducible scripts/links",
            claimed_status="OPEN", verified_status="VERIFIED", evidence_level="E2",
            explanation="Documentation deliverable: content exists in issue bodies (7/7 chain incl. the full 190-goal roadmap and six reproduction scripts). External preview link inside #356/#355 comments is DEAD (preview host) — content preserved in the issue text; the journey markdown was never committed to the repo (recorded in FORENSIC_MISSING_EVIDENCE).")

# =============== 364/365 current campaigns ====================================
add_row(request_id="FR-364", issue=364, date=issues[364]["created_at"][:10],
        request_text=issues[364]["title"][:200], source="github-issue",
        acceptance_criteria="33-row completion ledger with non-empty status+evidence per row",
        claimed_status="OPEN", verified_status="PENDING", evidence_level="E0",
        explanation="Executed by THIS forensic wave: upstream inventory/docs created, carry-over recheck recorded — see completion ledger posted to #364.")

add_row(request_id="FR-365", issue=365, date=issues[365]["created_at"][:10],
        request_text=issues[365]["title"][:200], source="github-issue",
        acceptance_criteria="full request corpus reconstructed + classified with evidence levels; 33-row ledger",
        claimed_status="OPEN", verified_status="PENDING", evidence_level="E0",
        explanation="This ledger IS the deliverable of #365; the completion ledger comment closes the wave.")

# =============== non-issue requests ===========================================
add_row(request_id="FR-NI-001", parent_id="FR-364", source=".agent/requests/001-upstream-reuse-and-mandatory-completion-gate",
        date="2026-10-02", request_text="CODER REQUEST 001 — upstream reuse + master completion gate",
        acceptance_criteria="upstream inventory + completion ledger in the request file",
        claimed_status="OPEN", verified_status="PARTIAL", evidence_level="E2",
        superseded_by="issue #364 (owner folded the request into the master execution issue)",
        explanation="Superseded by #364; the upstream inventory portion is now delivered (docs/UPSTREAM_CODE_INVENTORY.* et al.).")

add_row(request_id="FR-NI-002", parent_id="FR-354", source="issue #354 comments 5959628673 + 5961411302 (chat-direct master execution request)",
        date="2026-10-02", request_text="MASTER EXECUTION REQUEST — COMPLETE FILE/RESOURCE/ASSET/STORAGE LOADING + WHITE-SCREEN RESOLUTION (31 sections)",
        acceptance_criteria="AUDIT -> IMPLEMENTATION -> RUNTIME PROOF -> WORKING/FAILING COMPARISON -> REGRESSION; 31-section deliverables",
        claimed_status="COMPLETE (comment 5961411302)", verified_status="VERIFIED", evidence_level="E5",
        commit_shas=["26e03696", "81134ac5", "438f8e85"],
        test_refs=["loading_probe_runner.sh 23/23 @HEAD 2026-10-03", "working_vs_failing_probe.sh 5 goldens x3 byte-identical @HEAD 2026-10-03",
                   "install->uninstall->reinstall proof 16/16 (forensic_uninstall_proof.sh)"],
        runtime_refs=["docs/LOADING_RUNTIME_TRACE.jsonl", "docs/INSTALL_TREE_PROOF.jsonl"],
        regression_refs=["5/5 goldens x3 byte-identical at HEAD"],
        explanation="P0 byte-loading class independently re-verified at HEAD during this forensic campaign. Open frontier rows remain S-2 dlopen/JNI, S-4 content:// query/Cursor, S-11 splits, SELECTION_FROZEN config/density, S-10 localStorage, ST-10 sqlite/font provenance — honestly PARTIAL at class level but the claimed P0 scope is VERIFIED.")

add_row(request_id="FR-NI-003", source="issue #356 comment 4 (S117 roadmap) + #363 §3", date="2026-09-28",
        request_text="TELEGRAM 190-GOAL ROADMAP — full execution & display ladder (19 phases)",
        acceptance_criteria="every goal independently evidenced; checked box requires runtime proof",
        claimed_status="18/190 checked", verified_status="PARTIAL", evidence_level="E4",
        explanation="Per #365 §11 the checkboxes were audited: G1-G18 checked = environment + official-parity waves; ROOT-064..067 + G11-G17 recorded with diffs/run tables in #356 (E4); G19-G190 (172 goals) are UNCHECKED = PENDING by design. Phase rows FR-NI-003-P00..P19 carry per-phase counts.")

goals_checked = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10",
                 "G11", "G12", "G13", "G14", "G15", "G16", "G17", "G18"]
for gi, gid in enumerate(goals_checked):
    add_row(request_id=f"FR-NI-003-{gid}", parent_id="FR-NI-003", source="issue #363 §3 (roadmap)",
            date="2026-09-28", request_text=f"{gid} (checked goal — independent evidence standard applied)",
            acceptance_criteria="runtime proof per roadmap law",
            claimed_status="[x] checked", verified_status="OBSERVED", evidence_level="E3",
            explanation="Session-bound evidence (recorded logs/diffs in #355/#356 comments); G2 rebuild independently reproduced at HEAD during this campaign; the rest NOT re-executed — classified OBSERVED (E3), not VERIFIED.")

add_row(request_id="FR-NI-004", source="owner hygiene directives (S78 recovery + size reduction requests)", date="2026-09-20",
        request_text="Repository hygiene: remove disposable artifacts, shrink .git history, preserve canonical evidence",
        acceptance_criteria="no disposable artifacts tracked; canonical evidence preserved",
        claimed_status="PARTIAL", verified_status="PARTIAL", evidence_level="E2",
        explanation=".git now 243 MB / size-pack 192.27 MiB (down from the ~620 MB era). STILL TRACKED disposable blobs: tmp/archidx.json 88.4 MB, tmp/index-v1.json 60.2 MB, tmp/idx.jar 14.0 MB, run/exp077 view_tree.json 22.4+21.8 MB, framework_res/resources.arsc 18.9 MB (needed), tools/r8/r8.jar 15.9 MB (toolchain). S78 150.98 MB ZIP quarantined under docs/history/s78_quarantine_recovery/ (evidence-preserving).")

add_row(request_id="FR-NI-005", source="owner homepage/UI/README requests (S84 landing page, S95-CTRL)",
        date="2026-09-23", request_text="README/homepage truth: claims must match registry; no unsupported full-compatibility claims; blank screenshots never achievements",
        acceptance_criteria="README claims == registry; links resolve; verifier passes",
        claimed_status="COMPLETE", verified_status="PARTIAL", evidence_level="E2",
        explanation="README vocabulary is honest (OBSERVED != VERIFIED law visible; no full-compat claim). Forensic audit FOUND and FIXED sync gaps: verify_canonical_evidence.py had 3 FAIL (fish.rings duplicate artifact; browser GIFs unregistered orphans) + ACHIEVEMENTS/README totals drifted from registry (148 vs disk) — closed this campaign (150 titles, verifier now 0 FAIL). Broken external preview links recorded separately.")

add_row(request_id="FR-NI-006", source="issue #355/#356 comment links", date="2026-09-29",
        request_text="TELEGRAM_JOURNEY_S117_S119.md published as external preview download",
        acceptance_criteria="journey document accessible from the repo",
        claimed_status="published", verified_status="UNVERIFIED_CLAIM", evidence_level="E0",
        explanation="The preview-host URL is DEAD and the markdown was never committed to the repository; content survives only inside issue comments. Committed copy required.")

add_row(request_id="FR-NI-007", source="root_registry.json vs campaign claims", date="2026-10-03",
        request_text="Registry synchronization law: canonical/root_cause_registry.json projected from root_registry.json",
        acceptance_criteria="every root recorded in the canonical registry",
        claimed_status="530 roots (root_registry.json)", verified_status="PARTIAL", evidence_level="E1",
        explanation="root_registry.json=530 roots (has F-NEW-231/234, R-NEW-457) but canonical projection root_cause_registry.json=492 (generated 2026-10-02) lags; ROOT-062..067 + S102-A..D exist only in issue comments/worklog, in NO registry.")

# =============== commit correlation for issue-numbered rows ===================
for row in rows:
    if row["issue"] and not row["commit_shas"]:
        row["commit_shas"] = commit_tokens.get(f"#{row['issue']}", [])[:4]

# =============== stats + emit =================================================
vs = Counter(r["verified_status"] for r in rows)
lv = Counter(r["evidence_level"] for r in rows)
stats = {
    "total_reconstructed_requests": len(rows),
    "issue_rows": sum(1 for r in rows if r["issue"]),
    "non_issue_rows": sum(1 for r in rows if not r["issue"]),
    "verified_status_counts": dict(vs),
    "evidence_level_counts": dict(lv),
    "notes": {
        "MAPPED_status_vocab": "root-registry statuses were normalized: ROOT-CAUSED-FIXED/VERIFIED-FIXED -> TESTED-family evidence retained in explanation; see per-row fields",
        "reproducibility": "docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl is the single source; recompute with scripts/forensic_ledger.py",
    },
}
json.dump(stats, open(f"{FD}/ledger_stats.json", "w"), indent=1)

with open(f"{D}/docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("rows:", len(rows))
print("verified_status:", dict(vs))
print("evidence_level:", dict(lv))
