#!/usr/bin/env python3
"""CLOSED-ISSUE FORENSIC PROGRAM — batches #367 (50 HIGH/HARD), #368 (50 MEDIUM),
#369 (8 FINAL). Builds the per-issue classification dataset (18 required fields
each) and emits the canonical artifacts:

  docs/CLOSED_BATCH_{1,2,3}_AUDIT.md / .jsonl
  docs/CLOSED_BATCH_{1,2,3}_CLAIMS_VS_EVIDENCE.md
  docs/CLOSED_BATCH_{1,2,3}_FALSE_CLOSURES.md
  docs/CLOSED_BATCH_{1,2,3}_REGRESSION_STATUS.jsonl
  docs/CLOSED_BATCH_{1,2,3}_EVIDENCE_INDEX.jsonl

Honesty laws honored: closed/open state is not evidence; pixel-truth law
(BYTE-STABLE != PIXEL-TRUTH, F-NEW-233); synthetic micro-gap tests are never
promoted beyond their scope; current-HEAD evidence required for
'verified current'; no package-specific hacks.
"""
import json, os, re, subprocess, hashlib
from pathlib import Path

BASE = Path("/home/z/my-project")
HEAD_FULL = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE,
                           capture_output=True, text=True).stdout.strip()
HEAD = HEAD_FULL[:8]

B1 = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 17, 18, 68, 81, 121, 166, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 334, 335, 336, 337, 338, 340, 341, 342, 345, 347, 349, 350, 352]
B2 = [252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 273, 274, 275, 276, 277, 279, 280, 285, 286, 287, 289, 291, 292, 293, 294, 298, 299, 300, 301, 302, 303, 305, 306, 307, 308, 309, 310, 313, 314, 315, 316]
B3 = [317, 318, 319, 321, 323, 331, 332, 333]
BATCH_OF = {}
for n in B1: BATCH_OF[n] = 1
for n in B2: BATCH_OF[n] = 2
for n in B3: BATCH_OF[n] = 3

def load(p):
    return json.load(open(p))

def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

titles, comments = {}, {}
for n in BATCH_OF:
    titles[n] = load(BASE/f"forensic_data/batch367/issue_{n}.json")["title"]
    cs = load(BASE/f"forensic_data/batch367/issue_{n}_comments.json")
    comments[n] = cs

fr = jl(BASE/"docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl")
fr_by_issue = {}
for r in fr:
    if r.get("issue") in BATCH_OF:
        fr_by_issue.setdefault(r["issue"], []).append(r)

mgr = load(BASE/"docs/MICRO_GAP_REGISTRY.json")["tickets"]

# ── current-HEAD evidence facts (produced this campaign) ──────────────────
BATTERY_FACT = ("run_test_battery.sh @ " + HEAD + ": BATTERY GATE ALL PASS "
                "(121/121 stages; logs run/batch367_battery_v2.log); includes "
                "s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs "
                "15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/"
                "audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, "
                "G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden "
                "SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family "
                "+ F-074/F-050 goldens, corpus runs, uninstall gates")
GOLDEN_FACT = ("user_golden_gate.py @ " + HEAD + ": 4/4 PASS REAL_APP_CONTENT "
               "(2048: 535 colors/0.59 nonbg/34 draw ops; Snake Deluxe: 1203/"
               "0.72/262; MiniCraft: 2416/0.64/735; HelloWorld canonical L6 "
               "sha 83720c1028f832d0) — run/user_goldens/user_goldens.json")
DETERM_FACT = ("working_vs_failing_probe.sh @ " + HEAD + ": 5/5 anchors x3 "
               "byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, "
               "dooz d602648e8e401895, microtimer da73010a37dd0189, unote "
               "4f1a9e4e8f64fae8) — DETERMINISM gate only per F-NEW-233 "
               "(chess/dooz frames 100% white; never visual success)")
PROBE_FACT = ("loading_probe_runner.sh @ " + HEAD + ": 23/23 PASS incl. "
              "restart-persistence x3 and package isolation")
UNINSTALL_FACT = ("forensic_uninstall_proof.sh @ " + HEAD + ": 16/16 PASS "
                  "(store-level uninstall/reinstall semantics)")
WAVE = load(BASE/"evidence/batch367_rerun/wave_summary.json")["results"]
S107 = load(BASE/"evidence/audit_s107/three_run/three_run_summary.json")

def wave_note(title, extra=""):
    r = WAVE.get(title)
    if not r or "rc" not in r:
        return extra
    px = r.get("pixels", {})
    return (f"fresh re-run at HEAD {HEAD}: rc={r['rc']}, status={r['status']}, "
            f"unique_colors={px.get('unique_colors')}, "
            f"frame_delta={r.get('frame_delta_tap')} {extra}").strip()

MG_STAGE_MAP = {
    "s106_gif_law_test": "s106 gif laws (expect 17) PASS 17/17",
    "s106_text2_law_test": "s106 text2 laws (expect 14) PASS 14/14",
    "s106_cia_law_test": "s106 canvas/input/audio laws (expect 21) PASS 21/21",
    "s106_drawables_law_test": "s106 drawables laws (expect 39) PASS 39/39",
    "s106_layout_net_law_test": "s106 layout/net laws (expect 11) PASS 11/11",
    "s98 text laws": "s98 text laws (expect 21) PASS 21/21",
    "s98 scroll/transform laws": "s98 scroll/transform laws (expect 13) PASS 13/13",
    "s98 prefs laws": "s98 prefs laws (expect 15) PASS 15/15",
}

