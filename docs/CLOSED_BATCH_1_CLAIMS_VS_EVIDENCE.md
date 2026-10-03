# CLOSED BATCH 1 — CLAIMS vs EVIDENCE — #367

Audit head `9c3dc4d148c8feadb11f3fbfa33b475e00b9e631`. Per issue: the historical claim, the evidence that existed at closure, the evidence that exists at the current HEAD after this campaign, and the residual gap (recorded, never masked).

## #1 EXP-064 — REAL LOGIN IMAGE PROVEN BY PIXELS (OCR-validated PhoneView rendered)

- **Claim:** EXP-064: Telegram login screen (PhoneView) rendered with REAL pixels, OCR-validated, proven by screenshot metrics.
- **Evidence at closure:** FR-001 (OBSERVED/E3): session screenshot + OCR; commits 1e1ec2b4/c322b479/1dda55ae/78c182f3; predates golden/3-run laws.
- **Evidence at current HEAD:** session-era execution trace only; runtime chain superseded by S107+ Telegram boundary work; current carrier = forkgram (M3: x2 byte-identical bbb6cd10a834963d at abb57444).
- **Verdict:** historical-only verification
- **Residual gap:** Closed state honest for its era; superseded as current-carrier evidence by the S107+ chain and forkgram runs. Gap: golden Telegram APK lost.

## #2 EXP-065 — Fix multi-DEX const-string bug (FIELD_PREFERRED_AUDIO_LANGUAGES leak resolved)

- **Claim:** EXP-065: fixed the multi-DEX const-string bug (FIELD_PREFERRED_AUDIO_LANGUAGES leak) — strings from a second DEX resolve correctly.
- **Evidence at closure:** FR-002 (TESTED/E3): commits ff073348/b327292d/78c182f3; law re-verified by later multi-DEX campaigns.
- **Evidence at current HEAD:** multi-DEX const-string law is live in the current binary: forkgram (5-DEX) x2 byte-identical runs at abb57444 + battery semantic pass3-bridge stage ALL PASS at 9c3dc4d1.
- **Verdict:** verified current
- **Residual gap:** Law-level currency via current battery + forkgram determinism.

## #3 EXP-066 — Multi-DEX semantic audit + OutlineTextContainerView text capture (Phone number label visible)

- **Claim:** EXP-066: multi-DEX semantic audit + OutlineTextContainerView text capture (phone number captured from real view text).
- **Evidence at closure:** FR-003 (OBSERVED/E3): commit 1e1ec2b4; session evidence.
- **Evidence at current HEAD:** session-era; text-capture capability since generalized (text laws battery 21/21 at 9c3dc4d1).
- **Verdict:** historical-only verification
- **Residual gap:** Capability lineage continued by the current text pipeline.

## #4 EXP-067 — Resource resolution + AXML parser + Drawable decoding (real WebP images in Login UI)

- **Claim:** EXP-067: resource resolution + AXML parser + drawable decoding produced REAL WebP images in the login flow.
- **Evidence at closure:** FR-004 (OBSERVED/E3): commits 78c182f3 era; superseded by ARSC/AXML law waves (S126/S127 R-NEW-423).
- **Evidence at current HEAD:** superseded by stronger current laws: ARSC bag/style laws + AXML parse are battery-fenced (drawables 39/39 incl. AXML-driven vectors; G04 density oracle 11/11) at 9c3dc4d1.
- **Verdict:** superseded
- **Residual gap:** Superseded by a strictly stronger current implementation (registry law chain).

## #5 EXP-068 — Generic View inheritance + Floating Next button (semantic superclass resolution)

- **Claim:** EXP-068: generic View inheritance + semantic superclass resolution produced the floating Next button.
- **Evidence at closure:** FR-005 (OBSERVED/E3): session evidence.
- **Evidence at current HEAD:** view-inheritance laws since formalized (G11 ctor law 37/37 incl. superclass walk, F-074 engine-level super-run 6/6 GREEN at 9c3dc4d1).
- **Verdict:** historical-only verification
- **Residual gap:** Law lineage current; session claim itself not re-runnable.

## #6 EXP-069 — Generic text input + click dispatch: phone number injected + Next button clicked

