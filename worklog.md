# MiniAndroid Campaign Worklog (multi-agent shared)

---
Task ID: 1
Agent: Super Z (main)
Task: MASTER CAMPAIGN 3 — push old commits; context-layer verify-only finalize; Dooz #1 tutorial push; Dooz #2 discovery + push; regression battery; report.

Work Log:
- Pushed all old commits with user token: main 7a172e7c..f0d101d9, archive/local-main-167c27fb + archive/local-main-d358a0c9-stale published; origin/main 0/0. S25 commit 5f7772d8 pushed after fixes.
- Context Layer verify-only: ctx update --verify PASS ×2 (incremental == full rebuild, 2.29s); smoke symbol/bm25/pack/callers/verified-absence healthy; cosmetic bare-caller CLI crash recorded, NOT developed. FINALIZED → STOP.
- Dooz #1: reproduced frontier byte-exact (193466ead8fd21d6, rc=1, IAE id-0). Closed R-NEW-324 (F-091 DEX-collection iteration protocol + F-091b host-interface dispatch gate) and R-NEW-325 (F-092 getOnBackInvokedDispatcher). Now RC=0 ×3 deterministic, zero throwables, NavHost/composition/LayoutNode tree complete. New frontier R-NEW-328 (compose measure/draw 0 canvas ops).
- Dooz #2: found UltimateTTTAndroid v2.2.2 (real tic-tac-toe, no launch tutorial) → nl.hnogame.tictactoesuperttt_20.apk. Closed R-NEW-326 (F-093/F-093b theme-backed TypedArray + gate) and R-NEW-327 (F-094 plain-text manifest). Frontier: fragment host wiring + nextPlayerView inflation (honest, open).
- Regression: battery 91/92 (pre-existing GATE H only); Hello Color golden byte-identical (11e0056320d8546d); dooz deterministic ×3; ChessClock APK missing post-reset (honest, not re-verified).

Stage Summary:
- Registry 310→315 (4 roots closed, 1 new open frontier).
- Five generic family fixes; zero regressions.
- Full evidence: docs/maintenance/worklog.md S25-MAIN.

---
Task ID: S26-MAIN
Agent: Super Z (main)
Task: MASTER CAMPAIGN 3 continuation — push old commits; R-NEW-328 attack; fresh app suite with screenshots; interactive gameplay proof; progress report.

Work Log:
- Pushed old commits first (user directive): token rotated, main 5f7772d8..2ccd9de8 published, archives 0/0.
- R-NEW-328 root-caused via compose 1.6.7 upstream sources: missing ViewGroup.drawChild law (ViewLayer draw chain silently no-oped at the framework bridge). F-095 implemented (drawChild → child real-draw dispatch + isHardwareAccelerated=false software-truth). R-NEW-329 registered (compose placement gate: root child fails isPlaced).
- Fresh suite: microtimer/gmdice/stopwatch REAL UI renders; dooz det ×3; STTT honest frontier.
- INTERACTIVE PROOF: gmdice tap 1d6 → onClick → roll() → setText → repaint ("Roll it!"), pixel-diff 108,795 sampled.
- Battery 93/94 (pre-existing GATE H only) — zero regressions. Commits c7d3131a + e77684b9 pushed.

Stage Summary:
- Registry 315→316; 5 fix families total F-090..F-095; gameplay loop proven end-to-end on gmdice.
- Next: R-NEW-329 placement pass (unblocks all Compose apps), STTT fragment host, Advanced HelloWorld.

---
Task ID: S27-MAIN
Agent: Super Z (main)
Task: MASTER CAMPAIGN 3 continuation — push old commits; 9 GitHub issues reviewed/closed; battery 93/94 → 100% (GATE H re-earned); R-NEW-329 compose placement closed (F-096 lifecycle dispatch + F-096b getMode in-place law); Telegram golden re-acquired (K-26 lifted); fresh app suite + screenshots; percentage report.

Work Log:
- Pushed old commits first: e77684b9..79874955 → origin/main, 0/0 archives.
- GitHub: issues #1-#8 closed with verification comments (evidence verified at HEAD); #9 living roadmap updated with S27 frontier comment.
- GATE H: root-caused as a stale golden — the app bakes alpha-0x99 dim into unfocused theme colors (focusedColor forces 0xFF only for focused); runtime alpha-blending is CORRECT; IoU 0.950/0.997 re-proven with dim-aware thresholds; battery 94/94 = 100% ×2.
- R-NEW-329 closed: F-096 real-DEX measure+layout lifecycle for programmatic views (AndroidComposeView.onMeasure/onLayout never ran → placement chain dead) + F-096b MeasureSpec.getMode in-place mask law (compose compares mode==0x40000000; shifted answer hit the ISE arm). Placement chains now execute (live F074/MSPEC evidence).
- R-NEW-330 registered (DepthSortedSet.remove unattached node — honest open frontier). R-NEW-331 registered (fragment-host family: STTT + Telegram shared).
- Telegram golden f5e11927… RE-ACQUIRED from the official dl (K-26 lifted); executed to ApplicationLoader.onCreate + LifecycleRegistry; frontier = fragment host. WhatsApp/TikTok Play-only (honest).
- Regression: 94/94 battery, dooz SHA 193466ead8fd21d6 ×3, stopwatch byte-identical pre/post, 3 View apps render real UI. Registry 310→318.

Stage Summary:
- 100% battery; compose lifecycle laws landed; K-26 lifted; 8 issues closed; full session record at docs/maintenance/s27_session_record.md.
- Next: R-NEW-330 attach-propagation law → real dooz frame; R-NEW-331 fragment-host law (STTT+Telegram unblock); Advanced HelloWorld.