def mg_record(n):
    t = titles[n]
    m = re.match(r"\[(MG-\d+)\]", t)
    mg_id = m.group(1)
    tk = mgr[mg_id]
    ev = (tk.get("EVIDENCE") or "")
    stages = []
    for key, label in MG_STAGE_MAP.items():
        if key in ev or key in (tk.get("AFTER") or ""):
            stages.append(label)
    stage_txt = "; ".join(dict.fromkeys(stages)) if stages else None
    domain = tk.get("DOMAIN", "")
    claim = (f"Micro-gap [{mg_id}] ({domain}): {tk.get('API','')} — fenced as a "
             f"synthetic law checkpoint in the frozen 202-question corpus; "
             f"BEFORE: {tk.get('BEFORE') or '(recorded at close)'}")
    evid = (f"MICRO_GAP_REGISTRY.json[{mg_id}] STATUS={tk.get('STATUS')}; "
            f"EVIDENCE: {ev or '(see registry)'}; COMMIT: {tk.get('COMMIT') or '(wave of record)'}")
    if stage_txt:
        runtime_proof = (f"law checkpoint binary/stage re-executed at current "
                         f"HEAD {HEAD}: {stage_txt} (part of {BATTERY_FACT})")
        classification = "verified current"
        gap = ("synthetic-fixture scope (test-only corpus law): real-APK "
               "exercise of this exact law not demonstrated unless ticket "
               "FANOUT names real titles — never promoted beyond scope per "
               "the M5 honesty rule")
    else:
        runtime_proof = f"recorded at close; not re-fenced at current HEAD"
        classification = "historical-only verification"
        gap = "law stage not part of the current battery; current re-fence pending"
    fanout = tk.get("FANOUT", "")
    if fanout and fanout not in ("not_measured", ""):
        gap += f"; FANOUT={fanout}"
    rec = {
        "issue_number": n,
        "title": t,
        "historical_claim": claim,
        "historical_evidence": evid,
        "tested_runtime_commit": tk.get("COMMIT") or "(wave of record; registry)",
        "current_head": HEAD_FULL,
        "apk_identity": "N/A (synthetic law battery — no real APK bound to this micro-gap)",
        "runtime_proof": runtime_proof,
        "viewtree_proof": "per-ticket machine checks (law-test asserts); no viewtree claim where N/A",
        "state_change_proof": (tk.get("AFTER") or "(per-ticket law asserts)")[:220],
        "screenshot_metrics": "band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only",
        "reproducibility": ("law battery re-runnable via scripts/test/run_test_battery.sh; "
                            "stage deterministic") if stage_txt else "single-fence at close",
        "first_divergence": "N/A (synthetic law checkpoint; no app-execution divergence recorded)",
        "root_family": f"MICRO-GAP/{domain}",
        "pixel_truth": ("law-level (synthetic); visual-success claims are NOT made "
                        "from micro-gap tickets"),
        "final_classification": classification,
        "evidence_refs": [
            "docs/MICRO_GAP_REGISTRY.json#" + mg_id,
            "scripts/test/run_test_battery.sh",
            "run/batch367_battery_v2.log",
        ] + (["docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl"] if n in fr_by_issue else []),
        "notes": f"FR rows: " + ", ".join(
            f"{r['request_id']}={r.get('verified_status')}/E{r.get('evidence_level','?')[1:] if isinstance(r.get('evidence_level'), str) else r.get('evidence_level')}"
            for r in fr_by_issue.get(n, [])) + (". Gap: " + gap if gap else ""),
    }
    return rec

# ── hand-authored records for the 32 non-MG issues ────────────────────────
def R(n, **kw):
    base = {
        "issue_number": n,
        "title": titles[n],
        "current_head": HEAD_FULL,
        "evidence_refs": [],
        "notes": "",
    }
    base.update(kw)
    return base

SPECIAL = {}
# — Telegram EXP era (#1-#8) —
SPECIAL[1] = R(1,
    historical_claim="EXP-064: Telegram login screen (PhoneView) rendered with REAL pixels, OCR-validated, proven by screenshot metrics.",
    historical_evidence="FR-001 (OBSERVED/E3): session screenshot + OCR; commits 1e1ec2b4/c322b479/1dda55ae/78c182f3; predates golden/3-run laws.",
    tested_runtime_commit="1e1ec2b4 (era)",
    apk_identity="Telegram-era session APK; golden APK later lost (K-26); official download = 1.2MB stub installer sha 480263f8 (BLOCKED-APK-ABSENT).",
    runtime_proof="session-era execution trace only; runtime chain superseded by S107+ Telegram boundary work; current carrier = forkgram (M3: x2 byte-identical bbb6cd10a834963d at abb57444).",
    viewtree_proof="session-era; not reconstructable at HEAD.",
    state_change_proof="login page transition primitives proven by later EXP chain (#5/#6/#7).",
    screenshot_metrics="session screenshot with OCR-validated text; no F-NEW-233 metrics (pre-law era).",
    reproducibility="not re-runnable at HEAD (artifact absent); 3-run law not applicable to session era.",
    first_divergence="N/A (historical session).",
    root_family="TELEGRAM/exp-era",
    pixel_truth="historical pixel evidence predates F-NEW-233; no current visual claim asserted.",
    final_classification="historical-only verification",
    evidence_refs=["docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl#FR-001", "issue #7 comments (S27 review)"],
    notes="Closed state honest for its era; superseded as current-carrier evidence by the S107+ chain and forkgram runs. Gap: golden Telegram APK lost.")
SPECIAL[2] = R(2,
    historical_claim="EXP-065: fixed the multi-DEX const-string bug (FIELD_PREFERRED_AUDIO_LANGUAGES leak) — strings from a second DEX resolve correctly.",
    historical_evidence="FR-002 (TESTED/E3): commits ff073348/b327292d/78c182f3; law re-verified by later multi-DEX campaigns.",
    tested_runtime_commit="ff073348 (era)",
    apk_identity="Telegram-era session APK (multi-DEX, 3+ DEX files).",
    runtime_proof="multi-DEX const-string law is live in the current binary: forkgram (5-DEX) x2 byte-identical runs at abb57444 + battery semantic pass3-bridge stage ALL PASS at " + HEAD + ".",
    viewtree_proof="N/A (string-resolution law).",
    state_change_proof="downstream field-preference text rendered correctly in-era.",
    screenshot_metrics="N/A.",
    reproducibility="law re-exercised every battery run; deterministic.",
    first_divergence="N/A.",
    root_family="DEX/multi-dex-strings",
    pixel_truth="N/A (non-visual law).",
    final_classification="verified current",
    evidence_refs=["FR-002", "run/batch367_battery_v2.log", "scripts/s117_tg_run.sh forkgram records"],
    notes="Law-level currency via current battery + forkgram determinism.")
SPECIAL[3] = R(3,
    historical_claim="EXP-066: multi-DEX semantic audit + OutlineTextContainerView text capture (phone number captured from real view text).",
    historical_evidence="FR-003 (OBSERVED/E3): commit 1e1ec2b4; session evidence.",
    tested_runtime_commit="1e1ec2b4 (era)",
    apk_identity="Telegram-era session APK.",
    runtime_proof="session-era; text-capture capability since generalized (text laws battery 21/21 at " + HEAD + ").",
    viewtree_proof="session-era OutlineTextContainerView capture.",
    state_change_proof="phone number text captured in-era.",
    screenshot_metrics="session-era.",
    reproducibility="not re-runnable at HEAD (artifact absent).",
    first_divergence="N/A.",
    root_family="TELEGRAM/exp-era",
    pixel_truth="historical only.",
    final_classification="historical-only verification",
    evidence_refs=["FR-003"],
    notes="Capability lineage continued by the current text pipeline.")