- **Claim:** EXP-069: generic text input + click dispatch — phone number injected and Next clicked programmatically.
- **Evidence at closure:** FR-006 (OBSERVED/E3): session evidence.
- **Evidence at current HEAD:** input/dispatch laws current: G06 tap interaction golden (21 law checks) + 3-run tap determinism + tictactoe 9/9 DEX-dispatched clicks at 9c3dc4d1.
- **Verdict:** historical-only verification
- **Residual gap:** Session superseded; laws current.

## #7 EXP-071 — Telegram Login → SMS Code Page Transition (CHECKPOINT_M PROVEN)

- **Claim:** EXP-071: Telegram Login -> SMS Code page transition (CHECKPOINT_M PROVEN) end-to-end.
- **Evidence at closure:** FR-007 (OBSERVED/E4): 15 checkpoints in .agent/state.md (historical banner); S27 REVIEW approved at HEAD 79874955.
- **Evidence at current HEAD:** checkpoint session evidence in-era; current-era Telegram boundary is an ARTIFACT problem, not runtime: forkgram installs + runs deterministically (x2 byte-identical at abb57444).
- **Verdict:** historical-only verification
- **Residual gap:** Honest boundary: runtime capability proven historically; artifact acquisition remains blocked (consistent with #365 M3/M4).

## #8 MiniAndroid campaign evidence — verified achievements (REUSE-FIRST campaign, 2026-09-05)

- **Claim:** MiniAndroid campaign evidence mega-issue — 55-comment verified-achievements thread (REUSE-FIRST campaign 2026-09-05).
- **Evidence at closure:** FR-008 (SUPERSEDED/E3): superseded by canonical registries (S84+ one-record-per-title law).
- **Evidence at current HEAD:** superseded: canonical registries now the single source of truth (registry.json, root_registry.json, MICRO_GAP_REGISTRY.json, ARTIFACT_REGISTRY.json).
- **Verdict:** superseded
- **Residual gap:** Clean supersession — the canonical-registry law replaced the evidence thread.

## #10 [EXEC] HelloWorld — APK Execution & Visual Proof

- **Claim:** [EXEC] HelloWorld: APK execution + visual proof (canonical L6 fixture).
- **Evidence at closure:** FR-010 (VERIFIED/E5): battery + golden era records.
- **Evidence at current HEAD:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops; Snake Deluxe: 1203/0.72/262; MiniCraft: 2416/0.64/735; HelloWorld canonical L6 sha 83720c1028f832d0) — run/user_goldens/user_goldens.json
- **Verdict:** verified current
- **Residual gap:** User-designated golden test.

## #11 [EXEC] TicTacToe — APK Execution & Gameplay Proof

- **Claim:** [EXEC] TicTacToe: APK execution + gameplay proof (9 clicks, marks render, determinism).
- **Evidence at closure:** FR-011 (OBSERVED/E3): early session proof; canonical registry OBSERVED; the SS29 tictactoe_golden validator is the canonical fencing.
- **Evidence at current HEAD:** tictactoe_golden (SS29) stage PASS at 9c3dc4d1 inside run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates: 9/9 clicks DEX-dispatched, marks in cells with glyph ink, frames 7/8/9 frozen, run A/B 10-frame byte-identical (895fac7581b9...).
- **Verdict:** verified current
- **Residual gap:** SS29 validator re-baselined this campaign for the F-NEW-233 rc interplay (documented in-script; law checks unchanged).

## #12 [EXEC] ConnectFour — APK Execution & Gameplay Proof

- **Claim:** [EXEC] ConnectFour: APK execution + gameplay proof.
- **Evidence at closure:** FR-012 (OBSERVED/E3): early session proof only.
- **Evidence at current HEAD:** not re-run at current HEAD; not part of the battery.
- **Verdict:** historical-only verification
- **Residual gap:** Gap: APK not in the current canonical set; re-adoption would require artifact re-acquisition + 3-run fencing.

## #13 [EXEC] AndroidGameSnake — Autonomous Gameplay Proof

- **Claim:** [EXEC] AndroidGameSnake (zhangman.github.snake): autonomous gameplay proof (88 moves/22 turns/1 food; 4-run sweep).
- **Evidence at closure:** FR-013 (VERIFIED/E5): S73/S74 dossiers + canonical GIF + 4-run sweep at d7280a15; canonical dossier docs/compatibility/apps/androidgamesnake.json.
- **Evidence at current HEAD:** — fresh execution at current HEAD via evidence/batch367_rerun/zhangman.github.snake/.
- **Verdict:** verified current
- **Residual gap:** Fresh current-HEAD execution closes the currency question; restart gap remains honestly open.

