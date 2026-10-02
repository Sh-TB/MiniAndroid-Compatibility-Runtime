#!/usr/bin/env python3
"""forensic_post_ledgers.py — post the 33-row completion ledgers to issues
#365 (forensic verification) and #364 (upstream + carry-over campaign)."""
import subprocess, json, urllib.request

out = subprocess.run(["git", "credential", "fill"],
                     input="protocol=https\nhost=github.com\n\n",
                     capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "forensic-campaign"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode(), headers=HDRS, method="POST")
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read())
    print(f"posted #{issue} comment", res["id"], res["created_at"])
    return res["id"]


C365 = """## FORENSIC VERIFICATION WAVE — completion ledger (33 rows)

Executed per `.agent/CODER_REQUEST_PROTOCOL.md`. **This ledger is claims until independently verified by the owner** — every row links the evidence it rests on.

**HEAD:** `af1171f3` (range examined: full post-hygiene history `4151e231..af1171f3`, 597 commits; issue dates reach back to 2026-08-19 — pre-4151e231 history was rewritten in the recorded S78 hygiene wave).
**Corpus:** 365 issues + 708 owner comments + 597 commits + 7 registries + worklog (5,932 lines) + `.agent` laws → **390 canonical request rows** (`docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl`).

**Exact statistics (§19, computed from the ledger — reproducible via `scripts/forensic_ledger.py`):** total reconstructed **390** · VERIFIED **30** · UNVERIFIED_CLAIM **1** · PARTIAL **43** · BLOCKED **5** · PENDING **122** · REGRESSED **0** · SUPERSEDED **2** (plus TESTED 82, OBSERVED 105 — the tested/observed classes are included in the row totals; claimed-complete-without-evidence is the UNVERIFIED_CLAIM row). Evidence levels: E0=122, E1=6, E2=112, E3=87, E4=50, E5=13.

**Answer to §24-A:** ~2/3 of claimed work is real and evidenced; the VERIFIED core is the loading-campaign P0 class + the golden game/app set (re-run at HEAD today); the 202-title corpus reports are mostly never executed (161/202 NOT_TESTED by the project's own registry); Telegram is PARTIAL (0-error parity proven, full display honestly open); micro-gap CLOSED labels are synthetic-class (E2 cap).

### 33-row ledger

| # | Item | STATUS — RESULT — EVIDENCE |
|---|---|---|
| 1 | Historical request corpus reconstructed | VERIFIED — 390 rows in `docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl` + methodology in `.md` — regenerate via `scripts/forensic_ledger.py` |
| 2 | All GitHub Issues correlated | VERIFIED — 365/365 issues classified (metadata in `forensic_data/issues_all.json`), per-row join in the ledger |
| 3 | Issue comments correlated | VERIFIED — 708/708 comments fetched + mapped per issue; all authored by owner (requests, not verification) |
| 4 | `.agent` request history correlated | VERIFIED — requests/001 ledger filled; `state.md`+`master_campaign_state.md` recorded STALE (EXP-090/D05 era) in UNVERIFIED doc §U6 |
| 5 | worklog/campaign history correlated | OBSERVED — full tail read (S84→LOADING-EXEC-CLOSE); task IDs indexed (25 recorded waves) |
| 6 | Telegram 190-goal history audited | PARTIAL — all 190 goals parsed from #363 §3; 18 checked goals independently downgraded to OBSERVED/E3 (`FR-NI-003-G*`); 172 open = PENDING by design |
| 7 | Runtime foundation audited | TESTED — 530-root registry spot-audited (F-NEW-165/167/170/231/234, R-NEW-457 = commit+test+trace); ROOT-062..067 found MISSING from all registries (gap row FR-NI-007) |
| 8 | File/storage audited | VERIFIED — ONE path law + write/read family re-proven at HEAD (probe gate 23/23, 2026-10-03) |
| 9 | Resource/APK audited | VERIFIED — asset contract (missing→FNFE both sites), ARSC/AXML laws, installed identity (F-NEW-231/234) re-proven by probe gate |
| 10 | Streams/FD/PFD/AFD audited | VERIFIED — real-fd layer + read(byte[]) fill law + AFD bytes==entry bytes (probe rows) |
| 11 | URI/provider audited | PARTIAL — provider install stage proven; content:// query/Cursor + FileProvider open (S-4 continuation) |
| 12 | SharedPreferences audited | VERIFIED — atomic tmp+rename, XML escape round-trip, honest commit, real clear/remove (probe rows) |
| 13 | SQLite audited | VERIFIED — real WAL + single databases_dir authority (probe: WAL/db persisted on store) |
| 14 | Java/libcore audited | TESTED — String/BAOS/read-fill laws probe-proven; broader libcore surface not exhaustively re-audited |
| 15 | DEX/runtime audited | TESTED — engine law spot-checks (ROOT-064..067 diffs in #356); no full interpreter re-audit in this pass |
| 16 | Graphics/text audited | OBSERVED — text-bearing goldens byte-identical ×3 at HEAD; S132/S127 law records checked |
| 17 | WebView/HTML5 audited | PARTIAL — QuickJS in-tree + Breakout-71 game loop evidence rechecked; wider HTML5 matrix open |
| 18 | Compose frontier audited | PARTIAL — S102-B LocalDensity/recomposer open; Hilt S102-C BLOCKED (recorded) |
| 19 | White/blank/grey/splash/settings audited | VERIFIED — `WHITE_SCREEN_LOADING_ROOTS.md` re-checked: no white screen attributed to loading without a trace; first-missing stages stand |
| 20 | Working-app explanations verified | VERIFIED — `WORKING_APP_LOADING_EXPLANATIONS.md` consistent with fresh traces (working apps never called the voided APIs) |
| 21 | Failing-app explanations verified | PARTIAL — deferred-UI family + intro/auth chain recorded; Telegram not re-run at HEAD (M3) |
| 22 | Upstream reuse verified | VERIFIED — 7 docs delivered (inventory 11 rows, not-used 10, plan 7, license 17, usage 9 incl. WIRED_NOT_CONSUMED honesty, update 5) |
| 23 | Micro-gap/battery claims verified | PARTIAL — 311 tickets classified at synthetic cap E2 (TESTED 131/CLOSED 79/PARTIAL 27/OBSERVED 15/PENDING 59 by registry, vocabulary-normalized in ledger) |
| 24 | Repository/hygiene claims verified | PARTIAL — .git 243 MB (down from ~620 MB era); `tmp/` still tracks ~177 MB disposable blobs (archidx 88.4 + index-v1 60.2 + idx.jar 14 + view_trees 44.2 MB); no history rewrite (law) |
| 25 | README/homepage/UI claims verified | PARTIAL — vocabulary honest; verifier had 3 FAILs (R4 fish.rings duplicate, R10 ×2 unregistered browser GIFs) → FIXED this wave (0 FAIL, registry 148→150, README/ACHIEVEMENTS/CANONICAL_SCREENSHOTS synced) |
| 26 | Evidence index built | VERIFIED — `docs/FORENSIC_EVIDENCE_INDEX.jsonl` (52 artifacts, path/bytes/sha) |
| 27 | Claims-vs-evidence report built | VERIFIED — `docs/FORENSIC_CLAIMS_VS_EVIDENCE.md` (§24 A–J) |
| 28 | Unverified claims report built | VERIFIED — `docs/FORENSIC_UNVERIFIED_CLAIMS.md` (U1–U7, exact missing evidence) |
| 29 | Regression status verified | VERIFIED — `FORENSIC_REGRESSION_STATUS.jsonl`: 4 current-HEAD gates + 2 historical justified re-baselines; REGRESSED=0 |
| 30 | Current HEAD verified | VERIFIED — gates re-run at HEAD after this wave's fixes: goldens 5/5 ×3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8), probe 23/23, uninstall proof 16/16, validator 0 FAIL |
| 31 | Canonical documents synchronized | VERIFIED — CAMPAIGN_STATE.md, worklog, requests/001 ledger, canonical registry + README/ACHIEVEMENTS updated; push `438f8e85..af1171f3` verified |
| 32 | No fabricated counts/claims | VERIFIED — all numbers derive from `FORENSIC_ALL_REQUESTS_LEDGER.jsonl` / `ledger_stats.json`; scripts persisted for reproduction |
| 33 | Final honest status published | VERIFIED — this ledger + the 10 canonical forensic docs; nothing closed beyond its evidence |

### Generic fixes this wave (§21, with regression)

1. **`uninstall` command IMPLEMENTED+TESTED** — AOSP deletePackage semantics (codePath + record + internal data + Android/data|media|obb removal; NOT_INSTALLED honesty; package-isolation); closes the recorded PENDING row of F-NEW-231. Proof: `scripts/forensic_uninstall_proof.sh` 16/16; post-fix regression goldens ×3 + probe gate ALL PASS.
2. **Canonical-evidence sync fix** — registry 148→150 (S100 browser legs registered with provenance), stale duplicate artifact removed; validator 0 FAIL.

### Blockers (§24-F, concrete)

S-2 dlopen/JNI · S-4 content:// query/Cursor · S-11 splits · SELECTION_FROZEN config/density/fonts · S-10 localStorage · ST-10 sqlite/font provenance · Compose/Hilt/libGDX frontiers · Safir/Black BLOCKED-BY-IDENTITY (no APKs/records).

### Continuation queue (§24-J, by fan-out × evidence value)

1. Backfill registries: ROOT-062..067 + S102-A..D; regenerate canonical projection (492→530) — M1.
2. Commit `TELEGRAM_JOURNEY_S117_S119.md` (dead preview link = the 1 UNVERIFIED_CLAIM) — M2.
3. Fresh `scripts/s117_tg_run.sh` official+forkgram at HEAD (regression M3).
4. SELECTION_FROZEN config/density port (fan-out: all qualifier resources).
5. S-4 content:// Cursor → S-2 dlopen/JNI → S-11 splits.
6. Real-APK fan-out spot-checks for synthetic-class micro-gaps; corpus 161 NOT_TESTED titles honest closure or execution.

**Per §27 this completion statement is a CLAIM.** The evidence files, scripts, gates and ledger are in the repo at `af1171f3` for independent inspection."""