SPECIAL[4] = R(4,
    historical_claim="EXP-067: resource resolution + AXML parser + drawable decoding produced REAL WebP images in the login flow.",
    historical_evidence="FR-004 (OBSERVED/E3): commits 78c182f3 era; superseded by ARSC/AXML law waves (S126/S127 R-NEW-423).",
    tested_runtime_commit="78c182f3 (era)",
    apk_identity="Telegram-era session APK.",
    runtime_proof="superseded by stronger current laws: ARSC bag/style laws + AXML parse are battery-fenced (drawables 39/39 incl. AXML-driven vectors; G04 density oracle 11/11) at " + HEAD + ".",
    viewtree_proof="N/A.",
    state_change_proof="N/A.",
    screenshot_metrics="era WebP renders; superseded.",
    reproducibility="current via battery law stages.",
    first_divergence="N/A.",
    root_family="RESOURCES/arsc-axml",
    pixel_truth="current visual laws are fenced by band goldens + GATE-H.",
    final_classification="superseded",
    evidence_refs=["FR-004", "root_registry.json R-NEW-423 family", "run/batch367_battery_v2.log"],
    notes="Superseded by a strictly stronger current implementation (registry law chain).")
SPECIAL[5] = R(5,
    historical_claim="EXP-068: generic View inheritance + semantic superclass resolution produced the floating Next button.",
    historical_evidence="FR-005 (OBSERVED/E3): session evidence.",
    tested_runtime_commit="era session",
    apk_identity="Telegram-era session APK.",
    runtime_proof="view-inheritance laws since formalized (G11 ctor law 37/37 incl. superclass walk, F-074 engine-level super-run 6/6 GREEN at " + HEAD + ").",
    viewtree_proof="session-era view tree with floating button.",
    state_change_proof="button rendered + clickable (carried to #6).",
    screenshot_metrics="session-era.",
    reproducibility="laws current via battery; session not re-runnable.",
    first_divergence="N/A.",
    root_family="VIEW/inheritance",
    pixel_truth="historical.",
    final_classification="historical-only verification",
    evidence_refs=["FR-005", "miniandroid/tests/g11_ctor_law_test.cpp"],
    notes="Law lineage current; session claim itself not re-runnable.")
SPECIAL[6] = R(6,
    historical_claim="EXP-069: generic text input + click dispatch — phone number injected and Next clicked programmatically.",
    historical_evidence="FR-006 (OBSERVED/E3): session evidence.",
    tested_runtime_commit="era session",
    apk_identity="Telegram-era session APK.",
    runtime_proof="input/dispatch laws current: G06 tap interaction golden (21 law checks) + 3-run tap determinism + tictactoe 9/9 DEX-dispatched clicks at " + HEAD + ".",
    viewtree_proof="session-era.",
    state_change_proof="click state transitions proven in-era; current click laws battery-fenced.",
    screenshot_metrics="session-era.",
    reproducibility="laws re-fenced every battery run.",
    first_divergence="N/A.",
    root_family="INPUT/dispatch",
    pixel_truth="historical.",
    final_classification="historical-only verification",
    evidence_refs=["FR-006", "run/batch367_battery_v2.log (G06, tictactoe)"],
    notes="Session superseded; laws current.")
SPECIAL[7] = R(7,
    historical_claim="EXP-071: Telegram Login -> SMS Code page transition (CHECKPOINT_M PROVEN) end-to-end.",
    historical_evidence="FR-007 (OBSERVED/E4): 15 checkpoints in .agent/state.md (historical banner); S27 REVIEW approved at HEAD 79874955.",
    tested_runtime_commit="79874955 (S27 review head)",
    apk_identity="golden Telegram APK lost (K-26, docs/maintenance/NOT_DONE.md item 10); official download = 1.2MB stub (480263f8) BLOCKED-APK-ABSENT; forkgram_709208 = current carrier.",
    runtime_proof="checkpoint session evidence in-era; current-era Telegram boundary is an ARTIFACT problem, not runtime: forkgram installs + runs deterministically (x2 byte-identical at abb57444).",
    viewtree_proof="checkpoint-era view transitions.",
    state_change_proof="login -> SMS transition captured in-era.",
    screenshot_metrics="checkpoint-era captures (pre-F-NEW-233).",
    reproducibility="not re-runnable at HEAD without the lost APK; forkgram runs reproducible.",
    first_divergence="N/A.",
    root_family="TELEGRAM/checkpoint-era",
    pixel_truth="historical pixel claims predate the frame-truth law; no current visual VERIFIED claim is asserted from them.",
    final_classification="historical-only verification",
    evidence_refs=["FR-007", ".agent/state.md (HISTORICAL banner)", "docs/TELEGRAM_JOURNEY_S117_S119.md"],
    notes="Honest boundary: runtime capability proven historically; artifact acquisition remains blocked (consistent with #365 M3/M4).")
SPECIAL[8] = R(8,
    historical_claim="MiniAndroid campaign evidence mega-issue — 55-comment verified-achievements thread (REUSE-FIRST campaign 2026-09-05).",
    historical_evidence="FR-008 (SUPERSEDED/E3): superseded by canonical registries (S84+ one-record-per-title law).",
    tested_runtime_commit="campaign era",
    apk_identity="mixed (per-comment).",
    runtime_proof="superseded: canonical registries now the single source of truth (registry.json, root_registry.json, MICRO_GAP_REGISTRY.json, ARTIFACT_REGISTRY.json).",
    viewtree_proof="superseded.", state_change_proof="superseded.",
    screenshot_metrics="superseded.", reproducibility="via registries + battery.",
    first_divergence="N/A.", root_family="GOVERNANCE/registries",
    pixel_truth="per-record in registries.", final_classification="superseded",
    evidence_refs=["FR-008", "docs/evidence/canonical/registry.json"],
    notes="Clean supersession — the canonical-registry law replaced the evidence thread.")
# — EXEC era (#10-#18) —
SPECIAL[10] = R(10,
    historical_claim="[EXEC] HelloWorld: APK execution + visual proof (canonical L6 fixture).",
    historical_evidence="FR-010 (VERIFIED/E5): battery + golden era records.",
    tested_runtime_commit="golden era",
    apk_identity="org.miniandroid.helloworld fixture (rebuilt on demand; canonical artifact authority).",
    runtime_proof=GOLDEN_FACT,
    viewtree_proof="helloworld view tree with app text (battery hello golden 18 checks).",
    state_change_proof="text render deterministic.",
    screenshot_metrics="canonical artifact sha 83720c1028f832d0 (L6).",
    reproducibility="re-verified at " + HEAD + " (user golden gate).",
    first_divergence="N/A.", root_family="EXEC/hello",
    pixel_truth="PASS REAL_APP_CONTENT per F-NEW-233 gate.",
    final_classification="verified current",
    evidence_refs=["FR-010", "run/user_goldens/user_goldens.json", "scripts/user_golden_gate.py"],
    notes="User-designated golden test.")
