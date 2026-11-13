# CAMPAIGN_STATE — MiniAndroid-Compatibility-Runtime

HEAD at state update: CONT-41 (binary e1fc1915e88fe2a8 — the Notification$Builder fluent-chain law) ← CONT-40 eeae06db (binary 111340a583d48d92 — unchanged; the audit's prototype law PARKED) ← CONT-39 771b4b80 ← CONT-38 0d73926f ← CONT-38v 11a6c2b9 ← CONT-37 8cbd94e7
Date: 2026-10-10 (CONT-41 — the friend knowledge-package source-level audit: 1 genuinely missing generic law integrated, 6 claims already present, 2 rejected as unsafe, package script missing)

## CONT-41 HIGHLIGHT (2026-10-10)

**The friend-package audit closed: of the 13 claimed laws, SIX were already on main (two with the
CONT-38v probe proofs), TWO were rejected as semantically unsafe, and ONE genuinely missing generic
fix was integrated — F-NEW-303, the AOSP Notification$Builder fluent-chain object law.** The package
contained ONLY the two narrative Markdown files + images: the reported patch script
`/home/z/my-project/scripts/apply_all_patches.py` is NOT in the ZIP and NOT in the workspace — every
claim was verified by CONTENT against canonical source, per directive. Already present (canonical
equal or stronger): ServiceLoader dedicated iterator + F-NEW-252 decline gate; Class-key stability
(F-069/F-103 family — the friend's string-key patch would be WEAKER than the shipped stable-token
law); listIterator typed box + LAW-B; Bundle parcel-family interfaces; compose-pump drain + scoped
virtual-clock advance (F100-IDLEDRAIN + F-NEW-277 — the friend's unguarded advance would break the
frozen launch-frame law). Rejected: F-NEW-260 (R8 app-class exception suppression — canonical fixed
the storable-type instanceof walk honestly) and F-NEW-261 (fabricated isAttachedToWindow/synthetic
token — REJECTED on the merits by CONT-40's A/B: composition creation happens without a token and
shipping the law lost composeStopwatch's visible text). The ONE gap: no Notification$Builder law
anywhere — the CONT-38v recorded tananaev frontier (NotificationCompat$Builder.<init> pc=64 NPE →
DEFAULT_BACKGROUND_ONLY). F-NEW-303 (one generic bridge law: set* → THIS, build() → fresh
Notification; the §12 Builder family) flips the notif_builder_probe 28/28→56/0 markers ×3 (8/8 rows:
fluent identity, distinct build(), post-build reuse, the compat WRAPPER face) and advances the real
app FAILURE→PARTIAL SUCCESS with Errors=0 (NPE gone ×3; frame honestly unchanged d602648e8e401895;
next blocker = FragmentTransaction.commit REC-MISS — the Fragment/Preference family is the recorded
next wave; NO render claim). Full regression ZERO DRIFT at e1fc1915e88fe2a8 (anchors 24/24 +
composeStopwatch ×3 + battery == records + simplecalc ×3). Registry 610→611 (F-NEW-302 SKIPPED —
the standing frame-loop probe is named fnew302; ID collision avoided). Session-environment recovery
recorded in evidence (disk-full cleanup, 73-commit fast-forward, probe APK rebuilds, SHA-exact
F-Droid re-downloads, root-owned runtime/ moved aside). Evidence:
evidence/cont41/FRIEND_PACKAGE_AUDIT.md. Next: the Fragment/Preference family (fragment-commit
pending-op drain → addPreferencesFromResource → preference tag mapping through the REAL measure
laws — no fixed-geometry hacks), the dooz case-E boot budget, the identity-hash interleaving root.

## CONT-40 HIGHLIGHT (2026-10-10)

**The friend's Dooz claim audited and REJECTED; the real frontier is the execution budget.**
Static decode (field-ref-exact on the R8-renamed DEX): AbstractComposeView (Lr;) stores
getWindowToken() RAW with ZERO null-gates, getShouldCreate... is CONSTANT TRUE, the token
field has exactly ONE reader (its own setter), and composition creation runs
unconditionally — the real attach gate is the parent walk. Runtime: the call fires once
on Lho;; the F-050 frame clock DELIVERED (2 doFrame callbacks, monotonic virtual vsyncs);
the resumed composition executed 14.3 MILLION instructions (45 s budget also exhausted)
painting 151 app-owned ops before the F084 budget halt — case E (budget), NOT a parked
frame clock. The AOSP-faithful getWindowToken law was prototyped and A/B'd ON THE SAME
BINARY: it flips dooz to a valid-but-empty scheduling path AND loses composeStopwatch's
visible text (causality proven byte-exact via MINIANDROID_WTOKEN_NULL) — PARKED, not
shipped (shipping it would regress visible content for a non-problem). New standing probe
fnew302 (9 rows): the Choreographer RE-REGISTRATION loop proven end-to-end for the first
time (exact 16666667 ns quanta ×3); the window-token rows = the documented parked-law face
(6/9). Full regression ZERO DRIFT at the byte-exact CONT-39 binary. Evidence:
evidence/cont40/DOOZ_WTOKEN_AUDIT.md. Next: the identity-hash interleaving sensitivity
(the Lrz1 cycle-stub vs StateFlow-spin divergence) + the dooz boot-cost root (case E).

## CONT-39 HIGHLIGHT (2026-10-10)

**TextView.setTextColor → getCurrentTextColor round-trips exactly** — the
CONT-38 checkpoint (colorpipe PC-01..04, 13/4) is dead at the source. ROOT:
F-NEW-301 — the SETTER side was already faithful (the ViewShadow setTextColor
law stores the exact argb with provenance; [M3-SETTEXTCOLOR] shows every call
incl. PC-04's red→green), but the GETTER had NO law anywhere in the engine —
every call fell through to the typed-default int stub and answered 0. FIX (one
generic point, same state store): getCurrentTextColor answers the stored
ViewNode text_color, else mirrors the renderer's default law EXACTLY (0 →
opaque black, Button-label → white) so getter state and rendered pixels cannot
diverge; the CSL variant's draw-time default resolution stays the recorded gap.
PRE ×3 13/4 → POST ×3 on 111340a583d48d92 17/0 (value/alpha/black/recolor all
round-trip). Full regression: anchors 8/8 ×3 BYTE-IDENTICAL, composeStopwatch
3442d9a9dc0fa0f9 ×3 (the Compose path untouched), battery == the standing
records + cpipe 17/0, simplecalc ×3 FULL SUCCESS. Registry 609→610. Evidence:
evidence/cont39/TEXT_COLOR_STATE.md

## CONT-38 HIGHLIGHT (2026-10-10)

**composeStopwatch's text is VISIBLE with its real theme color** — the CONT-37
"TextPaints carry pipeline-default black" face is dead at the source. ROOT:
F-NEW-300 — Resources.getColor(int,Theme) resolved every resid through the APP
table only; the app's theme colors are android:color/system_* FRAMEWORK
resources (0x0106005e-0x010600c0) and all answered the black fallback ([RES]
rows "M3-COLOR-UNRESOLVED" x9) → the app's darkColorScheme materialized
ALL-BLACK → the M3 Surface's LocalContentColor provides SolidColor(black) →
the Text merged style color=black → TextPaint.setColor(0xff000000) →
black-on-dark. FIX (one generic point): the getColor law now routes through the
S127 package-routed law (0x01-package resids resolve through the FRAMEWORK
table + the ColorStateList file fallback; AOSP: package-agnostic AssetManager2).
PRE/POST: [RES] all-black → real values (0xffb9cbff/0xff30436e/0xff4c5e8b/...);
TextPaints 0xff000000 → 0xff30323a x3; frame bbaf8f76308dc267 → 3442d9a9dc0fa0f9
x3 (themed surface + accent + white text pixels — the frame-truth distinction
holds). The engine's color machinery verified EXACT during the decode
(Color.Unspecified=0x10 per androidx; the M3 palette constants correct). PROBE
FIRST: fixtures/colorpipe_probe (17 rows) — TR/SC rows ALL PASS x3 (the
identity-keyed HAMT scope-map machinery PROVEN SOUND), PC-01..04
TextView.setTextColor state FAIL x3 (the honest next checkpoint). Full
regression: anchors 8/8 x3 BYTE-IDENTICAL (zero collateral drift), battery ==
the standing records + ckey 15/0 + cpipe 13/4, simplecalc x3 FULL SUCCESS.
Registry 608→609. Evidence: evidence/cont38/TEXT_COLOR_FRONTIER.md

## CONT-38v HIGHLIGHT (2026-10-10)

The friend-reported "F-NEW-257"/"F-NEW-258" verified by CONTENT (the numbers are
occupied by unrelated CONT-7 roots): both are re-discoveries of already-fixed
generic roots (F-069/F-103/F-NEW-249/F-NEW-282 the Class-token identity family;
F-NEW-255 + LAW-B the ListIterator family) — verified with the new standing
classkey probe (15 rows) ×3 both directions. The probe EXPOSED F-NEW-299 (the
String copy-constructor content law): new String()/new String(String) left the
heap object unmaterialized → F-NEW-248's map-key content law fell back to
identity keying → const-string lookups missed. One generic point fixed; PRE
14/1 → POST 15/0 x3; ZERO drift. Phase-3 targets: dooz x3 honest anchor;
SimpleCalc x3 rc=0 (the friend's "calculator loads" claim TRUE on THIS lineage);
com.tananaev.calculator v1.10 = PARTIAL (NEW frontier: NotificationCompat$Builder
null-receiver NPE → DEFAULT_BACKGROUND_ONLY — recorded, not patched);
headingcalc re-supplied SHA-exact (274ec873…) → the new baseline be1cea9cf994b26a
x3. Registry 607→608. Evidence: evidence/cont38v/FRIEND_CLAIM_VERIFICATION.md

## CONT-33 HIGHLIGHT (2026-10-09)

**composeStopwatch paints its FIRST content** — after F-NEW-291 (String.format
Locale overload: the EXP093 bridge consumed the Locale AS the format string;
every Locale-overload call answered "" → Lwv;.p substring(0,2) SIOOBE) and
F-NEW-292 (libcore UUID+Enum interface rows + per-hop platform consult in
dalvik_class_assignable — the DisposableSaveableStateRegistry whitelist
{Serializable,…} rejected rememberSaveable(UUID) ×51/run and app enums ×26/
run), the app moves FAILURE → PARTIAL SUCCESS and renders a dialog window
(new deterministic frame 9afb2bd2606f303e ×3, was DEFAULT_BACKGROUND_ONLY
5c4a0172628849ba since CONT-31). Probes fnew291 (PRE FAIL 2/5 → POST PASS
7/0 ×3) and fnew292 (PRE FAIL 3/3 → POST PASS 9/0 ×3, negatives honest).
Full regression ZERO DRIFT: 24/24 anchors ×3, battery == CONT-28..32 records
exactly, simplecalc ×3 FULL SUCCESS. DataStore mangled path ROOT-CAUSED
(getFilesDir host-prefix leak) and honestly DEFERRED to CONT-34 with the
fix contract. Registry 599→601. Evidence: evidence/cont33/FORMAT_LOCALE_FRONTIER.md

## CONT-32 HIGHLIGHT (2026-10-09)

- F-NEW-290 Dialog object law ROOT_CAUSED_FIXED: Dialog.getWindow/getContext
  answered NULL for renamed Dialog receivers (DialogWrapper ctor killed the
  dialog path with ISE "Dialog has no window" x31/run, composeStopwatch).
  Fix = receiver-identity dispatch to DialogShadow + stable per-dialog Window
  object + per-receiver WindowManager.LayoutParams law. Probe fnew290 x3
  7/0; target ISE 31->0 x3; full regression ZERO DRIFT at c280b243f880e7e6.
- AndroidCompositionLocals CNFE verdict: FAITHFUL (class genuinely absent
  from the R8-minified APK; app catches; ART-identical).
- Registry 598->599. Next: Lwv;.p STR-BRIDGE SIOOBE, mangled DataStore path,
  standing F-NEW-288 + input-pump.
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

## 371/372/373 CONT WAVE (2026-10-04) — environment layer + skill product surface

- #373: pkginspect `prerequisites` section (APK-001..020 schema) +
  docs/ENVIRONMENT_PROFILE.json (ENV-001..010, profile sha16
  56e6347116942bfc) + 30-APK matrix + redroid-class live proof (EggReturnsHome
  arm64-only install-OK/fail-at-launch) + WS-001/002 audit (5 runtime vs
  2 env vs 1 dup) → R-NEW-465 IMPLEMENTED+TESTED.
- S137 laws: R-NEW-463 M3-19 CLASS_REF payload key refinement (fossifyclock
  A/B-fixed: App.onCreate death → MainActivity RESUMED); R-NEW-464
  Method.getModifiers (landed, PARTIAL: EventBus chain boundary named).
- #372: docs/DEEP_ROOT_CROSSMATCH.jsonl — 10 candidates A–F (4E/4B/1D/1C),
  zero duplicate roots.
- Agent Skill v2: skill_manifest.json (10 machine-readable ops) +
  skill_selftest.py 13/13 PASS — external-agent answer YES.
- Execution matrix: docs/EXECUTION_LEVEL_MATRIX.jsonl (L6=15, L3=2, L4=3,
  L2=4, L1=2, L0=3).
- NEW app fossifyclock + NEW game fairymahjong (F-NEW-084 halt, honest) +
  sudokusolver (Compose frontier) — installed-identity runs, first
  divergences recorded.
- Suntimes APK DRIFT A/B-proven (current F-Droid 135 bytes fail time4j at
  BOTH binaries → no regression; recorded a49f90d65a8fc5c8 evidence stands;
  ViewPager re-attempt needs SHA-pinned refetch).
- Final regression at 4c01757e8f11c8a0 ALL GREEN: anchors 5/5x3,
  goldens 4/4, battery 122/122 fresh, gate A 95/0/2 x2, negatives 17/17,
  reinstall 8/8, uninstall, NATX 10/10x3, skill selftest 13/13. Classifier
  untouched. Registry 538 roots. Issue ledgers posted to #371/#372/#373.

## CONT-30W (2026-10-09) — WHITE-SCREEN CLAIM AUDIT + R-NEW-466 SERVICELOADER TEST

HEAD b473c69b (binary b84114cd6f8bad1d, UNCHANGED — zero engine edits).
Report lineage reconciled: 5/6 claimed commits NOT FOUND; all R-IDs absent —
substances already carried by F-NEW-273/F-064/F-103/F-NEW-249/F-106 +
effective_content_root_(). Simple Calculator vc8 re-supplied SHA-exact
(68da25fd9fdf54b4) and FULL SUCCESS retained ×3 (7960bce447ac6d8f byte-identical);
dooz anchor byte-identical. R-NEW-466 defects do NOT reproduce on main
(fnew252 SLPOS runtime proof); its fix is absent and NOT transplanted;
composeStopwatch claims UNVERIFIED (APK NOT FOUND). Real find: fnew252 probe
packaging regression (META-INF/services lost in the w4 rebuild) — fixed
generically in the build script, proven ×3 (7/0 PASS). Registry UNCHANGED.
Evidence: evidence/cont30w/WHITESCREEN_CLAIM_AUDIT.md (§9 = next checkpoint).

## CONT-31 (2026-10-09) — composeStopwatch re-supply + F-NEW-289 MAIN-QUEUE DELIVERY IDENTITY (ROOT_CAUSED_FIXED)

Container reset recovered (56-commit chain from origin/main; binary rebuilt
byte-exact b84114cd6f8bad1d → wave binary 9bdd61328d0f01d9 after the fix).
composeStopwatch v1.9.1 vc1009011 re-supplied SHA-pinned (dbf937ebbe7c0b3d…).
R-NEW-466 verdicts on THIS lineage: Main-dispatcher ISE never occurs; l5/t5
materialize WITHOUT their patch; fix stays untransplanted. First genuine
divergence root-caused: park-drain delivered main-queue runnables with the
INHERITED WORKER identity (F-110d window) → LiveData assertMainThread ISE ×60/
run; F-NEW-289 law (main-delivery identity re-bind, 4 entry points, save/
restore) fixes it generically. Probe fnew289: pre QUEUE-MAIN|FAIL → post ×3
ALL PASS (28/0). Target post-fix ×3: ISE 0/run, frame byte-identical
(divergence honestly MOVED to "Dialog has no window" at Lea;.r). Full
regression ZERO DRIFT: 24/24 anchors ×3, battery == CONT-28/29/30 records
(fnew253 147/0, fnew286 10/0, fnew252 56/0), simplecalc ×3 FULL SUCCESS.
Registry 598. Evidence: evidence/cont31/COMPOSESTOPWATCH_FRONTIER.md.

## CONT-34 (2026-10-10) — GATE A VIRTUAL-PATH LAW (F-NEW-293 ROOT_CAUSED_FIXED)

Container reset recovered again (fast-forward 61 commits to 8081a64e; binary
rebuilt byte-exact 859557953a3b144c; composeStopwatch dbf937ebbe7c0b3d +
SimpleCalc 68da25fd9fdf54b4 re-supplied SHA-exact). CONT-33 §9's mangled
DataStore path decoded to ONE root: logical_android_path compared the
ABSOLUTE host side against prefixes from the DEFAULT RELATIVE root literal
("runtime/data") → silent no-op → dir getters minted Files with HOST
spellings → three consumers re-anchored by three different laws
(package_data_dir / app_data_root / raw) → prefix multiplication. Fix = two
lines (anchor canonicalization, same process anchor both sides). Probe
fnew293 PRE ×3 FAIL (double-prefix face) → POST ×3 PASS 7/0
(/data/data/<pkg>/files). composeStopwatch ×3: mangled app-visible
spellings 10→0, frame UNCHANGED 9afb2bd2606f303e (zero render drift).
Residual recorded PENDING: STREAM-OPEN exception MESSAGE spelling. Full
regression ZERO DRIFT at 702813ff2d5d8be8 (24/24 anchors ×3, battery ==
CONT-28..33 records, fnew293 56/0, simplecalc ×3 7960bce447ac6d8f).
Registry 601→602. Evidence: evidence/cont34/VIRTUAL_PATH_FRONTIER.md.
Next: composeStopwatch f141-null-recv + Lh4; ops=0 face; STREAM-OPEN
message spelling; standing F-NEW-288 (Track A) + SimpleCalc input-pump
(Track B).

---

## CONT-35 (2026-10-10) — TEXT-PIPELINE FRONTIERS: F-NEW-294/295/296

Environment recovery (fast-forward to 13d233b2; binary rebuilt BYTE-EXACT
702813ff2d5d8be8 == CONT-34 record; composeStopwatch dbf937ebbe7c0b3d +
SimpleCalc 68da25fd9fdf54b4 re-supplied SHA-exact). THREE generic roots
closed along the composeStopwatch text pipeline, one chain, probe-proven
each: (1) F-NEW-294 — the engine had NO Typeface law at all: sget
Typeface.DEFAULT hit SGET-MISS → NULL, create/defaultFromStyle fell to the
typed-default stub; the R8-inlined AndroidParagraphIntrinsics (Lk6;.<init>)
fed the null into the Kotlin platform-type `!!` (getClass BEFORE check-cast)
→ the recorded f141-null-recv at pc=409, one per run. Fix = sget constant
synthesis row (DEFAULT/DEFAULT_BOLD/SANS_SERIF/SERIF/MONOSPACE with
family/style fields) + bridge create×3/defaultFromStyle law (per-request
cached, non-null, family fallback). (2) F-NEW-295 — Layout$Alignment had no
kOrdinals rows → the 371-CLOSEOUT values() law answered NULL → Ljd1;.<clinit>
array-length NPE at pc=6; fix = 3 table rows in the decoded AOSP order
(NORMAL=0, OPPOSITE=1, CENTER=2; decoded from the android-34.jar clinit —
no ALIGN_LEFT/RIGHT on this API level). (3) F-NEW-296 — no
LineBreakConfig$Builder law (API 33+/34): new Builder() allocated but the
fluent setters returned NULL → chain broke at the SECOND link (the recorded
Lb1;.n pc=0 NPE); fix = Builder object law (fluent THIS, build() non-null)
+ StaticLayout$Builder.setLineBreakConfig whitelist row. Probes
fnew294/295/296 PRE ×3 FAIL (0/10, 0/6, 2/3 — exact recorded NPE messages)
→ POST ×3 PASS (10/0, 6/0, 5/0). composeStopwatch ×3: ALL uncaught
text-pipeline NPEs dead (pc409/Ljd1/Lb1 0 per run), only the 3 faithful
deferred faces + F084 budget halts remain, frame UNCHANGED 9afb2bd2606f303e
×3 — PARTIAL SUCCESS retained, text pass UNBLOCKED. Full regression ZERO
DRIFT at 6508a51d01b54280 (24/24 anchors ×3 byte-identical, probe battery ==
CONT-28..34 records EXACTLY, fnew294 77/0 + fnew295 49/0 + fnew296 42/0,
simplecalc ×3 rc=0 7960bce447ac6d8f). Registry 602→605. Evidence:
evidence/cont35/TEXT_PIPELINE_FRONTIER.md. Next: the Compose DRAW path
(Lh4; ops=0 — the layer drawContent → AndroidCanvas bridge family, dooz
shares it), empty dialog body; STREAM-OPEN message spelling (probe row
first); standing F-NEW-288 (Track A) + SimpleCalc input-pump (Track B).

---

## CONT-36 (2026-10-10) — DRAW-DISPATCH IDENTITY + LAYOUT.draw TEXT LAW (F-NEW-297 ROOT_CAUSED_FIXED)

CONT-35 independently verified first: local == origin/main (1cc38daa),
binary 6508a51d01b54280 byte-exact; probes fnew294/295/296 ×3 == records
(77/0, 49/0, 42/0); composeStopwatch ×3 9afb2bd2606f303e with all three
NPE faces 0/run; SimpleCalc ×3 FULL SUCCESS. Friend's Fragment/Preference
report verified per-claim: FragmentTransaction.commit no-drain + unhandled
addPreferencesFromResource CONFIRMED as real gaps (no failing consumer —
not speculatively patched); the friend's inflation patches NOT in this
lineage; the "F-NEW-253 nested in AudioAttributes" claim FALSE (top-level
view_ancestry.h rows, battery 147/0). Draw root decoded op-level: the
R8'd CanvasDrawScope (Loc0.c) is a REUSED dispatcher — the M3-19/F-098
re-entry key carried only 2 object args so every NESTED subtree draw
collided and was silently stubbed (125 stubs/run, depth 109-111): outer
shapes painted (ops=64), the text chain (Lg6.d → Layout.draw) never ran.
FIX (4 generic points, one family): identity cap 2→8 (keys strictly more
specific, depth-80 backstop); Layout.draw(Canvas) text law (ROOT-063
fields + carried paintOid, per-line DRAW_TEXT at the canvas translate
state, 0.928em ascent); CanvasShadow handles_class generic "Paint;" row
(TextPaint gate alignment, F-NEW-285 family); ROOT-063 paint_size probes
__text_size_px__ (F-NEW-226). Probe fnew297 (reused-dispatcher +
StaticLayout-draw shapes) PRE ×3 FAIL (nestedRan=0, 0 TEXT ops) → POST ×3
42/0 with BOTH text ops at the app's TRUE color/size (ff2244cc, 72px).
Target ×3: stubs 125→1 (Loc0.c 0), first-frame ops 64→236, frame UNCHANGED
9afb2bd2606f303e ×3; dooz anchor byte-stable ×3. dooz white frame DECODED:
RGB(250,250,250) theme background — boot composition burns the 15 s budget
then per-frame dispatchDraw halts at pc=2 (F084); frame-honesty law
ROOT_CAUSED/PENDING. FULL REGRESSION ZERO DRIFT at 054b9bd52fa695fc
(anchors 24/24 ×3, battery == CONT-28..35 records, fnew297 42/0,
simplecalc ×3 7960bce447ac6d8f). Registry 605→606. Evidence:
evidence/cont36/DRAW_DISPATCH_FRONTIER.md. Next: the paragraph-paint
dispatch (renamed DrawScope.drawText → Lte1.I/Lod1.I → Lg6 → Layout.draw
— Lte1.e0 runs in composition, its paint entry never fires); the
frame-honesty law (in-draw F084 halt → keep previous frame, dooz anchor
movement); STREAM-OPEN message spelling; standing F-NEW-288 (Track A) +
SimpleCalc input-pump (Track B).

---

CONT-37 (binary a181d7b317e015c8): the paint/present contract F-NEW-298
ROOT_CAUSED_FIXED as THREE coordinated generic points, one semantic
family. Decode op-level end-to-end: the text painter Lte1.I IS dispatched
(r=1, coordinator set; the attach-gate theory dead) and its resolution
SUCCEEDS — two silent gates inside the body killed it: (a) Lg6.d gates
the whole paragraph paint on Canvas.getClipBounds(Rect) — unhandled →
typed-default FALSE → silent abort BEFORE Layout.draw ([F298-GCB]); (b)
the StaticLayout$Builder law's "setText" PREFIX match conflated
setTextDirection — Compose calls setTextDirection FIRST and its heuristic
arg OVERWROTE the obtain-stored source (obtain text.len=17/2/2 → build
chars=0); (c) THE FRAME WIPE — composeStopwatch frame 1 drew 265 ops
INCLUDING all three texts and replayed them, frames 2-6 halted in-window,
and the unconditional fb.clear(win_bg)+present erased frame 1 (the
visible face was the (13,15,18) fill + the dialog). FIX: (1) CanvasShadow
getClipBounds law (tracked clip or device bounds, AOSP-honest); (2)
Builder setter EXACT match (setTextDirection stores textDir, never the
payload); (3) FRAME-HONESTY law — any halt unwinding the draw window
sets draw_window_budget_halted_, the compositor skips the presentation
([F298-KEEP]) and keeps the last COMPLETE frame (the P1-6 extension
recorded PENDING in CONT-36 §6; ART/SurfaceFlinger: an unfinished frame
is never presented). Build config: dalvik_engine.cpp now builds -O2 -g0
per-file (the TU outgrew the -g cc1plus peak on the 4 GB host; same
optimizer, debug sections dropped). PROBE fnew298 (frame-1 green marker +
frame-2 DEX busy loop halted mid-draw; runner-side KEEP-CORNER pixel row)
PRE ×3 on ddc37884601ca802 corner=(48,48,48) FAIL ×3 → POST ×3 on
a181d7b317e015c8 corner green ×3, 19/0. Target ×3: composeStopwatch
9afb2bd2606f303e → bbaf8f76308dc267 ×3 — the app's OWN first frame
presented for the first time (265 ops: black surface, cards, the three
StaticLayout texts at the app's positions/sizes; 45 Layout.draw text-op
rows/run). dooz anchor MOVED d602648e8e401895 → 31ddd4d5b8e6d18e ×3
(legitimate: the old 250-gray was the DISHONEST presentation of an
unfinished frame — the boot composition needs ~15.3 s, never completes;
the honest state is keep-empty white). FULL REGRESSION at a181d7b317e015c8:
7/8 anchors ×3 BYTE-IDENTICAL (KEEP=0, zero drift), battery == CONT-28..36
records EXACTLY + fnew298 19/0, simplecalc ×3 rc=0 7960bce447ac6d8f.
Registry 606→607. Evidence: evidence/cont37/FRAME_HONESTY_FRONTIER.md.
Friend-report question answered from the recorded CONT-36 §9 verdicts:
the calculator claim is OUR law chain (SimpleCalc 7960bce447ac6d8f ×3);
the friend's patches are NOT in this lineage. Next: the Compose
draw-brush color application (the TextPaints carry pipeline-default
black — the Lbo1 brush→paint application point is the last leg of text
visibility); the dooz boot-budget face (PENDING, composition-cost wave);
STREAM-OPEN message spelling; standing F-NEW-288 (Track A) + SimpleCalc
input-pump (Track B) + Fragment/Preference family (probe-first, build on
F-NEW-234).
