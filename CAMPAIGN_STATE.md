# CAMPAIGN_STATE — MiniAndroid-Compatibility-Runtime

HEAD at state update: #371 FINAL CLOSEOUT wave bd9e9fbd (binary 267bf47d5d901054) ← b3213f06 (Suntimes wave 2: framework-enum accessor + meta-data/FileProvider laws) ← 300f38a7 (GL/provenance/fanout) ← 731bb538 (Suntimes wave 1) ← b9f2c0d2 (S-2 native) ← 58f2dde2 (FINAL COMPLETION, binary b2b8c18bb92dab6a)
Date: 2026-10-03 (#371 FINAL CLOSEOUT — Suntimes/time4j + touch-claim + full regression)
← 51f7e5f9 (MASTER-CONT-371 verification) ← 9c35863b (GATE A) ← F-NEW-234 e9ce717b
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

## #371 FINAL COMPLETION WAVE (2026-10-03) — gate closure + fan-out

- Gate-A gaps: G-1/G-3 CLOSED (ContentResolver authority map + Cursor
  transport + failure contracts; probe PROV-02..09), G-4 CLOSED (install-time
  ABI-scoped lib extraction + real nativeLibraryDir; NAT-02/03), G-8 CLOSED
  (user_de prefix-strip bug fixed + DE fence + createDeviceProtectedStorage
  Context; DE-01), G-2 precision upgrade (3-shape ULE + env-gated real
  dlopen/dlerror; EXECUTION stays S-2 frontier). G-5/G-6/G-7 closed in the
  prior #371 wave.
- Generic engine laws from the fan-out: List.remove(int) removed-element,
  FileInputStream(FileDescriptor) PFD backing, ProviderInfo.grantUri
  Permissions manifest law (FileProvider.attachInfo SecurityException root),
  Uri.toString.
- Services/broadcasts core legs (SVC-01..04, BCAST-01..04); IntentFilter
  engine state; ST-10 provenance rows (SQLITE-OPEN/EXEC/WAL, FONT-FACE);
  multi-config probe (CFG-01..05) at the UNTOUCHED frozen profile.
- pkginspect = 15 sections incl. runtime + diagnostics (first divergence,
  deterministic JSONL) — #371 Phase C complete.
- PHASE D fan-out: flappycow (game) + notes_secuso (app) VERIFIED_REAL_APP_
  CONTENT ×3, byte-identical screenshots (13cf47464d9787f4 / eb5ebd559cad
  1028), source hidden, identity launch. A/B vs base 51f7e5f9: notes
  SecurityException eliminated by the grantUriPermissions law (crash.log
  1→0 errors); flappycow already at REAL_APP_CONTENT at base (evidence
  banked, no flip claimed).
- Deferred-UI re-test (CAMPAIGN next-target #3) EXECUTED: flappycow banked;
  klondike/tripeaks stay APP_DRAW_OPS frontier; ballbreak OBSERVED
  (PARTIAL_MARGINAL); tictactoedeluxe = libGDX GL frontier; stopwatch has
  NO launcher activity in its manifest (correct non-launch).
- Random corpus sample (seed 20261003): fishrings REAL_APP_CONTENT 44 draw
  ops (sha16 a341e3ad9092f640).

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

## Wave — DIFFERENTIAL-366 (2026-10-03, HEAD 204aed6b)

- Issue #366 answered diagnose-only: 4 WORKING (opencalc/unote/microtimer/bouncy) vs
  5 WHITE (fossifyclock/blockblast/asteroids/spacevertex/memory), all on CURRENT HEAD,
  installed-identity pipeline (source hidden), 3-run byte-identical x9.
- FIRST DIVERGENCES: 5 distinct generic roots — VIEWTREE/ATTACH (fossifyclock
  WINDOW_ROOT non-authoritative), COMPOSE (blockblast ComposeView not in class index),
  NATIVE/JNI (asteroids GodotActivity death; Arrays.toString null trigger),
  FRAGMENT (spacevertex recreation ISE), ANDROIDX-LIFECYCLE (memory WindowInsets
  s0$k clinit NPE). Loading layer innocent in all nine.
- REGRESSION reclassification: chess + dooz goldens are determinism gates with white
  frames (0 app draw ops) — pixel-truth lens (F-NEW-233) now mandatory for "working".
- Deliverables: docs/DIFFERENTIAL_WORKING_VS_WHITE.{md,jsonl},
  DIFFERENTIAL_FIRST_DIVERGENCES.jsonl, DIFFERENTIAL_EVIDENCE_INDEX.jsonl,
  run/diff366/stage_matrices.json, evidence/diff366/, scripts/diff366_{fetch,screen,final,report}.py.
- Next leverage (no fix applied this wave): java.util/java.lang shadow null-contracts,
  androidx WindowInsets compat static-init, Fragment recreation law, ComposeView
  materialization, Godot native surface.

---

## CONTINUATION WAVE (master continuation §0–§15) — LIVE STATE

HEAD at this update: `fb128799+` (PIXEL-TRUTH audit) ← 4e62b10b (§16 doc) ← 5dbfe5f2
(ROOT-B/C) ← f398c0f2 (ROOT-B) ← 5fa4cd84 (ROOT-A) ← 205b2e2d (run23 closure) ←
9289177d (#366 ledger) — date 2026-10-03.

Canonical numbers (single live source = this section):
- Root registry: **535 roots** (root_registry.json); canonical projection regenerated
  id-for-id == 535 (`canonical/root_cause_registry.json`, `scripts/cont_m1_root_projection.py`)
  — the historical "492 vs 530" mismatch is CLOSED (projection lag was the whole gap).
- Canonical title registry: 150 rows (docs/evidence/canonical/registry.json).
- Frozen corpus truth (M6 reconciliation, docs/FORENSIC_MISSING_EVIDENCE.jsonl): 202 total;
  **79 executed-with-evidence** (71 OBSERVED + 8 VERIFIED), **119 NOT_TESTED** (explicitly
  closed), **4 BLOCKED-DOWNLOAD** (FR-046/073/075/221). The older "41/161/96" numbers are a
  stale FR-024-era snapshot — do not re-quote.
- #366 differential: 11 apps × 3 runs byte-identical (microtimer+dooz run23 closure, option A);
  ROOT-A/B/C generic fixes landed (R-NEW-458..462); memory WHITE→REAL_APP_CONTENT;
  ROOT-D Compose honest 4-way separation; ROOT-E S-2 dlopen/JNI frontier reached cleanly.
- User golden gate: 2048 / Snake Deluxe / MiniCraft / HelloWorld **4/4 REAL_APP_CONTENT** PASS
  (scripts/user_golden_gate.py; chess+dooz are DETERMINISM anchors only — never visual success).
- Regression gates at this HEAD: goldens 5/5 ×3 byte-identical, loading probe 23/23,
  uninstall 16/16 — ALL PASS.
- Telegram M3: forkgram `3baeecb3…` ×2 byte-identical face `bbb6cd10a834963d` at current HEAD;
  official BLOCKED-APK-ABSENT (honest).
- Upstream plan (#364): UPP-001..007 dispositions recorded (docs/UPSTREAM_REPLACEMENT_PLAN.jsonl).
- Master checklist: repaired with evidence rows (docs/FINAL_COMPATIBILITY_CAMPAIGN.md §17).
- Historical .agent/* state files labeled; their numbers are era snapshots, not current.

---

## MASTER-CONT-371 WAVE — independent verification + Gate-A gap closure — LIVE STATE

HEAD at this update: `9c35863b+` (MASTER-CONT-371) — date 2026-10-03.
Binary lineage: clean rebuild reproduced Gate A binary `768085b1207ad55d`
byte-identically; post-fix binary `75cb214df1374992`.

Canonical numbers updated by this wave:
- GATE A (#370) capability: **59/60 API-matrix rows TESTED** (was 57/60):
  G-5 (AFD stream byte-equality), G-6 (list contains element-equality),
  G-7 (File.getParent starvation) CLOSED with generic laws + probe
  assertions; sole remaining GATE-A row = G-3 content:// query dispatch
  (ContentResolver authority map + Cursor transport).
- Verified-at-current-HEAD gates (all re-executed, none trusted): battery
  124/124 (cold-state; tooling set-e bug fixed, no stage weakened),
  goldens 4/4 REAL_APP_CONTENT, determinism 5/5×3 zero drift, loading
  probe 23/23, uninstall 16/16, Gate A probe 69/0/2 (strengthened),
  negatives 17/17, reinstall 8/8, multi-app 5/5.
- ROOT hold verification: ROOT-A spacevertex past forName divergence;
  ROOT-B memory REAL_APP_CONTENT; ROOT-C suntimes provider ISE absent.
- Honest open rows (unchanged truth): UPP-001..006 adoption rows
  (native S-2 execution, content:// Cursor, split APK, config/density,
  Compose ROOT-D, broadcasts/services), GATE-A G-1/G-3/G-4/G-8, corpus
  re-runs awaiting APK re-acquisition (hotdeath/bobball/pinyinfdroid).

## Wave — #371 FINAL CLOSEOUT (2026-10-03, HEAD bd9e9fbd, binary 267bf47d5d901054)

Suntimes/time4j frontier closed at the runtime level; 7 generic laws; full regression green.

| Item | Status | Evidence |
|------|--------|----------|
| §2 S-2 native execution | VERIFIED | NATX 10/10 ×3 byte-identical (ab01a3a1c239486a); gate A NAT-03/04 green with rebuilt extraction-backed libs; A/B NATX 0→10 (prior wave) |
| §3 Suntimes/time4j | VERIFIED at runtime level | BASE 6a6ef5b2a69f1f9d 3 process deaths vs PATCH 267bf47d5d901054 0 (isolated A/B arms, same APK/store/capture); time4j <clinit> chains all complete; WelcomeActivity REAL_APP_CONTENT ×3 byte-identical a49f90d65a8fc5c8 (owned=61452 ops=4) |
| §4 libGDX GL | PARTIAL (precisely named) | EGL JSR-239 facade law closed checkGL20; tictactoedeluxe BLOCKED-BY-IDENTITY — arm-only libgdx.so (no x86_64) = ARM translation boundary (UPP-001) |
| §5 deferred UI | VERIFIED for reachable targets | TriPeaks SUPERSEDED by direct ×3 evidence; suntimes welcome real content; ViewPager page-fragment materialization named as next generic primitive |
| §6 classification | DONE (classifier untouched) | VERIFIED ×3: flappycow 13cf47464d9787f4, notes_secuso eb5ebd559cad1028 (recorded shas exact); REAL_APP_CONTENT ×3: tripeaks/gmdice/sudoku/fishrings/suntimes; structural NO_ROOT: stopwatch (no <activity>); BLOCKED-BY-IDENTITY: tictactoedeluxe |
| §7 install/filesystem/persistence | VERIFIED | persistence 32/32 (prior wave, Telegram+calc+chess+notes); loading probe restart/WAL/file ALL PASS; reinstall 8/8; uninstall ALL PASS |
| §8 media provenance | VERIFIED | flappycow 12 bitmap events, dimensions match APK art exactly (prior wave); shas reproduced this wave |
| §9 new-app fan-out | VERIFIED | ≥2 new games (tripeaks, gmdice) + ≥2 new apps (sudoku, stopwatch) + random pick (fishrings, seed 20261004) — all ×3 |
| §10 A/B causality | VERIFIED | S-2: NATX 0→10; Suntimes: process deaths 3→0, tap target pager→button; evidence dirs isolated per binary, no overwrites |
| §11 regression | ALL GREEN at 267bf47d5d901054 | anchors 5/5×3, goldens 4/4, loading probe, gate A 95/0/2 (both stores), negatives 17/17, reinstall 8/8, uninstall, battery 124/124, multiapp 5/5, NATX 10/10×3, fan-out ×3 |
| Environment repair | DONE | container-reset bootstrap: toolchain relayout, EXT-01/02 SHA-exact, corpus re-fetch (blockblast 64589a3a7e5c0f73 matches), native libs rebuilt, monospace law env, battery link lines + Makefile resource_trace thunk |

Next frontier (recorded): ViewPager page-fragment materialization (generic
FragmentPagerAdapter container primitive; pager children empty, mCurItem
IGET-MISS, setCurrentItem cycle-stub). ARM binary translation remains the
sole tictactoedeluxe/GL dependency. Safir/BLACK remain BLOCKED-BY-IDENTITY.
