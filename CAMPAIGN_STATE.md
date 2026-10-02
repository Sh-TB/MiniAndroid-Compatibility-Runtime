# CAMPAIGN_STATE — MiniAndroid-Compatibility-Runtime

HEAD at state update: F-NEW-234 wave (IAPK campaign) ← e9ce717b (MEGA-W2) ← 286b4994
Date: 2026-10-03 (INSTALLED-APP FILESYSTEM + MEDIA campaign)

## LAWS READ

CONSTITUTION_V2 (evidence/regression/lifecycle/rendering/screenshot/registry/disk laws),
MASTER ROADMAP, source-first law, issue-per-problem law, FRAME_CAPTURE_TRUTH (12-item
proof chain), FRAMEWORK_CHROME_ONLY ≠ REAL_APP_CONTENT, F084 freeze, DEX register law,
class-init honesty, REC-MISS 7-class, no-package-specific-fixes, bounded logging,
screenshot/runtime proof laws (21-P0-6 pixel ownership), APK hygiene laws,
installed-APK filesystem requirements, canonical/v10_results_latest.json,
docs/corpus/s82/title_registry.json (frozen corpus = 202 titles, NOT 255),
README/ACHIEVEMENTS/ROADMAP_STATUS, issue #354 comment 5956211403.

## MASTER MERGED CHECKLIST

The ONE master checklist lives at **docs/FINAL_COMPATIBILITY_CAMPAIGN.md**
(mega-campaign §15). Current highlights:

| # | Item | Status |
|---|------|--------|
| 1 | F-NEW-231 INSTALLED_APK_ACCESS (§3 mandatory) | IMPLEMENTED+TESTED — 10/10 claims, 2 APKs, source-hidden proof |
| 2 | F-NEW-234 per-package context-root law (installed-app FILESYSTEM) | IMPLEMENTED+TESTED — 3-layout mismatch root-caused; 12 installed runs ×3; sources quarantined; file-IO + asset provenance; pkgaudit capability; goldens ×3 MATCH |
| 3 | F-NEW-232 deferred-UI observability | IMPLEMENTED+TESTED — fishrings NEW SUCCESS ×3 |
| 4 | F-NEW-233 unconditional frame-truth law | IMPLEMENTED+TESTED — false-SUCCESS family closed |
| 5 | F-NEW-230 golden validity | PARTIAL — 4 goldens VALID ×3 w/ repro blocks; whatsapp REJECTED; 4 STALE recorded |
| 6 | F-NEW-229 CL MATCH_PARENT spec law | OPEN (next attack) |
| 7 | F-NEW-221 R8 merged-class / F-NEW-217 kotlinx resume / F-NEW-204..207 / F-NEW-192 | OPEN |
| 8 | secuso sudoku button-text gap | REGISTERED (wave-2 finding) |
| 9 | Telegram title-overlap + intro/auth chain | REGISTERED — installed-mode filesystem RULED OUT as cause (F-NEW-234 file-IO trace: only benign first-launch theme-extract misses) |
| 10 | Safir / Black sentinels | BLOCKED-BY-IDENTITY (zero project records; APKs needed) |
| 11 | Families A–W root/fan-out audit | IN PROGRESS — deferred-UI fan-out family identified (7+ titles) |
| 12 | README/front-page + release audit (Phases 10–21) | NOT STARTED (stray uuid auto-commit 7abb39ce flagged) |
| 13 | APK-inspection skill feasibility | PARTIAL — `pkgaudit` runtime capability landed (F-NEW-234 wave) |
| 14 | Uninstall command | PENDING (recorded, not faked) |

## LIVE STATE

- Registry: 529 roots (F-NEW-234 IMPLEMENTED+TESTED)
- Installed-state gate (store run/iapk/store2, sources hidden): opencalc
  e364b001ee7abd66 ×3 = golden; bouncy b6dde6074bf47264 ×3; chess
  b5a7a35d5fe0564b ×3; telegram bbb6cd10a834963d ×3; unote (seeded random)
  4f1a9e4e8f64fae8 = golden; whatsapp (seeded random) = known face, no drift.
- Golden gate (sideload, ×3): dooz/microtimer/unote/opencalc ALL MATCH under
  the F-NEW-234 law.
