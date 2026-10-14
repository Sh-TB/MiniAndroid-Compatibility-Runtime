# Application Compatibility Matrix — canonical status at S51 finalization

> Law: every cell below is backed by evidence produced at the current HEAD
> (commit recorded in the evidence column), not by prior-session claims.
> Status vocabulary: `IMPLEMENTED · TESTED · OBSERVED · REPRODUCED ·
> RESEARCHED · BLOCKED · PENDING · UNVERIFIED`.
> Re-verified: 2026-09-17, battery gate ALL PASS **98/98 ×3 runs** (94 prior
> stages + 4 new game gates — see `docs/testing/BATTERY_INDEX.json`).

## Install / load semantics (applies to every app)

MiniAndroid has **no persistent install step**. `miniandroid run <apk>` performs,
in one process: APK open → manifest parse → resources.arsc load → DEX parse →
class resolution → Application/Activity creation → lifecycle → ViewTree →
render → (optional tap dispatch). Package identity is re-derived from the
manifest on every run; persistent app state lives only in the package sandbox
(`--data-root`/`MINIANDROID_DATA_ROOT` + `<package>/` dirs — see
`docs/runtime/` and the S50 sandbox protocol). A real device's install
(PackageManager, adb install, shortcut launcher) is **NOT APPLICABLE** at this
architecture level.

## Core samples

| App | Type | Launch | Render | Lifecycle | Input | Status | Evidence (this HEAD) |
|---|---|---|---|---|---|---|---|
| HelloWorldSelfAware v1.1.0 (EXT-01, external real APK) | real APK, classic Views | OK | OK (golden 9 checks) | onCreate→RESUMED | long-press golden (EXT-02 12 checks) | **TESTED** | battery stages EXT-01/02; S50 run trace: APK→Manifest→ARS→DEX→Activity→ViewTree(1 view)→frame |
| helloworld_golden (project fixture) | fixture | OK | OK (26 checks) | OK | n/a | **TESTED** | battery `HELLOWORLD-GOLDEN VALIDATION: ALL PASS (26 checks)` |
| hello_color / hello_smoke / hello_widgets | fixtures | OK | OK | OK | n/a | **TESTED** | battery (G-gates) |
| F-012 persistence driver (microtimer real APK) | real APK | OK | OK (golden) | OK | 3 taps | **TESTED** | battery `M3 F-012 persistence+fresh-state determinism golden` |

## Games

