#!/usr/bin/env python3
"""CONTINUATION — final completion ledgers to issues #364, #365, #366
(same-Issue protocol; STATUS — RESULT — EVIDENCE per row)."""
import json, subprocess, sys

HEAD = "abb57444a75d0f1788ef527c373af472768c7699"
BIN16 = "15599ee7129be128"

COMMON = f"""
CURRENT HEAD `{HEAD}` · runtime binary sha256-16 `{BIN16}` (rebuilt in-wave from the
ROOT-A/B/C generic fixes; regression gates re-proven after every rebuild).
"""

L366 = COMMON + r"""
# DIFFERENTIAL EXECUTION — CONTINUATION LEDGER (same-Issue protocol, §0–§15)

## §0 Evidence integrity (run1-only vs claimed x9)
- **STATUS: CLOSED BY EXECUTION (option A).** RESULT — the contradiction was real and
  disclosed: the first publication's row 18 claimed 3-run ×9 while
  `DIFFERENTIAL_EVIDENCE_INDEX.jsonl` carried `run1` only for MicroTimer + dooz. The missing
  run2/run3 were **executed** (`scripts/diff366_run23.py`): microtimer `da73010a37dd0189…` ×3
  byte-identical (REAL_APP_CONTENT, rc=0 ×3), dooz `d602648e8e401895…` ×3 byte-identical
  (DEFAULT_BACKGROUND_ONLY, rc=1 ×3 — same as run1); pkgaudit live re-hash match; sources
  still hidden; first divergence stable; per-run trace SHAs recorded (`trace_shas`).
  EVIDENCE — correction comment 5965370293 (this Issue); MD §10 now 11 rows + closure
  paragraph; no `single-run` residue. E4.

## §1 Current-HEAD truth
- **STATUS: VERIFIED (additive).** RESULT — CURRENT-HEAD-TRUTH record appended to
  `docs/FORENSIC_REGRESSION_STATUS.jsonl` (438f8e85 + 204aed6b baselines preserved). At this
  HEAD: goldens 5/5 ×3 byte-identical, loading probe 23/23, uninstall 16/16 — ALL PASS
  (the initial probe 23-FAIL was environmental: gitignored `tools/ecj` restored via
  `scripts/build/bootstrap_toolchain.sh`, recorded in the record). EVIDENCE — gates + record. E4.

## §2 PIXEL-TRUTH law (BYTE-STABLE != PIXEL-TRUTH)
- **STATUS: IMPLEMENTED.** RESULT — chess + dooz anchors relabeled **DETERMINISM GATES
  ONLY** (100% white, 0 app draw ops — never visual success); registries verified already
  OBSERVED/E3/L1 (no visual-VERIFIED claim existed to downgrade); user-designated golden
  gate added. EVIDENCE — `scripts/user_golden_gate.py` **4/4 REAL_APP_CONTENT** (2048:
  535 colors/0.59 nonbg/34 draw ops; Snake Deluxe: 1203/0.72/262; MiniCraft: 2416/0.64/735;
  HelloWorld canonical L6 re-verified); audit row in FORENSIC_REGRESSION_STATUS.jsonl. E4.

## §3 ROOT-A — java.util/java.lang null contracts — FIXED (R-NEW-458/459/460)
- **STATUS: IMPLEMENTED+TESTED.** RESULT — `Arrays.toString` law (null→"null" string);
  `Class.getModifiers` (real DEX access_flags) + `isMemberClass/isAnonymousClass` + 
  `newInstance` (constructs via real `<init>` or throws InstantiationException — never
  silent null); bytecode-proven androidx `FragmentTransaction.add` branch law. Fan-out 8
  apps: asteroids past the GodotActivity Intrinsics NPE; spacevertex past BOTH the
  forName-newInstance NPE and the "must be a public static class" ISE (view tree 2→8 nodes
  incl. the app Scene class, zero uncaught exceptions); 4 goldens + 2 controls byte-identical.
  NEXT first divergences recorded (not hidden). EVIDENCE — `evidence/diff366/root_a/`,
  disasm scripts, root_registry 530→533. E4.

## §3 ROOT-B — WindowInsets compat — FIXED (R-NEW-461)
- **STATUS: IMPLEMENTED+TESTED.** RESULT — `WindowInsets.CONSUMED` (API 30+) seeded as a
  real heap object; memory v34 appcompat decor clinit no longer dies: **WHITE →
  REAL_APP_CONTENT** (sha `67845303a9460d86…`, 2 app draw ops). AndroidX controls
  fossifyclock/blockblast byte-identical (unrelated roots). NEXT divergence recorded
  (memory URI-null). EVIDENCE — `evidence/diff366/root_a/`, root_registry 533→534. E4.

## §3 ROOT-C — Fragment recreation — FIXED (via R-NEW-459 + R-NEW-462)
- **STATUS: IMPLEMENTED+TESTED.** RESULT — FragmentFactory path carried by the Class laws;
  unrelated Fragment apps fan-out: suntimes "CalculatorProvider null context" ISE root-caused
  (5-step diag loop) to ViewShadow claiming provider receivers → 3-part receiver-identity
  gate (not_handled for non-views + `Provider;` shape exclusion + DEX-hierarchy skip); both
  suntimes providers now receive the app context. NEXT divergences recorded
  (ActivityResultLauncher null; WorkManagerInitializer). EVIDENCE —
  `evidence/diff366/root_c/`, root_registry 534→535. E4.

## §3 ROOT-D — ComposeView: honest 4-way separation (diagnose-only)
- **STATUS: OBSERVED (separated, not collapsed).** RESULT — (1) blockblast: ComposeView
  cannot materialize (view_count=0, WINDOW_ROOT); (2) dooz: host materializes (Lho; 1080×1920)
  but composition produces no draw ops; (3) upstream trigger: R8-renamed
  `AndroidCompositionLocals_androidKt` absent → composition-locals CNFE (the #350 family);
  (4) rendering backend: NOT OBSERVABLE (no compose app reaches draw). EVIDENCE —
  report §16 + per-app artifacts. E3/E4.

## §3 ROOT-E — native/Godot (S-2 frontier REACHED, not fixed)
- **STATUS: OBSERVED.** RESULT — asteroids executes the FULL non-native path (onCreate →
  onStart → onResume incl. R8 lambda dispatch, providers OK) and arrests exactly at the
  missing dlopen/JNI layer (GodotView/GodotLib absent by design). Native compatibility is
  NOT marked fixed. EVIDENCE — `evidence/diff366/root_e/asteroids_current/`. E4.

## §13 Final regression (this HEAD)
- **STATUS: VERIFIED.** RESULT — determinism gate 5/5 ×3 byte-identical; user golden gate
  4/4 REAL_APP_CONTENT; loading probe 23/23; uninstall 16/16; 8-app differential fan-out
  zero drift. EVIDENCE — gate outputs this session, `run/user_goldens/user_goldens.json`. E4.

## §15 Open rows (honest)
- Memory URI-null · ActivityResultLauncherCompat null · WorkManagerInitializer (honest empty
  startup metaData consequence) · Compose composition machinery (4-way) · S-2 dlopen/JNI ·
  chess start.onCreate NPE + RecyclerView binding · official-Telegram APK absent (M3/M4
  BLOCKED-APK-ABSENT). Each carries its recorded first divergence.
"""

