# CLOSED BATCH 3 AUDIT — #369

**Program:** CLOSED ISSUE FORENSIC PROGRAM — BATCH 3/3 — 8 FINAL CASES

**Batch scope:** animation/input/audio/graphics final cases.

**Audit head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631` (runtime binary rebuilt from this commit; battery-repair commit 9c3dc4d1 is the runtime code under test).

**Method:** for every issue in the frozen batch membership: body + comments + linked evidence re-read; historical claim independently reconstructed; APK identity checked; historical runtime commit vs current HEAD distinguished; current-HEAD evidence produced this campaign (gates + 121/121 battery + fresh re-run wave); pixel-truth law applied (BYTE-STABLE != PIXEL-TRUTH, F-NEW-233); closed/open state ignored as evidence.

**Classification distribution:** verified current = 7, historical-only verification = 1.

**Classification policy (honest, strict):** `verified current` requires evidence produced at the CURRENT runtime binary (this campaign's gates, battery, or re-run wave) or a law fenced by the current battery. Evidence only at older HEADs (even 3-run) = `historical-only verification` (reproducibility proven, currency not re-confirmed). Synthetic micro-gap laws are `verified current` ONLY at law level with their test-only scope explicitly retained (M5 honesty rule).

## Per-issue audit table

| # | Title | Classification | Key current-HEAD evidence |
|---|-------|----------------|---------------------------|
| #317 | [MG-209] canvas rotation — graphics/render (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #318 | [MG-210] nested transforms — graphics/render (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #319 | [MG-146] event cancellation — input (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #321 | [MG-149] touch outside bounds — input (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #323 | [MG-223] ValueAnimator basic timing — animation (PARTIAL) | historical-only verification | recorded at close; not re-fenced at current HEAD |
| #331 | [MG-231] SoundPool initialization — audio (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #332 | [MG-232] MediaPlayer initialization — audio (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |
| #333 | [MG-233] resource audio loading — audio (PARTIAL) | verified current | law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: B |

## Per-issue detail

### #317 — [MG-209] canvas rotation — graphics/render (PARTIAL)

- **historical_claim:** Micro-gap [MG-209] (graphics/render): canvas rotation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-209] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test C3' (rot90 maps +x onto +y (y-down clockwise); FIXED pre_rotate computing M·Rᵀ (rotated the wrong way)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
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
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-209; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-317=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #318 — [MG-210] nested transforms — graphics/render (PARTIAL)

- **historical_claim:** Micro-gap [MG-210] (graphics/render): nested transforms — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-210] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test C4' (nested save/translate/rotate composes M0∘T∘R exactly (hand-verified)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
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
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-210; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-318=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #319 — [MG-146] event cancellation — input (PARTIAL)

- **historical_claim:** Micro-gap [MG-146] (input): event cancellation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-146] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test I1' (DOWN→CANCEL unpresses, no click, no long-press (View.java L17172-17184 cleanup law)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/input
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-146; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-319=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #321 — [MG-149] touch outside bounds — input (PARTIAL)

- **historical_claim:** Micro-gap [MG-149] (input): touch outside bounds — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-149] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test I2' (touch outside bounds never targets/presses/clicks; in-bounds control clicks); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/input
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-149; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-321=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #323 — [MG-223] ValueAnimator basic timing — animation (PARTIAL)

- **historical_claim:** Micro-gap [MG-223] (animation): ValueAnimator basic timing — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: ValueAnimator.ofInt/ofFloat factories returned NULL object -> next instance invoke hit F-141 null-receiver law (babydots setRepeatCount NPE, onCreate dead)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-223] STATUS=CLOSED; EVIDENCE: S99 run/s99/full_load/com.serwylo.babydots/obs_obs.log [ANIM] ValueAnimator.ofFloat -> animator obj=560; battery 105/105 ALL PASS after landing; COMMIT: d0f03cb7 (S99)
- **tested_runtime_commit:** d0f03cb7 (S99)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** recorded at close; not re-fenced at current HEAD
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** AnimatorShadow: factories allocate Landroid/animation/ValueAnimator; object, setDuration fluent, start/cancel/end lifecycle + isRunning/isStarted, setter family, getAnimatedValue null-before-start law (AOSP ValueAnimator
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** single-fence at close
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/animation
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **historical-only verification**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-223; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-323=TESTED/E2. Gap: law stage not part of the current battery; current re-fence pending; FANOUT=corpus-wide: every app with property-animation entry points (material FABs, progress animators)

### #331 — [MG-231] SoundPool initialization — audio (PARTIAL)

- **historical_claim:** Micro-gap [MG-231] (audio): SoundPool initialization — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-231] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test A2' (SoundPool construct→load→play: sample loaded, stream PLAYING, stop->STOPPED; audio module WIRED into the build (was source-only)); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/audio
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-231; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-331=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #332 — [MG-232] MediaPlayer initialization — audio (PARTIAL)

- **historical_claim:** Micro-gap [MG-232] (audio): MediaPlayer initialization — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-232] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test A1' (MediaPlayer IDLE→INITIALIZED→PREPARED→STARTED→PLAYBACK_COMPLETED with AOSP illegal-transition error law); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/audio
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-232; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-332=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

### #333 — [MG-233] resource audio loading — audio (PARTIAL)

- **historical_claim:** Micro-gap [MG-233] (audio): resource audio loading — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **historical_evidence:** MICRO_GAP_REGISTRY.json[MG-233] STATUS=CLOSED; EVIDENCE: battery stage 's106_cia_law_test A3' (real RIFF/WAVE decodes to PCM (rate/channels/duration exact) via decode_audio_file); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **tested_runtime_commit:** (wave of record; registry)
- **current_head:** `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`
- **apk_identity:** N/A (synthetic law battery — no real APK bound to this micro-gap)
- **runtime_proof:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 canvas/input/audio laws (expect 21) PASS 21/21 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **viewtree_proof:** per-ticket machine checks (law-test asserts); no viewtree claim where N/A
- **state_change_proof:** (per-ticket law asserts)
- **screenshot_metrics:** band-verdict pixel goldens where the family fences one (F-0xx pattern); else law-assert only
- **reproducibility:** law battery re-runnable via scripts/test/run_test_battery.sh; stage deterministic
- **first_divergence:** N/A (synthetic law checkpoint; no app-execution divergence recorded)
- **root_family:** MICRO-GAP/audio
- **pixel_truth:** law-level (synthetic); visual-success claims are NOT made from micro-gap tickets
- **final_classification:** **verified current**
- **evidence_refs:** docs/MICRO_GAP_REGISTRY.json#MG-233; scripts/test/run_test_battery.sh; run/batch367_battery_v2.log; docs/FORENSIC_ALL_REQUESTS_LEDGER.jsonl
- **notes:** FR rows: FR-333=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106
