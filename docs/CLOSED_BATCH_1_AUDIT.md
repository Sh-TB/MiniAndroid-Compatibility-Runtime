# CLOSED BATCH 1 AUDIT — #367

**Program:** CLOSED ISSUE FORENSIC PROGRAM — BATCH 1/3 — 50 HIGH/HARD CASES

**Batch scope:** historical Telegram/login/runtime achievements, genuine gameplay/EXEC cases, crash/Compose/theme frontier, first text/layout/storage families.

**Audit head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631` (runtime binary rebuilt from this commit; battery-repair commit 9c3dc4d1 is the runtime code under test).

**Method:** for every issue in the frozen batch membership: body + comments + linked evidence re-read; historical claim independently reconstructed; APK identity checked; historical runtime commit vs current HEAD distinguished; current-HEAD evidence produced this campaign (gates + 121/121 battery + fresh re-run wave); pixel-truth law applied (BYTE-STABLE != PIXEL-TRUTH, F-NEW-233); closed/open state ignored as evidence.

**Classification distribution:** verified current = 38, historical-only verification = 9, superseded = 2, partial closure = 1.

**Classification policy (honest, strict):** `verified current` requires evidence produced at the CURRENT runtime binary (this campaign's gates, battery, or re-run wave) or a law fenced by the current battery. Evidence only at older HEADs (even 3-run) = `historical-only verification` (reproducibility proven, currency not re-confirmed). Synthetic micro-gap laws are `verified current` ONLY at law level with their test-only scope explicitly retained (M5 honesty rule).

## Per-issue audit table

| # | Title | Classification | Key current-HEAD evidence |
|---|-------|----------------|---------------------------|
| #1 | EXP-064 — REAL LOGIN IMAGE PROVEN BY PIXELS (OCR-validated PhoneView rendered) | historical-only verification | session-era execution trace only; runtime chain superseded by S107+ Telegram boundary work; current carrier = forkgram (M3: x2 byte-identical bbb6cd10a834963d a |
| #2 | EXP-065 — Fix multi-DEX const-string bug (FIELD_PREFERRED_AUDIO_LANGUAGES leak resolved) | verified current | multi-DEX const-string law is live in the current binary: forkgram (5-DEX) x2 byte-identical runs at abb57444 + battery semantic pass3-bridge stage ALL PASS at  |
| #3 | EXP-066 — Multi-DEX semantic audit + OutlineTextContainerView text capture (Phone number label visible) | historical-only verification | session-era; text-capture capability since generalized (text laws battery 21/21 at 9c3dc4d1). |
| #4 | EXP-067 — Resource resolution + AXML parser + Drawable decoding (real WebP images in Login UI) | superseded | superseded by stronger current laws: ARSC bag/style laws + AXML parse are battery-fenced (drawables 39/39 incl. AXML-driven vectors; G04 density oracle 11/11) a |
| #5 | EXP-068 — Generic View inheritance + Floating Next button (semantic superclass resolution) | historical-only verification | view-inheritance laws since formalized (G11 ctor law 37/37 incl. superclass walk, F-074 engine-level super-run 6/6 GREEN at 9c3dc4d1). |
| #6 | EXP-069 — Generic text input + click dispatch: phone number injected + Next button clicked | historical-only verification | input/dispatch laws current: G06 tap interaction golden (21 law checks) + 3-run tap determinism + tictactoe 9/9 DEX-dispatched clicks at 9c3dc4d1. |
| #7 | EXP-071 — Telegram Login → SMS Code Page Transition (CHECKPOINT_M PROVEN) | historical-only verification | checkpoint session evidence in-era; current-era Telegram boundary is an ARTIFACT problem, not runtime: forkgram installs + runs deterministically (x2 byte-ident |
| #8 | MiniAndroid campaign evidence — verified achievements (REUSE-FIRST campaign, 2026-09-05) | superseded | superseded: canonical registries now the single source of truth (registry.json, root_registry.json, MICRO_GAP_REGISTRY.json, ARTIFACT_REGISTRY.json). |
| #10 | [EXEC] HelloWorld — APK Execution & Visual Proof | verified current | user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops; Snake Deluxe: 1203/0.72/262; MiniCraft: 2416/0.64/735; Hello |
| #11 | [EXEC] TicTacToe — APK Execution & Gameplay Proof | verified current | tictactoe_golden (SS29) stage PASS at 9c3dc4d1 inside run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log);  |
| #12 | [EXEC] ConnectFour — APK Execution & Gameplay Proof | historical-only verification | not re-run at current HEAD; not part of the battery. |
| #13 | [EXEC] AndroidGameSnake — Autonomous Gameplay Proof | verified current | — fresh execution at current HEAD via evidence/batch367_rerun/zhangman.github.snake/. |
| #15 | [EXEC] Unote — Runtime/UI Completion | verified current | working_vs_failing_probe.sh @ 9c3dc4d1: 5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73 |
| #17 | [EXEC] GMDice — APK Execution & Visual Proof | verified current | battery corpus run stage PASS at 9c3dc4d1; fresh re-run at HEAD 9c3dc4d1: rc=0, status=SUCCESS ✅, unique_colors=892, frame_delta=False. |
| #18 | [EXEC] MicroTimer — APK Execution & Visual Proof | verified current | working_vs_failing_probe.sh @ 9c3dc4d1: 5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73 |
| #68 | [GAME-044] com.smorgasbork.hotdeath — compatibility report | historical-only verification | S107 x3 runs recorded; NOT re-run at current HEAD (APK not in current canonical set). |
| #81 | [GAME-057] org.bobstuff.bobball — compatibility report | historical-only verification | S107 x3 runs; not re-run at current HEAD. |
| #121 | [GAME-097] com.dozingcatsoftware.bouncy — compatibility report | verified current | diff366 ROOT-A fan-out at edecae3e: byte-identical zero drift; fresh re-run at HEAD 9c3dc4d1: rc=1, status=PARTIAL SUCCESS ⚠️, unique_colors=413, frame_delta=Fa |
| #166 | [APP-042] org.ucam.ssb22.pinyinfdroid — compatibility report | historical-only verification | x3 runs at S107 audit; not re-run at current HEAD (APK not in current canonical set). |
| #234 | [MG-051] Font fallback selection — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #235 | [MG-073] ellipsize — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #236 | [MG-080] Unicode combining marks — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #237 | [MG-081] RTL basic shaping — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #238 | [MG-082] Arabic joining — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #239 | [MG-083] emoji fallback — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #240 | [MG-084] surrogate pairs — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #241 | [MG-085] UTF-8/UTF-16 boundary — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #242 | [MG-115] requestLayout propagation — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 layout/net laws (expect 11) PASS 11/11 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY G |
| #243 | [MG-123] scroll offset — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #244 | [MG-124] translationX — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #245 | [MG-125] translationY — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #246 | [MG-126] scaleX — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #247 | [MG-127] scaleY — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #248 | [MG-128] rotation — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #249 | [MG-129] pivot — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part o |
| #250 | [MG-171] SharedPreferences default file — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #251 | [MG-172] custom file — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #334 | [GAMES-1] Full-load 5-10 games end-to-end (launch + render + interaction evidence) | verified current | wave evidence + current-HEAD re-confirmation of the flagged titles: snake-deluxe (golden gate), 2048 (golden gate), tictactoedeluxe + snakeneon + androidgamesna |
| #335 | [GAMES-2] Autonomous Snake Deluxe play (self-play, no game-memory cheating) | verified current | user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (Snake Deluxe leg). |
| #336 | [GAMES-3] House-building autonomous play (Minicraft) | verified current | user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (MiniCraft leg: REAL_APP_CONTENT, 735 draw ops). |
| #337 | [GAMES-4] NEW snake variant — build, load, autonomous play | verified current | fresh re-run at HEAD 9c3dc4d1: rc=0, status=SUCCESS ✅, unique_colors=884, frame_delta=True — frame delta TRUE (game animates). |
| #338 | [GAMES-5] Autonomous 2048 play | verified current | user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (2048 leg: REAL_APP_CONTENT, 34 draw ops). |
| #340 | [GAMES-7] Autonomous TicTacToe Deluxe play | verified current | — tap interaction produced frame delta TRUE. |
| #341 | [GAMES-8] Wave evidence package + gh-pages gameplay GIFs | verified current | artifact existence verified at 9c3dc4d1: docs/evidence/s98/games_full_load.json, minicraft_autoplay.gif, snakeneon_autoplay.gif present; docs/EXECUTED_GIFS.md + |
| #342 | [F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attr resolution gap for non-AppCompat-ancestor themes (mykanji family) | verified current | ARSC style law current: M3 ARSC style law 17/17 + M3 style geometry golden (6 checks) + density-matrix oracle 11/11 at 9c3dc4d1; before/after: droidify DEFAULT_ |
| #345 | [F-NEW-168] crash-on-launch family — rc=1 NPE chains (raumballer/tictactoe-classic) + dooz rc=-11 process-death | verified current | dooz determinism x3 byte-identical at 9c3dc4d1 (5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microti |
| #347 | [F-NEW-169] dooz compose-navigation NPE chain — 3 roots after rc=-11 fix | verified current | dooz runs gracefully x3 byte-identical at 9c3dc4d1; 41/41-frame runs recorded at closure. |
| #349 | [S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked on null registry receiver inside ComponentActivity.<init> | verified current | fix laws live in the current binary (F-NEW-160 in root_registry; solitaire reaches onStart, 3-run 6588621c4a0c4182 frontier state recorded); battery 121/121 at  |
| #350 | [S102-B] compose frontier: 'CompositionLocal LocalDensity not present' — WindowRecomposer host wiring (solitaire, the real compose-runtime root) | partial closure | LocalDensity ISE eliminated (closure evidence); Compose pipeline laws current: F-NEW-179 canonical pump + F-NEW-201 one-stable-content-object (registry IMPLEMEN |
| #352 | [S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park has no blocking semantics) | verified current | park law live: F-074 fixture (which encodes the dooz DispatchedContinuation drained-continuation law) runs 6/6 GREEN at 9c3dc4d1; F-050 frame-pump golden PASS ( |

## Per-issue detail

### #1 — EXP-064 — REAL LOGIN IMAGE PROVEN BY PIXELS (OCR-validated PhoneView rendered)

- **historical_claim:** EXP-064: Telegram login screen (PhoneView) rendered with REAL pixels, OCR-validated, proven by screenshot metrics.
- **historical_evidence:** FR-001 (OBSERVED/E3): session screenshot + OCR; commits 1e1ec2b4/c322b479/1dda55ae/78c182f3; predates golden/3-run laws.
- **tested_runtime_commit:** 1e1ec2b4 (era)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** Telegram-era session APK; golden APK later lost (K-26); official download = 1.2MB stub installer sha 480263f8 (BLOCKED-APK-ABSENT).
- **runtime_proof:** session-era execution trace only; runtime chain superseded by S107+ Telegram boundary work; current carrier = forkgram (M3: x2 byte-identical bbb6cd10a834963d at abb57444).
- **viewtree_proof:** session-era; not reconstructable at HEAD.
- **state_change_proof:** login page transition primitives proven by later EXP chain (#5/#6/#7).
- **screenshot_metrics:** session screenshot with OCR-validated text; no F-NEW-233 metrics (pre-law era).
- **reproducibility:** not re-runnable at HEAD (artifact absent); 3-run law not applicable to session era.
- **first_divergence:** N/A (historical session).
- **root_family:** TELEGRAM/exp-era
- **pixel_truth:** historical pixel evidence predates F-NEW-233; no current visual claim asserted.
- **final_classification:** **historical-only verification**
- **evidence_refs:** docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl#FR-001; issue #7 comments (S27 review)
- **notes:** Closed state honest for its era; superseded as current-carrier evidence by the S107+ chain and forkgram runs. Gap: golden Telegram APK lost.

### #2 — EXP-065 — Fix multi-DEX const-string bug (FIELD_PREFERRED_AUDIO_LANGUAGES leak resolved)

- **historical_claim:** EXP-065: fixed the multi-DEX const-string bug (FIELD_PREFERRED_AUDIO_LANGUAGES leak) — strings from a second DEX resolve correctly.
- **historical_evidence:** FR-002 (TESTED/E3): commits ff073348/b327292d/78c182f3; law re-verified by later multi-DEX campaigns.
- **tested_runtime_commit:** ff073348 (era)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** Telegram-era session APK (multi-DEX, 3+ DEX files).
- **runtime_proof:** multi-DEX const-string law is live in the current binary: forkgram (5-DEX) x2 byte-identical runs at abb57444 + battery semantic pass3-bridge stage ALL PASS at 9c3dc4d1.
- **viewtree_proof:** N/A (string-resolution law).
- **state_change_proof:** downstream field-preference text rendered correctly in-era.
- **screenshot_metrics:** N/A.
- **reproducibility:** law re-exercised every battery run; deterministic.
- **first_divergence:** N/A.
- **root_family:** DEX/multi-dex-strings
- **pixel_truth:** N/A (non-visual law).
- **final_classification:** **verified current**
- **evidence_refs:** FR-002; run/batch367_battery_v2.log; scripts/s117_tg_run.sh forkgram records
- **notes:** Law-level currency via current battery + forkgram determinism.

### #3 — EXP-066 — Multi-DEX semantic audit + OutlineTextContainerView text capture (Phone number label visible)

- **historical_claim:** EXP-066: multi-DEX semantic audit + OutlineTextContainerView text capture (phone number captured from real view text).
- **historical_evidence:** FR-003 (OBSERVED/E3): commit 1e1ec2b4; session evidence.
- **tested_runtime_commit:** 1e1ec2b4 (era)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** Telegram-era session APK.
- **runtime_proof:** session-era; text-capture capability since generalized (text laws battery 21/21 at 9c3dc4d1).
- **viewtree_proof:** session-era OutlineTextContainerView capture.
- **state_change_proof:** phone number text captured in-era.
- **screenshot_metrics:** session-era.
- **reproducibility:** not re-runnable at HEAD (artifact absent).
- **first_divergence:** N/A.
- **root_family:** TELEGRAM/exp-era
- **pixel_truth:** historical only.
- **final_classification:** **historical-only verification**
- **evidence_refs:** FR-003
- **notes:** Capability lineage continued by the current text pipeline.

### #4 — EXP-067 — Resource resolution + AXML parser + Drawable decoding (real WebP images in Login UI)

- **historical_claim:** EXP-067: resource resolution + AXML parser + drawable decoding produced REAL WebP images in the login flow.
- **historical_evidence:** FR-004 (OBSERVED/E3): commits 78c182f3 era; superseded by ARSC/AXML law waves (S126/S127 R-NEW-423).
- **tested_runtime_commit:** 78c182f3 (era)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** Telegram-era session APK.
- **runtime_proof:** superseded by stronger current laws: ARSC bag/style laws + AXML parse are battery-fenced (drawables 39/39 incl. AXML-driven vectors; G04 density oracle 11/11) at 9c3dc4d1.
- **viewtree_proof:** N/A.
- **state_change_proof:** N/A.
- **screenshot_metrics:** era WebP renders; superseded.
- **reproducibility:** current via battery law stages.
- **first_divergence:** N/A.
- **root_family:** RESOURCES/arsc-axml
- **pixel_truth:** current visual laws are fenced by band goldens + GATE-H.
- **final_classification:** **superseded**
- **evidence_refs:** FR-004; root_registry.json R-NEW-423 family; run/batch367_battery_v2.log
- **notes:** Superseded by a strictly stronger current implementation (registry law chain).

### #5 — EXP-068 — Generic View inheritance + Floating Next button (semantic superclass resolution)

- **historical_claim:** EXP-068: generic View inheritance + semantic superclass resolution produced the floating Next button.
- **historical_evidence:** FR-005 (OBSERVED/E3): session evidence.
- **tested_runtime_commit:** era session
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** Telegram-era session APK.
- **runtime_proof:** view-inheritance laws since formalized (G11 ctor law 37/37 incl. superclass walk, F-074 engine-level super-run 6/6 GREEN at 9c3dc4d1).
- **viewtree_proof:** session-era view tree with floating button.
- **state_change_proof:** button rendered + clickable (carried to #6).
- **screenshot_metrics:** session-era.
- **reproducibility:** laws current via battery; session not re-runnable.
- **first_divergence:** N/A.
- **root_family:** VIEW/inheritance
- **pixel_truth:** historical.
- **final_classification:** **historical-only verification**
- **evidence_refs:** FR-005; miniandroid/tests/g11_ctor_law_test.cpp
- **notes:** Law lineage current; session claim itself not re-runnable.

### #6 — EXP-069 — Generic text input + click dispatch: phone number injected + Next button clicked

- **historical_claim:** EXP-069: generic text input + click dispatch — phone number injected and Next clicked programmatically.
- **historical_evidence:** FR-006 (OBSERVED/E3): session evidence.
- **tested_runtime_commit:** era session
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** Telegram-era session APK.
- **runtime_proof:** input/dispatch laws current: G06 tap interaction golden (21 law checks) + 3-run tap determinism + tictactoe 9/9 DEX-dispatched clicks at 9c3dc4d1.
- **viewtree_proof:** session-era.
- **state_change_proof:** click state transitions proven in-era; current click laws battery-fenced.
- **screenshot_metrics:** session-era.
- **reproducibility:** laws re-fenced every battery run.
- **first_divergence:** N/A.
- **root_family:** INPUT/dispatch
- **pixel_truth:** historical.
- **final_classification:** **historical-only verification**
- **evidence_refs:** FR-006; run/batch367_battery_v2.log (G06, tictactoe)
- **notes:** Session superseded; laws current.

### #7 — EXP-071 — Telegram Login → SMS Code Page Transition (CHECKPOINT_M PROVEN)

- **historical_claim:** EXP-071: Telegram Login -> SMS Code page transition (CHECKPOINT_M PROVEN) end-to-end.
- **historical_evidence:** FR-007 (OBSERVED/E4): 15 checkpoints in .agent/state.md (historical banner); S27 REVIEW approved at HEAD 79874955.
- **tested_runtime_commit:** 79874955 (S27 review head)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** golden Telegram APK lost (K-26, docs/maintenance/NOT_DONE.md item 10); official download = 1.2MB stub (480263f8) BLOCKED-APK-ABSENT; forkgram_709208 = current carrier.
- **runtime_proof:** checkpoint session evidence in-era; current-era Telegram boundary is an ARTIFACT problem, not runtime: forkgram installs + runs deterministically (x2 byte-identical at abb57444).
- **viewtree_proof:** checkpoint-era view transitions.
- **state_change_proof:** login -> SMS transition captured in-era.
- **screenshot_metrics:** checkpoint-era captures (pre-F-NEW-233).
- **reproducibility:** not re-runnable at HEAD without the lost APK; forkgram runs reproducible.
- **first_divergence:** N/A.
- **root_family:** TELEGRAM/checkpoint-era
- **pixel_truth:** historical pixel claims predate the frame-truth law; no current visual VERIFIED claim is asserted from them.
- **final_classification:** **historical-only verification**
- **evidence_refs:** FR-007; .agent/state.md (HISTORICAL banner); docs/TELEGRAM_JOURNEY_S117_S119.md
- **notes:** Honest boundary: runtime capability proven historically; artifact acquisition remains blocked (consistent with #365 M3/M4).

### #8 — MiniAndroid campaign evidence — verified achievements (REUSE-FIRST campaign, 2026-09-05)

- **historical_claim:** MiniAndroid campaign evidence mega-issue — 55-comment verified-achievements thread (REUSE-FIRST campaign 2026-09-05).
- **historical_evidence:** FR-008 (SUPERSEDED/E3): superseded by canonical registries (S84+ one-record-per-title law).
- **tested_runtime_commit:** campaign era
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** mixed (per-comment).
- **runtime_proof:** superseded: canonical registries now the single source of truth (registry.json, root_registry.json, MICRO_GAP_REGISTRY.json, ARTIFACT_REGISTRY.json).
- **viewtree_proof:** superseded.
- **state_change_proof:** superseded.
- **screenshot_metrics:** superseded.
- **reproducibility:** via registries + battery.
- **first_divergence:** N/A.
- **root_family:** GOVERNANCE/registries
- **pixel_truth:** per-record in registries.
- **final_classification:** **superseded**
- **evidence_refs:** FR-008; docs/evidence/canonical/registry.json
- **notes:** Clean supersession — the canonical-registry law replaced the evidence thread.

### #10 — [EXEC] HelloWorld — APK Execution & Visual Proof

- **historical_claim:** [EXEC] HelloWorld: APK execution + visual proof (canonical L6 fixture).
- **historical_evidence:** FR-010 (VERIFIED/E5): battery + golden era records.
- **tested_runtime_commit:** golden era
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** org.miniandroid.helloworld fixture (rebuilt on demand; canonical artifact authority).
- **runtime_proof:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops; Snake Deluxe: 1203/0.72/262; MiniCraft: 2416/0.64/735; HelloWorld canonical L6 sha 83720c1028f832d0) — run/user_goldens/user_goldens.json
- **viewtree_proof:** helloworld view tree with app text (battery hello golden 18 checks).
- **state_change_proof:** text render deterministic.
- **screenshot_metrics:** canonical artifact sha 83720c1028f832d0 (L6).
- **reproducibility:** re-verified at 9c3dc4d1 (user golden gate).
- **first_divergence:** N/A.
- **root_family:** EXEC/hello
- **pixel_truth:** PASS REAL_APP_CONTENT per F-NEW-233 gate.
- **final_classification:** **verified current**
- **evidence_refs:** FR-010; run/user_goldens/user_goldens.json; scripts/user_golden_gate.py
- **notes:** User-designated golden test.

### #11 — [EXEC] TicTacToe — APK Execution & Gameplay Proof

- **historical_claim:** [EXEC] TicTacToe: APK execution + gameplay proof (9 clicks, marks render, determinism).
- **historical_evidence:** FR-011 (OBSERVED/E3): early session proof; canonical registry OBSERVED; the SS29 tictactoe_golden validator is the canonical fencing.
- **tested_runtime_commit:** golden era
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** tictactoe fixture APK, SHA256 9d1c2954c675813cb5f890190f765bcca94662e76f9ceb7b90ce5eaa797fe858 (battery build).
- **runtime_proof:** tictactoe_golden (SS29) stage PASS at 9c3dc4d1 inside run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates: 9/9 clicks DEX-dispatched, marks in cells with glyph ink, frames 7/8/9 frozen, run A/B 10-frame byte-identical (895fac7581b9...).
- **viewtree_proof:** state machine validated from real DEX listeners (SS29 section [3]).
- **state_change_proof:** click 1..9 state transitions asserted by SS29.
- **screenshot_metrics:** frame SHAs asserted; pixel discriminators correct.
- **reproducibility:** deterministic replay verified (run B).
- **first_divergence:** N/A.
- **root_family:** EXEC/tictactoe
- **pixel_truth:** game-content pixel discriminators asserted; run exits via the documented F-NEW-233 PARTIAL verdict (laws hold; golden mandatory).
- **final_classification:** **verified current**
- **evidence_refs:** FR-011; miniandroid/tests/fixtures/tictactoe_golden/validate_tictactoe_golden.sh; run/batch367_battery_v2.log
- **notes:** SS29 validator re-baselined this campaign for the F-NEW-233 rc interplay (documented in-script; law checks unchanged).

### #12 — [EXEC] ConnectFour — APK Execution & Gameplay Proof

- **historical_claim:** [EXEC] ConnectFour: APK execution + gameplay proof.
- **historical_evidence:** FR-012 (OBSERVED/E3): early session proof only.
- **tested_runtime_commit:** early era
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** early-session APK; not pinned in current canonical APK set.
- **runtime_proof:** not re-run at current HEAD; not part of the battery.
- **viewtree_proof:** session-era only.
- **state_change_proof:** session-era.
- **screenshot_metrics:** session-era.
- **reproducibility:** not re-runnable at HEAD (artifact not in canonical set).
- **first_divergence:** N/A.
- **root_family:** EXEC/connectfour
- **pixel_truth:** no current visual claim.
- **final_classification:** **historical-only verification**
- **evidence_refs:** FR-012
- **notes:** Gap: APK not in the current canonical set; re-adoption would require artifact re-acquisition + 3-run fencing.

### #13 — [EXEC] AndroidGameSnake — Autonomous Gameplay Proof

- **historical_claim:** [EXEC] AndroidGameSnake (zhangman.github.snake): autonomous gameplay proof (88 moves/22 turns/1 food; 4-run sweep).
- **historical_evidence:** FR-013 (VERIFIED/E5): S73/S74 dossiers + canonical GIF + 4-run sweep at d7280a15; canonical dossier docs/compatibility/apps/androidgamesnake.json.
- **tested_runtime_commit:** d7280a15 (S74 checkpoint)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** upload/s72_w4_apks/snake_v1.0_vc1.apk (sha16 54cf48a9, pinned in dossier).
- **runtime_proof:** — fresh execution at current HEAD via evidence/batch367_rerun/zhangman.github.snake/.
- **viewtree_proof:** dossier: ConstraintLayout root + SnakePanelView EXACT 1080x780 (20x15dp x 2.625).
- **state_change_proof:** frame delta TRUE at current HEAD (game animates); historical autonomous loop 88 moves.
- **screenshot_metrics:** fresh run colors=41 (flat game palette); canonical GIF in docs/evidence/canonical/.
- **reproducibility:** 4-run sweep (S73) + fresh HEAD run; deterministic face recorded.
- **first_divergence:** restart-after-game-over honestly NOT observed (dossier status_note) — open interaction gap.
- **root_family:** EXEC/androidgamesnake
- **pixel_truth:** real game content (board + snake) rendered; autoplay GIF canonical.
- **final_classification:** **verified current**
- **evidence_refs:** FR-013; docs/compatibility/apps/androidgamesnake.json; evidence/batch367_rerun/zhangman.github.snake/record.json
- **notes:** Fresh current-HEAD execution closes the currency question; restart gap remains honestly open.

### #15 — [EXEC] Unote — Runtime/UI Completion

- **historical_claim:** [EXEC] Unote: runtime/UI completion (notes app renders + interacts).
- **historical_evidence:** FR-015 (VERIFIED/E5): golden 4f1a9e4e8f64fae8 x3 re-verified at HEAD 2026-10-03.
- **tested_runtime_commit:** current line
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** app.varlorg.unote_30.apk (upload/canonical_apks; installed store run/audit/regression/store_unote).
- **runtime_proof:** working_vs_failing_probe.sh @ 9c3dc4d1: 5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — DETERMINISM gate only per F-NEW-233 (chess/dooz frames 100% white; never visual success); uninstall store keeps byte-identical app identity.
- **viewtree_proof:** notes list view tree renders (golden era records).
- **state_change_proof:** editor interactions in golden-era session records.
- **screenshot_metrics:** golden sha da7301.../4f1a9e4e family recorded.
- **reproducibility:** x3 byte-identical at 9c3dc4d1.
- **first_divergence:** N/A.
- **root_family:** EXEC/unote
- **pixel_truth:** REAL_APP_CONTENT era-verified visual golden.
- **final_classification:** **verified current**
- **evidence_refs:** FR-015; run/user_goldens/; scripts/working_vs_failing_probe.sh
- **notes:** Also serves as an unrelated control in later fan-outs (diff366 zero drift).

### #17 — [EXEC] GMDice — APK Execution & Visual Proof

- **historical_claim:** [EXEC] GMDice: APK execution + visual proof (AXML inflation + OCR text D05).
- **historical_evidence:** FR-017 (VERIFIED/E4): AXML + OCR session records.
- **tested_runtime_commit:** D05 era
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** de.duenndns.gmdice_8.apk (upload/canonical_apks; battery corpus set).
- **runtime_proof:** battery corpus run stage PASS at 9c3dc4d1; fresh re-run at HEAD 9c3dc4d1: rc=0, status=SUCCESS ✅, unique_colors=892, frame_delta=False.
- **viewtree_proof:** dice UI inflated from real AXML.
- **state_change_proof:** tap registered (no visual face change expected on static screen; frame delta False recorded honestly).
- **screenshot_metrics:** fresh run colors=892 (real content).
- **reproducibility:** battery stage deterministic; fresh HEAD run SUCCESS.
- **first_divergence:** N/A.
- **root_family:** EXEC/gmdice
- **pixel_truth:** real dice UI pixels (892 colors) — passes visual sanity; no visual-VERIFIED claim beyond metrics.
- **final_classification:** **verified current**
- **evidence_refs:** FR-017; run/batch367_battery_v2.log (corpus run gmdice); evidence/batch367_rerun/de.duenndns.gmdice/record.json
- **notes:** OCR text proof is era evidence; current evidence = render + battery.

### #18 — [EXEC] MicroTimer — APK Execution & Visual Proof

- **historical_claim:** [EXEC] MicroTimer: APK execution + visual proof.
- **historical_evidence:** FR-018 (VERIFIED/E5): golden da73010a37dd0189 x3 re-verified at HEAD 2026-10-03.
- **tested_runtime_commit:** current line
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** dubrowgn.microtimer_8.apk (miniandroid/download/exp076_corpus; installed store).
- **runtime_proof:** working_vs_failing_probe.sh @ 9c3dc4d1: 5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — DETERMINISM gate only per F-NEW-233 (chess/dooz frames 100% white; never visual success); M3 F-012 persistence+fresh-state determinism golden PASS at 9c3dc4d1 (alarm row persists across runs; frames byte-deterministic across independent pairs).
- **viewtree_proof:** timer UI tree rendered (golden era).
- **state_change_proof:** DB row count 0->1->2 across runs (F-012 machine proof).
- **screenshot_metrics:** golden da73010a37dd0189.
- **reproducibility:** x3 byte-identical + F-012 two-pair determinism.
- **first_divergence:** N/A.
- **root_family:** EXEC/microtimer
- **pixel_truth:** REAL_APP_CONTENT visual golden.
- **final_classification:** **verified current**
- **evidence_refs:** FR-018; run/batch367_battery_v2.log (M3 F-012); run/user_goldens/
- **notes:** F-012 stage helper re-baselined to the evolved FHS store layout (data/data/<pkg>) this campaign — documented in-script.

### #68 — [GAME-044] com.smorgasbork.hotdeath — compatibility report

- **historical_claim:** [GAME-044] com.smorgasbork.hotdeath compatibility report — full-load + render evidence.
- **historical_evidence:** FR-068 (VERIFIED/E4): canonical game registry record; S107 audit 3-run VERIFIED_3RUN (634 unique colors, sha-stable 7c811bffb9a7c590, PARTIAL SUCCESS rc per F-NEW-233-era honesty).
- **tested_runtime_commit:** S107 audit head (rebuilt from c0b7f501)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.smorgasbork.hotdeath 1.0.11 (vc 11) per S107 three_run_summary.json.
- **runtime_proof:** S107 x3 runs recorded; NOT re-run at current HEAD (APK not in current canonical set).
- **viewtree_proof:** S107 run records.
- **state_change_proof:** render evidence; interaction not claimed.
- **screenshot_metrics:** 634 colors / nonbg 0.108 / sha-stable x3.
- **reproducibility:** 3-run proven at S107 audit head.
- **first_divergence:** N/A at current HEAD (not re-run).
- **root_family:** GAME/report
- **pixel_truth:** 634-color content is real render; visual-VERIFIED not asserted beyond the registry record.
- **final_classification:** **historical-only verification**
- **evidence_refs:** FR-068; evidence/audit_s107/three_run/com.smorgasbork.hotdeath_run1..3; docs/evidence/canonical/com.smorgasbork.hotdeath.gif
- **notes:** Gap: current-HEAD re-run pending APK re-acquisition; runtime itself regression-free at HEAD (battery 121/121).

### #81 — [GAME-057] org.bobstuff.bobball — compatibility report

- **historical_claim:** [GAME-057] org.bobstuff.bobball compatibility report.
- **historical_evidence:** FR-081 (VERIFIED/E4): canonical record; S107 3-run VERIFIED_3RUN (476 colors, sha-stable).
- **tested_runtime_commit:** S107 audit head
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** org.bobstuff.bobball per S107 three_run_summary.json.
- **runtime_proof:** S107 x3 runs; not re-run at current HEAD.
- **viewtree_proof:** S107 records.
- **state_change_proof:** render evidence.
- **screenshot_metrics:** 476 colors, sha-stable x3.
- **reproducibility:** 3-run at S107 head.
- **first_divergence:** N/A.
- **root_family:** GAME/report
- **pixel_truth:** real render; no beyond-registry claim.
- **final_classification:** **historical-only verification**
- **evidence_refs:** FR-081; evidence/audit_s107/three_run/org.bobstuff.bobball_run1..3; docs/evidence/canonical/org.bobstuff.bobball.gif
- **notes:** Gap: current-HEAD re-run pending artifact.

### #121 — [GAME-097] com.dozingcatsoftware.bouncy — compatibility report

- **historical_claim:** [GAME-097] com.dozingcatsoftware.bouncy compatibility report.
- **historical_evidence:** FR-121 (VERIFIED/E4): canonical record; S107 3-run VERIFIED_3RUN (494 colors).
- **tested_runtime_commit:** S107 audit head; re-confirmed at 9c3dc4d1
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** upload/canonical_apks/bouncy.apk.
- **runtime_proof:** diff366 ROOT-A fan-out at edecae3e: byte-identical zero drift; fresh re-run at HEAD 9c3dc4d1: rc=1, status=PARTIAL SUCCESS ⚠️, unique_colors=413, frame_delta=False (rc=1 is the documented F-NEW-233 PARTIAL verdict, laws hold).
- **viewtree_proof:** diff366 fan-out records (evidence/diff366/).
- **state_change_proof:** tap registered in wave run (physics may pre-move; delta recorded honestly False on 3-frame window).
- **screenshot_metrics:** fresh run colors=413 (S107: 494; palette stable family).
- **reproducibility:** S107 x3 + current-HEAD runs.
- **first_divergence:** N/A.
- **root_family:** GAME/report
- **pixel_truth:** real render both eras.
- **final_classification:** **verified current**
- **evidence_refs:** FR-121; evidence/diff366/; evidence/batch367_rerun/com.dozingcatsoftware.bouncy/record.json
- **notes:** Bouncy doubles as an unrelated-app regression control (ROOT-A fan-out).

### #166 — [APP-042] org.ucam.ssb22.pinyinfdroid — compatibility report

- **historical_claim:** [APP-042] org.ucam.ssb22.pinyinfdroid compatibility report.
- **historical_evidence:** S107 closure comment: fresh run at HEAD 1818a325 + AUDIT RESULT 'closure re-verified VERIFIED 3RUN' (rebuilt from c0b7f501); S107 three_run_summary VERIFIED_3RUN (208 colors, sha-stable e03921ecbff1246d). The FR-166 PENDING/E0 row is STALE relative to this evidence.
- **tested_runtime_commit:** 1818a325 (S107) / c0b7f501 rebuild
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** org.ucam.ssb22.pinyinfdroid 2.12.74 (vc 109) per S107 records.
- **runtime_proof:** x3 runs at S107 audit; not re-run at current HEAD (APK not in current canonical set).
- **viewtree_proof:** S107 records.
- **state_change_proof:** render evidence.
- **screenshot_metrics:** 208 colors / nonbg 0.015 (sparse UI) / sha-stable x3.
- **reproducibility:** 3-run at S107 head.
- **first_divergence:** N/A.
- **root_family:** APP/report
- **pixel_truth:** sparse-content render honestly recorded (nonbg 0.015) — not a visual-success claim.
- **final_classification:** **historical-only verification**
- **evidence_refs:** evidence/audit_s107/three_run/org.ucam.ssb22.pinyinfdroid_run1..3; evidence/s107_games/org.ucam.ssb22.pinyinfdroid_run1..2; issue #166 closure comments
- **notes:** FR ledger row corrected by this audit (PENDING -> evidence-backed historical verification).

### #234 — [MG-051] Font fallback selection — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-051] (text/font): Font fallback selection — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: CJK face never loaded — now loaded; notdef==0 via fallback chain
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-051] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery s98 text laws T1/T2 (21/21)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-051; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-234=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #235 — [MG-073] ellipsize — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-073] (text/font): ellipsize — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: ellipsize absent — IMPLEMENTED END/START/MIDDLE + maxLines=1 no-wrap
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-073] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery s98 text laws T3-T7,T14
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-073; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-235=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #236 — [MG-080] Unicode combining marks — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-080] (text/font): Unicode combining marks — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced combining-mark shape law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-080] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T8
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-080; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-236=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #237 — [MG-081] RTL basic shaping — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-081] (text/font): RTL basic shaping — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced RTL first-strong law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-081] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T9
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-081; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-237=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #238 — [MG-082] Arabic joining — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-082] (text/font): Arabic joining — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced Arabic joining advance law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-082] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T10
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-082; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-238=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #239 — [MG-083] emoji fallback — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-083] (text/font): emoji fallback — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: bogus DejaVu emoji glyph swallowed slot — emoji-presentation claim law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-083] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T11
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-083; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-239=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #240 — [MG-084] surrogate pairs — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-084] (text/font): surrogate pairs — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced surrogate single-cluster law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-084] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T12
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-084; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-240=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #241 — [MG-085] UTF-8/UTF-16 boundary — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-085] (text/font): UTF-8/UTF-16 boundary — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: PHANTOM-NUL fix: hb buffer fed N+1 units — every string shaped with garbage trailing cluster
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-085] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **tested_runtime_commit:** 4ac6c542
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T13
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-085; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-241=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #242 — [MG-115] requestLayout propagation — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-115] (layout/geometry): requestLayout propagation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-115] STATUS=CLOSED; EVIDENCE: battery stage 's106_layout_net_law_test L1/L2' (FIXED View.requestLayout() bridge swallowing the call as no-op — now raises the R-NEW-302 layout_dirty traversal flag (AOSP PFLAG_FORCE_LAYOUT law); setLayoutParams path re-verified); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 layout/net laws (expect 11) PASS 11/11 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-115; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-242=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #243 — [MG-123] scroll offset — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-123] (layout/geometry): scroll offset — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: scrollTo/scrollBy/getScrollX/Y absent — IMPLEMENTED + draw-walk content delta
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-123] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **tested_runtime_commit:** 62ef579f
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery s98 scroll/transform T1-T3,T8 (13/13)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-123; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-243=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #244 — [MG-124] translationX — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-124] (layout/geometry): translationX — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: translationX property + walk delta law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-124] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **tested_runtime_commit:** 62ef579f
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T4,T8
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-124; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-244=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #245 — [MG-125] translationY — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-125] (layout/geometry): translationY — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: translationY property + walk delta law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-125] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **tested_runtime_commit:** 62ef579f
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T4,T8
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-125; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-245=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #246 — [MG-126] scaleX — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-126] (layout/geometry): scaleX — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: scaleX property law (state+getters; matrix render = recorded frontier)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-126] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **tested_runtime_commit:** 62ef579f
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T5
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-126; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-246=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #247 — [MG-127] scaleY — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-127] (layout/geometry): scaleY — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: scaleY property law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-127] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **tested_runtime_commit:** 62ef579f
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T5
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-127; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-247=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #248 — [MG-128] rotation — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-128] (layout/geometry): rotation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: rotation property law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-128] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **tested_runtime_commit:** 62ef579f
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T6
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-128; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-248=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #249 — [MG-129] pivot — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-129] (layout/geometry): pivot — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: pivot property law
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-129] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **tested_runtime_commit:** 62ef579f
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** battery T7
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/layout/geometry
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-129; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-249=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

### #250 — [MG-171] SharedPreferences default file — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-171] (storage/state): SharedPreferences default file — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-171] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: default-file law (app-dir root) — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-171; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-250=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #251 — [MG-172] custom file — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-172] (storage/state): custom file — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-172] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: namespace isolation — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-172; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-251=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #334 — [GAMES-1] Full-load 5-10 games end-to-end (launch + render + interaction evidence)

- **historical_claim:** [GAMES-1] Full-load 5-10 games end-to-end (launch + render + interaction evidence).
- **historical_evidence:** FR-334 (VERIFIED/E5): docs/evidence/s98/games_full_load.json; closure comment 9/10 FULL_LOAD_PASS + 1 honest LOAD_ISSUE.
- **tested_runtime_commit:** S98 wave
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** per-title pinned in games_full_load.json (in-house builds + corpus APKs).
- **runtime_proof:** wave evidence + current-HEAD re-confirmation of the flagged titles: snake-deluxe (golden gate), 2048 (golden gate), tictactoedeluxe + snakeneon + androidgamesnake ( etc.).
- **viewtree_proof:** per-run frame evidence under run/s98_*.
- **state_change_proof:** interaction column in games_full_load.json (tap->SHA delta).
- **screenshot_metrics:** ink ratios recorded per title at S98.
- **reproducibility:** current subset re-run at HEAD (this campaign); full wave re-run possible via scripts/s98.
- **first_divergence:** 1 honest LOAD_ISSUE title recorded at S98 (never masked).
- **root_family:** GAMES/wave
- **pixel_truth:** ink metrics + interaction deltas; no white frame claimed as success.
- **final_classification:** **verified current**
- **evidence_refs:** FR-334; docs/evidence/s98/games_full_load.json; evidence/batch367_rerun/wave_summary.json
- **notes:** The 1 honest LOAD_ISSUE remains recorded (honesty law).

### #335 — [GAMES-2] Autonomous Snake Deluxe play (self-play, no game-memory cheating)

- **historical_claim:** [GAMES-2] Autonomous Snake Deluxe play (self-play, no game-memory cheating).
- **historical_evidence:** FR-335 (VERIFIED/E5): S80 vision-based driver re-run on S98 binary — 7 captures, final continuous 120-frame run with 56-frame SHA-pinned prefix; snake ate food and grew (C1/C3/C4/C7 laws held); autoplay GIF canonical.
- **tested_runtime_commit:** S98 binary
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.miniandroid.snakedeluxe (upload/s80_games/build_sd; sha 551eca798f88c1bb).
- **runtime_proof:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (Snake Deluxe leg).
- **viewtree_proof:** game view renders (262 draw ops).
- **state_change_proof:** food-eaten + growth state changes in the S98 autonomous run.
- **screenshot_metrics:** screenshot sha 34a712689ce66e58; 1203 colors.
- **reproducibility:** determinism-gated (user golden gate); driver re-runnable.
- **first_divergence:** N/A.
- **root_family:** GAMES/autoplay
- **pixel_truth:** REAL_APP_CONTENT; autonomous-play proof is driver-based (no game-memory cheat) per S80 method.
- **final_classification:** **verified current**
- **evidence_refs:** FR-335; docs/evidence/s98/ (autoplay GIF); run/user_goldens/user_goldens.json
- **notes:** Vision-based driver method note kept from closure comment.

### #336 — [GAMES-3] House-building autonomous play (Minicraft)

- **historical_claim:** [GAMES-3] House-building autonomous play (Minicraft): real taps (dpad walk + BLOCK cycle + PLACE/DIG + DEMO); cottage built.
- **historical_evidence:** FR-336 (OBSERVED/E4): S98 driver — cursor moved (269,712)->(577,1000); materials placed brick 0->68432px, plank 0->49392px, roof 0->113190px; digs observed; minicraft_autoplay.gif canonical.
- **tested_runtime_commit:** S98 binary
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.miniandroid.minicraft (s86_games build).
- **runtime_proof:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (MiniCraft leg: REAL_APP_CONTENT, 735 draw ops).
- **viewtree_proof:** game canvas renders.
- **state_change_proof:** material-placement pixel deltas are the recorded state-change proof (S98).
- **screenshot_metrics:** screenshot sha 46d3de34-family recorded in user_goldens.json (2416 colors).
- **reproducibility:** app re-verifies at HEAD; driver re-runnable (scripts/s98/s98_minicraft_autoplay.py).
- **first_divergence:** full house-building LOOP end-to-end automation not claimed beyond the S98 material deltas (honest FR OBSERVED).
- **root_family:** GAMES/autoplay
- **pixel_truth:** REAL_APP_CONTENT; autoplay evidence = pixel-delta based.
- **final_classification:** **verified current**
- **evidence_refs:** FR-336; docs/evidence/s98/minicraft_autoplay.gif; run/user_goldens/user_goldens.json
- **notes:** Currency: app render re-verified at HEAD; the autonomous house-build proof remains the S98 driver record (scope honestly stated).

### #337 — [GAMES-4] NEW snake variant — build, load, autonomous play

- **historical_claim:** [GAMES-4] NEW snake variant (snake-neon) — build, load, autonomous play; mechanically NEW (wrap-around walls + obstacles + speed HUD).
- **historical_evidence:** FR-337 (OBSERVED/E4): S98 build (9156 teal px + 1252 food px, 0 errors) + snakeneon_autoplay.gif; FULL_LOAD_PASS row in games_full_load.json.
- **tested_runtime_commit:** S98 binary
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.miniandroid.snakeneon (upload/s98_games/build_snakeneon/snakeneon_v1.0_vc1.apk).
- **runtime_proof:** fresh re-run at HEAD 9c3dc4d1: rc=0, status=SUCCESS ✅, unique_colors=884, frame_delta=True — frame delta TRUE (game animates).
- **viewtree_proof:** game HUD + board render.
- **state_change_proof:** frame delta TRUE at HEAD; autonomous-play GIF at S98.
- **screenshot_metrics:** fresh run colors=884.
- **reproducibility:** fresh HEAD run + S98 GIF.
- **first_divergence:** N/A.
- **root_family:** GAMES/new-variant
- **pixel_truth:** real game content both eras.
- **final_classification:** **verified current**
- **evidence_refs:** FR-337; docs/evidence/s98/snakeneon_autoplay.gif; evidence/batch367_rerun/com.miniandroid.snakeneon/record.json
- **notes:** Fresh current-HEAD execution upgrades the OBSERVED row with currency evidence.

### #338 — [GAMES-5] Autonomous 2048 play

- **historical_claim:** [GAMES-5] Autonomous 2048 play (GIF + score-to-200 state change).
- **historical_evidence:** FR-338 (VERIFIED/E5): g2048 autoplay GIF + score state change.
- **tested_runtime_commit:** S-era autoplay; golden current
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.miniandroid.g2048 (upload/s80_games/g2048).
- **runtime_proof:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (2048 leg: REAL_APP_CONTENT, 34 draw ops).
- **viewtree_proof:** 2048 board renders.
- **state_change_proof:** score progression to 200 recorded in the autoplay session.
- **screenshot_metrics:** screenshot sha 7ad9a8bdefba539b; 535 colors.
- **reproducibility:** determinism-gated (user golden gate).
- **first_divergence:** N/A.
- **root_family:** GAMES/autoplay
- **pixel_truth:** REAL_APP_CONTENT.
- **final_classification:** **verified current**
- **evidence_refs:** FR-338; run/user_goldens/user_goldens.json; docs/evidence/canonical/
- **notes:** User-designated golden test.

### #340 — [GAMES-7] Autonomous TicTacToe Deluxe play

- **historical_claim:** [GAMES-7] Autonomous TicTacToe Deluxe play (GIF + session record).
- **historical_evidence:** FR-340 (VERIFIED/E4): tictactoe deluxe GIF + session record; canonical GIF docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif.
- **tested_runtime_commit:** S-era; fresh at 9c3dc4d1
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.miniandroid.tictactoedeluxe (rebuilt via scripts/s83_build_tictactoe.sh — canonical aapt2/ECJ/D8 recipe).
- **runtime_proof:** — tap interaction produced frame delta TRUE.
- **viewtree_proof:** board grid renders (2022 colors).
- **state_change_proof:** frame delta TRUE on tap at HEAD.
- **screenshot_metrics:** fresh run colors=2022.
- **reproducibility:** build recipe deterministic; fresh HEAD run SUCCESS.
- **first_divergence:** N/A.
- **root_family:** GAMES/autoplay
- **pixel_truth:** real board content.
- **final_classification:** **verified current**
- **evidence_refs:** FR-340; docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif; evidence/batch367_rerun/com.miniandroid.tictactoedeluxe/record.json
- **notes:** Registry graphics verdict record exists (registry/graphics_verdicts/).

### #341 — [GAMES-8] Wave evidence package + gh-pages gameplay GIFs

- **historical_claim:** [GAMES-8] Wave evidence package + gh-pages gameplay GIFs (docs/evidence/s98/ + EXECUTED_GIFS.md).
- **historical_evidence:** FR-341 (VERIFIED/E4): closure comment lists games_full_load.json + minicraft_autoplay.gif + snakeneon_autoplay.gif + per-run frame evidence.
- **tested_runtime_commit:** S98 wave (artifact set)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (evidence-package claim).
- **runtime_proof:** artifact existence verified at 9c3dc4d1: docs/evidence/s98/games_full_load.json, minicraft_autoplay.gif, snakeneon_autoplay.gif present; docs/EXECUTED_GIFS.md + canonical GIF set present; docs/verified_executed_games.json (26 games) present.
- **viewtree_proof:** N/A.
- **state_change_proof:** N/A.
- **screenshot_metrics:** N/A (package claim).
- **reproducibility:** artifact checks re-runnable.
- **first_divergence:** N/A.
- **root_family:** GAMES/evidence-package
- **pixel_truth:** N/A.
- **final_classification:** **verified current**
- **evidence_refs:** FR-341; docs/EXECUTED_GIFS.md; docs/evidence/s98/; docs/verified_executed_games.json
- **notes:** Existence + integrity of the evidence package is the claim; verified.

### #342 — [F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attr resolution gap for non-AppCompat-ancestor themes (mykanji family)

- **historical_claim:** [F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attribute resolution chain killed apps on deep MaterialComponents style chains.
- **historical_evidence:** root_registry.json F-NEW-165 = ROOT-CAUSED-FIXED; S100 closure comment: ARSC parent-chain max_parent_hops=8 bound MyKanji's ~12-14-hop MaterialComponents chain -> fix bound/extended the hop law.
- **tested_runtime_commit:** S100 wave
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** MyKanji face (com...mykanji era APK); family-generic fix.
- **runtime_proof:** ARSC style law current: M3 ARSC style law 17/17 + M3 style geometry golden (6 checks) + density-matrix oracle 11/11 at 9c3dc4d1; before/after: droidify DEFAULT_BACKGROUND_ONLY -> REAL content (registry before/after).
- **viewtree_proof:** registry before/after records.
- **state_change_proof:** theme resolution now completes; apps inflate past createSubDecor.
- **screenshot_metrics:** registry before/after face metrics.
- **reproducibility:** battery ARSC stages re-run every battery.
- **first_divergence:** next divergence moved downstream (registry notes).
- **root_family:** RESOURCES/theme-gate
- **pixel_truth:** after-face REAL content per registry.
- **final_classification:** **verified current**
- **evidence_refs:** root_registry.json#F-NEW-165; run/batch367_battery_v2.log (ARSC stages)
- **notes:** Generic theme-chain law (no package conditionals).

### #345 — [F-NEW-168] crash-on-launch family — rc=1 NPE chains (raumballer/tictactoe-classic) + dooz rc=-11 process-death

- **historical_claim:** [F-NEW-168] crash-on-launch family: dooz rc=-11 SIGSEGV (process death) + raumballer/tictactoe-classic rc=1 NPE chains — DoD: no-signal law + named next frontiers.
- **historical_evidence:** root_registry.json F-NEW-168 = OBSERVED-FAIL (WhatsApp-chain faces honestly open); S100 closure comment: dooz rc=-11 ROOT-CAUSED + FIXED (LayoutInflater::measure_raw child_sizes built before real-DEX onMeasure hook materialized views).
- **tested_runtime_commit:** S100 wave; current 9c3dc4d1
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** io.github.yamin8000.dooz_23 (installed store run/audit/regression/store_dooz).
- **runtime_proof:** dooz determinism x3 byte-identical at 9c3dc4d1 (5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — DETERMINISM gate only per F-NEW-233 (chess/dooz frames 100% white); graceful rc; no signal — no-signal law holds; crash_forensics last-op ring (S100 SS3) in binary.
- **viewtree_proof:** dooz view tree composes (ComposeView materialization documented separately).
- **state_change_proof:** no process death across 3 runs.
- **screenshot_metrics:** dooz face = 100% white (0 app draw ops) — DETERMINISM anchor only.
- **reproducibility:** x3 every regression run.
- **first_divergence:** raumballer / tictactoe-classic NPE chains remain the named next frontier (honestly open; registry OBSERVED-FAIL).
- **root_family:** CRASH/no-signal
- **pixel_truth:** BYTE-STABLE != PIXEL-TRUTH: dooz white frames anchor determinism only — never visual success.
- **final_classification:** **verified current**
- **evidence_refs:** root_registry.json#F-NEW-168; scripts/working_vs_failing_probe.sh; run/batch367_battery_v2.log
- **notes:** Classification applies to the issue's DoD (no-signal + named frontiers); the family's remaining faces stay honestly OBSERVED-FAIL.

### #347 — [F-NEW-169] dooz compose-navigation NPE chain — 3 roots after rc=-11 fix

- **historical_claim:** [F-NEW-169] dooz compose-navigation NPE chain — 3 named roots + 2 cascades after the rc=-11 fix.
- **historical_evidence:** closure comment at HEAD 176710b1: all 3 named roots + 2 cascades executed with commits (Handler.postAtFrontOfQueue null-receiver law; Object.getClass null via Field.get reflection family; View.getWidth null).
- **tested_runtime_commit:** 176710b1 (closure head)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** io.github.yamin8000.dooz_23_toplevel.apk / dooz_23 (installed store).
- **runtime_proof:** dooz runs gracefully x3 byte-identical at 9c3dc4d1; 41/41-frame runs recorded at closure.
- **viewtree_proof:** compose tree materialization documented in the ROOT-D 4-way separation (not merged into a single 'Compose root').
- **state_change_proof:** no uncaught NPE chains at onCreate after fixes.
- **screenshot_metrics:** dooz frames 100% white (0 app draw ops) — composition materializes but does not draw (ROOT-D case 2).
- **reproducibility:** x3 determinism every regression run.
- **first_divergence:** dooz's remaining divergence = rendering backend (Compose no-draw frontier; ROOT-D case family) — honestly documented, NOT closed.
- **root_family:** COMPOSE/navigation-NPE
- **pixel_truth:** BYTE-STABLE != PIXEL-TRUTH: dooz is a determinism anchor; no visual-success claim.
- **final_classification:** **verified current**
- **evidence_refs:** root_registry.json#F-NEW-169; scripts/working_vs_failing_probe.sh; docs/DIFFERENTIAL_WORKING_VS_WHITE.md
- **notes:** Crash-law closure is current; the visual frontier remains open by design of the honest 4-way Compose separation.

### #349 — [S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked on null registry receiver inside ComponentActivity.<init>

- **historical_claim:** [S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked on R8-merged MatcherMatchResult null receiver.
- **historical_evidence:** closure comment at HEAD 176710b1 (S104 FIX-005 / S106 re-verification) to L5; root analysis: R8 horizontal class merging; solitaire_71 face also root-caused via F-NEW-160 (DEX instance-field identity law).
- **tested_runtime_commit:** 176710b1; field-identity law current at 9c3dc4d1
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.vayunmathur.games.solitaire.
- **runtime_proof:** fix laws live in the current binary (F-NEW-160 in root_registry; solitaire reaches onStart, 3-run 6588621c4a0c4182 frontier state recorded); battery 121/121 at 9c3dc4d1 with zero drift on unrelated goldens.
- **viewtree_proof:** S134-era sol_v13.log records (delegate constructed; AppCompat theme machinery ran).
- **state_change_proof:** chain advanced past SavedStateRegistry attach (per closure evidence).
- **screenshot_metrics:** 3-run face SHA 6588621c4a0c4182 (frontier state).
- **reproducibility:** law current; solitaire face re-runnable.
- **first_divergence:** next faces honestly recorded (SharedPreferences.getBoolean null at c/m.aR, FragmentManager family) — open frontier.
- **root_family:** R8/horizontal-merge
- **pixel_truth:** no visual claim asserted.
- **final_classification:** **verified current**
- **evidence_refs:** issue #349 closure comment; root_registry.json#F-NEW-160; run/s134/ records
- **notes:** REGISTRY GAP (recorded, not masked): literal id 'S102-A' is absent from root_registry.json — its laws are covered under F-NEW-160 family; cross-reference recorded by this audit.

### #350 — [S102-B] compose frontier: 'CompositionLocal LocalDensity not present' — WindowRecomposer host wiring (solitaire, the real compose-runtime root)

- **historical_claim:** [S102-B] compose frontier: 'CompositionLocal LocalDensity not present' at WindowRecomposer host creation killed composition startup.
- **historical_evidence:** closure comment at HEAD 176710b1: named blocker no longer occurs (windowRecomposer host laws landed).
- **tested_runtime_commit:** 176710b1; current 9c3dc4d1
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** com.vayunmathur.games.solitaire (+ eu.veldsoft.no.thanks family).
- **runtime_proof:** LocalDensity ISE eliminated (closure evidence); Compose pipeline laws current: F-NEW-179 canonical pump + F-NEW-201 one-stable-content-object (registry IMPLEMENTED); battery compose-adjacent stages pass at 9c3dc4d1.
- **viewtree_proof:** ROOT-D 4-way separation: (1) ComposeView materialization, (2) composition-without-draw, (3) recomposer/state machinery, (4) rendering backend — documented separately, NOT merged.
- **state_change_proof:** composition starts (was: ISE before any composition).
- **screenshot_metrics:** compose faces remain non-drawing (ROOT-D case 2) — honest.
- **reproducibility:** gates re-run every regression.
- **first_divergence:** Compose titles still do not reach visible app pixels: the compose-no-draw + recomposer + backend cases are the OPEN frontier (docs/DIFFERENTIAL_WORKING_VS_WHITE.md).
- **root_family:** COMPOSE/recomposer
- **pixel_truth:** no visual success claimed for Compose titles.
- **final_classification:** **partial closure**
- **evidence_refs:** issue #350 closure comment; root_registry.json (F-NEW-179/201); docs/DIFFERENTIAL_WORKING_VS_WHITE.md
- **notes:** Named blocker fixed; the broader Compose visual frontier remains open — honest partial.

### #352 — [S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park has no blocking semantics)

- **historical_claim:** [S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park family).
- **historical_evidence:** FR-352 (TESTED/E4): LockSupport park law landed; worker spin resolved in session records (S102 wave).
- **tested_runtime_commit:** S102 wave; current 9c3dc4d1
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** coroutines-bearing titles (dooz DispatchedContinuation real-APK evidence cited by the battery F-074 note).
- **runtime_proof:** park law live: F-074 fixture (which encodes the dooz DispatchedContinuation drained-continuation law) runs 6/6 GREEN at 9c3dc4d1; F-050 frame-pump golden PASS (pump starvation law); battery 121/121.
- **viewtree_proof:** N/A (scheduler law).
- **state_change_proof:** worker parks instead of spinning (session records + law fixture).
- **screenshot_metrics:** F-074 6-band verdicts GREEN.
- **reproducibility:** F-074/F-050 stages re-run every battery.
- **first_divergence:** N/A.
- **root_family:** CONCURRENCY/coroutines
- **pixel_truth:** N/A (non-visual law).
- **final_classification:** **verified current**
- **evidence_refs:** FR-352; miniandroid/tests/fixtures/f074_super_run; run/batch367_battery_v2.log (F-074/F-050)
- **notes:** REGISTRY GAP (recorded): literal id 'S102-D' absent from root_registry.json; laws covered by F-074/F-050 fixture law family + R-NEW-345 park-drain law.
