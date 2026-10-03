# CLOSED BATCH 2 AUDIT — #368

**Program:** CLOSED ISSUE FORENSIC PROGRAM — BATCH 2/3 — 50 MEDIUM CASES

**Batch scope:** storage/state, animation, network, resource/asset, text/font, layout/geometry, vector/state-list, graphics families.

**Audit head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631` (runtime binary rebuilt from this commit; battery-repair commit 9c3dc4d1 is the runtime code under test).

**Method:** for every issue in the frozen batch membership: body + comments + linked evidence re-read; historical claim independently reconstructed; APK identity checked; historical runtime commit vs current HEAD distinguished; current-HEAD evidence produced this campaign (gates + 121/121 battery + fresh re-run wave); pixel-truth law applied (BYTE-STABLE != PIXEL-TRUTH, F-NEW-233); closed/open state ignored as evidence.

**Classification distribution:** verified current = 50.

**Classification policy (honest, strict):** `verified current` requires evidence produced at the CURRENT runtime binary (this campaign's gates, battery, or re-run wave) or a law fenced by the current battery. Evidence only at older HEADs (even 3-run) = `historical-only verification` (reproducibility proven, currency not re-confirmed). Synthetic micro-gap laws are `verified current` ONLY at law level with their test-only scope explicitly retained (M5 honesty rule).

## Per-issue audit table

| # | Title | Classification | Key current-HEAD evidence |
|---|-------|----------------|---------------------------|
| #252 | [MG-173] boolean persistence — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #253 | [MG-174] int persistence — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #254 | [MG-175] long persistence — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #255 | [MG-176] float persistence — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #256 | [MG-177] string persistence — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #257 | [MG-178] editor apply — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #258 | [MG-179] editor commit — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #259 | [MG-180] remove — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #260 | [MG-181] clear — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #261 | [MG-182] contains — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #262 | [MG-183] preference process persistence — storage/state (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE AL |
| #263 | [MG-214] GIF disposal NONE — animation (OBSERVED) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 gif laws (expect 17) PASS 17/17 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL |
| #264 | [MG-215] GIF disposal BACKGROUND — animation (OBSERVED) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 gif laws (expect 17) PASS 17/17 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL |
| #265 | [MG-216] GIF disposal PREVIOUS — animation (OBSERVED) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 gif laws (expect 17) PASS 17/17 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL |
| #266 | [MG-248] HTTP GET — network (PENDING) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 layout/net laws (expect 11) PASS 11/11 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY G |
| #267 | [MG-047] adaptive icon foreground — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #268 | [MG-048] adaptive icon background — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #269 | [MG-052] Missing glyph detection — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #270 | [MG-053] tofu detection — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #273 | [MG-061] lineSpacing — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #274 | [MG-062] includeFontPadding — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #275 | [MG-067] font ascent — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #276 | [MG-068] font descent — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #277 | [MG-071] whitespace handling — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #279 | [MG-074] maxLines — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #280 | [MG-075] singleLine — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #285 | [MG-086] font file loading failure semantics — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #286 | [MG-087] Android resource font family — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #287 | [MG-088] downloadable-font failure fallback — text/font (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE A |
| #289 | [MG-130] ViewGroup child ordering — layout/geometry (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 layout/net laws (expect 11) PASS 11/11 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY G |
| #291 | [MG-002] Vector viewportWidth/viewportHeight — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #292 | [MG-003] Vector path fillType — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #293 | [MG-004] Vector path winding — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #294 | [MG-005] Vector path strokeWidth — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #298 | [MG-009] Vector group pivotX/pivotY — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #299 | [MG-010] Vector group rotation — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #300 | [MG-011] Vector group scale — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #301 | [MG-012] Vector group translation — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #302 | [MG-013] Vector nested group transforms — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #303 | [MG-014] Vector alpha inheritance — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #305 | [MG-016] Layer-list ordering — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #306 | [MG-017] Layer-list inset — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #307 | [MG-020] State-list selected state — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #308 | [MG-021] State-list disabled state — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #309 | [MG-022] State-list checked state — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #310 | [MG-023] State-list state fallback — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #313 | [MG-046] mipmap XML indirection — resource/asset (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GA |
| #314 | [MG-204] scaling filter quality classes — graphics/render (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #315 | [MG-207] canvas translation — graphics/render (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #316 | [MG-208] canvas scale — graphics/render (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |

## Per-issue detail

### #252 — [MG-173] boolean persistence — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-173] (storage/state): boolean persistence — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-173] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: boolean round-trip — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-173; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-252=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #253 — [MG-174] int persistence — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-174] (storage/state): int persistence — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-174] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: int round-trip — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-174; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-253=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #254 — [MG-175] long persistence — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-175] (storage/state): long persistence — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-175] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: long round-trip (>int32) — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-175; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-254=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #255 — [MG-176] float persistence — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-176] (storage/state): float persistence — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-176] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: float round-trip — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-176; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-255=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #256 — [MG-177] string persistence — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-177] (storage/state): string persistence — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-177] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: string round-trip (UTF-8 multibyte) — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-177; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-256=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #257 — [MG-178] editor apply — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-178] (storage/state): editor apply — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-178] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: apply() persists — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-178; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-257=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #258 — [MG-179] editor commit — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-179] (storage/state): editor commit — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-179] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: commit() returns true on sync write — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-179; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-258=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #259 — [MG-180] remove — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-180] (storage/state): remove — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-180] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: remove() drops exact key — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-180; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-259=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #260 — [MG-181] clear — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-181] (storage/state): clear — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-181] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: clear() empties — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-181; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-260=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #261 — [MG-182] contains — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-182] (storage/state): contains — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-182] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: contains() post-commit law — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-182; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-261=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #262 — [MG-183] preference process persistence — storage/state (PARTIAL)

- **historical_claim:** Micro-gap [MG-183] (storage/state): preference process persistence — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-183] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **tested_runtime_commit:** s98 storage batch
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** machine-proven: process persistence (fresh instance reads all committed) — 15/15 prefs law battery
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/storage/state
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-183; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-262=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

### #263 — [MG-214] GIF disposal NONE — animation (OBSERVED)

- **historical_claim:** Micro-gap [MG-214] (animation): GIF disposal NONE — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-214] STATUS=CLOSED; EVIDENCE: battery stage 's106_gif_law_test G1' (GIF89a disposal 1 (leave-in-place) composited over canvas — stbi_load_gif_from_memory wired into GifDecoder; frame N content survives into N+1); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 gif laws (expect 17) PASS 17/17 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/animation
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-214; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-263=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #264 — [MG-215] GIF disposal BACKGROUND — animation (OBSERVED)

- **historical_claim:** Micro-gap [MG-215] (animation): GIF disposal BACKGROUND — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-215] STATUS=CLOSED; EVIDENCE: battery stage 's106_gif_law_test G2' (disposal 2 = restore to BACKGROUND (transparent black, GIF89a + Android/Skia law) — FIXED vendored stb deviation (restored pre-frame canvas)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 gif laws (expect 17) PASS 17/17 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/animation
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-215; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-264=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #265 — [MG-216] GIF disposal PREVIOUS — animation (OBSERVED)

- **historical_claim:** Micro-gap [MG-216] (animation): GIF disposal PREVIOUS — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-216] STATUS=CLOSED; EVIDENCE: battery stage 's106_gif_law_test G3' (disposal 3 = restore to PREVIOUS — FIXED stb two_back dangling pointer (OOB read across realloc) with per-GIF prev_canvas snapshot); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 gif laws (expect 17) PASS 17/17 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/animation
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-216; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-265=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #266 — [MG-248] HTTP GET — network (PENDING)

- **historical_claim:** Micro-gap [MG-248] (network): HTTP GET — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-248] STATUS=CLOSED; EVIDENCE: battery stage 's106_layout_net_law_test W1-W4' (REAL HTTP GET: parse_url decomposition, 200+exact body, 404 status preserved, transport error named (NET-001 client against a live local server)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 layout/net laws (expect 11) PASS 11/11 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/network
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-248; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-266=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #267 — [MG-047] adaptive icon foreground — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-047] (resource/asset): adaptive icon foreground — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-047] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test A1' (adaptive-icon background color fills the canvas); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-047; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-267=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #268 — [MG-048] adaptive icon background — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-048] (resource/asset): adaptive icon background — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-048] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test A2' (adaptive-icon foreground vector draws OVER background); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-048; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-268=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #269 — [MG-052] Missing glyph detection — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-052] (text/font): Missing glyph detection — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-052] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X1' (uncovered codepoint (PUA U+E700) flags notdef_count>=1); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-052; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-269=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #270 — [MG-053] tofu detection — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-053] (text/font): tofu detection — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-053] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X2' (covered mixed-script string reports notdef_count==0 (no false tofu)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-053; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-270=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #273 — [MG-061] lineSpacing — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-061] (text/font): lineSpacing — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-061] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X3' (line spacing mult=2 doubles line box; add=6 adds flat px (StaticLayout law)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-061; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-273=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #274 — [MG-062] includeFontPadding — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-062] (text/font): includeFontPadding — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-062] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X4' (includeFontPadding: pad=true uses |fm.top| >= |fm.ascent|; pad=false tracks ascent exactly); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-062; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-274=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #275 — [MG-067] font ascent — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-067] (text/font): font ascent — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-067] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X5' (font ascent positive + deterministic across calls); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-067; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-275=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #276 — [MG-068] font descent — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-068] (text/font): font descent — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-068] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X6' (descent positive; ascent+descent <= line_height); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-068; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-276=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #277 — [MG-071] whitespace handling — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-071] (text/font): whitespace handling — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-071] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X7' (trailing spaces excluded from line width (layout law)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-071; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-277=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #279 — [MG-074] maxLines — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-074] (text/font): maxLines — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-074] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X8' (max_lines=2 caps block at 2 lines; FIXED off-by-one that emitted an extra empty line past the cap); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-074; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-279=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #280 — [MG-075] singleLine — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-075] (text/font): singleLine — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-075] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X9' (singleLine (max_lines=1) never word-wraps); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-075; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-280=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #285 — [MG-086] font file loading failure semantics — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-086] (text/font): font file loading failure semantics — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-086] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X10' (unknown font family resolution falls back to usable face (honest failure semantics, no crash)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-086; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-285=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #286 — [MG-087] Android resource font family — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-087] (text/font): Android resource font family — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-087] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X11' (resolve_family distinguishes monospace vs sans-serif faces); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-087; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-286=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #287 — [MG-088] downloadable-font failure fallback — text/font (PARTIAL)

- **historical_claim:** Micro-gap [MG-088] (text/font): downloadable-font failure fallback — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-088] STATUS=CLOSED; EVIDENCE: battery stage 's106_text2_law_test X12' (unavailable (downloadable) family falls back to system face — TextView fallback law); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 text2 laws (expect 14) PASS 14/14 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/text/font
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-088; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-287=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #289 — [MG-130] ViewGroup child ordering — layout/geometry (PARTIAL)

- **historical_claim:** Micro-gap [MG-130] (layout/geometry): ViewGroup child ordering — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-130] STATUS=CLOSED; EVIDENCE: battery stage 's106_layout_net_law_test L3' (ViewGroup children preserve document order; getChildAt/getChildCount resolve by index); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
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
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-130; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-289=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #291 — [MG-002] Vector viewportWidth/viewportHeight — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-002] (resource/asset): Vector viewportWidth/viewportHeight — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-002] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V1' (viewport units map by raster/vp scale (24u@2x vs 48u@1x ink bboxes exact)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-002; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-291=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #292 — [MG-003] Vector path fillType — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-003] (resource/asset): Vector path fillType — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-003] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V2' (fillType=evenOdd punches hole in overlap (center px alpha=0)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-003; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-292=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #293 — [MG-004] Vector path winding — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-004] (resource/asset): Vector path winding — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-004] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V3' (nonZero fill winding-direction-insensitive (single reversed contour fills identically)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-004; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-293=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #294 — [MG-005] Vector path strokeWidth — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-005] (resource/asset): Vector path strokeWidth — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-005] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V4' (stroke ink widens with strokeWidth; FIXED fill/stroke independence (stroke-only paths drew nothing)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-005; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-294=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #298 — [MG-009] Vector group pivotX/pivotY — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-009] (resource/asset): Vector group pivotX/pivotY — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-009] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V5' (pivot-relative transform composition law (scale2 about pivot0 vs pivot12 differs by exactly pivot-delta*(s-1)*scale_px)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-009; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-298=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #299 — [MG-010] Vector group rotation — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-010] (resource/asset): Vector group rotation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-010] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V5' (rotation 90 exact mapping (x,y)->(24-y,x) about pivot (12,12)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-010; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-299=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #300 — [MG-011] Vector group scale — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-011] (resource/asset): Vector group scale — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-011] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V6' (group scaleX/Y 2 doubles ink bbox from pivot); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-011; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-300=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #301 — [MG-012] Vector group translation — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-012] (resource/asset): Vector group translation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-012] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V7' (group translateX/Y shifts ink by exact px); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-012; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-301=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #302 — [MG-013] Vector nested group transforms — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-013] (resource/asset): Vector nested group transforms — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-013] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V8' (nested group matrices compose in document order (outer translate ∘ inner rotate)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-013; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-302=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #303 — [MG-014] Vector alpha inheritance — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-014] (resource/asset): Vector alpha inheritance — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-014] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test V9' (IMPLEMENTED group android:alpha inheritance (multiplicative through the group chain; fill+stroke alpha multiply)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-014; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-303=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #305 — [MG-016] Layer-list ordering — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-016] (resource/asset): Layer-list ordering — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-016] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test L1' (layer-list items parse in DOCUMENT ORDER with colors preserved); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-016; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-305=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #306 — [MG-017] Layer-list inset — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-017] (resource/asset): Layer-list inset — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-017] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test L2' (layer-list left/top insets land as px offsets (12dp x density 2.625 = 32px)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-017; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-306=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #307 — [MG-020] State-list selected state — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-020] (resource/asset): State-list selected state — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-020] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test S1' (state_selected=true picks the selected item (first-match)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-020; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-307=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #308 — [MG-021] State-list disabled state — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-021] (resource/asset): State-list disabled state — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-021] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test S2' (state_enabled=false picks the disabled item); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-021; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-308=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #309 — [MG-022] State-list checked state — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-022] (resource/asset): State-list checked state — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-022] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test S3' (IMPLEMENTED state_checked in BgStateItem + pick_state_list (AOSP Checkable family law)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-022; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-309=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #310 — [MG-023] State-list state fallback — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-023] (resource/asset): State-list state fallback — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-023] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test S4' (no state match -> wildcard last item fallback); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-023; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-310=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #313 — [MG-046] mipmap XML indirection — resource/asset (PARTIAL)

- **historical_claim:** Micro-gap [MG-046] (resource/asset): mipmap XML indirection — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-046] STATUS=CLOSED; EVIDENCE: battery stage 's106_drawables_law_test M1' (mipmap XML indirection: @mipmap id -> resolve_full -> XML -> drawable reference chain); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 drawables laws (expect 39) PASS 39/39 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/resource/asset
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-046; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-313=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #314 — [MG-204] scaling filter quality classes — graphics/render (PARTIAL)

- **historical_claim:** Micro-gap [MG-204] (graphics/render): scaling filter quality classes — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-204] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test C5' (draw_image_region nearest-neighbour upscale keeps block structure (Paint.FilterBitmap=false default law)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/graphics/render
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-204; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-314=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #315 — [MG-207] canvas translation — graphics/render (PARTIAL)

- **historical_claim:** Micro-gap [MG-207] (graphics/render): canvas translation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-207] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test C1' (canvas translate maps by +t; T∘S != S∘T pre-concat law (Skia)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/graphics/render
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-207; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-315=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #316 — [MG-208] canvas scale — graphics/render (PARTIAL)

- **historical_claim:** Micro-gap [MG-208] (graphics/render): canvas scale — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-208] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test C2' (scale multiplies linear columns; mean_scale=sqrt|det| (Skia stroke law)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/graphics/render
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-208; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-316=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106
