# 371/372/373 CONTINUATION LEDGER — from CURRENT HEAD 59c57519

Contract: read/reconcile #371→#372→#373, continue unresolved #364–#370, do not open another issue. Every row: STATUS—RESULT—EVIDENCE—TESTS.

## §0 — TouchDispatcher commit (contract item 6)

STATUS: ALREADY VERIFIED | RESULT: touch_dispatcher.cpp AOSP claim law committed at `d0eec40e` (first-topmost-claimant-wins law; suntimes bottom-bar tap → Next button, PerformClick dispatched, listener runs setCurrentItem); file present in HEAD tree, no uncommitted delta | EVIDENCE: `git log d0eec40e`; `git status` clean for the file | TESTS: commit-existence check

## §1 — Baseline reconciliation at HEAD

STATUS: VERIFIED | RESULT: clean build at `59c57519` reproduced recorded BASE binary `267bf47d5d901054` byte-identically; container-reset repair (toolchain relayout, fixture APK rebuilds SHA-verified, EXT-01/02 re-fetched SHA-exact `009b4671…`/`121d479c…`, native probe libs x86_64 `d5ec1f57fef3d271` = recorded) | EVIDENCE: run/battery_closeout_final2.log | TESTS: anchors 5/5×3, goldens 4/4, loading probe ALL, gate A 95/0/2 ×2 stores, negatives 17/17, reinstall 8/8, uninstall ALL, battery ALL PASS, density matrix 11/11, NATX 10/10×3, multiapp 5/5

## §2 — Agent Skill is a real product surface (#371 P0)

STATUS: IMPLEMENTED+TESTED | RESULT: `docs/execution-skill/skill_manifest.json` — 10 machine-readable operations (apk_intake, prerequisites, full_inspection, install, run, observe, first_divergence, classify_white_black, evidence_bundle, uninstall) with CLI/return/error contracts + deterministic status & frame-verdict vocabularies + L0–L6 definitions; SKILL.md v2 operational surface; `scripts/skill_selftest.py` drives EVERY operation end-to-end with manifest-documented CLIs only (no source imports) → **13/13 PASS** | EVIDENCE: docs/execution-skill/selftest_report.json | TESTS: 13 checks incl. malformed-APK loud failure, installed-identity run, frame-truth observe, 3-way white/black cause, run-pair determinism, provenance, uninstall NOT_INSTALLED honesty, manifest self-containment

**External-agent answer: YES** — an agent can receive an APK and reach a machine-readable verdict (prerequisites → install → run → frame truth → first divergence → cause classification) without reading MiniAndroid source or guessing from screenshots.

## §3 — Execution truth L0–L6 (#371 50-title target)

STATUS: VERIFIED | RESULT: 29 evidence-backed rows in `docs/EXECUTION_LEVEL_MATRIX.jsonl` — **L6 = 15** (opencalc e364b001ee7abd66 ×3, chess b5a7a35d5fe0564b ×3 (determinism anchor, NOT a pixel golden), dooz d602648e8e401895 ×3, microtimer da73010a37dd0189 ×3, unote 4f1a9e4e8f64fae8 ×3, goldens 2048/SnakeDeluxe/MiniCraft/HelloWorld, flappycow 13cf47464d9787f4 ×3, notes_secuso eb5ebd559cad1028 ×3, gmdice/tripeaks/fishrings/suntimes fan-out ×3), L3 = 2, L4 = 3, L2 = 4, L1 = 2, L0 = 3 (BLOCKED-BY-IDENTITY ×2, Telegram auth external boundary). INSTALLED_ONLY ≠ EXECUTED strictly maintained (blockblast = installed-inspection leg only) | EVIDENCE: docs/EXECUTION_LEVEL_MATRIX.jsonl + recorded sha blocks | TESTS: as per row

## §4 — NEW app + NEW game (contract item 8)