SPECIAL[11] = R(11,
    historical_claim="[EXEC] TicTacToe: APK execution + gameplay proof (9 clicks, marks render, determinism).",
    historical_evidence="FR-011 (OBSERVED/E3): early session proof; canonical registry OBSERVED; the SS29 tictactoe_golden validator is the canonical fencing.",
    tested_runtime_commit="golden era",
    apk_identity="tictactoe fixture APK, SHA256 9d1c2954c675813cb5f890190f765bcca94662e76f9ceb7b90ce5eaa797fe858 (battery build).",
    runtime_proof="tictactoe_golden (SS29) stage PASS at " + HEAD + " inside " + BATTERY_FACT + ": 9/9 clicks DEX-dispatched, marks in cells with glyph ink, frames 7/8/9 frozen, run A/B 10-frame byte-identical (895fac7581b9...).",
    viewtree_proof="state machine validated from real DEX listeners (SS29 section [3]).",
    state_change_proof="click 1..9 state transitions asserted by SS29.",
    screenshot_metrics="frame SHAs asserted; pixel discriminators correct.",
    reproducibility="deterministic replay verified (run B).",
    first_divergence="N/A.",
    root_family="EXEC/tictactoe",
    pixel_truth="game-content pixel discriminators asserted; run exits via the documented F-NEW-233 PARTIAL verdict (laws hold; golden mandatory).",
    final_classification="verified current",
    evidence_refs=["FR-011", "miniandroid/tests/fixtures/tictacto e_golden/validate_tictactoe_golden.sh".replace(" ", ""), "run/batch367_battery_v2.log"],
    notes="SS29 validator re-baselined this campaign for the F-NEW-233 rc interplay (documented in-script; law checks unchanged).")
SPECIAL[12] = R(12,
    historical_claim="[EXEC] ConnectFour: APK execution + gameplay proof.",
    historical_evidence="FR-012 (OBSERVED/E3): early session proof only.",
    tested_runtime_commit="early era",
    apk_identity="early-session APK; not pinned in current canonical APK set.",
    runtime_proof="not re-run at current HEAD; not part of the battery.",
    viewtree_proof="session-era only.", state_change_proof="session-era.",
    screenshot_metrics="session-era.", reproducibility="not re-runnable at HEAD (artifact not in canonical set).",
    first_divergence="N/A.", root_family="EXEC/connectfour",
    pixel_truth="no current visual claim.",
    final_classification="historical-only verification",
    evidence_refs=["FR-012"],
    notes="Gap: APK not in the current canonical set; re-adoption would require artifact re-acquisition + 3-run fencing.")
SPECIAL[13] = R(13,
    historical_claim="[EXEC] AndroidGameSnake (zhangman.github.snake): autonomous gameplay proof (88 moves/22 turns/1 food; 4-run sweep).",
    historical_evidence="FR-013 (VERIFIED/E5): S73/S74 dossiers + canonical GIF + 4-run sweep at d7280a15; canonical dossier docs/compatibility/apps/androidgamesnake.json.",
    tested_runtime_commit="d7280a15 (S74 checkpoint)",
    apk_identity="upload/s72_w4_apks/snake_v1.0_vc1.apk (sha16 54cf48a9, pinned in dossier).",
    runtime_proof=wave_note("zhangman.github.snake", "— fresh execution at current HEAD via evidence/batch367_rerun/zhangman.github.snake/."),
    viewtree_proof="dossier: ConstraintLayout root + SnakePanelView EXACT 1080x780 (20x15dp x 2.625).",
    state_change_proof="frame delta TRUE at current HEAD (game animates); historical autonomous loop 88 moves.",
    screenshot_metrics="fresh run colors=41 (flat game palette); canonical GIF in docs/evidence/canonical/.",
    reproducibility="4-run sweep (S73) + fresh HEAD run; deterministic face recorded.",
    first_divergence="restart-after-game-over honestly NOT observed (dossier status_note) — open interaction gap.",
    root_family="EXEC/androidgamesnake",
    pixel_truth="real game content (board + snake) rendered; autoplay GIF canonical.",
    final_classification="verified current",
    evidence_refs=["FR-013", "docs/compatibility/apps/androidgamesnake.json", "evidence/batch367_rerun/zhangman.github.snake/record.json"],
    notes="Fresh current-HEAD execution closes the currency question; restart gap remains honestly open.")
SPECIAL[15] = R(15,
    historical_claim="[EXEC] Unote: runtime/UI completion (notes app renders + interacts).",
    historical_evidence="FR-015 (VERIFIED/E5): golden 4f1a9e4e8f64fae8 x3 re-verified at HEAD 2026-10-03.",
    tested_runtime_commit="current line",
    apk_identity="app.varlorg.unote_30.apk (upload/canonical_apks; installed store run/audit/regression/store_unote).",
    runtime_proof=DETERM_FACT + "; uninstall store keeps byte-identical app identity.",
    viewtree_proof="notes list view tree renders (golden era records).",
    state_change_proof="editor interactions in golden-era session records.",
    screenshot_metrics="golden sha da7301.../4f1a9e4e family recorded.",
    reproducibility="x3 byte-identical at " + HEAD + ".",
    first_divergence="N/A.", root_family="EXEC/unote",
    pixel_truth="REAL_APP_CONTENT era-verified visual golden.",
    final_classification="verified current",
    evidence_refs=["FR-015", "run/user_goldens/", "scripts/working_vs_failing_probe.sh"],
    notes="Also serves as an unrelated control in later fan-outs (diff366 zero drift).")
SPECIAL[17] = R(17,
    historical_claim="[EXEC] GMDice: APK execution + visual proof (AXML inflation + OCR text D05).",
    historical_evidence="FR-017 (VERIFIED/E4): AXML + OCR session records.",
    tested_runtime_commit="D05 era",
    apk_identity="de.duenndns.gmdice_8.apk (upload/canonical_apks; battery corpus set).",
    runtime_proof="battery corpus run stage PASS at " + HEAD + "; " + wave_note("de.duenndns.gmdice") + ".",
    viewtree_proof="dice UI inflated from real AXML.",
    state_change_proof="tap registered (no visual face change expected on static screen; frame delta False recorded honestly).",
    screenshot_metrics="fresh run colors=892 (real content).",
    reproducibility="battery stage deterministic; fresh HEAD run SUCCESS.",
    first_divergence="N/A.", root_family="EXEC/gmdice",
    pixel_truth="real dice UI pixels (892 colors) — passes visual sanity; no visual-VERIFIED claim beyond metrics.",
    final_classification="verified current",
    evidence_refs=["FR-017", "run/batch367_battery_v2.log (corpus run gmdice)", "evidence/batch367_rerun/de.duenndns.gmdice/record.json"],
    notes="OCR text proof is era evidence; current evidence = render + battery.")