## #15 [EXEC] Unote — Runtime/UI Completion

- **Claim:** [EXEC] Unote: runtime/UI completion (notes app renders + interacts).
- **Evidence at closure:** FR-015 (VERIFIED/E5): golden 4f1a9e4e8f64fae8 x3 re-verified at HEAD 2026-10-03.
- **Evidence at current HEAD:** working_vs_failing_probe.sh @ 9c3dc4d1: 5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — DETERMINISM gate only per F-NEW-233 (chess/dooz frames 100% white; never visual success); uninstall store keeps byte-identical app identity.
- **Verdict:** verified current
- **Residual gap:** Also serves as an unrelated control in later fan-outs (diff366 zero drift).

## #17 [EXEC] GMDice — APK Execution & Visual Proof

- **Claim:** [EXEC] GMDice: APK execution + visual proof (AXML inflation + OCR text D05).
- **Evidence at closure:** FR-017 (VERIFIED/E4): AXML + OCR session records.
- **Evidence at current HEAD:** battery corpus run stage PASS at 9c3dc4d1; fresh re-run at HEAD 9c3dc4d1: rc=0, status=SUCCESS ✅, unique_colors=892, frame_delta=False.
- **Verdict:** verified current
- **Residual gap:** OCR text proof is era evidence; current evidence = render + battery.

## #18 [EXEC] MicroTimer — APK Execution & Visual Proof

- **Claim:** [EXEC] MicroTimer: APK execution + visual proof.
- **Evidence at closure:** FR-018 (VERIFIED/E5): golden da73010a37dd0189 x3 re-verified at HEAD 2026-10-03.
- **Evidence at current HEAD:** working_vs_failing_probe.sh @ 9c3dc4d1: 5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — DETERMINISM gate only per F-NEW-233 (chess/dooz frames 100% white; never visual success); M3 F-012 persistence+fresh-state determinism golden PASS at 9c3dc4d1 (alarm row persists across runs; frames byte-deterministic across independent pairs).
- **Verdict:** verified current
- **Residual gap:** F-012 stage helper re-baselined to the evolved FHS store layout (data/data/<pkg>) this campaign — documented in-script.

## #68 [GAME-044] com.smorgasbork.hotdeath — compatibility report

- **Claim:** [GAME-044] com.smorgasbork.hotdeath compatibility report — full-load + render evidence.
- **Evidence at closure:** FR-068 (VERIFIED/E4): canonical game registry record; S107 audit 3-run VERIFIED_3RUN (634 unique colors, sha-stable 7c811bffb9a7c590, PARTIAL SUCCESS rc per F-NEW-233-era honesty).
- **Evidence at current HEAD:** S107 x3 runs recorded; NOT re-run at current HEAD (APK not in current canonical set).
- **Verdict:** historical-only verification
- **Residual gap:** Gap: current-HEAD re-run pending APK re-acquisition; runtime itself regression-free at HEAD (battery 121/121).

## #81 [GAME-057] org.bobstuff.bobball — compatibility report

- **Claim:** [GAME-057] org.bobstuff.bobball compatibility report.
- **Evidence at closure:** FR-081 (VERIFIED/E4): canonical record; S107 3-run VERIFIED_3RUN (476 colors, sha-stable).
- **Evidence at current HEAD:** S107 x3 runs; not re-run at current HEAD.
- **Verdict:** historical-only verification
- **Residual gap:** Gap: current-HEAD re-run pending artifact.

## #121 [GAME-097] com.dozingcatsoftware.bouncy — compatibility report

- **Claim:** [GAME-097] com.dozingcatsoftware.bouncy compatibility report.
- **Evidence at closure:** FR-121 (VERIFIED/E4): canonical record; S107 3-run VERIFIED_3RUN (494 colors).
- **Evidence at current HEAD:** diff366 ROOT-A fan-out at edecae3e: byte-identical zero drift; fresh re-run at HEAD 9c3dc4d1: rc=1, status=PARTIAL SUCCESS ⚠️, unique_colors=413, frame_delta=False (rc=1 is the documented F-NEW-233 PARTIAL verdict, laws hold).
- **Verdict:** verified current
- **Residual gap:** Bouncy doubles as an unrelated-app regression control (ROOT-A fan-out).

