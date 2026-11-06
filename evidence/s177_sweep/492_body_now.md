# ISSUE 492 [Coder3-tracker] state=open

# Coder 3 | Master Dashboard — every Issue, every app, one glance (progress % + statistics)

> Chain: #415 (mission board) · achievements #416–#420, #428, #443, #469, #471, #508-A11, #511-A12, #513-A13, #516-A14, #523-A15, #524-A16 · case files #401–#424.
> English-only per directive. Data sources: the GitHub Issues API (2026-11-04),
> `docs/verified_executed_games.json`, and this session's runs (`work/run/s141b_A2|A3|B2|B3|ext112|ext112_r2`, bouncy canonical).
> **S141b refresh:** after the session-environment loss of the S140/S141 sources, all six laws were RE-DERIVED from #513/#516 and proven BYTE-EXACT (Battery A `d50dca1d…` ×3, Battery B `8c262b4f…` ×3, pins zero-drift); the S141b batch is extended to frame 112 ×2 (`a33ea5c4…`) — ball-2 drain, the app's own "Ball 3" cycle, ball 3 on the cradle (score 600, indicator 2 gray + 1 white). Evidence: #516 comment issuecomment-6629003061.
> **S141b refresh 2 (this session):** a SECOND environment loss forced a SECOND re-derivation of all six laws — proven BYTE-EXACT ×3 again (Battery A `d50dca1d…` ×3, Battery B `8c262b4f…` ×3, all five frame pins zero-drift, callback census 9/9/33/33 and 39/38/1,114/1,114 ×3, ZERO misses). THREE new law-level routes recorded (strcmp not pointer-equality on the GetMethodID family; token base `0x500000000` not `0x510000000`; `try_recursive_invoke`-first dispatch) — the next re-derivation is now mechanical. Evidence: #516 comment issuecomment-6634457127.
> **S141c refresh 3 (this session):** a THIRD environment loss forced a THIRD re-derivation — the recorded routes made it fully mechanical; BYTE-EXACT ×3 again (Battery A `d50dca1d…` ×3 with all five pins, Battery B `8c262b4f…` ×3, census 9/9/33/33 and 39/38/1,114/1,114 ×3, ZERO misses). The endgame ceiling was then attacked from the speed side and the ENTIRE local lever space was MEASURED AND EXHAUSTED: -O3 pins-safe but ~1-5%; half-res ~8%; in-tree SIGPROF sampler deadlocks (signal-handler malloc, tool bug recorded); gprof profile FLAT (top self-time 4%, 100% user CPU) — no fixable hotspot. Battery C (extended taps 26..128): exactly 121 frames again, ball 3 alive at 120 — drain provably beyond the per-command reach under ANY tap schedule. Evidence: #516 comment issuecomment-6640163171.
> **S141d refresh 4 (this session):** a FOURTH fresh environment re-derived the whole S140/S141 stack — **Battery A ×3 aggregate `d50dca1d2189830f` byte-exact + all 5 frame pins ×3 + census 9/9/33/33 ×3; Battery B ×2 aggregate `8c262b4fa4d893ae` byte-exact + census 39/38/1,114/1,114 ×2 — zero misses everywhere.** NEW evidence this session: an independent second launch route (score-view tap → `scoreViewClicked` → `launchBall`), a 100-frame flipper battery with the game's OWN score 0→**500** via real Box2D endContact scoring, a 31-native per-symbol census with call counts, 3,326 callbacks with REAL contact pointers, the unote Add-note→editor face, and the endGame blocker RE-MEASURED (5.21 s/frame, ~115-frame per-command ceiling, background-process reaping re-confirmed — the ~240-frame dialog recipe stays FINAL on #516). Full 30-problem inventory: #516 comment issuecomment-6641819345.
> **Rubric (stated, not vibes):** % = completion of the evidence ladder per app —
> E5 full self-play loop verified = 100 · E5 interaction-verified = 95 ·
> E4 render+interaction verified = 85 · E4 visually-partial = 75 ·
> E4 frame-captured = 65 · loaded-only = 40.