L365 = COMMON + r"""
# FORENSIC LEDGER — CONTINUATION COMPLETION (same-Issue protocol, M1–M6 + §7–§12)

## M1 Root registries (ROOT-062..067 + S102 registration; 492-vs-530)
- **STATUS: RESOLVED.** RESULT — root_registry.json is the single writable store at **535
  roots** (R-NEW-450..462 + F-NEW-222..233 waves all registered); the canonical
  `root_cause_registry.json` projection was regenerated id-for-id == 535
  (`scripts/cont_m1_root_projection.py`) — the "492 vs 530" mismatch was projection lag and
  is closed with an identity assertion. EVIDENCE — projection file `generated` stamp +
  verification output. E4.

## M2 TELEGRAM_JOURNEY_S117_S119.md
- **STATUS: RECONSTRUCTED + COMMITTED.** RESULT — `docs/TELEGRAM_JOURNEY_S117_S119.md`
  rebuilt from preserved repo evidence only (worklog, forensic ledger, scripts, evidence
  dirs): 31 STATUS—RESULT—EVIDENCE rows + a 9-item gap register (G1–G9) — including the
  honest findings that the real S117–S119 waves were graphics waves, the forkgram chain is
  the committed one (errors 32→7→6→0, face `59fdbfcd…`), and official-Telegram records are
  PARTIAL/BLOCKED-class. The UNVERIFIED_CLAIM (dead link) is now a committed document with
  provenance banner. EVIDENCE — the file itself. E3 (reconstruction of E4-class history).

## M3 s117_tg_run.sh official + forkgram at CURRENT HEAD
- **STATUS: PARTIAL (forkgram EXECUTED; official BLOCKED).** RESULT — the six #361 scripts
  were recovered byte-exact from the #361 issue body and materialized (all six, exec bits,
  syntax-verified — closing the §12/M10 finding); `scripts/s117_tg_run.sh forkgram` executed
  ×2 at this HEAD: face `bbb6cd10a834963d` **byte-identical ×2** (matches the recorded
  golden — no drift), first divergence `NPE unwound ActionBar/d6;.b0` (recorded). official:
  `upload/tg/telegram_official.apk` ABSENT from the workspace with no fetch URL recorded —
  BLOCKED-APK-ABSENT, not fabricated. EVIDENCE — `run/s117_head/M3_run_record.json`. E4
  (forkgram), BLOCKED (official).

## M4 G18 inventory + G19/G20 resource-path evidence
- **STATUS: PARTIAL.** RESULT — G18 official inventory remains impossible without the
  official APK (honest blocker, see M3); G19/G20 resource-path evidence stands on the
  committed load-audit matrices (LOAD_COMPATIBILITY_MATRIX.jsonl,
  WORKING_VS_FAILING_LOADING_MATRIX.jsonl rows) — referenced, not duplicated. EVIDENCE —
  those registries. E3.

## M5 Micro-gap honesty
- **STATUS: MAINTAINED.** RESULT — no synthetic micro-gap was promoted to VERIFIED this
  wave; the real-APK fan-out law is exercised by the ROOT-A/B/C waves instead (every fix
  proven on failing real APKs + unrelated apps). EVIDENCE — root_registry fanout fields. E4.

## M6 Frozen 202-title corpus
- **STATUS: RECONCILED (no fabrication).** RESULT — current truth from the forensic ledger:
  **79 executed-with-evidence** (71 OBSERVED + 8 VERIFIED), **119 PENDING explicitly closed
  as NOT_TESTED** (per-title evidence pointers kept), **4 BLOCKED-DOWNLOAD**
  (FR-046/073/075/221); registry orphans recomputed 123 (the stale "41/161/96" was an
  FR-024-era snapshot). M6 record appended to `docs/FORENSIC_MISSING_EVIDENCE.jsonl`. E4.

## §7 Master checklist / §8 Documentation drift / §9 Homepage / §10 Hygiene / §12 Scripts
- **STATUS: EXECUTED.** RESULT — `docs/FINAL_COMPATIBILITY_CAMPAIGN.md` repaired with 14
  evidence rows (uninstall 16/16 closes the PENDING row; 535==535; F-NEW rows brought to
  current truth; 0 UNRESOLVED); state files synced (`.agent/state.md` labeled HISTORICAL
  with live-state pointer; CAMPAIGN_STATE.md continuation wave = single live source; count
  fix 536→535 in the differential report); README `CURRENT CAPABILITY STATE` section added
  (working-vs-white, corpus, Telegram, Compose/WebView/native, installed-APK, upstream,
  roadmap, vocabulary); hygiene finding verified STALE (tmp blobs already externalized by
  d6237036 + ledgered; 35.65 MiB pack residual documented, history rewrite ruled NOT
  justified); the six #361 scripts materialized + `docs/REPRO_SCRIPTS_CROSSCHECK.md`. EVIDENCE —
  those files at HEAD. E4.

## §11 Safir / Black
- **STATUS: BLOCKED-BY-IDENTITY (unchanged).** RESULT — zero APK/package evidence exists;
  no identity invented. EVIDENCE — CAMPAIGN_STATE row 10. BLOCKED.

## §13–§14 Final regression + evidence rule
- **STATUS: VERIFIED.** RESULT — all gates ALL PASS at this HEAD (determinism 5/5 ×3, user
  goldens 4/4 pixel-truth, probe 23/23, uninstall 16/16); no issue closed on rc=0/loaded/
  parsed/screenshot-exists grounds — every claim carries runtime + state-change + consumer
  evidence. EVIDENCE — gate outputs + user_goldens.json. E4.
"""

