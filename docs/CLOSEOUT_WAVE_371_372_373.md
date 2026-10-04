# FINAL CLOSEOUT LEDGER — #371/#372/#373 continuation wave (2026-10-04)

HEAD at closeout: `59c57519` (start) → wave commits (this ledger's commit).
FINAL BINARY SHA16: `4c01757e8f11c8a0` (PATCH wave binary).
BASE for A/B: `267bf47d5d901054` — the recorded #371 final binary, reproduced
BYTE-IDENTICALLY by a clean `make` at start (`run/closeout/` build log +
sha printout in `scripts/closeout_baseline.sh` output captured in worklog).

## §0 — IMMEDIATE BLOCKER (contract item 6)

STATUS: ALREADY VERIFIED | RESULT: touch_dispatcher.cpp AOSP claim law IS
COMMITTED at `d0eec40e` (371-FINAL: TouchDispatcher AOSP ViewGroup.
dispatchTouchEvent claim law — first topmost claimant wins; suntimes
bottom-bar taps → Next button, PerformClick dispatched, listener runs
setCurrentItem); the file is in HEAD's tree
(`git ls-tree HEAD miniandroid/src/framework/touch_dispatcher.cpp`) | EVIDENCE:
git log d0eec40e; no uncommitted touch_dispatcher delta (`git status` clean)
| TESTS: n/a (commit-existence check)

## §1 — BASELINE RECONCILIATION AT CURRENT HEAD

STATUS: VERIFIED | RESULT: clean build at HEAD reproduced recorded binary
`267bf47d5d901054` byte-identically; full gate suite re-executed green at it
before any change (container-reset repair: toolchain relayout via
scripts/build/bootstrap_toolchain.sh, gate_a/native/hmap fixture APKs
rebuilt SHA-verified, EXT-01/02 re-fetched SHA-exact
`009b4671…`/`121d479c…`, blockblast re-fetched `64589a3a7e5c0f73` =
recorded, native probe libs x86_64 `d5ec1f57fef3d271` = recorded) |
EVIDENCE: run/battery_closeout_final2.log; run/audit; probe_store rows |
TESTS: anchors 5/5 ×3, goldens 4/4, loading probe ALL, gate A 95/0/2
(×2 stores), negatives 17/17, reinstall 8/8, uninstall ALL, battery 114/114
(then 122/122 fresh), density matrix 11/11, NATX 10/10 ×3, multiapp 5/5

## §2 — #373 ENVIRONMENT/PREREQUISITE MATRIX (priority 4/5)

STATUS: IMPLEMENTED+TESTED (R-NEW-465) | RESULT:
(a) `docs/ENVIRONMENT_PROFILE.json` ENV-001..010 — default device:
API 34/"14", MiniAndroid/miniandroid profile, 420dpi 1080×1920,
x86_64 host, advertised-vs-executable ABI truth
([arm64-v8a,armeabi-v7a,armeabi] advertised / [x86_64] executable /
nativeBridge=false), PortableGL GLES2 software (no Vulkan), decoder list,
hardware presence map, profile SHA16 `56e6347116942bfc` (ENV-010).
(b) `pkginspect --what prerequisites` — APK-001..020 machine-readable schema
per APK (minSdk/targetSdk/usesFeatures/dangerousPermissions/abiLibs/
abiElfMachines/webview/nativeAbiVerdict/environmentMismatches/
missingCapabilities/recommendedNextProbe — the #373 §12 API-001..005 shape).
(c) `docs/ENV_PREREQUISITE_MATRIX.jsonl` — 30 corpus APKs profiled: 16
NO_NATIVE_CODE, 10 EXECUTABLE_NATIVE, 2 ABI_MISMATCH_TRANSLATION_REQUIRED
(EggReturnsHome, forkgram); vulkan mismatch flagged on asteroids_revenge.
(d) REDROID-CLASS LIVE PROOF: com.yepgoryo.EggReturnsHome_1.apk (arm64-only
libgodot.so) — install rc=0, run stops DEFAULT_BACKGROUND_ONLY with 0 app
draw ops; first divergence = GodotActivity.onCreate → godot_fragment_container
empty (Fragment materialization frontier) AND arm64 lib not executable →
DUAL-CAUSE, recorded in `docs/WS_PREREQUISITE_AUDIT.md` | EVIDENCE:
run/closeout/env_egg_run1.log; prerequisites JSON rows | TESTS: 30 APK
profiles + 1 live install/run + probe store refresh

## §3 — WS-001/WS-002 WHITE/BLACK PREREQUISITE AUDIT (priority 5)

STATUS: VERIFIED | RESULT: every near-blank corpus case classified with
prerequisite evidence — **5 ordinary runtime roots** (fossify clock
ViewTree/lifecycle family, blockblast Compose, spacevertex Fragment,
memory WindowInsets (fixed post-#366), sudoku/whatsapp window chain),
**2 environment-caused/dual** (EggReturnsHome ARM-only+fragment,
asteroids_revenge Vulkan-on-GLES2), **1 duplicate** (recorded telegram
navigation face). ANSWER: the white/black population is predominantly
ordinary runtime roots; environment prerequisites are a REAL but MINORITY
cause (2 of 8 classified faces), and the prerequisite layer now
machine-readably separates them BEFORE running | EVIDENCE:
docs/WS_PREREQUISITE_AUDIT.md/.jsonl; docs/DIFFERENTIAL_WORKING_VS_WHITE.md
(#366) | TESTS: 8 case classifications + 30-APK prereq matrix

## §4 — #372 DEEP ROOT-CAUSE CROSS-MATCH (priority 3)

STATUS: VERIFIED | RESULT: 10 externally-researched candidates
cross-matched against the 538-root registry with A–F classifications —
4×E NOT APPLICABLE (gralloc/fences/compositor/RRO: no such layer in a
host-process software-rendered runtime), 4×B SAME_ROOT/NEW_EVIDENCE
(linker/dlopen=S-2 law, Binder/service=#370 B5, surface identity,
WS prerequisite family), 1×D NEW ROOT (ABI-truth → R-NEW-465,
implemented+tested this wave), 1×C WATCH (colorspace/premultiplication —
no divergence; deliberately NOT implemented). NO duplicate roots created |
EVIDENCE: docs/DEEP_ROOT_CROSSMATCH.jsonl | TESTS: 10 classifications

## §5 — NEW ROOTS FIXED THIS WAVE (priority 1 continuation)

STATUS: R-NEW-463 ROOT-CAUSED-FIXED | RESULT: S137 law — M3-19 re-entrancy
key refinement: CLASS_REF payloads (`@<descriptor>` key parts, both arms).
A/B: BASE `0dcf8deddf4c5814` (pre-R-NEW-428 patch binary) killed
fossifyclock at App.onCreate (f141-null-recv NPE "Set.iterator on null" ←
M3-19 cycle stub nulled the Lifecycling d.a hierarchy recursion because
Class payloads were invisible to the key); PATCH `4c01757e8f11c8a0` —
App.onCreate passes, SplashActivity + MainActivity RESUMED, new frontiers
exposed (EventBus getModifiers + XmlPullParser inflate chain) — the causal
chain advanced two stages | EVIDENCE: run/cont371/fossifyclock2/r1.log vs
run/cont371/fossifyclock_0dcf8deddf4c5814/run1; disasm
scripts/cont_disasm_fossify_lifecycle.py (d.a pc=0x74/0x7c) | TESTS: A/B ×1
+ full regression green at PATCH

STATUS: R-NEW-428→464 PARTIAL | RESULT: Method.getModifiers law landed
(DEX access_flags minted into Method records + bridge handler with PUBLIC
fallback); EventBus LO5/d;.i chain STILL throws EventBusException at
pc=392 — some minted-record getModifiers calls still route REC-MISS;
honest boundary: the reflection Method-record call route needs
deterministic bridge dispatch before EventBus subscriber scans pass |
EVIDENCE: run/cont371/fossifyclock2/r1.log lines 406–442 (11 REC-MISS
remain) | TESTS: A/B ×1

## §6 — #371 EXECUTION MATRIX L0–L6 (priority 2)

STATUS: VERIFIED (evidence-backed rows) | RESULT: 29 titles leveled —
**L6 = 15** (opencalc/chess/dooz/microtimer/unote anchors ×3 byte-identical;
2048/SnakeDeluxe/MiniCraft/HelloWorld goldens; flappycow/notes_secuso/
gmdice/tripeaks/fishrings/suntimes fan-out VERIFIED ×3 at recorded SHAs),
L3 = 2, L4 = 3, L2 = 4, L1 = 2, L0 = 3 (BLOCKED-BY-IDENTITY Safir/Black,
Telegram auth external boundary). INSTALLED_ONLY strictly distinguished
from EXECUTED (blockblast = L1 render-FAIL inspection leg, never counted
as execution) | EVIDENCE: docs/EXECUTION_LEVEL_MATRIX.jsonl | TESTS: as
recorded per row

## §7 — NEW APP + NEW GAME (priority 8)

STATUS: TESTED (honest) | RESULT: NEW APP fossifyclock
(org.fossify.clock, F-Droid, sha16 64589a3a-era corpus) — L1/L2: App.onCreate
died at BASE; after S137 fix reaches MainActivity RESUMED with white face;
roots R-NEW-463 (fixed) + R-NEW-464 (partial) + XmlPullParser inflate chain
(recorded). NEW GAME fairymahjong (com.fairytrick.fairymahjong) — L2: real
view tree builds (addView chain works), game-init constructor hits the
F-NEW-084 interpreter halt (50001-visit loop cap) → WINDOW_ROOT never
lands; honest freeze-law boundary, NOT fixed (raising the cap risks the
determinism gates). BONUS: sudokusolver — Compose Navigation frontier
("Could not find Navigator with name 'composable'") = F-NEW-221 family.
All three installed-identity runs with hidden sources, first divergences
recorded | EVIDENCE: run/cont371/screen_miniandroid.json;
run/cont371/sudokusolver_screen; worklog | TESTS: 1 run each (screen mode)

## §8 — AGENT SKILL (priority 1 / #371 P0)

STATUS: IMPLEMENTED+TESTED | RESULT: `docs/execution-skill/skill_manifest.json`
(10 machine-readable operations with CLI/return/error contracts,
deterministic status + frame-verdict vocabularies, L0–L6 definitions);
SKILL.md v2 operational surface; `scripts/skill_selftest.py` drives EVERY
manifest operation end-to-end with manifest-documented CLIs only —
**13/13 PASS** (intake, prerequisites schema, malformed-APK loud failure,
install identity, run-by-installed-identity, frame-truth observe, 3-way
white/black cause, run-pair determinism, provenance bundle, uninstall +
NOT_INSTALLED, manifest self-containment). External-agent answer: YES — an
agent can receive an APK and reach a machine-readable verdict without
reading MiniAndroid source | EVIDENCE:
docs/execution-skill/selftest_report.json | TESTS: 13 checks

## §9 — VIEWPAGER/FRONTIER + SUNTIMES APK DRIFT (priority 7)

STATUS: PARTIAL (honest boundary) | RESULT: Suntimes re-run attempt exposed
**APK DRIFT, not regression**: the current F-Droid `135` file
(sha16 `bd0fbe51f684895d`) produces NO_ROOT + time4j deaths at BOTH the
recorded BASE binary `267bf47d5d901054` AND the PATCH `4c01757e8f11c8a0`
(A/B isolated stores, same APK) — the recorded REAL_APP_CONTENT evidence
(a49f90d65a8fc5c8 ×3) remains valid for the recorded APK bytes; the
upstream file changed under the same versionCode. ViewPager primitive
(page-fragment materialization, mCurItem IGET-MISS at ViewPager.populate)
remains the named frontier — the drifted APK blocks re-attempting it on
Suntimes until a SHA-pinned refetch | EVIDENCE: run/closeout/sun_base/r1.log
vs run/closeout/sun_s137/r1.log | TESTS: A/B ×1 each binary

## §10 — FINAL REGRESSION AT FINAL BINARY (priority 9)

STATUS: ALL GREEN | RESULT: binary `4c01757e8f11c8a0` — anchors 5/5 ×3
byte-identical (e364b001ee7abd66 / b5a7a35d5fe0564b / d602648e8e401895 /
da73010a37dd0189 / 4f1a9e4e8f64fae8), user goldens 4/4 REAL_APP_CONTENT,
loading probe ALL PASS, fresh battery 122/122 RC=0, gate A probe 95/0/2
(both stores), negatives 17/17, reinstall 8/8, uninstall ALL PASS, NATX
10/10 ×3 byte-identical (0f2dafacaa807aa0), skill selftest 13/13.
Classifier UNTOUCHED | EVIDENCE: run/battery_final_fresh.log; run/audit;
run/closeout/S137_binary_sha.txt | TESTS: as listed

## §11 — REGRESSION LAW COMPLIANCE

No package-name/APK-specific code (all changes are engine laws: M3-19 key
refinement, Method reflection minting, prerequisite inspection section).
No gate weakened. No classifier change. Battery repaired earlier (S-2
link lines) predates this wave; this wave changed no battery stage.