## #166 [APP-042] org.ucam.ssb22.pinyinfdroid — compatibility report

- **Claim:** [APP-042] org.ucam.ssb22.pinyinfdroid compatibility report.
- **Evidence at closure:** S107 closure comment: fresh run at HEAD 1818a325 + AUDIT RESULT 'closure re-verified VERIFIED 3RUN' (rebuilt from c0b7f501); S107 three_run_summary VERIFIED_3RUN (208 colors, sha-stable e03921ecbff1246d). The FR-166 PENDING/E0 row is STALE relative to this evidence.
- **Evidence at current HEAD:** x3 runs at S107 audit; not re-run at current HEAD (APK not in current canonical set).
- **Verdict:** historical-only verification
- **Residual gap:** FR ledger row corrected by this audit (PENDING -> evidence-backed historical verification).

## #234 [MG-051] Font fallback selection — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-051] (text/font): Font fallback selection — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: CJK face never loaded — now loaded; notdef==0 via fallback chain
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-051] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-234=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #235 [MG-073] ellipsize — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-073] (text/font): ellipsize — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: ellipsize absent — IMPLEMENTED END/START/MIDDLE + maxLines=1 no-wrap
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-073] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-235=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #236 [MG-080] Unicode combining marks — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-080] (text/font): Unicode combining marks — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced combining-mark shape law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-080] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-236=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #237 [MG-081] RTL basic shaping — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-081] (text/font): RTL basic shaping — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced RTL first-strong law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-081] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-237=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #238 [MG-082] Arabic joining — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-082] (text/font): Arabic joining — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced Arabic joining advance law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-082] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-238=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #239 [MG-083] emoji fallback — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-083] (text/font): emoji fallback — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: bogus DejaVu emoji glyph swallowed slot — emoji-presentation claim law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-083] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-239=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #240 [MG-084] surrogate pairs — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-084] (text/font): surrogate pairs — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: fenced surrogate single-cluster law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-084] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-240=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #241 [MG-085] UTF-8/UTF-16 boundary — text/font (PARTIAL)

- **Claim:** Micro-gap [MG-085] (text/font): UTF-8/UTF-16 boundary — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: PHANTOM-NUL fix: hb buffer fed N+1 units — every string shaped with garbage trailing cluster
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-085] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 4ac6c542
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-241=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #242 [MG-115] requestLayout propagation — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-115] (layout/geometry): requestLayout propagation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: (recorded at close)
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-115] STATUS=CLOSED; EVIDENCE: battery stage 's106_layout_net_law_test L1/L2' (FIXED View.requestLayout() bridge swallowing the call as no-op — now raises the R-NEW-302 layout_dirty traversal flag (AOSP PFLAG_FORCE_LAYOUT law); setLayoutParams path re-verified); commit of record = S106 wave; battery ALL PASS at close; COMMIT: (wave of record)
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s106 layout/net laws (expect 11) PASS 11/11 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-242=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=fenced_s106

## #243 [MG-123] scroll offset — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-123] (layout/geometry): scroll offset — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: scrollTo/scrollBy/getScrollX/Y absent — IMPLEMENTED + draw-walk content delta
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-123] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-243=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #244 [MG-124] translationX — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-124] (layout/geometry): translationX — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: translationX property + walk delta law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-124] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-244=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #245 [MG-125] translationY — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-125] (layout/geometry): translationY — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: translationY property + walk delta law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-125] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-245=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #246 [MG-126] scaleX — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-126] (layout/geometry): scaleX — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: scaleX property law (state+getters; matrix render = recorded frontier)
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-126] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-246=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #247 [MG-127] scaleY — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-127] (layout/geometry): scaleY — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: scaleY property law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-127] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-247=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #248 [MG-128] rotation — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-128] (layout/geometry): rotation — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: rotation property law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-128] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-248=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #249 [MG-129] pivot — layout/geometry (PARTIAL)