- Filesystem law: ALL runtime app writes land in
  <data-root>/data/data/<package>/ (23/23 files in the AFTER suite); external
  app dirs = <data-root>/storage/emulated/0/Android/data/<pkg>/.
- Instruments: MINIANDROID_FILE_IO (file-IO JSONL provenance), gfx
  byte_source, `pkgaudit` command.
- Corpus reality: 202 frozen titles (100 game + 100 app + 2 mandatory); s107
  tmp APKs purged; local honest pool ~25 APKs; random ledger row 1 banked
  (seed 20261002).
- Disk free: ~6.9G; run/ artifacts kept bounded.

## NEXT TARGETS (priority order)

1. F-NEW-229 (opencalc full button width — CL spec routing trace).
2. Sudoku button-text gap + forkgram/ssw/headingcalc/secuso golden re-banks (F-NEW-230).
3. Time-driven re-test of the deferred-UI family (chess/klondike/tripeaks/flappycow/
   ballbreak — same first divergence as fishrings).
4. Telegram intro/auth chain + title-overlap bug.
5. F-NEW-217/221 deep legs; README/release audit phases.

---

## LOADING-CAMPAIGN IMPLEMENTATION WAVE (2026-10-03) — audit → implementation → proof

### LAWS READ

CONSTITUTION_V2 (§16 first-divergence, §17 silent-wrong, §25 ARSC, §26
end-to-end), FINAL_COMPATIBILITY_CAMPAIGN §15, CAMPAIGN_STATE (F-NEW-231..234),
REAL_ANDROID_LOADING_ORACLE (14 subsystem law families), AOSP sources
(AssetManager2, ResourcesImpl, ContextImpl, SharedPreferencesImpl, ActivityThread
handleBindApplication/installContentProviders, libcore File/UnixFileSystem/
InputStream, sepolicy appdomain device-node law), FRAME_CAPTURE_TRUTH
(F-NEW-233), 21-P0-6 pixel ownership, no-package-specific-fixes law.

### NEW LAWS DISCOVERED (probe-driven, registered)

read(byte[]) fill law ≡ read(b,0,b.length); ByteArrayOutputStream family;
String(byte[]) __string_value__ materialization (new-instance identity);
()J INT64 register-pair law (File.length/lastModified, AFD getStartOffset/
getLength); character-device bounded-read law (/dev/urandom AOSP-legal);
ONE path law categories (SANDBOX_DATA/INSTALLED_APK/VIRTUAL_EXTERNAL/
SYSTEM_IMAGE/DEVICE_NODE/DENIED_HOST_PATH); ONE databases_dir authority.

### STATE

- P0 fix wave IMPLEMENTED: ST-1/ST-2/R-1/R-2/R-5/R-7/R-10/ST-4/ST-5/ST-6/
  ST-7/S-1(launch)/S-5/S-7/ST-11 — all generic, all AOSP-cited, all runtime-
  proven via the synthetic probe (fixtures/loading_probe, 23/23 gate).
- Probe gate: scripts/loading_probe_runner.sh — ALL PASS.
- Regression gate: opencalc e364b001ee7abd66 ×3 / chess b5a7a35d5fe0564b ×3 /
  dooz d602648e8e401895 ×3 / microtimer da73010a37dd0189 ×3 / unote
  4f1a9e4e8f64fae8 ×3 / telegram bbb6cd10a834963d ×1 — ALL == goldens.
- Deliverables: WORKING_VS_FAILING_LOADING_MATRIX.jsonl,
  WORKING_APP_LOADING_EXPLANATIONS.md, LOADING_API_COVERAGE_MATRIX.jsonl,
  AUDIT_REQUIREMENT_COVERAGE.jsonl, INSTALL_TREE_PROOF.jsonl,
  LOADING_RUNTIME_TRACE.jsonl, LOADING_ROOT_FANOUT.md,
  LOADING_FAILURE_DIAGNOSTICS.md, WHITE_SCREEN_LOADING_ROOTS.md,
  loading_probe_runner.sh / working_vs_failing_probe.sh /
  storage_tree_proof.sh; FILE_RESOURCE_LOADING_COMPATIBILITY §9/§10;
  FINAL_COMPATIBILITY_CAMPAIGN §16; registry R-NEW-457.

### NEXT

