# LEGACY-100 — the 100 oldest open compatibility issues: audit ledger

*Generated 2026-11-12 for issue **#585**; runtime HEAD `62cd00f9+1 (S223 wave, binary 72628d05dbc8f8db)` (audit data fetched via the GitHub API the same day; states are record states, NOT fresh execution claims).*

## Method

1. The 100 currently-open issues sorted by `created:asc` were retrieved from the GitHub API (`#9` through `#115`).
2. Each record's body/labels/updated-at were parsed for its recorded compatibility state (the `State:` field of the GAME-series reports), failure-family markers, and evidence dates.
3. Each record was mapped to the #585 Stage-E state ladder and clustered by SHARED first-divergence finding, not by app title.
4. **A record state is historical bookkeeping.** Per the #585 audit rule, a label or historical screenshot is not proof of current compatibility; the `next_action` column defines the work that turns a record into evidence.

## Distribution (the one-line summary)

| Stage state | Count | Meaning |
|---|---|---|
| NOT-LOADED | 64 | no app content proven; NOT diagnosed (Stage A+B pending) |
| NONBLANK | 23 | pixels differ from background; FAIL family recorded (lower-level milestone only) |
| EXEC-CANDIDATE | 4 | older EXEC records; reproduce vs current HEAD pending |
| DONE-PENDING-REVALIDATION | 2 | body says blockers resolved; current-HEAD revalidation pending before closure |
| BLOCKED | 2 | exact blocker recorded |
| CONTROL | 1 | roadmap index |
| ACTIVE-EXECUTION | 1 | active decode/fix wave (dooz) |
| UMBRELLA | 1 | wave-tracking record |
| GRAPHICALLY-NONTRIVIAL | 1 | graphics advanced; interaction/state proof pending |
| RENDERED | 1 | app-owned content visible; visual subchecks + state proof pending |

## Ranked shared-blocker clusters (fix once, propagate to the cohort)