C364 = """## UPSTREAM REUSE + CARRY-OVER CAMPAIGN — completion ledger (33 rows)

Executed jointly with the #365 forensic wave at HEAD `af1171f3`. Statuses per the protocol vocabulary; every row carries its evidence.

| # | Requirement | STATUS — RESULT — EVIDENCE |
|---|---|---|
| 1 | Laws read | VERIFIED — CONSTITUTION_V2, CAMPAIGN_STATE, worklog, `.agent/*` (+2 files recorded STALE), upstream sources cross-checked via reuse_registry |
| 2 | Upstream inventory complete | VERIFIED — `docs/UPSTREAM_CODE_INVENTORY.md` + `.jsonl` (11 rows: VENDORED/HOST-LINKED/AOSP-PORTED/ADAPTED/REGISTRY with runtime call paths) |
| 3 | Available-but-unused search complete | VERIFIED — `docs/UPSTREAM_AVAILABLE_NOT_USED.jsonl` (10 rows: nanoSVG/FFmpeg/Wuffs/resvg/litehtml/Lexbor/SDL2/Yoga/…, each with reason) |
| 4 | Duplicate/custom implementation audit complete | VERIFIED — `docs/UPSTREAM_RUNTIME_USAGE.jsonl` flags WIRED_NOT_CONSUMED (PortableGL, mpg123/sndfile) vs PROVEN consumers |
| 5 | License/attribution audit complete | VERIFIED — `docs/UPSTREAM_LICENSE_MATRIX.jsonl` (17 rows; AOSP Apache-2.0 attribution law noted) |
| 6 | Maintenance/update-path audit complete | VERIFIED — `docs/UPSTREAM_UPDATE_TRACKING.jsonl` (5 rows, per-component strategy) |
| 7 | Resource/APK loading audit/fixes | VERIFIED — P0 asset contract + ARSC/AXML laws re-proven at HEAD (probe 23/23) |
| 8 | File/storage/path audit/fixes | VERIFIED — ONE path law + write family + NEW uninstall (16/16 proof) |
| 9 | Stream audit/fixes | VERIFIED — read(byte[]) fill law, BAOS family (probe rows) |
| 10 | FD/PFD/AFD audit/fixes | VERIFIED — real-fd layer, AFD bytes == entry bytes (probe rows) |
| 11 | URI/provider audit/fixes | PARTIAL — install stage proven; query/Cursor + FileProvider = UPP-002 PENDING |
| 12 | SharedPreferences audit/fixes | VERIFIED — atomic+escape+honest commit (probe rows) |
| 13 | SQLite audit/fixes | VERIFIED — real WAL + single databases_dir (probe rows) |
| 14 | Java/libcore audit/fixes | TESTED — probe-proven String/stream laws; full surface open |
| 15 | DEX/runtime audit/fixes | TESTED — engine laws spot-verified; ROOT-062..067 recorded in #356 (registry backfill = continuation M1) |
| 16 | Graphics/text audit/fixes | TESTED — S132/S127 laws; text goldens byte-identical ×3 at HEAD |
| 17 | Working-app explanations | VERIFIED — `docs/WORKING_APP_LOADING_EXPLANATIONS.md` re-checked against fresh traces |
| 18 | White/blank/grey/splash tracing | VERIFIED — `docs/WHITE_SCREEN_LOADING_ROOTS.md` first-missing stages stand |
| 19 | Backlog P0 rechecked | VERIFIED — P0 class closed by loading campaign (re-proven) |
| 20 | Backlog P1 rechecked | PARTIAL — F-NEW-217/221, F-NEW-204..207/192 remain OPEN (master checklist rows 1-4) |
| 21 | Backlog P2 rechecked | PARTIAL — secuso families / golden re-banks partially banked (checklist rows 5,9) |
| 22 | Backlog P3 rechecked | PENDING — README/release audit phases NOT STARTED (checklist rows 14-15) |
| 23 | Loading campaign coverage rechecked | VERIFIED — 38-API coverage matrix + gates re-run at HEAD |
| 24 | Upstream campaign coverage rechecked | VERIFIED — this wave's 7 docs + reuse_registry reconciliation |
| 25 | High-fan-out implementation/porting | PARTIAL — uninstall wave done; SELECTION_FROZEN/S-2/S-4/S-11 = UPP-001..004 PENDING |
| 26 | Synthetic probes | VERIFIED — loading_probe 23/23 at HEAD |
| 27 | Real APK tests | VERIFIED — 5 goldens from installed stores (sources hidden), telegram installed ×3 record |
| 28 | 3-run reproducibility | VERIFIED — goldens ×3 byte-identical at HEAD (SHAs in REG-CURRENT-001) |
| 29 | Corpus regression | VERIFIED — gates ALL PASS; REGRESSED=0 (2 historical re-baselines justified) |
| 30 | Attribution/licenses/notices | PARTIAL — matrix built; NOTICE file for release still to add |
| 31 | Upstream update strategy | VERIFIED — UPDATE_TRACKING rows |
| 32 | Justification for remaining custom code | VERIFIED — AVAILABLE_NOT_USED reasons + WIRED_NOT_CONSUMED honesty + UPP plans |
| 33 | Final repository synchronization | VERIFIED — push `438f8e85..af1171f3`; CAMPAIGN_STATE/worklog/requests/001 synced; remote HEAD verified |

**Open rows keep this request OPEN by protocol:** rows 11/14/15/16/20/21/22/25/30 + the UPP plan. Continuation queue mirrors #365 (registry backfill → journey doc → fresh Telegram runs → SELECTION_FROZEN → S-4 → S-2 → S-11)."""

post(365, C365)
post(364, C364)