S-2 (dlopen/JNI), S-4 (content:// query/Cursor + FileProvider), S-11 splits,
S-3/S-13 broadcasts/services, SELECTION_FROZEN (config/density/fonts),
S-10 localStorage; sqlite/font provenance traces (ST-10); provider-stage
consumer proof on an androidx.startup-shipping app end-to-end.

## FORENSIC VERIFICATION WAVE (2026-10-03, issue #365) + UPSTREAM WAVE (issue #364)

### LAWS READ
CONSTITUTION_V2 (§0-46 headers + evidence/verdict laws), CAMPAIGN_STATE, worklog
(S84..LOADING-EXEC-CLOSE), .agent/{CODER_REQUEST_PROTOCOL,mission,state,
master_campaign_state,decisions,backlog,requests/001} — state.md +
master_campaign_state.md recorded STALE (EXP-090/D05 era), issue #354 comments
(37), issues #353-365, 190-goal roadmap (#363 §3).

### INDEPENDENT HEAD TRUTH (all re-run 2026-10-03 at HEAD)
- WORKING-VS-FAILING-GATE 5/5 goldens x3 byte-identical (opencalc e364b001ee7abd66,
  chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189,
  unote 4f1a9e4e8f64fae8).
- LOADING-PROBE-GATE 23/23 ALL PASS.
- UNINSTALL-PROOF-GATE 16/16 ALL PASS — NEW generic `uninstall` command
  (codePath + record + internal + Android/{data,media,obb} removal, isolation,
  NOT_INSTALLED honesty, reinstall-clean); closes the F-NEW-231 recorded
  PENDING row.
- CANONICAL EVIDENCE VALIDATOR 0 FAIL (was 3 FAIL: R4 fish.rings duplicate
  artifact removed; R10 x2 S100 browser GIFs registered; registry 148->150;
  README/ACHIEVEMENTS/CANONICAL_SCREENSHOTS synchronized).

### FORENSIC DELIVERABLES (issue #365)
FORENSIC_ALL_REQUESTS_LEDGER.jsonl/.md (390 request rows; strict §2 vocabulary),
FORENSIC_CLAIMS_VS_EVIDENCE.md, FORENSIC_VERIFIED_WORK.md,
FORENSIC_UNVERIFIED_CLAIMS.md, FORENSIC_MISSING_EVIDENCE.md,
FORENSIC_REQUEST_GRAPH.md/.jsonl (338 edges), FORENSIC_REGRESSION_STATUS.jsonl
(4 current-HEAD gates + 2 historical justified re-baselines; REGRESSED=0),
FORENSIC_EVIDENCE_INDEX.jsonl (52 artifacts).
Key findings: 202-title corpus 41/202 executed (161 NOT_TESTED, 96 registry
orphans); ROOT-062..067 + S102-* in NO registry (coverage gap); canonical
projection lags root_registry.json (492 vs 530); TELEGRAM_JOURNEY doc never
committed (UNVERIFIED_CLAIM); tmp/ still tracks ~177 MB disposable blobs
(88.4+60.2+14+22.4+21.8); .agent state files stale.

### UPSTREAM DELIVERABLES (issue #364)
UPSTREAM_CODE_INVENTORY.md/.jsonl (11 rows), UPSTREAM_AVAILABLE_NOT_USED.jsonl,
UPSTREAM_REPLACEMENT_PLAN.jsonl (7 pending plans S-2/S-4/S-11/SELECTION_FROZEN/
compose/broadcasts/ST-10), UPSTREAM_LICENSE_MATRIX.jsonl (17),
UPSTREAM_RUNTIME_USAGE.jsonl (PROVEN vs WIRED_NOT_CONSUMED),
UPSTREAM_UPDATE_TRACKING.jsonl.

### STATUS VOCAB (ledger counts)
VERIFIED 30 / TESTED 82 / OBSERVED 105 / PARTIAL 43 / PENDING 122 / BLOCKED 5 /
SUPERSEDED 2 / UNVERIFIED_CLAIM 1 / REGRESSED 0 (evidence: E0=122 E1=6 E2=112
E3=87 E4=50 E5=13).

### NEXT
M1 registry backfill (ROOT-062..067, S102-*); M2 commit journey doc; M3 fresh
s117_tg_run.sh at HEAD; then the §21 continuation queue (S-2, S-4, S-11,
SELECTION_FROZEN).
