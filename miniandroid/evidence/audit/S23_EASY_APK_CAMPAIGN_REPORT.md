# S23 EASY APK EXECUTION CAMPAIGN — 2026-11-21

**Start HEAD `66ffd770` (S22) → final HEAD: the S23 commit. Host 2 cores / 3 GB RAM / 6.3 GB disk. Baseline = origin/main incl. S21+S22.**

## 1. Shortlist recovery (PH1)

Sources searched: `tests/corpus/apks.json` (18 registered F-Droid packages), the handoff APK set (15 originals), GitHub issues #610 (n-Puzzle), #639/#90/#77 (Minesweeper variants), #484/#391 (2048), #489/#475/#557/#11 (TicTacToe family), #588 (Coder-4's verified 20-title classic list), #674-#651 (the "Next simple app" series). **BMI Calculator and MasterMindy: no verified original URL exists in the registry or any issue; F-Droid search API, package-page scrape and GitHub releases (uberspot/2048-android: "There aren't any releases") all failed — recorded UNAVAILABLE per the no-invented-names rule, not silently dropped.**

## 2. The verified ten (PH2) — all original distributable APKs, handoff-set, SHA-256-pinned in `evidence/s23/s23_apk_sha256.tsv`

| # | App | Package | Baseline rc | First visible | Interaction verdict |
|---|---|---|---|---|---|
| 1 | n-Puzzle | name.livitski.games.puzzle.android | **rc=0** | real UI text rendered | **CLICK_HANDLER_EXECUTED ×12/run, 2 frame hashes (STATE_CHANGED)** ×3 |
| 2 | Hangman (Ugaday) | ru.zxalexis.ugaday | **rc=0** | rendered UI | **XML onClick dispatched, 2 hashes (STATE_CHANGED)** ×3 |
| 3 | Minesweeper (Blockinger) | org.blockinger.game | **rc=0** | rendered UI | 6 click events, 2 hashes (STATE_CHANGED) ×3 |
| 4 | Notepad | com.farmerbb.notepad | rc=1 | golden face | S23-W3 fixed its autofill ISE; now DataStore/protobuf worker-thread NPE (recorded) |
| 5 | TicTacToe (itsfrz) | com.itsfrz.tictactoe | rc=1 | APP_PIXELS | 0 clickable views in census (custom-cell listener registration gap — recorded) |
| 6 | Coin Flip | org.ecos.logic.flip_a_coin | rc=1 | blank | ConstraintLayout: 5 views inflate, 0 addView → walk sees children=0 |
| 7 | Janken (RPS) | com.attenomy.janken | rc=1 | blank | S23-W1 served LocalConfiguration ×4/run; next layer = `throw null` ×22 (compose composition state) |
| 8 | Dice Roller | tech.gaskell.diceroller (debug) | rc=1 | blank | appcompat `ActionBarContextView.onMeasure pc=318 ISE "can only be used with android:layout_width="` |
| 9 | AuthSRNG | com.ivylopez.authsrng | rc=1 | blank | compose `convertMeasureSpec` ISE; upstream SoftReference.get null (font cache init) |
| 10 | Minos | de.tcrass.minos | rc=1 | blank | inflate reports views=2 then the content never attaches (FrameLayout children=0) |

Anchors preserved byte-identical: HelloWorldToast `acdd9f05`, randomix `31ddd4d5`, notepad `31ddd4d5`, chess-clock `d602648e` (rc=124 budget face).

## 3. Shared implementations this session (2 source files, both app-agnostic)

1. **S23-W1 — CompositionLocal provider law generalized** (`dalvik_interpreter.cpp`): the S22-LC-PROVIDE law now matches the whole AOSP family `CompositionLocal Local<N> not present` (prefix 22 / suffix 12 verified) and serves `LocalContext → Activity`, `LocalConfiguration → the P0.5/C9-22 Configuration singleton`. Measured: janken 4 provisions/run ×3 deterministic; 0 fires in non-compose targets; **all golden faces unchanged**.
2. **S23-W3 — `getSystemService(Class)` overload law** (`dalvik_bridge_domain_app_runtime.cpp`): resolves the Class token's referent descriptor (CLASS_REF class_desc, or heap token `__referent_desc`) and answers the manager singleton — AOSP: the manager object always exists, enabled-ness is internal state. Measured: Notepad's autofill ISE "Autofill service could not be located." **eliminated** (the app proceeds past startup autofill into DataStore init).