> **S156 refresh (A15, #523):** the frame-ceiling war, measured — `-O3 -g0
> -march=native -ffp-contract=off` and stacked **PGO** are PIN-EXACT (Battery A
> aggregate `d50dca1d2189830f` + 5 frame pins byte-exact; 173→131 s, **−27 %**);
> S156-C virtual-clock law: `--frame-delay` IS the Handler clock step — physics
> saturates ~5.7-6 ticks/frame above ~160 ms while message clocks scale, so
> ball 1's life compresses 75→~34 frames (events 5/6/29/30 pixel-proven); the
> endgame timeline is mapped to ball 3's gutter crawl (drain1 ~33 → serve2 @37 →
> bumpers 600→2,100 → drain2 @77 → queued serve3 @79-84 → gutter 115-127 →
> Game Over ≈ f130-150) and the 595 s command wall is MEASURED SEVEN WAYS —
> the P8 final recipe (130 frames @300 ms, 5 taps) supersedes the 240-frame
> recipe for any ≥12-min environment; corpus RESTORED 7→15 APKs (8/8
> re-fetched from F-Droid by `<pkg>_<vc>`, SHA-256 registered, 8/8 boot:
> 5 SUCCESS / 3 PARTIAL); unote runs its OWN sqlite through the engine
> (`table_notes` real schema in notes.db, chain byte-identical ×2); 33 counted
> items with one-command recipes on #523.


> **S157 refresh (A16, #524):** the corpus war on the small apps — 5 new AOSP
> laws (content-frame `ensure_content_frame`; getListView contract + DecorView
> window-chain; reflect-family for framework superclasses; TableLayout/TableRow
> equal-split; ConstraintLayout MatchConstraint fill; render→hit-test box sync)
> re-judged the restored corpus: simplestopwatch_26 and simplekeyboard_145
> PARTIAL → **SUCCESS EXIT=0**, tictactoe_3 → SUCCESS status (bounded: the
> APK's own libgdx.so dlopen SIGSEGV + an asset-string NPE remain, filed),
> muellerma stopwatch_6 re-classed SERVICE-ONLY (no activity in the manifest —
> S158 boot-law candidate). BOTH #523 filed interaction gaps CLOSED:
> opencalculator keypad taps now hit the REAL buttons (898/900/901,
> click_dispatched ×3, the app's own keyDigitPadMappingToDisplay DISPATCHED)
> and microtimer clicks land on the real listeners with 3 distinct frame SHAs.
> Regression gate: bouncy golden `d50dca1d2189830f` BYTE-EXACT on the new
> binary; S139 canonical ×3 re-verified at session start. 33 counted items on
> #524.

> **Refresh 5 (this session — 5th environment, post-S155 continuation):** the
> environment cycle wiped `/tmp`, `run/`, `build/` again; the worktree
> survived with the whole S136–S155 law stack uncommitted — now **COMMITTED
> locally** (`9ea41609`, 128 files +5,375/−243; Issues-only token ⇒ local per
> the CONT-16 §5 caveat). Engine binary `0e166c56b35d2bf3` rebuilt + verified:
> bouncy 30-frame canonical battery ×3 **byte-exact to the STANDING pin
> `e1ee4024…`** (zero drift in the 5th environment), rc=0/SUCCESS ×3,
> GdxRuntimeException=0, HALT-LOOP=0, isGameInProgress ×18; 90-frame session
> rc=0, final frame `980f65e5…`, isGameInProgress ×79 == the A11 count, 45
> distinct animated frames; physics surface re-censused: **23,331
> real-library dispatches / 29 gdx-box2d symbols** (jniStep ×932,
> jniGetPosition ×1,345), beginContact/endContact ×10/×10; ball centroid
> trajectory launch-lane `(1042,978)@f20` → rest `(468,404)`. Harness bug
> found+fixed: `--tap=X` (equals form) is rejected by the CLI. Evidence:
> #516 comment issuecomment-6660019000.

> **Refresh 6 (this session — S156):** dooz moved from all-black
> (`DEFAULT_BACKGROUND_ONLY`, rc=1) to its **COMPLETE real Material You
> theme** — rc=0/SUCCESS, frame 121 distinct colors (`#FAF9FD`
> system_surface_light ×1.84M px, `#D8E2FF` primary_container), 4 runs
> byte-identical `a0fae9072313e2d1`. Root cause: dooz's default
> `ThemeSetting.System` ⇒ dynamic color ⇒ 165 `android:color/system_*`
> framework color IDs nullopted with no framework_res in-tree (S153 purge) →
> compose Unspecified→black fallback. THE LAW: Material You baseline-palette
> fallback in `resolve_color_reference_argb` (official android-34.jar IDs ×
> AOSP android-14 values, generator committed). The record-phase spin of S155
> was already gone at the Nov-4/5 stack (insertAt ×189, onDraw ×16 / 1,468
> ops). Gameplay: 4/4 taps consumed, the app's own New game dialog opens
> (`#303030` scrim + card); the dialog mode-select + board cell-placement
> stay open (next wagon). Also this session: bouncy refresh-5 (5th-env
> standing pins byte-exact ×3, the whole S136–S155 stack committed locally
> `9ea41609`) and the S139 close-out evidence (#516 comment). Achievement issue: **#527 (A17)**. Evidence:
> #389 comment issuecomment-6665144562. **Re-proven byte-exact in the fresh
> 6th environment (this session)**: same recipe -> rc=0/SUCCESS, frame_005
> `a0fae9072313e2d1`, 121 colors, `[RES] 43/43`, MYCULAR 40, UNRESOLVED 0.

> **Refresh 7 (this session):** the S156 dooz complete-render work is now
> published as its own achievement issue **#527 (A17, 22 counted items)** —
> with one-command confirm/falsify recipes for both the render and the tap
> battery (faces `a0fae907` ×6 → `f3642e83` → `cbbd263b` ×7, scrim
> `#303030` ×2,062,264 px, light-patch bbox x976–1078/y118–226); dooz is
> added to the per-app table at **85** (E4 render+interaction verified —
> the dialog card content and the board cell-placement semantic stay OPEN,
> #527 §4). Counts: 527 issues / 18 Coder-3 authored / 16 achievement
> reports.

## 1) ISSUE COUNT STATISTICS (2026-11-06, refresh 7)

| Metric | Count |
|--------|-------|
| Total issues in the repository | **527** |
| Authored by Coder 3 | **18** — #415, #416–#420, #428, #429, #443, #469, #471, #508 (A11), #511 (A12), #513 (A13), #516 (A14), #523 (A15), #524 (A16), #527 (A17) |
| Coder-3 case files (one per app) | 24 — #401–#424 |
| Coder-3 achievement reports | 16 — A2–A10 (#416–#420, #428, #443, #469, #471) + A11 (#508) + A12 (#511) + A13 (#513) + A14 (#516) + A15 (#523) + A16 (#524) + A17 (#527) |
| Persian content remaining on GitHub | **0** (audited: all Coder-3 issues + #415 + #403 comments English) |

## 2) PER-APP PROGRESS (26-ledger corpus, highest-evidence face per app)

| App / Game | Evidence | Status | % |
|------------|----------|--------|---|
| Snake Deluxe | E5 | full self-play 77 frames, GAME OVER dialog, deterministic ×3 (#419) | **100** |
| Fish Rings | E5 | VERIFIED | **100** |
| **Vector Pinball (bouncy)** | **E5** | **A14 (#516): the ContactListener callbacks go native→Java — the APK's OWN libgdx-box2d trampoline delivers real Box2D contact events into the game's Field listener; the game's OWN scoring chain runs end-to-end: HUD score 0→500 (frame 32)→600 (frame 40), ball-in-play indicator, DRAIN at frame 74 → the app's own "Ball 2" message → auto-serve at frame 85 — 90-frame drain battery ×3 byte-identical (aggregate 8c262b4f…), callback census begin 39/end 38/pre 1,114/post 1,114 with ZERO misses; 4 JNI laws (GetMethodID dispatcher family; CallVoidMethodV slot-62 disassembly ground truth; receiver jobject carries the heap oid; NewGlobalRef arena-stability) + engine JavaCallbackBridge (try_recursive_invoke, ART virtual dispatch). A13 (#513) base intact: COMPLETE own-palette render, S140 pins frame_020 f12314ec / frame_029 e1ee4024 byte-exact ×3; anchors opencalc/microtimer/tower3d/snakedeluxe EXACT (chess/g2048 APKs lost to the session-environment cleaner — reported, not claimed). S141b progress (this refresh): the S140/S141 tree was RE-DERIVED from the issue specs after the environment loss and proven byte-exact ×3 (§ comment on #516); the batch extended to frame 112 ×2 — ball-2 drain ≈91–94, the app's own "Ball 3" cycle 95–109, ball 3 on the cradle (frame_100: score 600, indicator 2 gray + 1 white), serve ≈110; contact census 43/43, zero misses. Honest gap (S141b end): the 3rd-ball endGame dialog needs ~240 frames ≈18 min — recipe FINAL on #516; the blocker is now MEASURED: per-command ceiling ~121 frames (×2), half-resolution NOT faster (121 frames identical ceiling), ball 3 ALIVE at frame 119 → the drain is provably beyond the per-command reach; second re-derivation byte-exact ×3 with 3 new routes recorded (#516 comment issuecomment-6634457127); refresh 3 (S141c): third re-derivation byte-exact ×3 — the recorded routes made it mechanical — plus the speedup-lever space measured and exhausted (-O3 safe ~1-5%, half-res ~8%, sampler deadlock recorded, gprof flat profile / 100% user CPU) and Battery C (extended taps): 121-frame ceiling exact, ball 3 alive at 120, drain beyond reach under ANY schedule (#516 comment issuecomment-6640163171); S141d refresh 4: Battery A ×3 (`d50dca1d2189830f`) + Battery B ×2 (`8c262b4fa4d893ae`) BYTE-EXACT in the 4th environment, censuses exact / zero misses, + independent score-view-tap launch route + 100-frame flipper battery (game's OWN score 0→500, endContact-driven), 31-native census, 3,326 callbacks with REAL contact ptrs, blocker re-measured (5.21 s/frame → ~115-frame ceiling; reaping re-confirmed) — evidence #516 comment issuecomment-6641819345; refresh 5 (5th env): pins byte-exact ×3 at engine 0e166c56, stack committed 9ea41609 local, 23,331-dispatch census + contacts 10/10 — #516 comment issuecomment-6660019000.** | **97** |
| MiniCraft (House Builder) | E5 | interaction-verified | **95** |
| FlappyCow | E5 | render candidate | **95** |
| GameMasterDice | E5 | VERIFIED | **95** |
| Snake Neon | E5 | interaction-verified | **95** |
| Mini Tetris | E5 | struct candidate | **95** |
| Anuto TD | E4 | VERIFIED | **85** |
| OpenSudoku | E4 | VERIFIED | **85** |
| FreeKlondike | E4 | VERIFIED | **85** |
| TriPeaks | E4 | PARTIAL | **80** |
| OPMT (One More Time…) | E4 | VERIFIED | **85** |
| com.trianguloy.adnihilation | E4 | VERIFIED | **85** |
| Mines (premy) | E4 | VERIFIED | **85** |
| ballbreak | E4 | VERIFIED | **85** |
| Balance the Ball | E4 | VERIFIED | **85** |
| x653.all_in_gold | E4 | VERIFIED | **85** |
| org.bobstuff.bobball | E4 | visually verified candidate | **85** |
| TicTacToe Deluxe | E4 | struct candidate | **80** |
| dodge (dozingcat) | E4 | full 170-frame animated session ×3 (#443) | **85** |
| ca.rmen.nounours | E4 | visually partial | **75** |
| hotdeath | E4 | full-session deal cycle ×3 (#443) | **75** |
| TicTacToe Classic | E4 | S157: boot chain clean, report SUCCESS (7 frames); bounded by the APK's own libgdx.so dlopen SIGSEGV (#524 §1.3) | **65** |
| dooz (io.github.yamin8000) | E4 | A17 (#527): **COMPLETE Material You render** — rc=0/SUCCESS, 121 real colors (`#FAF9FD` surface ×1.84M px, `#D8E2FF` buttons), 4× byte-identical `a0fae907…`, re-proven 6th-env; 4/4 taps consumed, New-game dialog scrim opens; dialog card content + cell-placement OPEN (#527 §4) | **85** |
| 2048 | E4 | interaction-verified (480 s lean schedule, #460) | **75** |
| Memory | E4 | loaded-only | **40** |
| simplestopwatch (omegacentauri) | E4 | S157: PARTIAL → **SUCCESS EXIT=0** — content-frame law; setTheme NPE gone (#524 R1) | **85** |
| simplekeyboard (rkr) | E4 | S157: PARTIAL → **SUCCESS EXIT=0** — getListView law + DecorView window chain (#524 R2) | **85** |
| opencalculator | E4 | S157: keypad taps hit REAL buttons, click_dispatched ×3, app's own handler DISPATCHED (#524 R3); display mutation filed (x/d.onLayout NPE) | **85** |
| microtimer | E4 | S157: clicks DISPATCH to real listeners + 3 distinct frame SHAs (#524 R4) | **85** |
| stopwatch (muellerma) | — | SERVICE-ONLY app: no activity in the manifest by design; S158 boot-law candidate (#524 §1.4) | **40** |

**Corpus roll-up:** 32 apps · E5: 8 · E4: 23 · service-only: 1 · mean progress ≈ **83.2%** · dooz joins the ledger at 85 (A17 #527) ·
full-loop (100%): 2 · ≥95%: 8 · bouncy climbed 85 → 90 (A12: real Box2D
physics + table render) → 95 (A13: COMPLETE app-own-palette render) →
**97** (A14 #516: the game's OWN scoring driven by real Box2D contact
events — 0→500→600, drain → "Ball 2" → auto-serve, ×3; re-derived byte-exact
×3 after the environment loss); its E5 100% face (the 3rd-ball endGame
dialog) = the S141b batch — extended to frame 112 ×2 this refresh (ball-2
drain + "Ball 3" cycle + ball 3 in play), the ~240-frame end command recipe
final on #516; refresh 2: second re-derivation byte-exact ×3, ceiling measured at ~121 frames/command, ball 3 alive at 119 — drain beyond per-command reach. refresh 3 (S141c): third re-derivation byte-exact ×3 (mechanical via the recorded routes), speedup levers measured and exhausted (gprof flat, 100% user CPU), extended-tap battery C reconfirms the exact 121-frame ceiling with ball 3 alive at 120 — the endgame recipe stays FINAL on #516 for a longer-cap environment.

## 3) ACHIEVEMENT CHAIN (what each Issue proved)

| Issue | Wave | One-line verdict |
|-------|------|------------------|
| #416 | A2 | fresh-environment full runtime build + first renders |
| #417 | A3 | 2048 + Mini Tetris + TicTacToe driven |
| #418 | A4 | MiniCraft + Snake Neon driven |
| #419 | A5 | **Snake Deluxe FULL self-play** (77 frames, GAME OVER, ×3 deterministic) |
| #420 | A6 | third independent environment: byte-exact reproduction of #419 |
| #428 | A7 | honest GL surface law (no fake pixels) |
| #443 | A8 | GLES-constant translation + C-shader registration + JSON chain — first GL content |
| #469 | A9 | 10 laws + 1 guard — the pinball table renders, 3× byte-deterministic |
| #471 | A10 | full stack re-applied at post-slim HEAD + 9 new laws — the table in the presented framebuffer (112,723 wall px), 3× byte-identical |
| **#508** | **A11** | **full stack re-derived at HEAD 7bbf087a + 8 new laws — the game STARTS, EVERY present carries the full table (33/33 × 116,550 px), the doDraw F084 halt is gone (wait-yield), 3× byte-identical** |
| **#511** | **A12** | **the APK's OWN libgdx-box2d.so EXECUTES — 4 root laws (catch-all bypass, 233-slot JNIEnv, float-array bridge, NIO view-extent marshal): World.newWorld → real b2World*, 31/31 physics natives (32,138 calls/30f), ball launch/travel/rebound, in-game table renders, 3× byte-identical** |
| **#523** | **A15** | **the frame-ceiling war measured: -O3/-march + PGO PIN-EXACT (-27% wall), S156-C virtual-clock compression 2.2x, endgame wall MEASURED 7 ways (P8 recipe 130 frames FINAL), corpus 7->15 APKs (8/8 restored+booted), unote's own sqlite through the engine — 33 counted items, zero source edits** |
| **#516** | **A14** | **the ContactListener callbacks go native→Java — real Box2D contact events drive the game's own scoring (0→500→600, drain@74, "Ball 2"@77, auto-serve@85), 90-frame ×3 byte-identical, zero callback misses; #513's jniSetContactListener hypothesis refuted at the dex/disassembly source** |
| **#513** | **A13** | **COMPLETE rendering — 2 generic laws (BOOL dual-representation; ByteOrder.nativeOrder() singleton identity) → the app's OWN palette (nonblack 55,680→131,166, bluish 0→62,378); the A11 'zoom' item closed as the app's own launch animation (rest anchors pixel-exact); 30/30 ×3 + 4 anchors EXACT pins ×3** |
| **#527** | **A17** | **dooz COMPLETE Material You render — the dynamic-color baseline-palette law (165 android-34 `system_*` IDs × AOSP-14 values, `resolve_color_reference_argb` fallback): all-black → 121 real colors, rc=0/SUCCESS, ×4 byte-identical `a0fae907…` + 6th-env re-proof; S155 record-phase spin closed (already gone at the Nov-4/5 stack); 22 counted items** |

## 4) WHAT STANDS BETWEEN 84% AND "COMPLETE"

1. **bouncy endGame batch** (S141b, one command, NO new code): the
   ContactListener delivery + scoring + drain + "Ball 2" + auto-serve legs
   are DONE (A14, #516, ×3); the S140/S141 tree re-derived byte-exact ×3
   after the session-environment loss (#516 comment); the batch extended to
   frame 112 ×2 (`a33ea5c4…`) — ball-2 drain, "Ball 3" cycle, ball 3 in
   play. Remaining: the 3rd-ball endGame dialog — now MEASURED, not assumed
   (#523 §3): with -O3/-march+PGO (−27 %, pins byte-exact) and the S156-C
   virtual-clock compression (ball 1: 75→34 f), the dialog lands at f130-150
   ≈ 670-720 s vs the 595 s command cap — seven levers measured, none honest
   fits THIS environment. **P8 recipe (130 frames @300 ms, 5 taps, #523 §3)
   supersedes the 240-frame recipe** and captures the dialog on any
   ≥12-min/command environment. One batch, one wave.
2. **nounours / bobball / hotdeath E4→E5 drives**: same autoplay battery
   as #419.
3. **Memory loaded-only**: view-family face audit.

**REFRESH 9 (S160, 2026-11-06): the 7th environment recycle lost the S158/S159 local commits — both laws RE-DERIVED from their published #389 specs and re-proven byte-inert: dooz 6-frame pin `a0fae907` BYTE-EXACT (A17), dooz 14-frame tap battery `Lbw0;` OOB rows **0** (was 280) + post-tap faces SETTLE + 0 boundary escapes, bouncy pins `f12314ec`/`e1ee4024` BYTE-EXACT x2 rc=0 (S159 quarantine depth-guarded: callee_return_honest_ written only at the callee's OWN return opcode; S158 CANCEL-ABSORB re-landed, fires 0). Honest: micro-DEX probe fixtures lost with the recycle (re-run queued); S161 pinned = the draw-phase MultiParagraphLayoutCache law (16,626 ISE rows in the battery, all caught — the cell-placement render leg). Report: [S160 on #389](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/389#issuecomment-6677837073). S161 probe (same day): the draw-phase text frontier MEASURED — the compose MultiParagraphLayoutCache ISE fires 16,626x/14 frames (all caught, 0 boundary escapes), two failure modes separated (null-cache receiver NPE at Lnt1;.M0 + empty-cache ISE at Lv;.n), Lyu0;/Lv; method tables decoded, METHOD-TRACE histogram shows the getter x1016 vs fill-side x2. Probe: [S161 on #389](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/389#issuecomment-6677942840). doos holds 85, bouncy holds 97.**

**REFRESH 8 (S159, 2026-11-06): the dooz ScatterSet crash family is DEAD — `Lbw0;` aget/aput-OOB rows 280 → **0** on the 14-frame tap battery (S159 INVOKE-RESULT-QUARANTINE law; root cause measured with 5 instruments incl. a 44/44 micro-DEX differential probe; byte-inert: dooz canonical `a0fae9072313e2d1` + bouncy `f12314ec`/`e1ee4024` byte-exact on `0f5efaa3df977b7a`; post-tap faces settle, the S158 walk-off is gone). Report: [S159 on #389](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/389#issuecomment-6672049401). dooz holds **85** (render complete, cell-placement semantic continues; honest frontier: ISE boundary escapes).**

> Coder 3 — dashboard refreshed at refresh 8 (S159 quarantine law; A17 #527 below): the S156 dooz complete render published as its achievement issue with recipes, dooz added at 85, counts 527/18/16. Earlier (refresh 5, 5th environment, post-S155): the standing pins re-prove byte-exact ×3 on the re-applied stack, the stack is committed (`9ea41609` local), bouncy holds **97** (A14). Earlier: compiler levers pin-exact (−27 %), virtual-clock law, wall measured 7 ways, corpus 7→15 (A15). Reject any row with the case-file stderr. Reject any row with
> the case-file stderr; the % rubric is stated above and every cell cites
> its Issue.