STATUS: TESTED (honest) | RESULT:
- **NEW APP org.fossify.clock** — BASE killed App.onCreate (f141-null-recv NPE: M3-19 cycle stub nulled the Lifecycling `d.a` hierarchy recursion because Class payloads were invisible to the re-entrancy key). **GENERIC FIX S137 (R-NEW-463 ROOT-CAUSED-FIXED)**: CLASS_REF payload key refinement `@<descriptor>` in both arms; A/B: PATCH advances App.onCreate → SplashActivity + MainActivity RESUMED. Next frontiers exposed and recorded: R-NEW-464 Method.getModifiers (landed, PARTIAL — EventBus chain boundary named) + LayoutInflater null-XmlPullParser chain (#366-consistent).
- **NEW GAME com.fairytrick.fairymahjong** — real view tree builds (addView chain works); game-init constructor hits the F-NEW-084 interpreter halt (50001-visit loop cap) → WINDOW_ROOT never lands. Honest freeze-law boundary; raising the cap would risk the determinism gates.
- BONUS com.galaxyrio.sudokusolver — Compose Navigation frontier ("Could not find Navigator with name 'composable'") = F-NEW-221 family.
| EVIDENCE: run/cont371/screen_miniandroid.json; run/cont371/fossifyclock2/r1.log vs run/cont371/fossifyclock_0dcf8deddf4c5814/run1; scripts/cont_disasm_fossify_lifecycle.py (bytecode pc=0x74/0x7c chain) | TESTS: A/B + registry R-NEW-463/464

## §5 — #372 deep root-cause cross-match (no duplicates)

STATUS: VERIFIED | RESULT: 10 externally-researched candidates classified A–F against the 538-root registry (`docs/DEEP_ROOT_CROSSMATCH.jsonl`): 4×E NOT APPLICABLE (gralloc/fences/compositor/RRO — no such layer in this host-process software-rendered runtime), 4×B SAME_ROOT/NEW_EVIDENCE (linker=S-2 dlopen law, Binder/services=#370 B5, surface identity, WS family), 1×D NEW ROOT → **R-NEW-465 implemented+tested this wave** (ABI-truth prerequisite layer), 1×C WATCH (colorspace/premultiplication — no divergence, deliberately not implemented) | EVIDENCE: docs/DEEP_ROOT_CROSSMATCH.jsonl | TESTS: 10 classifications, 0 duplicate roots

## §6 — #373 environment matrix + WS audit (contract items 4/5)

STATUS: IMPLEMENTED+TESTED | RESULT:
- ENV-001..010 machine-readable (`docs/ENVIRONMENT_PROFILE.json`, profile sha16 56e6347116942bfc): **API 34/"14", MiniAndroid/miniandroid device, 420dpi 1080×1920, x86_64 host, ADVERTISED [arm64-v8a,armeabi-v7a,armeabi] vs EXECUTABLE [x86_64] (nativeBridge=false — honest), PortableGL GLES2 (no Vulkan), decoder list, hardware presence map**.
- `pkginspect --what prerequisites` = #373 §12 API-001..005 shape (APK-001..020 rows per APK; machine-readable). 30-APK matrix: 16 NO_NATIVE_CODE / 10 EXECUTABLE_NATIVE / **2 ABI_MISMATCH_TRANSLATION_REQUIRED**.
- **Redroid-class LIVE PROOF**: com.yepgoryo.EggReturnsHome_1.apk (arm64-only libgodot.so) INSTALLS (rc=0) then stops DEFAULT_BACKGROUND_ONLY with 0 app draw ops — dual cause: arm64 lib not executable + godot_fragment_container Fragment never materializes.
- WS-002 ANSWER: white/black faces are **predominantly ordinary runtime roots (5 of 8)**; environment prerequisites are real but minority (2 of 8: ARM-only native, Vulkan-on-GLES2); 1 duplicate. The prerequisite layer separates them machine-readably BEFORE running.
| EVIDENCE: docs/WS_PREREQUISITE_AUDIT.md/.jsonl; docs/ENV_PREREQUISITE_MATRIX.jsonl; run/closeout/env_egg_run1.log | TESTS: 30 profiles + live A/B

## §7 — ViewPager frontier + Suntimes APK drift

STATUS: PARTIAL (honest boundary) | RESULT: current F-Droid suntimeswidget_135 bytes (sha16 bd0fbe51f684895d) DIFFER from the recorded APK — A/B at BOTH binaries (BASE 267bf47d5d901054 and PATCH 4c01757e8f11c8a0, isolated stores, same APK) shows identical time4j deaths + NO_ROOT → **APK DRIFT, zero runtime regression**; recorded REAL_APP_CONTENT evidence (a49f90d65a8fc5c8 ×3) stands for the recorded bytes. ViewPager page-fragment materialization (mCurItem IGET-MISS at ViewPager.populate) remains the named frontier; re-attempt requires a SHA-pinned refetch | EVIDENCE: run/closeout/sun_base/r1.log vs run/closeout/sun_s137/r1.log | TESTS: A/B ×2 binaries

## §8 — Final regression (contract item 9)

STATUS: ALL GREEN | RESULT: final binary **`4c01757e8f11c8a0`** (commit 58b5c14e) — anchors 5/5×3 byte-identical (all recorded shas), user goldens 4/4 REAL_APP_CONTENT, loading probe ALL PASS, fresh battery 122/122 RC=0, gate A probe 95/0/2 (both stores), negatives 17/17, reinstall 8/8, uninstall ALL PASS, NATX 10/10×3 byte-identical (0f2dafacaa807aa0), skill selftest 13/13, classifier UNTOUCHED | EVIDENCE: run/battery_final_fresh.log; run/closeout/S137_binary_sha.txt | TESTS: as listed

## Remaining open (honest)

- R-NEW-464 PARTIAL (Method-record reflection route → EventBus chain).
- ViewPager page-fragment materialization (needs SHA-pinned Suntimes refetch).
- fairymahjong F-NEW-084 loop-cap boundary; Compose family (F-NEW-221) still open.
- CPU translation for ARM-only APKs = F EXTERNAL/FUTURE boundary (quantified 2/30 corpus APKs).
- Full ledger: docs/CLOSEOUT_WAVE_371_372_373.md; commit 58b5c14e; binary 4c01757e8f11c8a0.