SPECIAL[18] = R(18,
    historical_claim="[EXEC] MicroTimer: APK execution + visual proof.",
    historical_evidence="FR-018 (VERIFIED/E5): golden da73010a37dd0189 x3 re-verified at HEAD 2026-10-03.",
    tested_runtime_commit="current line",
    apk_identity="dubrowgn.microtimer_8.apk (miniandroid/download/exp076_corpus; installed store).",
    runtime_proof=DETERM_FACT + "; M3 F-012 persistence+fresh-state determinism golden PASS at " + HEAD + " (alarm row persists across runs; frames byte-deterministic across independent pairs).",
    viewtree_proof="timer UI tree rendered (golden era).",
    state_change_proof="DB row count 0->1->2 across runs (F-012 machine proof).",
    screenshot_metrics="golden da73010a37dd0189.",
    reproducibility="x3 byte-identical + F-012 two-pair determinism.",
    first_divergence="N/A.", root_family="EXEC/microtimer",
    pixel_truth="REAL_APP_CONTENT visual golden.",
    final_classification="verified current",
    evidence_refs=["FR-018", "run/batch367_battery_v2.log (M3 F-012)", "run/user_goldens/"],
    notes="F-012 stage helper re-baselined to the evolved FHS store layout (data/data/<pkg>) this campaign — documented in-script.")
# — GAME/APP reports (#68, #81, #121, #166) —
SPECIAL[68] = R(68,
    historical_claim="[GAME-044] com.smorgasbork.hotdeath compatibility report — full-load + render evidence.",
    historical_evidence="FR-068 (VERIFIED/E4): canonical game registry record; S107 audit 3-run VERIFIED_3RUN (634 unique colors, sha-stable 7c811bffb9a7c590, PARTIAL SUCCESS rc per F-NEW-233-era honesty).",
    tested_runtime_commit="S107 audit head (rebuilt from c0b7f501)",
    apk_identity="com.smorgasbork.hotdeath 1.0.11 (vc 11) per S107 three_run_summary.json.",
    runtime_proof="S107 x3 runs recorded; NOT re-run at current HEAD (APK not in current canonical set).",
    viewtree_proof="S107 run records.", state_change_proof="render evidence; interaction not claimed.",
    screenshot_metrics="634 colors / nonbg 0.108 / sha-stable x3.",
    reproducibility="3-run proven at S107 audit head.",
    first_divergence="N/A at current HEAD (not re-run).",
    root_family="GAME/report",
    pixel_truth="634-color content is real render; visual-VERIFIED not asserted beyond the registry record.",
    final_classification="historical-only verification",
    evidence_refs=["FR-068", "evidence/audit_s107/three_run/com.smorgasbork.hotdeath_run1..3", "docs/evidence/canonical/com.smorgasbork.hotdeath.gif"],
    notes="Gap: current-HEAD re-run pending APK re-acquisition; runtime itself regression-free at HEAD (battery 121/121).")
SPECIAL[81] = R(81,
    historical_claim="[GAME-057] org.bobstuff.bobball compatibility report.",
    historical_evidence="FR-081 (VERIFIED/E4): canonical record; S107 3-run VERIFIED_3RUN (476 colors, sha-stable).",
    tested_runtime_commit="S107 audit head",
    apk_identity="org.bobstuff.bobball per S107 three_run_summary.json.",
    runtime_proof="S107 x3 runs; not re-run at current HEAD.",
    viewtree_proof="S107 records.", state_change_proof="render evidence.",
    screenshot_metrics="476 colors, sha-stable x3.",
    reproducibility="3-run at S107 head.",
    first_divergence="N/A.", root_family="GAME/report",
    pixel_truth="real render; no beyond-registry claim.",
    final_classification="historical-only verification",
    evidence_refs=["FR-081", "evidence/audit_s107/three_run/org.bobstuff.bobball_run1..3", "docs/evidence/canonical/org.bobstuff.bobball.gif"],
    notes="Gap: current-HEAD re-run pending artifact.")
SPECIAL[121] = R(121,
    historical_claim="[GAME-097] com.dozingcatsoftware.bouncy compatibility report.",
    historical_evidence="FR-121 (VERIFIED/E4): canonical record; S107 3-run VERIFIED_3RUN (494 colors).",
    tested_runtime_commit="S107 audit head; re-confirmed at " + HEAD,
    apk_identity="upload/canonical_apks/bouncy.apk.",
    runtime_proof="diff366 ROOT-A fan-out at edecae3e: byte-identical zero drift; " + wave_note("com.dozingcatsoftware.bouncy") + " (rc=1 is the documented F-NEW-233 PARTIAL verdict, laws hold).",
    viewtree_proof="diff366 fan-out records (evidence/diff366/).",
    state_change_proof="tap registered in wave run (physics may pre-move; delta recorded honestly False on 3-frame window).",
    screenshot_metrics="fresh run colors=413 (S107: 494; palette stable family).",
    reproducibility="S107 x3 + current-HEAD runs.",
    first_divergence="N/A.", root_family="GAME/report",
    pixel_truth="real render both eras.",
    final_classification="verified current",
    evidence_refs=["FR-121", "evidence/diff366/", "evidence/batch367_rerun/com.dozingcatsoftware.bouncy/record.json"],
    notes="Bouncy doubles as an unrelated-app regression control (ROOT-A fan-out).")
SPECIAL[166] = R(166,
    historical_claim="[APP-042] org.ucam.ssb22.pinyinfdroid compatibility report.",
    historical_evidence="S107 closure comment: fresh run at HEAD 1818a325 + AUDIT RESULT 'closure re-verified VERIFIED 3RUN' (rebuilt from c0b7f501); S107 three_run_summary VERIFIED_3RUN (208 colors, sha-stable e03921ecbff1246d). The FR-166 PENDING/E0 row is STALE relative to this evidence.",
    tested_runtime_commit="1818a325 (S107) / c0b7f501 rebuild",
    apk_identity="org.ucam.ssb22.pinyinfdroid 2.12.74 (vc 109) per S107 records.",
    runtime_proof="x3 runs at S107 audit; not re-run at current HEAD (APK not in current canonical set).",
    viewtree_proof="S107 records.", state_change_proof="render evidence.",
    screenshot_metrics="208 colors / nonbg 0.015 (sparse UI) / sha-stable x3.",
    reproducibility="3-run at S107 head.",
    first_divergence="N/A.", root_family="APP/report",
    pixel_truth="sparse-content render honestly recorded (nonbg 0.015) — not a visual-success claim.",
    final_classification="historical-only verification",
    evidence_refs=["evidence/audit_s107/three_run/org.ucam.ssb22.pinyinfdroid_run1..3", "evidence/s107_games/org.ucam.ssb22.pinyinfdroid_run1..2", "issue #166 closure comments"],
    notes="FR ledger row corrected by this audit (PENDING -> evidence-backed historical verification).")