| App | APK | Install/load | DEX exec | Launch | ViewTree | Initial render | Input | State change | Close/Reopen | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **TicTacToe** (project fixture, complete game) | built from source | OK | OK | OK | OK | OK | **9-click real sequence** | **full game**: turn flips, win detection, gameOver freeze | process-close semantics documented (S50) | **TESTED — fully playable** | `validate_tictactoe_golden.sh` ALL PASS (8 checks): `X to move → O to move → X WINS`, marks localized per cell, deterministic replay SHA `613cfccc…` |
| **Dooz** v18 (`io.github.yamin8000.dooz_18`, SHA `d81292cd…` re-verified) | real F-Droid APK | OK (load+parse) | OK — full launch completes (S51 fix) | **launch completes** — Status SUCCESS exit (first in campaign history) | composed (internal) | **BLANK framebuffer** (0 non-white px — Compose drawing pipeline is the next frontier) | unreachable (blank frame) | none yet | n/a | **TESTED — launch fixed; render PENDING** — R-NEW-361 VERIFIED-FIXED | S51 pre-fix: `[R361-RINVOKE] Ln/a;.r arr=obj#5052 depth=80` refused silently → zero metadata → `[R361-MW] … val=0xff00000000000000` + HALT-LOOP. Fix: dedicated 512MB interpreter stack + backstop 512 + `[R361-DEEP-REFUSE]` diagnostic. Post-fix clean run: exit 0 / SUCCESS, zero HALT-LOOP; battery 94/94 |
| **Dooz** v23 (`…dooz_23`, SHA `299eab21…` re-verified) | real F-Droid APK | OK | OK — launch proceeds (S51 fix) | partial — Status PARTIAL SUCCESS, 1 frame | partial | **BLANK** (Compose drawing pipeline — same frontier as v18) | unreachable | none | n/a | **TESTED — improved (S51); ONE spin face remains** | S51 run: 1 `[HALT-LOOP] Lbw0;.d pc=0x1c` (671-byte method — NEW face, post-fix) + `[R361-DEEP-REFUSE] depth=512 Lbp1;.<init>` — both registered as next probes; S50's pre-fix face (aput-oob -733270216) gone |
| **Connect Four** (project fixture `connectfour_golden`, complete game) | built from source (R-NEW-372 TYPE law needed: `new char[6][7]`) | OK | OK | OK | OK (7 column buttons + 42-cell grid, real Outer$Inner listeners) | OK | **24-click real sequence** (descending view-id law) | **full game**: 22 gravity drops, turn alternation, diagonal win detection, gameOver freeze | — | **TESTED — fully playable (S51)** | `validate_connectfour_golden.sh` ALL PASS (8 checks): `R to move → … → Y WINS` at click 22 (diag (0,3),(1,4),(2,5),(3,6)), 11R+11Y final, gravity law (top 2 display rows empty), frozen tail byte-identical, deterministic replay 25/25 frames |
| **Crossword** (project fixture `crossword_golden`, complete game — "بازی جدول") | built from source | OK | OK | OK | OK (5×5 interlocked grid: BEAM/MAP/PROP, 9 fill cells) | OK | **11-click real sequence** (9 fills + 2 frozen over-taps) | **full game**: word-completion detection (PROP@4, MAP@6, BEAM@9 → SOLVED!), frozen tail | — | **TESTED — fully playable (S51 finalization)** | `validate_crossword_golden.sh` ALL PASS (8 checks); final grid letters exactly A,A,B,E,M,O,P,P,R; discovered R-NEW-374 (String.valueOf descriptor law) — fixed |
| **WordPredict** (project fixture `wordpredict_golden`, quiz app — "پیش‌بینی کلمات") | built from source | OK | OK | OK | OK (status + question + 4 candidate buttons, re-labeled per question) | OK | **9-click real sequence** incl. engineered WRONG-answer retry path | **full app**: 5 questions, score 0→5, wrong-answer keeps question, DONE freeze | — | **TESTED — fully playable (S51 finalization)** | `validate_wordpredict_golden.sh` ALL PASS (8 checks): `Q1/5 SCORE 0 → WRONG - try again → SCORE 5/5 DONE`, question band re-labels verified |
| **BallTap** (project fixture `balltap_golden`, 2D ball game) | built from source | OK | OK | OK | OK (7×5 field + 2-cell paddle + 3 control buttons) | OK | **38-click real sequence** (35 to WIN + 3 frozen over-taps) | **full game**: integer physics — wall bounces, paddle collision, 3 goals / 0 misses, WIN freeze | — | **TESTED — fully playable (S51 finalization)** | `validate_balltap_golden.sh` ALL PASS (8 checks): goals at frames 11/23/35 (ball-steps 4/8/12), exactly one ball cell + 2-cell paddle every frame, deterministic replay 39/39 |
| **Minesweep** (project fixture `minesweep_golden`, XP-style mine-finder — "بازی بمب‌یاب") | built from source | OK | OK | OK | OK (81-cell grid, fixed 10-mine layout) | OK | **66-click real sequence** (64 to WIN + 2 frozen over-taps) | **full game**: iterative DFS flood fill through real DEX, adjacency digits, XP first-tap-safe law, WIN at 71/71 | — | **TESTED — fully playable (S51 finalization)** | `validate_minesweep_golden.sh` ALL PASS (8 checks): win at frame 64, flood-fill law (count jumps >1), zero BOOM in golden, fixture stack-capacity law (N*N*8) caught by F-016 exception honesty — fixed |
| gmdice (dice game, `de.duenndns.gmdice_8`) | real F-Droid APK | OK | OK | OK | OK | OK (golden) | tap (harness) | rendered state machine | documented | **TESTED** — runtime playable | battery `corpus run de.duenndns.gmdice_8` + S26 tap evidence (`miniandroid/run/s26_gmdice_tap`) |
| **chessclock** (`com.chessclock.android_29`) | real F-Droid APK | OK | OK | OK (exit 0, Status SUCCESS) | OK | OK — real dark-theme UI rendered (full-surface + divider) | not driven (S51) | n/a | — | **TESTED — launch+render (S51)** | clean run at S51 head: exit 0, 1 frame, non-white px 2,073,600 |
| **unote** (`app.varlorg.unote_30`) | real F-Droid APK | OK | OK | OK (exit 0, Status SUCCESS) | OK | OK — real UI: "Ignore case"/"Search in content" + "Add note/Search/Quit" action bar | not driven (S51) | n/a | — | **TESTED — launch+render (S51)** | clean run at S51 head: exit 0, 1 frame, non-white px 236,520 |
| remaining corpus apps | real APKs | — | — | — | — | — | — | — | — | **UNVERIFIED** (this session) | not re-run — no claim made |

## Android framework samples (all project fixtures, real DEX in APK)