L364 = COMMON + r"""
# UPSTREAM + COMPATIBILITY CAMPAIGN — CONTINUATION LEDGER (same-Issue, §6 + §13–§15)

## §6 UPP-001..007 dispositions (no blind imports)
- **STATUS: RECORDED (7/7 rows, closed vocabulary).** RESULT —
  UPP-001 dlopen/JNI **PENDING_RESEARCH** (S-2 frontier reached cleanly by asteroids; design
  undecided); UPP-002 content:// Cursor/FileProvider **AVAILABLE_NOT_USED** (provider-install
  leg proven R-NEW-460/462; zero Cursor code; frameworks_base oracle recorded); UPP-003 split
  APK **AVAILABLE_NOT_USED** (layer MISSING in loading matrix; AOSP oracle recorded; F-NEW-231
  store = landing site); UPP-004 config/density/fonts **AVAILABLE_NOT_USED** (matcher AOSP-
  verbatim; device frozen 420dpi by design — determinism collision unmade); UPP-005 Compose
  **PENDING_RESEARCH** (ROOT-D 4-way separation = four distinct problems; androidx +
  compose-multiplatform-core oracles recorded); UPP-006 Broadcasts/Services
  **AVAILABLE_NOT_USED** (0 corpus hits; ActiveServices upstream recorded; R-NEW-462 =
  groundwork); UPP-007 SQLite/font provenance **ADAPTED** (sqlite_shadow.cpp real WAL in
  place with ×3 consumer evidence; ST-10 trace extension honestly not-done). Each row now
  carries source-url/license/semantic-law/integration-point/tests/maintenance/why (URLs only
  where the repo actually records them — NOT_RECORDED otherwise). EVIDENCE —
  `docs/UPSTREAM_REPLACEMENT_PLAN.jsonl` at HEAD. E4.

## §13 Final regression (shared truth with #365/#366)
- **STATUS: VERIFIED.** RESULT — goldens 5/5 ×3 byte-identical; user goldens 2048/Snake
  Deluxe/MiniCraft/HelloWorld 4/4 REAL_APP_CONTENT; probe 23/23; uninstall 16/16; 8-app
  differential fan-out zero drift. EVIDENCE — gate outputs, `run/user_goldens/`. E4.

## Newly VERIFIED roots this wave
- **STATUS: IMPLEMENTED+TESTED.** RESULT — R-NEW-458 Arrays.toString; R-NEW-459
  Class.getModifiers/isMemberClass/isAnonymousClass/newInstance; R-NEW-460
  ContentProvider.getContext; R-NEW-461 WindowInsets.CONSUMED; R-NEW-462 provider
  receiver-identity gate. Registry 530→535, projection == store. EVIDENCE —
  root_registry.json + evidence/diff366/root_{a,c,e}/. E4.

## Regressions
- **STATUS: NONE.** RESULT — every wave re-proved the full battery; the only reclassification
  (chess/dooz determinism-vs-visual) predates this wave and is now labeled in the gate itself. E4.

## Open blockers + remaining PENDING
- official-Telegram APK absent (M3/M4); memory URI-null; ActivityResultLauncherCompat null;
  WorkManagerInitializer; Compose composition machinery (4-way, diagnose-only); S-2
  dlopen/JNI; chess RecyclerView binding; F-NEW-229/221/217/204..207/192 rows per the
  repaired master checklist (each with its recorded evidence class).

## Exact next continuation
1. S-2 dlopen/JNI/native-surface campaign (asteroids is the clean probe app).
2. Compose composition machinery per the 4-way separation (start with composition-locals
   R8-rename law).
3. Memory zip/WebView path (URI-null) + ActivityResult infrastructure.
4. Startup-provider meta-data (WorkManagerInitializer family) — manifest provider meta-data
   parsing.
5. official-Telegram APK re-acquisition (M3/M4 unblock).
"""

def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None

def post(token, issue, body):
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": body}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        cid = resp.get("id")
        print(f"issue #{issue}: comment id={cid} url={resp.get('html_url')}")
        return cid
    except Exception:
        print(f"issue #{issue}: RAW {r.stdout[:200]}")
        return None

def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    post(token, 366, L366)
    post(token, 365, L365)
    post(token, 364, L364)

if __name__ == "__main__":
    main()