# — GAMES-1..8 —
SPECIAL[334] = R(334,
    historical_claim="[GAMES-1] Full-load 5-10 games end-to-end (launch + render + interaction evidence).",
    historical_evidence="FR-334 (VERIFIED/E5): docs/evidence/s98/games_full_load.json; closure comment 9/10 FULL_LOAD_PASS + 1 honest LOAD_ISSUE.",
    tested_runtime_commit="S98 wave",
    apk_identity="per-title pinned in games_full_load.json (in-house builds + corpus APKs).",
    runtime_proof="wave evidence + current-HEAD re-confirmation of the flagged titles: snake-deluxe (golden gate), 2048 (golden gate), tictactoedeluxe + snakeneon + androidgamesnake (" + wave_note("com.miniandroid.tictactoedeluxe") + " etc.).",
    viewtree_proof="per-run frame evidence under run/s98_*.",
    state_change_proof="interaction column in games_full_load.json (tap->SHA delta).",
    screenshot_metrics="ink ratios recorded per title at S98.",
    reproducibility="current subset re-run at HEAD (this campaign); full wave re-run possible via scripts/s98.",
    first_divergence="1 honest LOAD_ISSUE title recorded at S98 (never masked).",
    root_family="GAMES/wave",
    pixel_truth="ink metrics + interaction deltas; no white frame claimed as success.",
    final_classification="verified current",
    evidence_refs=["FR-334", "docs/evidence/s98/games_full_load.json", "evidence/batch367_rerun/wave_summary.json"],
    notes="The 1 honest LOAD_ISSUE remains recorded (honesty law).")
SPECIAL[335] = R(335,
    historical_claim="[GAMES-2] Autonomous Snake Deluxe play (self-play, no game-memory cheating).",
    historical_evidence="FR-335 (VERIFIED/E5): S80 vision-based driver re-run on S98 binary — 7 captures, final continuous 120-frame run with 56-frame SHA-pinned prefix; snake ate food and grew (C1/C3/C4/C7 laws held); autoplay GIF canonical.",
    tested_runtime_commit="S98 binary",
    apk_identity="com.miniandroid.snakedeluxe (upload/s80_games/build_sd; sha 551eca798f88c1bb).",
    runtime_proof=GOLDEN_FACT.split(";")[0] + " (Snake Deluxe leg).",
    viewtree_proof="game view renders (262 draw ops).",
    state_change_proof="food-eaten + growth state changes in the S98 autonomous run.",
    screenshot_metrics="screenshot sha 34a712689ce66e58; 1203 colors.",
    reproducibility="determinism-gated (user golden gate); driver re-runnable.",
    first_divergence="N/A.", root_family="GAMES/autoplay",
    pixel_truth="REAL_APP_CONTENT; autonomous-play proof is driver-based (no game-memory cheat) per S80 method.",
    final_classification="verified current",
    evidence_refs=["FR-335", "docs/evidence/s98/ (autoplay GIF)", "run/user_goldens/user_goldens.json"],
    notes="Vision-based driver method note kept from closure comment.")
SPECIAL[336] = R(336,
    historical_claim="[GAMES-3] House-building autonomous play (Minicraft): real taps (dpad walk + BLOCK cycle + PLACE/DIG + DEMO); cottage built.",
    historical_evidence="FR-336 (OBSERVED/E4): S98 driver — cursor moved (269,712)->(577,1000); materials placed brick 0->68432px, plank 0->49392px, roof 0->113190px; digs observed; minicraft_autoplay.gif canonical.",
    tested_runtime_commit="S98 binary",
    apk_identity="com.miniandroid.minicraft (s86_games build).",
    runtime_proof=GOLDEN_FACT.split(";")[0] + " (MiniCraft leg: REAL_APP_CONTENT, 735 draw ops).",
    viewtree_proof="game canvas renders.",
    state_change_proof="material-placement pixel deltas are the recorded state-change proof (S98).",
    screenshot_metrics="screenshot sha 46d3de34-family recorded in user_goldens.json (2416 colors).",
    reproducibility="app re-verifies at HEAD; driver re-runnable (scripts/s98/s98_minicraft_autoplay.py).",
    first_divergence="full house-building LOOP end-to-end automation not claimed beyond the S98 material deltas (honest FR OBSERVED).",
    root_family="GAMES/autoplay",
    pixel_truth="REAL_APP_CONTENT; autoplay evidence = pixel-delta based.",
    final_classification="verified current",
    evidence_refs=["FR-336", "docs/evidence/s98/minicraft_autoplay.gif", "run/user_goldens/user_goldens.json"],
    notes="Currency: app render re-verified at HEAD; the autonomous house-build proof remains the S98 driver record (scope honestly stated).")
SPECIAL[337] = R(337,
    historical_claim="[GAMES-4] NEW snake variant (snake-neon) — build, load, autonomous play; mechanically NEW (wrap-around walls + obstacles + speed HUD).",
    historical_evidence="FR-337 (OBSERVED/E4): S98 build (9156 teal px + 1252 food px, 0 errors) + snakeneon_autoplay.gif; FULL_LOAD_PASS row in games_full_load.json.",
    tested_runtime_commit="S98 binary",
    apk_identity="com.miniandroid.snakeneon (upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk).",
    runtime_proof=wave_note("com.miniandroid.snakeneon", "— frame delta TRUE (game animates)."),
    viewtree_proof="game HUD + board render.",
    state_change_proof="frame delta TRUE at HEAD; autonomous-play GIF at S98.",
    screenshot_metrics="fresh run colors=884.",
    reproducibility="fresh HEAD run + S98 GIF.",
    first_divergence="N/A.", root_family="GAMES/new-variant",
    pixel_truth="real game content both eras.",
    final_classification="verified current",
    evidence_refs=["FR-337", "docs/evidence/s98/snakeneon_autoplay.gif", "evidence/batch367_rerun/com.miniandroid.snakeneon/record.json"],
    notes="Fresh current-HEAD execution upgrades the OBSERVED row with currency evidence.")
SPECIAL[338] = R(338,
    historical_claim="[GAMES-5] Autonomous 2048 play (GIF + score-to-200 state change).",
    historical_evidence="FR-338 (VERIFIED/E5): g2048 autoplay GIF + score state change.",
    tested_runtime_commit="S-era autoplay; golden current",
    apk_identity="com.miniandroid.g2048 (upload/s80_games/g2048).",
    runtime_proof=GOLDEN_FACT.split(";")[0] + " (2048 leg: REAL_APP_CONTENT, 34 draw ops).",
    viewtree_proof="2048 board renders.",
    state_change_proof="score progression to 200 recorded in the autoplay session.",
    screenshot_metrics="screenshot sha 7ad9a8bdefba539b; 535 colors.",
    reproducibility="determinism-gated (user golden gate).",
    first_divergence="N/A.", root_family="GAMES/autoplay",
    pixel_truth="REAL_APP_CONTENT.",
    final_classification="verified current",
    evidence_refs=["FR-338", "run/user_goldens/user_goldens.json", "docs/evidence/canonical/"],
    notes="User-designated golden test.")