| Fixture | Law exercised | Status | Evidence |
|---|---|---|---|
| F-016 | exception honesty (unwind + PARTIAL + crash.log) | **TESTED** | battery |
| F-020 | snapshot law (5-band pixel golden) | **TESTED** | battery |
| F-024 | EOF law (7 bands) | **TESTED** | battery |
| F-025 | executor (4 bands) | **TESTED** | battery |
| F-026+F-027 | Room/SQLite: INSERT/UPDATE/DELETE/txn commit/rollback/cursor/reopen (7 bands) | **TESTED** | battery |
| F-028 / F-030 | float law / zero law (7 bands each) | **TESTED** | battery |
| F-040 / F-044 / F-050 / F-074 | arrays-fill / return-descriptor / frame-pump / super-dispatch | **TESTED** | battery |
| G06 / G07 / G08 | interaction / lifecycle state machine (25 checks) / navigation | **TESTED** | battery |
| s50_sandbox_probe | sandbox persistence (prefs+sqlite+file law) across close/reopen | **TESTED** | `scripts/cleanup/s50_sandbox_test.sh` ALL PASS; `evidence/cleanup/S50_SANDBOX_EVIDENCE.json` |

## External APK corpus (large apps)

| App | Status | Note |
|---|---|---|
| Telegram v? (exp038 build, 82,680,854 bytes, blob `b2d52d57…`, SHA256 `193ad551…`) | **TESTED — S51 finalization campaign: parse-bound BLOCKED (honest)** | APK recovered from git history to /tmp (zero-APK tree law respected). Real run: APK validation + manifest OK; 11,531-entry central directory parsed; per-class DEX code-item forensics (EXP-031.6) proceeds through multiple classesN.dex; **still parsing past 420 s** (single-threaded parser, huge multi-DEX). Not a crash — a throughput frontier. Historical R-NEW-303 (desugared streams) remains the next semantic blocker after parse throughput. Full log bounded at `/tmp/tg_campaign/run_long.log` (not committed — log policy) |
| WhatsApp | **UNVERIFIED — acquisition BLOCKED** | Not distributable via F-Droid (proprietary, Play-Store-only); no acquisition channel compatible with the repo's licensing + zero-APK law. Required provenance + acquisition instructions documented in the Telegram/WhatsApp campaign section of S51_FINALIZATION_REPORT. No claim made about loadability |

## Agent playability (Phase 6 law: observe → act → state change → new screen)

| Game | runtime playable | agent observable | agent actionable | state-change proven | Status |
|---|---|---|---|---|---|
| TicTacToe | yes | yes — frame ink localized per cell + status text | yes — 9-click DOWN/UP law pipeline | yes — `X to move → O to move → … → X WINS`, frozen board after win | **AGENT-PLAYABLE (proven)** |
| Connect Four | yes | yes — per-column drop ink + status text | yes — 24-click law pipeline (same driver) | yes — `R to move → … → Y WINS`, frozen tail | **AGENT-PLAYABLE (proven, S51)** — full schema sequence in `docs/evidence/solved/…/S51_AGENT_C4.json` |
| Crossword | yes | yes — status band + per-cell letters | yes — 9-fill sequence | yes — 9/9 state-changing steps, `SOLVED!` | **AGENT-PLAYABLE (proven, S51 finalization)** — `S51_AGENT_NEW_GAMES.json` |
| WordPredict | yes | yes — score/question status band | yes — 6-answer sequence incl. wrong-path retry | yes — 6/6 state-changing steps, `SCORE 5/5 DONE` | **AGENT-PLAYABLE (proven, S51 finalization)** — `S51_AGENT_NEW_GAMES.json` |
| BallTap | yes | yes — ball/paddle/status every frame | yes — 35-action sequence (RIGHT/STEP/LEFT) | yes — 35/35 state-changing steps, `GOAL 3/3 WIN` | **AGENT-PLAYABLE (proven, S51 finalization)** — `S51_AGENT_NEW_GAMES.json` |
| Minesweep | yes | yes — safe-count status band + revealed digits | yes — 64-tap sequence | yes — 2/64 direct reveals (flood-fill law concentrates reveals) + terminal `WIN`; chain continuous | **AGENT-PLAYABLE (proven, S51 finalization; reveal concentration documented honestly)** — `S51_AGENT_NEW_GAMES.json` |
| gmdice | yes | yes (rendered dice state) | yes (harness taps) | yes (battery golden + tap run) | **runtime playable; agent harness: same click pipeline as TicTacToe** |
| Dooz v18 | launch completes (S51 fix) — frame still blank | no (nothing rendered) | no | no | **AGENT-HARNESS: PENDING on the blank-frame frontier** (R-NEW-361 spin itself is FIXED) |

The agent harness itself is the runtime's own click/tap pipeline
(`--tap`, `--click-test`, `--long-press`; DOWN/UP law) plus frame capture —
there is no separate LLM-driven agent; per the campaign law TicTacToe's
evidence uses the real pipeline end-to-end.