- **Claim:** Micro-gap [MG-129] (layout/geometry): pivot — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: pivot property law
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-129] STATUS=CLOSED; EVIDENCE: named battery stage 's98 text laws (expect 21)' / 's98 scroll/transform laws (expect 13)'; canonical battery ALL PASS; COMMIT: 62ef579f
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 text laws (expect 21) PASS 21/21; s98 scroll/transform laws (expect 13) PASS 13/13 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-249=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=corpus-wide (text pipeline / draw walk)

## #250 [MG-171] SharedPreferences default file — storage/state (PARTIAL)

- **Claim:** Micro-gap [MG-171] (storage/state): SharedPreferences default file — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-171] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-250=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

## #251 [MG-172] custom file — storage/state (PARTIAL)

- **Claim:** Micro-gap [MG-172] (storage/state): custom file — fenced as a synthetic law checkpoint in the frozen 202-question corpus; BEFORE: implemented, unfenced (PARTIAL)
- **Evidence at closure:** MICRO_GAP_REGISTRY.json[MG-172] STATUS=CLOSED; EVIDENCE: named battery stage 's98 prefs laws (expect 15)' on the REAL AndroidAPI::SharedPreferences layer; COMMIT: s98 storage batch
- **Evidence at current HEAD:** law checkpoint binary/stage re-executed at current HEAD 9c3dc4d1: s98 prefs laws (expect 15) PASS 15/15 (part of run_test_battery.sh @ 9c3dc4d1: BATTERY GATE ALL PASS (121/121 stages; logs run/batch367_battery_v2.log); includes s98 text laws 21/21, s98 scroll/transform 13/13, s98 prefs 15/15, s106 gif 17/17, s106 text2 14/14, s106 canvas/input/audio 21/21, s106 drawables 39/39, s106 layout/net 11/11, G06/G07/G08 goldens + 3-run determinisms, tictactoe_golden SS29, M3 F-012 persistence, EXT-01/02, F-0xx fixture family + F-074/F-050 goldens, corpus runs, uninstall gates)
- **Verdict:** verified current
- **Residual gap:** FR rows: FR-251=TESTED/E2. Gap: synthetic-fixture scope (test-only corpus law): real-APK exercise of this exact law not demonstrated unless ticket FANOUT names real titles — never promoted beyond scope per the M5 honesty rule; FANOUT=all SharedPreferences-consuming titles

## #334 [GAMES-1] Full-load 5-10 games end-to-end (launch + render + interaction evidence)

- **Claim:** [GAMES-1] Full-load 5-10 games end-to-end (launch + render + interaction evidence).
- **Evidence at closure:** FR-334 (VERIFIED/E5): docs/evidence/s98/games_full_load.json; closure comment 9/10 FULL_LOAD_PASS + 1 honest LOAD_ISSUE.
- **Evidence at current HEAD:** wave evidence + current-HEAD re-confirmation of the flagged titles: snake-deluxe (golden gate), 2048 (golden gate), tictactoedeluxe + snakeneon + androidgamesnake ( etc.).
- **Verdict:** verified current
- **Residual gap:** The 1 honest LOAD_ISSUE remains recorded (honesty law).

## #335 [GAMES-2] Autonomous Snake Deluxe play (self-play, no game-memory cheating)

- **Claim:** [GAMES-2] Autonomous Snake Deluxe play (self-play, no game-memory cheating).
- **Evidence at closure:** FR-335 (VERIFIED/E5): S80 vision-based driver re-run on S98 binary — 7 captures, final continuous 120-frame run with 56-frame SHA-pinned prefix; snake ate food and grew (C1/C3/C4/C7 laws held); autoplay GIF canonical.
- **Evidence at current HEAD:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (Snake Deluxe leg).
- **Verdict:** verified current
- **Residual gap:** Vision-based driver method note kept from closure comment.

## #336 [GAMES-3] House-building autonomous play (Minicraft)

- **Claim:** [GAMES-3] House-building autonomous play (Minicraft): real taps (dpad walk + BLOCK cycle + PLACE/DIG + DEMO); cottage built.
- **Evidence at closure:** FR-336 (OBSERVED/E4): S98 driver — cursor moved (269,712)->(577,1000); materials placed brick 0->68432px, plank 0->49392px, roof 0->113190px; digs observed; minicraft_autoplay.gif canonical.
- **Evidence at current HEAD:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (MiniCraft leg: REAL_APP_CONTENT, 735 draw ops).
- **Verdict:** verified current
- **Residual gap:** Currency: app render re-verified at HEAD; the autonomous house-build proof remains the S98 driver record (scope honestly stated).