| Rank | Shared finding | Records | Member issues |
|---|---|---|---|
| 1 | untriaged population (#585 finding 2); Stage A+B required | 64 | #34, #35, #37, #45, #46, #48, #50, #51, #52, #53, #54, #55, #56, #57, … (64 total) |
| 2 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND shared family | 19 | #25, #26, #27, #29, #30, #31, #33, #36, #38, #41, #43, #44, #47, #49, … (19 total) |
| 3 | per-title reproduce -> Stage B first-divergence | 4 | #19, #20, #21, #23 |
| 4 | F-NEW-003 shared family | 4 | #32, #39, #40, #42 |
| 5 | stale-closure bookkeeping (#585 finding 5) | 2 | #11, #12 |
| 6 | roadmap pointer; superseded per-wave by the #585 recovery ladder | 1 | #9 |
| 7 | Compose scheduling/measure frontier (#582 S221/S222 chain) | 1 | #14 |
| 8 | Fragment/FragmentManager host family (S225 #16 row) | 1 | #16 |
| 9 | Service-launch family | 1 | #22 |
| 10 | onCreate APP-BOUNDARY-UNWIND family + image decode-vs-render (#229) | 1 | #24 |
| 11 | evidence threshold: render != interactive | 1 | #28 |
| 12 | evidence-threshold inconsistency (#585 finding 3/4) | 1 | #76 |

**Cluster 1 — F-NEW-156 (onCreate APP-BOUNDARY-UNWIND), 19 records — the largest cluster.**

This is the same family the #585 body cites via #24 (`19/25 in that wave`). The shared runtime work is ALREADY in flight and must be propagated, not re-invented:

* **S222-A laws landed** (commit `eff78882`, gate ALL HOLD): contained nested-invoke exception honesty (APP-BOUNDARY process-death records 54→0 for runtime-injected unwinds), F-023b framework-object materialization defaults (`Configuration.setToDefaults()` face on EVERY `new-instance` path — fontScale/densityDpi/orientation), S221 measure-bridge cadence law (`MINIANDROID_S222_FRAME_BRIDGE=1` = complete-render config).
* **S223 wave landed** (this audit's session, binary `72628d05dbc8f8db`, gate ALL HOLD byte-exact, test-all 27/27): NATIVE-001/JNI-001/JNI-002/BITMAP-001/ELF-001 memory+JNI laws, F-NEW-283 stale-cache removal + constructor-failure propagation (inflation honesty — the poisoned-View path the GAME-NONBLANK cohort dies through), LOG-001/003/004/005/007 stage-truth laws, CALL-001..004 trace enrichment.
* **Next:** cohort rerun of the F-NEW-156 members after the wave lands; each affected GAME record then gets its before/after delta per Stage D.

## The per-record ledger (100 rows)

| # | Title | Record state | Stage state | First-divergence signature | Shared finding | Next action |
|---|---|---|---|---|---|---|
| #9 | MASTER-ROADMAP v3 — MiniAndroid Compatibility  | — | CONTROL | n/a (roadmap issue) | roadmap pointer; superseded per-wave by  | keep as index; wave statuses live in the per-family issues |
| #11 | [EXEC] TicTacToe — APK Execution & Gameplay Pr | — | DONE-PENDING-REVALIDATION | no open blocker (body: 'Current blocker: None') | stale-closure bookkeeping (#585 finding  | revalidate vs current HEAD pin (ttt pin 7354c1b2 x3 cold run |
| #12 | [EXEC] ConnectFour — APK Execution & Gameplay  | — | DONE-PENDING-REVALIDATION | no open blocker (body: 'Current blocker: None') | stale-closure bookkeeping (#585 finding  | revalidate vs current HEAD pin (ttt pin 7354c1b2 x3 cold run |
| #14 | [EXEC] Dooz — Runtime/UI Completion | — | ACTIVE-EXECUTION | Compose post-NewGame blocker chain; S221/S222 decode wave la | Compose scheduling/measure frontier (#58 | complete-render run + pin a0fae907 BLOCKED->PASS transition |
| #16 | [EXEC] Telegram — Runtime Compatibility | — | BLOCKED | ApplicationLoader + LifecycleRegistry reached; fragment-host | Fragment/FragmentManager host family (S2 | fragment-commit pending-op drain wave (recorded next family  |
| #19 | [EXEC] FishRings — APK Execution & Gameplay Pr | — | EXEC-CANDIDATE | historical: layout/anchor or game-logic frontier | per-title reproduce -> Stage B first-div | reproduce vs current HEAD; update first-divergence evidence  |
| #20 | [EXEC] TriPeaks — APK Execution & Visual Proof | — | EXEC-CANDIDATE | historical: layout/anchor or game-logic frontier | per-title reproduce -> Stage B first-div | reproduce vs current HEAD; update first-divergence evidence  |
| #21 | [EXEC] Bouncy — APK Execution & Visual Proof | — | EXEC-CANDIDATE | historical: layout/anchor or game-logic frontier | per-title reproduce -> Stage B first-div | reproduce vs current HEAD; update first-divergence evidence  |
| #22 | [EXEC] Stopwatch — Service-Launch Family | — | BLOCKED | Tile/Service launch contract mismatch (launch family, not Ac | Service-launch family | reproduce + first-divergence trace of the Service launch pat |
| #23 | [EXEC] OPMT — APK Execution & Visual Proof | — | EXEC-CANDIDATE | historical: layout/anchor or game-logic frontier | per-title reproduce -> Stage B first-div | reproduce vs current HEAD; update first-divergence evidence  |
| #24 | S81 — REAL APP VISUAL COMPATIBILITY: audit lad | — | UMBRELLA | S81 wave: onCreate app-boundary unwind family 19/25 = domina | onCreate APP-BOUNDARY-UNWIND family + im | shared-root closure propagation: map every fixed shared law  |
| #25 | [GAME-001] com.qwde.ccm — compatibility report | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #26 | [GAME-002] com.astroloop.game — compatibility  | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #27 | [GAME-003] app.halma — compatibility report | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #28 | [GAME-004] com.jeffliu.balancetheball — compat | STATE-GRAPHICALLY-NONTRIVIAL | GRAPHICALLY-NONTRIVIAL | nontrivial graphics reached; interaction/state proof pending | evidence threshold: render != interactiv | Stage A/B re-run + interaction proof |
| #29 | [GAME-005] crypto.o0o0o0o0o.games.blackjack —  | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #30 | [GAME-006] eu.veldsoft.no.thanks — compatibili | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #31 | [GAME-007] com.simondalvai.ball2box — compatib | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #32 | [GAME-008] si.palcka.tarok — compatibility rep | STATE-NONBLANK | NONBLANK | F-NEW-003 | F-NEW-003 shared family | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #33 | [GAME-009] cos.premy.mines — compatibility rep | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #34 | [GAME-010] com.sidhant.puzzle — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #35 | [GAME-011] com.ivylopez.authsrng — compatibili | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #36 | [GAME-012] io.github.hathibelagal.mykanji — co | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #37 | [GAME-013] io.github.ebraminio.bouncy — compat | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #38 | [GAME-014] de.tobiasbielefeld.solitaire — comp | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #39 | [GAME-015] eu.quelltext.memory — compatibility | STATE-NONBLANK | NONBLANK | F-NEW-003 | F-NEW-003 shared family | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #40 | [GAME-016] com.sidhant.queens — compatibility  | STATE-NONBLANK | NONBLANK | F-NEW-003 | F-NEW-003 shared family | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #41 | [GAME-017] page.codeberg.lanticy.guandan — com | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #42 | [GAME-018] xyz.deepdaikon.quinb — compatibilit | STATE-NONBLANK | NONBLANK | F-NEW-003 | F-NEW-003 shared family | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #43 | [GAME-019] com.vayunmathur.games.solitaire — c | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #44 | [GAME-020] bim.app — compatibility report | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #45 | [GAME-021] de.schwarz.boardgamepal — compatibi | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #46 | [GAME-022] com.dash1971.maia_chess — compatibi | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #47 | [GAME-023] org.secuso.privacyfriendlybattleshi | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #48 | [GAME-024] com.kingalex.kingpong — compatibili | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #49 | [GAME-025] com.vovagorodok.blichess — compatib | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #50 | [GAME-026] io.itch.pirate_solitaire — compatib | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #51 | [GAME-027] com.dozingcatsoftware.dodge — compa | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #52 | [GAME-028] com.helddertierwelt.mentalmath — co | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #53 | [GAME-029] com.sidhant.bubbleshooter — compati | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #54 | [GAME-030] net.tigr.navyfleetbattle — compatib | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #55 | [GAME-031] com.hazelhope.dubster.hamtest — com | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #56 | [GAME-032] ca.rmen.nounours — compatibility re | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #57 | [GAME-033] com.nima.triviaapp — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #58 | [GAME-034] ru.wohlsoft.thextech.fdroid — compa | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #59 | [GAME-035] com.willie.mancala — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #60 | [GAME-036] org.lichess.mobileV2 — compatibilit | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #61 | [GAME-037] de.georgsieber.ballbreak — compatib | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #62 | [GAME-038] com.quietgrid.app — compatibility r | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #63 | [GAME-039] com.octbit.rutmath — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #64 | [GAME-040] com.galaxyrio.sudokusolver — compat | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #65 | [GAME-041] org.lufebe16.pysolfc — compatibilit | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #66 | [GAME-042] com.kaeruct.raumballer — compatibil | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #67 | [GAME-043] com.sanskritbasics.memory — compati | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #69 | [GAME-045] com.serwylo.retrowars — compatibili | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #70 | [GAME-046] org.opensurge2d.surgeengine — compa | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #71 | [GAME-047] com.eightsines.firestrike.opensourc | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #72 | [GAME-048] com.clavierhaus.gnubg — compatibili | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #73 | [GAME-049] com.sidhant.arrowescape — compatibi | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #74 | [GAME-050] com.vovagorodok.blidraughts — compa | STATE-NONBLANK | NONBLANK | F-NEW-156 | F-NEW-156 onCreate APP-BOUNDARY-UNWIND s | cohort rerun after the shared F-NEW-156 wave (S222-A laws la |
| #75 | [GAME-051] com.yepgoryo.EggReturnsHome — compa | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #76 | [GAME-052] com.rocket9labs.boxcars — compatibi | STATE-RENDERED | RENDERED | rendered frame; visual subchecks (layout/drawables/canvas) P | evidence-threshold inconsistency (#585 f | semantic state proof + interaction; do NOT count as complete |
| #77 | [GAME-053] io.github.johnathan.minesweeper — c | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #78 | [GAME-054] org.piepmeyer.gauguin — compatibili | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #79 | [GAME-055] jwtc.android.chess — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #80 | [GAME-056] org.pipoypipagames.cowsrevenge — co | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #82 | [GAME-058] com.vayunmathur.games.alchemist — c | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #83 | [GAME-059] ru.hyst329.openfool — compatibility | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #84 | [GAME-060] org.codeberg.scovillo.bubble — comp | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #85 | [GAME-061] com.towerillusion.abdal — compatibi | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #86 | [GAME-062] com.sidhant.blockblast — compatibil | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #87 | [GAME-063] org.quentin_bettoum.librememorygame | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #88 | [GAME-064] com.fairytrick.fairymahjong — compa | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #89 | [GAME-065] com.tacticmaster — compatibility re | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #90 | [GAME-066] com.joeld.minesweeper — compatibili | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #91 | [GAME-067] com.adilhanney.ricochlime — compati | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #92 | [GAME-068] com.dozingcatsoftware.cardswithcats | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #93 | [GAME-069] eu.veldsoft.scribe4 — compatibility | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #94 | [GAME-070] me.lecaro.breakout — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #95 | [GAME-071] cube.run — compatibility report | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #96 | [GAME-072] fr.arnaudguyon.spacevertex — compat | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #97 | [GAME-073] de.saschahlusiak.freebloks — compat | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #98 | [GAME-074] org.secuso.privacyfriendlymemory —  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #99 | [GAME-075] paper.loop — compatibility report | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #100 | [GAME-076] dev.serwin.AnarchRE — compatibility | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #101 | [GAME-077] com.dozingcatsoftware.mouse_pounce  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #102 | [GAME-078] com.sidhant.shikaku — compatibility | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #103 | [GAME-079] eve.game.tracker — compatibility re | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #104 | [GAME-080] com.sanskritbasics — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #105 | [GAME-081] eu.veldsoft.vitosha.blackjack — com | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #106 | [GAME-082] com.mostafa.brickblast — compatibil | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #107 | [GAME-083] com.fr.laboussole.track — compatibi | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #108 | [GAME-084] eu.mokrzycki.learndigits — compatib | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #109 | [GAME-085] com.game.asteroids_revenge — compat | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #110 | [GAME-086] paper.loop2 — compatibility report | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #111 | [GAME-087] org.pgnapps.pk2 — compatibility rep | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #112 | [GAME-088] org.secuso.privacyfriendlydame — co | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #113 | [GAME-089] com.itsfrz.tictactoe — compatibilit | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #114 | [GAME-090] nodomain.playmaker — compatibility  | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |
| #115 | [GAME-091] com.chenyifaer.fafarunner — compati | STATE-NOT-LOADED | NOT-LOADED | NOT DIAGNOSED - no first failing method recorded; recorded n | untriaged population (#585 finding 2); S | Stage A cold run x3 + Stage B first-divergence trace; cluste |

## Closure candidates (the #585 immediate batch, item 1)

* **#11 TicTacToe / #12 ConnectFour** — both bodies state the previous blockers are resolved (`Current blocker: None`). The runtime side keeps byte-exact HOLD pins for the family (`ttt 7354c1b2` ×3 cold runs on binary `72628d05dbc8f8db`, 0 uncaught exceptions — same-day evidence). Closure rule per #585 Stage E: a fresh current-HEAD acceptance run against each issue's own checklist, then close with the run linked — the ledger marks both `CLOSURE-CANDIDATE`.

## What this ledger does NOT claim

* No fresh APK execution happened for the 100 records in this audit pass (the audit is record triage, exactly as #585 allows: `This is a triage/audit of GitHub records, not a claim that all 100 APKs were freshly executed`).
* The 64 `NOT-LOADED` records are a TRIAGE POPULATION with no first-divergence evidence; they are not 64 individual bugs.
* The same-day S223 wave evidence (gate pins, 27/27 tests) covers the shared runtime laws, not per-record app acceptance.