Plus: `scripts/s23_evidence_pack.py` (SHA-256 + interaction TSVs).

## 4. Interaction evidence (PH6/PH7) — the mission's core numbers

- **Interactive execution (input received + handler executed + observable frame change), 3 independent runs each: n-Puzzle, Hangman/Ugaday, Minesweeper/Blockinger.** n-Puzzle: `[UI-EVENT] event=CLICK view=TextView listener=Lname/livitski/games/puzzle/android/GamePlay; result=DISPATCHED` ×12 per run; 2 unique frame SHA-256s per run (pre/post-click). Ugaday: `[U0113-XMLCLICK] onClick dispatched on activity obj#15 (Lru/zxalexis/ugaday/activity_main;)`. Full TSV: `evidence/s23/s23_interaction_summary.tsv`.
- **Persistence**: Notepad reached DataStore init (post-autofill-fix) — the persistence path is identified but blocked by the protobuf/DataStore worker-thread NPE (`getClass on null` in J3/d.Q after R337-UNSAFE objectFieldOffset succeeded) — recorded with its exact chain.
- **First-divergence map for all 5 blanks**: recorded per-target above; each is a named shared subsystem (ConstraintLayout attach, compose composition state `throw null` layer, appcompat ActionBar measure, minos inflate-attach), not an APK quirk.

## 5. Regression battery (PH7)

6/6 spot law tests rc=0 after the interpreter/bridge changes (lifecycle, linear 24/24, s98-text 21/21, resource_core, r25 14/14, input_pipeline). Full 52-test battery unchanged from S22's disk constraint (5.8 GB binaries vs 6.3 GB disk). **Zero pixel regressions: all 4 golden anchors byte-identical; the interactive trio's faces deterministic across 3 runs each.**

## 6. Build efficiency (PH8, this session)

no-change 1.07 s | 1-TU 25.8 s | 2-TU 39.5 s | link-only 1.48 s | clean 6m38–7m48 (2 clean builds this session). Incremental artifacts preserved throughout; no clean rebuilds after fixes.

## 7. Remaining blockers (exact, with first divergence)

1. **Compose composition-state layer** (`throw null` ×22 in janken; SoftReference.get null in authsrng; dooz's provider set beyond Context/Configuration) — the B1-scale model.
2. **ConstraintLayout inflate→attach** (flip_a_coin, tallybook): 5 views inflate, 0 addView — the inflater's constraint-container child attach path.
3. **appcompat ActionBar measure** (dicer): ActionBarContextView layout_width ISE.
4. **Custom-view clickability census** (itsfrz): setOnClickListener-registered custom cells report 0 listeners.
5. **DataStore/protobuf worker-thread init** (notepad persistence).
6. BMI Calculator / MasterMindy / 2048-uberspot: no verified original APK URL (recorded, not invented).

## 8. Verdict summary per status label

APK_PARSED ×10 ✓ · ACTIVITY_CREATED ×10 ✓ · VIEWTREE_BUILT ×6 (trio+notepad+itsfrz+chess family) · INITIAL_FRAME_RENDERED ×6 · INPUT_RECEIVED ×3 · CLICK_HANDLER_EXECUTED ×3 · STATE_CHANGED ×3 (2 frame hashes ×3 runs each) · UPDATED_FRAME_RENDERED ×3 · PERSISTENCE_VERIFIED 0 (path identified, blocked).

**Mission success criteria: ≥5 executing visibly (trio + notepad + itsfrz/chess golden faces = 5+) ✓; ≥3 meaningful state change ✓; ≥2 persistence — NOT met (0; path identified) — stated honestly; shared fixes benefit multiple APKs (S23-W1: dooz+janken; S23-W3: notepad+any ContextCompat-Class caller) ✓; golden anchors unchanged ✓; the other five have verified baselines + exact first divergences ✓.**