## #337 [GAMES-4] NEW snake variant — build, load, autonomous play

- **Claim:** [GAMES-4] NEW snake variant (snake-neon) — build, load, autonomous play; mechanically NEW (wrap-around walls + obstacles + speed HUD).
- **Evidence at closure:** FR-337 (OBSERVED/E4): S98 build (9156 teal px + 1252 food px, 0 errors) + snakeneon_autoplay.gif; FULL_LOAD_PASS row in games_full_load.json.
- **Evidence at current HEAD:** fresh re-run at HEAD 9c3dc4d1: rc=0, status=SUCCESS ✅, unique_colors=884, frame_delta=True — frame delta TRUE (game animates).
- **Verdict:** verified current
- **Residual gap:** Fresh current-HEAD execution upgrades the OBSERVED row with currency evidence.

## #338 [GAMES-5] Autonomous 2048 play

- **Claim:** [GAMES-5] Autonomous 2048 play (GIF + score-to-200 state change).
- **Evidence at closure:** FR-338 (VERIFIED/E5): g2048 autoplay GIF + score state change.
- **Evidence at current HEAD:** user_golden_gate.py @ 9c3dc4d1: 4/4 PASS REAL_APP_CONTENT (2048: 535 colors/0.59 nonbg/34 draw ops (2048 leg: REAL_APP_CONTENT, 34 draw ops).
- **Verdict:** verified current
- **Residual gap:** User-designated golden test.

## #340 [GAMES-7] Autonomous TicTacToe Deluxe play

- **Claim:** [GAMES-7] Autonomous TicTacToe Deluxe play (GIF + session record).
- **Evidence at closure:** FR-340 (VERIFIED/E4): tictactoe deluxe GIF + session record; canonical GIF docs/evidence/canonical/com.miniandroid.tictactoedeluxe.gif.
- **Evidence at current HEAD:** — tap interaction produced frame delta TRUE.
- **Verdict:** verified current
- **Residual gap:** Registry graphics verdict record exists (registry/graphics_verdicts/).

## #341 [GAMES-8] Wave evidence package + gh-pages gameplay GIFs

- **Claim:** [GAMES-8] Wave evidence package + gh-pages gameplay GIFs (docs/evidence/s98/ + EXECUTED_GIFS.md).
- **Evidence at closure:** FR-341 (VERIFIED/E4): closure comment lists games_full_load.json + minicraft_autoplay.gif + snakeneon_autoplay.gif + per-run frame evidence.
- **Evidence at current HEAD:** artifact existence verified at 9c3dc4d1: docs/evidence/s98/games_full_load.json, minicraft_autoplay.gif, snakeneon_autoplay.gif present; docs/EXECUTED_GIFS.md + canonical GIF set present; docs/verified_executed_games.json (26 games) present.
- **Verdict:** verified current
- **Residual gap:** Existence + integrity of the evidence package is the claim; verified.

## #342 [F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attr resolution gap for non-AppCompat-ancestor themes (mykanji family)

- **Claim:** [F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attribute resolution chain killed apps on deep MaterialComponents style chains.
- **Evidence at closure:** root_registry.json F-NEW-165 = ROOT-CAUSED-FIXED; S100 closure comment: ARSC parent-chain max_parent_hops=8 bound MyKanji's ~12-14-hop MaterialComponents chain -> fix bound/extended the hop law.
- **Evidence at current HEAD:** ARSC style law current: M3 ARSC style law 17/17 + M3 style geometry golden (6 checks) + density-matrix oracle 11/11 at 9c3dc4d1; before/after: droidify DEFAULT_BACKGROUND_ONLY -> REAL content (registry before/after).
- **Verdict:** verified current
- **Residual gap:** Generic theme-chain law (no package conditionals).

## #345 [F-NEW-168] crash-on-launch family — rc=1 NPE chains (raumballer/tictactoe-classic) + dooz rc=-11 process-death

- **Claim:** [F-NEW-168] crash-on-launch family: dooz rc=-11 SIGSEGV (process death) + raumballer/tictactoe-classic rc=1 NPE chains — DoD: no-signal law + named next frontiers.
- **Evidence at closure:** root_registry.json F-NEW-168 = OBSERVED-FAIL (WhatsApp-chain faces honestly open); S100 closure comment: dooz rc=-11 ROOT-CAUSED + FIXED (LayoutInflater::measure_raw child_sizes built before real-DEX onMeasure hook materialized views).
- **Evidence at current HEAD:** dooz determinism x3 byte-identical at 9c3dc4d1 (5/5 anchors x3 byte-identical (opencalc e364b001ee7abd66, chess b5a7a35d5fe0564b, dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8) — DETERMINISM gate only per F-NEW-233 (chess/dooz frames 100% white); graceful rc; no signal — no-signal law holds; crash_forensics last-op ring (S100 SS3) in binary.
- **Verdict:** verified current
- **Residual gap:** Classification applies to the issue's DoD (no-signal + named frontiers); the family's remaining faces stay honestly OBSERVED-FAIL.

## #347 [F-NEW-169] dooz compose-navigation NPE chain — 3 roots after rc=-11 fix

- **Claim:** [F-NEW-169] dooz compose-navigation NPE chain — 3 named roots + 2 cascades after the rc=-11 fix.
- **Evidence at closure:** closure comment at HEAD 176710b1: all 3 named roots + 2 cascades executed with commits (Handler.postAtFrontOfQueue null-receiver law; Object.getClass null via Field.get reflection family; View.getWidth null).
- **Evidence at current HEAD:** dooz runs gracefully x3 byte-identical at 9c3dc4d1; 41/41-frame runs recorded at closure.
- **Verdict:** verified current
- **Residual gap:** Crash-law closure is current; the visual frontier remains open by design of the honest 4-way Compose separation.

## #349 [S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked on null registry receiver inside ComponentActivity.<init>

- **Claim:** [S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked on R8-merged MatcherMatchResult null receiver.
- **Evidence at closure:** closure comment at HEAD 176710b1 (S104 FIX-005 / S106 re-verification) to L5; root analysis: R8 horizontal class merging; solitaire_71 face also root-caused via F-NEW-160 (DEX instance-field identity law).
- **Evidence at current HEAD:** fix laws live in the current binary (F-NEW-160 in root_registry; solitaire reaches onStart, 3-run 6588621c4a0c4182 frontier state recorded); battery 121/121 at 9c3dc4d1 with zero drift on unrelated goldens.
- **Verdict:** verified current
- **Residual gap:** REGISTRY GAP (recorded, not masked): literal id 'S102-A' is absent from root_registry.json — its laws are covered under F-NEW-160 family; cross-reference recorded by this audit.

## #350 [S102-B] compose frontier: 'CompositionLocal LocalDensity not present' — WindowRecomposer host wiring (solitaire, the real compose-runtime root)

- **Claim:** [S102-B] compose frontier: 'CompositionLocal LocalDensity not present' at WindowRecomposer host creation killed composition startup.
- **Evidence at closure:** closure comment at HEAD 176710b1: named blocker no longer occurs (windowRecomposer host laws landed).
- **Evidence at current HEAD:** LocalDensity ISE eliminated (closure evidence); Compose pipeline laws current: F-NEW-179 canonical pump + F-NEW-201 one-stable-content-object (registry IMPLEMENTED); battery compose-adjacent stages pass at 9c3dc4d1.
- **Verdict:** partial closure
- **Residual gap:** Named blocker fixed; the broader Compose visual frontier remains open — honest partial.

## #352 [S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park has no blocking semantics)

- **Claim:** [S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park family).
- **Evidence at closure:** FR-352 (TESTED/E4): LockSupport park law landed; worker spin resolved in session records (S102 wave).
- **Evidence at current HEAD:** park law live: F-074 fixture (which encodes the dooz DispatchedContinuation drained-continuation law) runs 6/6 GREEN at 9c3dc4d1; F-050 frame-pump golden PASS (pump starvation law); battery 121/121.
- **Verdict:** verified current
- **Residual gap:** REGISTRY GAP (recorded): literal id 'S102-D' absent from root_registry.json; laws covered by F-074/F-050 fixture law family + R-NEW-345 park-drain law.