SPECIAL[340] = R(340,
    historical_claim="[GAMES-7] Autonomous TicTacToe Deluxe play (GIF + session record).",
    historical_evidence="FR-340 (VERIFIED/E4): tictactoe deluxe GIF + session record; canonical GIF docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif.",
    tested_runtime_commit="S-era; fresh at " + HEAD,
    apk_identity="com.miniandroid.tictactoedeluxe (rebuilt via scripts/s83_build_tictactoe.sh — canonical aapt2/ECJ/D8 recipe).",
    runtime_proof=wave_note("com.miniandroid.tictactoedeluxe", "— tap interaction produced frame delta TRUE."),
    viewtree_proof="board grid renders (2022 colors).",
    state_change_proof="frame delta TRUE on tap at HEAD.",
    screenshot_metrics="fresh run colors=2022.",
    reproducibility="build recipe deterministic; fresh HEAD run SUCCESS.",
    first_divergence="N/A.", root_family="GAMES/autoplay",
    pixel_truth="real board content.",
    final_classification="verified current",
    evidence_refs=["FR-340", "docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif", "evidence/batch367_rerun/com.miniandroid.tictactoedeluxe/record.json"],
    notes="Registry graphics verdict record exists (registry/graphics_verdicts/).")
SPECIAL[341] = R(341,
    historical_claim="[GAMES-8] Wave evidence package + gh-pages gameplay GIFs (docs/evidence/s98/ + EXECUTED_GIFS.md).",
    historical_evidence="FR-341 (VERIFIED/E4): closure comment lists games_full_load.json + minicraft_autoplay.gif + snakeneon_autoplay.gif + per-run frame evidence.",
    tested_runtime_commit="S98 wave (artifact set)",
    apk_identity="N/A (evidence-package claim).",
    runtime_proof="artifact existence verified at " + HEAD + ": docs/evidence/s98/games_full_load.json, minicraft_autoplay.gif, snakeneon_autoplay.gif present; docs/EXECUTED_GIFS.md + canonical GIF set present; docs/verified_executed_games.json (26 games) present.",
    viewtree_proof="N/A.", state_change_proof="N/A.",
    screenshot_metrics="N/A (package claim).",
    reproducibility="artifact checks re-runnable.",
    first_divergence="N/A.", root_family="GAMES/evidence-package",
    pixel_truth="N/A.", final_classification="verified current",
    evidence_refs=["FR-341", "docs/EXECUTED_GIFS.md", "docs/evidence/s98/", "docs/verified_executed_games.json"],
    notes="Existence + integrity of the evidence package is the claim; verified.")
# — F-NEW / S102 —
SPECIAL[342] = R(342,
    historical_claim="[F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attribute resolution chain killed apps on deep MaterialComponents style chains.",
    historical_evidence="root_registry.json F-NEW-165 = ROOT-CAUSED-FIXED; S100 closure comment: ARSC parent-chain max_parent_hops=8 bound MyKanji's ~12-14-hop MaterialComponents chain -> fix bound/extended the hop law.",
    tested_runtime_commit="S100 wave",
    apk_identity="MyKanji face (com...mykanji era APK); family-generic fix.",
    runtime_proof="ARSC style law current: M3 ARSC style law 17/17 + M3 style geometry golden (6 checks) + density-matrix oracle 11/11 at " + HEAD + "; before/after: droidify DEFAULT_BACKGROUND_ONLY -> REAL content (registry before/after).",
    viewtree_proof="registry before/after records.",
    state_change_proof="theme resolution now completes; apps inflate past createSubDecor.",
    screenshot_metrics="registry before/after face metrics.",
    reproducibility="battery ARSC stages re-run every battery.",
    first_divergence="next divergence moved downstream (registry notes).",
    root_family="RESOURCES/theme-gate",
    pixel_truth="after-face REAL content per registry.",
    final_classification="verified current",
    evidence_refs=["root_registry.json#F-NEW-165", "run/batch367_battery_v2.log (ARSC stages)"],
    notes="Generic theme-chain law (no package conditionals).")
SPECIAL[345] = R(345,
    historical_claim="[F-NEW-168] crash-on-launch family: dooz rc=-11 SIGSEGV (process death) + raumballer/tictactoe-classic rc=1 NPE chains — DoD: no-signal law + named next frontiers.",
    historical_evidence="root_registry.json F-NEW-168 = OBSERVED-FAIL (WhatsApp-chain faces honestly open); S100 closure comment: dooz rc=-11 ROOT-CAUSED + FIXED (LayoutInflater::measure_raw child_sizes built before real-DEX onMeasure hook materialized views).",
    tested_runtime_commit="S100 wave; current " + HEAD,
    apk_identity="io.github.yamin8000.dooz_23 (installed store run/audit/regression/store_dooz).",
    runtime_proof="dooz determinism x3 byte-identical at " + HEAD + " (" + DETERM_FACT.split(":")[1].split(";")[0].strip() + "); graceful rc; no signal — no-signal law holds; crash_forensics last-op ring (S100 SS3) in binary.",
    viewtree_proof="dooz view tree composes (ComposeView materialization documented separately).",
    state_change_proof="no process death across 3 runs.",
    screenshot_metrics="dooz face = 100% white (0 app draw ops) — DETERMINISM anchor only.",
    reproducibility="x3 every regression run.",
    first_divergence="raumballer / tictactoe-classic NPE chains remain the named next frontier (honestly open; registry OBSERVED-FAIL).",
    root_family="CRASH/no-signal",
    pixel_truth="BYTE-STABLE != PIXEL-TRUTH: dooz white frames anchor determinism only — never visual success.",
    final_classification="verified current",
    evidence_refs=["root_registry.json#F-NEW-168", "scripts/working_vs_failing_probe.sh", "run/batch367_battery_v2.log"],
    notes="Classification applies to the issue's DoD (no-signal + named frontiers); the family's remaining faces stay honestly OBSERVED-FAIL.")
SPECIAL[347] = R(347,
    historical_claim="[F-NEW-169] dooz compose-navigation NPE chain — 3 named roots + 2 cascades after the rc=-11 fix.",
    historical_evidence="closure comment at HEAD 176710b1: all 3 named roots + 2 cascades executed with commits (Handler.postAtFrontOfQueue null-receiver law; Object.getClass null via Field.get reflection family; View.getWidth null).",
    tested_runtime_commit="176710b1 (closure head)",
    apk_identity="io.github.yamin8000.dooz_23_toplevel.apk / dooz_23 (installed store).",
    runtime_proof="dooz runs gracefully x3 byte-identical at " + HEAD + "; 41/41-frame runs recorded at closure.",
    viewtree_proof="compose tree materialization documented in the ROOT-D 4-way separation (not merged into a single 'Compose root').",
    state_change_proof="no uncaught NPE chains at onCreate after fixes.",
    screenshot_metrics="dooz frames 100% white (0 app draw ops) — composition materializes but does not draw (ROOT-D case 2).",
    reproducibility="x3 determinism every regression run.",
    first_divergence="dooz's remaining divergence = rendering backend (Compose no-draw frontier; ROOT-D case family) — honestly documented, NOT closed.",
    root_family="COMPOSE/navigation-NPE",
    pixel_truth="BYTE-STABLE != PIXEL-TRUTH: dooz is a determinism anchor; no visual-success claim.",
    final_classification="verified current",
    evidence_refs=["root_registry.json#F-NEW-169", "scripts/working_vs_failing_probe.sh", "docs/DIFFERENTIAL_WORKING_VS_WHITE.md"],
    notes="Crash-law closure is current; the visual frontier remains open by design of the honest 4-way Compose separation.")
SPECIAL[349] = R(349,
    historical_claim="[S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked on R8-merged MatcherMatchResult null receiver.",
    historical_evidence="closure comment at HEAD 176710b1 (S104 FIX-005 / S106 re-verification) to L5; root analysis: R8 horizontal class merging; solitaire_71 face also root-caused via F-NEW-160 (DEX instance-field identity law).",
    tested_runtime_commit="176710b1; field-identity law current at " + HEAD,
    apk_identity="com.vayunmathur.games.solitaire.",
    runtime_proof="fix laws live in the current binary (F-NEW-160 in root_registry; solitaire reaches onStart, 3-run 6588621c4a0c4182 frontier state recorded); battery 121/121 at " + HEAD + " with zero drift on unrelated goldens.",
    viewtree_proof="S134-era sol_v13.log records (delegate constructed; AppCompat theme machinery ran).",
    state_change_proof="chain advanced past SavedStateRegistry attach (per closure evidence).",
    screenshot_metrics="3-run face SHA 6588621c4a0c4182 (frontier state).",
    reproducibility="law current; solitaire face re-runnable.",
    first_divergence="next faces honestly recorded (SharedPreferences.getBoolean null at c/m.aR, FragmentManager family) — open frontier.",
    root_family="R8/horizontal-merge",
    pixel_truth="no visual claim asserted.",
    final_classification="verified current",
    evidence_refs=["issue #349 closure comment", "root_registry.json#F-NEW-160", "run/s134/ records"],
    notes="REGISTRY GAP (recorded, not masked): literal id 'S102-A' is absent from root_registry.json — its laws are covered under F-NEW-160 family; cross-reference recorded by this audit.")
SPECIAL[350] = R(350,
    historical_claim="[S102-B] compose frontier: 'CompositionLocal LocalDensity not present' at WindowRecomposer host creation killed composition startup.",
    historical_evidence="closure comment at HEAD 176710b1: named blocker no longer occurs (windowRecomposer host laws landed).",
    tested_runtime_commit="176710b1; current " + HEAD,
    apk_identity="com.vayunmathur.games.solitaire (+ eu.veldsoft.no.thanks family).",
    runtime_proof="LocalDensity ISE eliminated (closure evidence); Compose pipeline laws current: F-NEW-179 canonical pump + F-NEW-201 one-stable-content-object (registry IMPLEMENTED); battery compose-adjacent stages pass at " + HEAD + ".",
    viewtree_proof="ROOT-D 4-way separation: (1) ComposeView materialization, (2) composition-without-draw, (3) recomposer/state machinery, (4) rendering backend — documented separately, NOT merged.",
    state_change_proof="composition starts (was: ISE before any composition).",
    screenshot_metrics="compose faces remain non-drawing (ROOT-D case 2) — honest.",
    reproducibility="gates re-run every regression.",
    first_divergence="Compose titles still do not reach visible app pixels: the compose-no-draw + recomposer + backend cases are the OPEN frontier (docs/DIFFERENTIAL_WORKING_VS_WHITE.md).",
    root_family="COMPOSE/recomposer",
    pixel_truth="no visual success claimed for Compose titles.",
    final_classification="partial closure",
    evidence_refs=["issue #350 closure comment", "root_registry.json (F-NEW-179/201)", "docs/DIFFERENTIAL_WORKING_VS_WHITE.md"],
    notes="Named blocker fixed; the broader Compose visual frontier remains open — honest partial.")
SPECIAL[352] = R(352,
    historical_claim="[S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park family).",
    historical_evidence="FR-352 (TESTED/E4): LockSupport park law landed; worker spin resolved in session records (S102 wave).",
    tested_runtime_commit="S102 wave; current " + HEAD,
    apk_identity="coroutines-bearing titles (dooz DispatchedContinuation real-APK evidence cited by the battery F-074 note).",
    runtime_proof="park law live: F-074 fixture (which encodes the dooz DispatchedContinuation drained-continuation law) runs 6/6 GREEN at " + HEAD + "; F-050 frame-pump golden PASS (pump starvation law); battery 121/121.",
    viewtree_proof="N/A (scheduler law).",
    state_change_proof="worker parks instead of spinning (session records + law fixture).",
    screenshot_metrics="F-074 6-band verdicts GREEN.",
    reproducibility="F-074/F-050 stages re-run every battery.",
    first_divergence="N/A.",
    root_family="CONCURRENCY/coroutines",
    pixel_truth="N/A (non-visual law).",
    final_classification="verified current",
    evidence_refs=["FR-352", "miniandroid/tests/fixtures/f074_super_run", "run/batch367_battery_v2.log (F-074/F-050)"],
    notes="REGISTRY GAP (recorded): literal id 'S102-D' absent from root_registry.json; laws covered by F-074/F-050 fixture law family + R-NEW-345 park-drain law.")

records = {n: (SPECIAL[n] if n in SPECIAL else mg_record(n)) for n in BATCH_OF}

# ── validation ────────────────────────────────────────────────────────────
REQUIRED = ["issue_number", "title", "historical_claim", "historical_evidence",
            "tested_runtime_commit", "current_head", "apk_identity", "runtime_proof",
            "viewtree_proof", "state_change_proof", "screenshot_metrics",
            "reproducibility", "first_divergence", "root_family", "pixel_truth",
            "final_classification", "evidence_refs", "notes"]
missing = []
for n, r in records.items():
    for k in REQUIRED:
        if k not in r or r[k] in (None, ""):
            missing.append((n, k))
assert not missing, f"missing fields: {missing}"
VOCAB = {"false closure", "historical-only verification", "current regression",
         "blocked APK/fetch", "partial closure", "test-only", "superseded",
         "verified current"}
for n, r in records.items():
    assert r["final_classification"] in VOCAB, (n, r["final_classification"])

json.dump(records, open(BASE/"forensic_data/batch367/records_final.json", "w"), indent=1)
from collections import Counter
print("records:", len(records))
print(Counter(r["final_classification"] for r in records.values()))
print("OK -> forensic_data/batch367/records_final.json")
