# ISSUE 523 [Coder3-A15] state=open

> Chain: #415 (master board) · #416-#420 (A1-A6) · #428 (A7) · #443 (A8) ·
> #469 (A9) · #471 (A10) · #508 (A11) · #511 (A12) · #513 (A13) · #516 (A14) ·
> case file #403. Governing law: **no fake success** — every number below is
> from this session's own runs (dirs `/tmp/s156_A1`, `/tmp/e2a_A1`, `/tmp/pgo_A1`,
> `/tmp/p2_natural`, `/tmp/p3_cycle`, `/tmp/p4_vfast`, `/tmp/p5_endgame`,
> `/tmp/p6_300`, `/tmp/p7_endgame`, `/tmp/p8_final`, `/tmp/unote_chain{1,2}`,
> `/tmp/calc_*`, `/tmp/mt_*`, `/tmp/dooz_s156`, `/tmp/boot_*`; every recipe
> reproduces in one command). Issues remain the ONLY channel. **33 counted
> session items** (§5). Environment: 5th re-derivation environment (HEAD
> `be9329bb`, working tree 12,401 M + 2 untracked paths INTACT, binary
> build-current at session start).

---

## 0) THE RESULT (one glance)

1. **The per-command frame ceiling was attacked with the two compiler levers
   the recorded lever table had NOT measured — and BOTH are pin-exact.**
   `-O3 -g0 -march=native -ffp-contract=off` = **−21 %** wall (141 s vs the
   recorded ~173 s for Battery A); stacking **PGO** (instrumented build →
   2 profile runs → `-fprofile-use`) = **−27 % cumulative** (131 s, 3.80 s/frame
   at 200 ms cadence). **Battery A aggregate `d50dca1d2189830f` and all five
   frame pins are BYTE-EXACT under both builds** — the speed is honest and the
   determinism law survives the optimizer.
2. **The virtual-clock law (S156-C): `--frame-delay` is the Handler virtual
   clock STEP** (`main.cpp` `--frames` route: "advance the Handler virtual
   clock by --frame-delay per frame"). Physics progress per frame SATURATES at
   ~5.7-6 ticker firings per frame for any step ≳160 ms, while message/timeout
   clocks keep scaling with the step — so a 200 ms step compresses ball 1's
   75-frame (40 ms) life to ~34 frames **with identical physics events**.
3. **The endgame timeline is now mapped end-to-end at 200 ms steps**: drain 1
   ~f33 (UNAIDED — no flipper taps needed) → plunger tap @36 serves ball 2 →
   ball 2's own bumper cycle scores 600→2,100 → drain 2 @77 → tap @78 QUEUES
   and fires at placement (serve 3 @79-84) → ball 3 gutter crawl @115-127 →
   drain 3 + Game Over ≈ f130-150. **The dialog remains beyond the 595 s
   command cap under every honest configuration measured (7 levers, §3) —
   the wall is now measured, not assumed, and the FINAL recipe shrank from
   S141b's 240 frames to a 130-frame P8 schedule.**
4. **Corpus restored 7 → 15 APKs**: all 8 cleaner-lost canonical APKs
   re-fetched FIRST-TRY from F-Droid by `<pkg>_<vc>.apk` direct URL (§4,
   SHA-256 registered); 8/8 boot-and-render (5 SUCCESS, 3 PARTIAL).
5. **unote runs its OWN sqlite through the engine**: Add-note → editor →
   Save → return-to-list, byte-identical ×2, and the app's own
   `SQLiteOpenHelper.onCreate` created the REAL `table_notes` schema in
   `databases/notes.db` on the engine's storage stack (§4.3).

---

## 1) ONE-COMMAND VERIFICATION (confirm or falsify everything above)

**R1 — the PGO speed build is pin-exact (the §0.1 claim):**
```bash
cd /home/z/my-project && START=$(date +%s)
./miniandroid/build/miniandroid run --execution-mode real-dalvik \
  --frames 30 --frame-delay 200 --width 1080 --height 1920 \
  --tap 519,609@15 --tap 540,1600@20 --tap 540,1600@21 \
  -o /tmp/v_pgoA work/apks/bouncy_43.apk   # (PGO binary; recipe + build flags §2)
echo "WALL=$(( $(date +%s) - START ))s"    # session: 131 s / 136 s (rebuild)
cd /tmp/v_pgoA/frames && sha256sum frame_*.png | sha256sum | cut -c1-16
```
PASS: aggregate = `d50dca1d2189830f` (the standing S140 pin, zero drift) and
frame pins 000/015/020/025/029 = `7579c536…`/`ee7a8a4e…`/`f12314ec…`/`0480aaa5…`/`e1ee4024…`,
with WALL ≤ ~145 s. FALSIFIED if aggregate differs or WALL > 165 s.
(The same recipe under the plain `-O3 -g0 -march=native -ffp-contract=off`
build = E2a: session WALL 141 s, aggregate EXACT.)

**R2 — the virtual-clock compression law (§0.2, S156-C):**
```bash
MINIANDROID_AWAITUP_GATE_MS=0 ./miniandroid/build/miniandroid run \
  --execution-mode real-dalvik --frames 45 --frame-delay 200 \
  --width 1080 --height 1920 --tap 519,609@3 --tap 540,1600@4 \
  --tap 810,1700@16 --tap 810,1700@25 -o /tmp/v_p4 work/apks/bouncy_43.apk
python3 scripts/p2_census.py /tmp/v_p4   # region-diff event finder (in-tree tool this session)
```
PASS (session P4): rc=0, 45 frames, WALL ≈ 197 s, event frames {5,6,29,30} —
launch @5-6, the 600-score flipper landing @29-30 — i.e. ball 1's ENTIRE
40 ms-cadence life (launch 21 → drain 75) compressed ~2.2× with the SAME event
sequence; 1,101 ContactListener callbacks delivered, zero misses. FALSIFIED if
the landing lands at f≥45 (no compression) or events reorder.

**R3 — 300 ms steps: physics frame-identical, message clock faster (§3):**
```bash
MINIANDROID_AWAITUP_GATE_MS=0 ./miniandroid/build/miniandroid run \
  --execution-mode real-dalvik --frames 45 --frame-delay 300 \
  --width 1080 --height 1920 --tap 519,609@2 --tap 540,1600@3 \
  --tap 810,1700@24 --tap 810,1700@36 -o /tmp/v_p6 work/apks/bouncy_43.apk
```
PASS (session P6): landing event at 28-29 (P4's 200 ms landing was 29-30 —
SAME physics frame ±1), WALL ≈ 227 s (4.67 s/f — cost flat vs 200 ms).
FALSIFIED if the landing shifts >2 frames (physics would be step-dependent).

**R4 — unote full interaction chain ×2 + the app's own DB (§4.3):**
```bash
for i in 1 2; do
  MINIANDROID_AWAITUP_GATE_MS=0 ./miniandroid/build/miniandroid run \
    --execution-mode real-dalvik --frames 18 --frame-delay 200 \
    --tap 180,1857@6 --tap 270,1857@11 \
    -o /tmp/v_unote$i upload/canonical_apks/app.varlorg.unote_30.apk
done
cd /tmp/v_unote1/frames && sha256sum frame_*.png | sha256sum | cut -c1-16
cd /tmp/v_unote2/frames && sha256sum frame_*.png | sha256sum | cut -c1-16
python3 -c "import sqlite3; print(sqlite3.connect('/home/z/my-project/runtime/data/data/data/app.varlorg.unote/databases/notes.db').execute(\"SELECT sql FROM sqlite_master WHERE name='table_notes'\").fetchone())"
```
PASS: both aggregates = `70a38ec86cc35db9` (byte-identical ×2; rc=1 PARTIAL
from the recorded `Window.setStatusBarColor` REC-MISS — cosmetic, logged);
the SELECT returns the app's own schema `CREATE TABLE table_notes (ID INTEGER
PRIMARY KEY AUTOINCREMENT, Note TEXT NOT NULL, Titre TEXT NOT NULL,
Date_creation T…` — created by the APK's OWN `SQLiteOpenHelper` code through
the engine. FALSIFIED by any aggregate mismatch or missing table.

**R5 — corpus restoration (§4):** the loop in §4 boot-probes all 8 restored
APKs (4 frames each); session verdicts: chessclock SUCCESS, gmdice SUCCESS,
notes SUCCESS, headingcalculator SUCCESS, tictactoe/stopwatch/simplestopwatch/
simplekeyboard PARTIAL (frames render in all 8). FALSIFIED by any non-booting APK.

**R6 — the LTO+PGO conflict (§2, S156-B):**
```bash
cd /home/z/my-project/work/repo/miniandroid && make CXXFLAGS="-std=c++17 -O3 -g0 -march=native -ffp-contract=off -flto=1 -MMD -MP -fprofile-use=/tmp/pgo -fprofile-correction" build/dex/dalvik_engine.o 2>&1 | grep -c "coverage-mismatch"
```
PASS: count ≥ 2 (`arcs` + `time_profiler` counters on `json.hpp:19680 create<>`),
build FAILS — LTO's CFG rewrite invalidates the PGO counters; GCC
`-Werror=coverage-mismatch` is default-on. Recorded as the reason LTO is
REJECTED for this tree (fallback lever measured, documented, not shipped).

---

## 2) THE LAWS (each with route; ZERO production-code edits this session)

| # | Law | Route / lever | Evidence |
|---|-----|--------------|----------|
| S156-A | **Build-speed law**: `-O3 -g0 -march=native -ffp-contract=off` is pin-safe and −21 % | `make CXXFLAGS=…` override (Makefile L5; the giant-TU `-g0` rules at L116-130 inherit it); `-ffp-contract=off` is REQUIRED (S141c recorded it pin-safe) | Battery A aggregate + 5 pins EXACT (R1); 141 s |
| S156-B | **PGO chain law**: instrumented → profile → use is pin-safe, −27 % cumulative | build 1: `-fprofile-generate -fprofile-dir=/tmp/pgo`; profile runs: Battery A (30 f) + 80 f launch-drain segment; build 2: `-fprofile-use=/tmp/pgo -fprofile-correction`; 70/84 TUs profiled | `pgo_A1` 131 s + `pgo_A2` (post-rebuild) 136 s, aggregate EXACT both |
| S156-C | **Virtual-clock law**: `--frame-delay` = Handler clock step; physics saturates ~5.7-6 ticks/frame above ~160 ms; message clocks scale with step | `src/main.cpp` `--frames` route comment (L1293-1308) + the frame pump ("fire every due postDelayed Runnable") | P4 2.2× compression, events 5/6/29/30; P6 landing 28-29 ≈ P4's 29-30 |
| S156-D | **Gate-off law**: `MINIANDROID_AWAITUP_GATE_MS=0` is behavior-neutral on tap dispatch | `src/runtime/execution_engine.cpp` L7370-7374 (the S154 gate reads the env) | Battery A with gate OFF: aggregate `d50dca1d…` EXACT |
| S156-E | **Resolution-crop law**: sub-1080×1920 surfaces CROP the table (fixed world scale), they do NOT rescale it | 810×1440 probe `/tmp/p_res`: static zoomed top-right crop, launch taps unreceiveable | frame_011 sheet; lever INVALID for tap batteries |
| S156-F | **LTO+PGO conflict**: `-flto=1 -fprofile-use` fails `-Werror=coverage-mismatch` on `nlohmann/json.hpp create<>` | R6; `src/dex/dalvik_engine.cpp` TU includes json.hpp | build error recorded verbatim |
| S156-G | **No auto-serve law (bouncy v43)**: after a drain the next ball is served ONLY by a plunger tap | P2 (3 taps): static f77-129, zero serve; Battery B's "auto-serve@85" was the tap@80 | P2 census; P3 serve@81-82 after tap@80 |
| S156-H | **Serve-tap queue law**: a plunger tap fired during the post-drain message QUEUES and executes at placement; a tap 1 frame after the drain works | P3 tap@124 → serve ~130-135; P7 tap@78 (drain2@77) → serve3 @79-84 | both runs' event frames |
| S156-I | **Natural-drain law**: ball 1 drains UNAIDED (launch → arc → drain ~75 f @40 ms / ~33 f @200 ms) — flipper taps only destabilize balls 2-3 | P2 vs Battery B: drain 75 vs 74 — ±1 frame | P2 census |
| S156-J | **Ball-cycle timeline (200 ms)**: drain1 ~33 → serve2 @37 → bumpers 600→2,100 → drain2 @77 → serve3 @79-84 → gutter 115-127 → Game Over ≈ f130-150 | P5/P7/P8 census sheets (score HUD pixel-proven) | §3 |
| S156-K | **`--text` is HOST_SHORTCUT-only**: real-dalvik text injection route does not exist | `src/runtime/execution_engine.cpp` L2420 (`stage_execute_application_legacy` only) | code route; unote typing gap filed |

Build chain this session: canonical `-O2` binary BACKED UP untouched at
`work/s156/miniandroid_o2_canonical` (99 MB); E2a and PGO builds are
flag-only variants of the SAME sources — the working tree (12,401 M paths)
is UNCHANGED.

## 3) THE WALL, MEASURED SEVEN WAYS (honest frontier — unchanged verdict, new depth)

| lever | result | verdict |
|---|---|---|
| E2a flags (−21 %) | 4.13 s/f @200 ms | adopted |
| PGO (−27 % cum.) | 3.80 s/f @200 ms base; **4.70-4.73 s/f in drain-cycle content** (P5/P7: the app's own message/serve/gutter churn) | adopted |
| LTO | conflicts with PGO (S156-F); alone untested (time) | rejected |
| half/0.75 res | CROPS the viewport (S156-E) — taps invalid | invalid |
| 200 ms virtual step | ball 1 life 75→~34 f (2.2×) | adopted |
| 300 ms virtual step | physics frame-identical, cost flat (4.67) — message clocks 1.5× faster only | adopted for P8 |
| tap-density | P4 (4 taps) 4.0 vs P5 (9 taps) 4.70 — but P7 (5 taps) 4.73 ⇒ the cost is CONTENT (drain churn), not taps | measured |

**P8 — the FINAL endgame recipe (130 frames, supersedes S141b's 240-frame
recipe; needs any environment with ≥12 min/command):**
```bash
MINIANDROID_AWAITUP_GATE_MS=0 ./miniandroid/build/miniandroid run \
  --execution-mode real-dalvik --frames 130 --frame-delay 300 \
  --width 1080 --height 1920 --tap 519,609@3 --tap 540,1600@4 \
  --tap 810,1700@36 --tap 810,1700@78 --tap 810,1700@120 \
  -o /tmp/v_p8 work/apks/bouncy_43.apk
```
Session P8 reached **f127/130 before the 595 s kill** — ball 3 IN THE GUTTER
(f115-127, pixel sheets), score 2,100, indicator 1 white + 2 gray, physics
events identical to P7 (77/79/84/92/115/116). Projected dialog f130-150 ⇒
~670-720 s. The verdict of #516 §3/S141c stands, now measured with the
compiler levers stacked: **no honest configuration in THIS environment
reaches the dialog in one command.**

## 4) CORPUS + APP EXTENSIONS

**§4.1 — 8/8 cleaner-lost APKs restored (F-Droid direct, first-try):**

| APK | SHA-256 (16) | boot probe |
|---|---|---|
| com.chessclock.android_29 | `5ca6f2c54c05efe7` | SUCCESS, 4/4 frames |
| com.emmanuelmess.tictactoe_3 | `760fe5acf7b39435` | PARTIAL, 4/4 |
| com.github.muellerma.stopwatch_6 | `3b6a10c8dc8ddc72` | PARTIAL, 4/4 |
| de.duenndns.gmdice_8 | `1621eda11b5dbc0c` | SUCCESS, 4/4 |
| omegacentauri.mobi.simplestopwatch_26 | `b3ec1a5ec24ce53b` | PARTIAL, 4/4 |
| org.billthefarmer.notes_139 | `82cf8bc44c163748` | SUCCESS, 4/4 |
| org.debian.eugen.headingcalculator_1 | `274ec873098eea51` | SUCCESS, 4/4 |
| rkr.simplekeyboard.inputmethod_145 | `d83060833dc2bc97` | PARTIAL, 4/4 |

Restored into `upload/canonical_apks_restored/`; the purge manifest's 10 lost
entries now have 8 back (unote + microtimer already survived). **Usable
corpus: 7 → 15 APKs.**

**§4.2 — dooz (v23) S156 record-loop spin re-measured on the PGO build:**
4 frames in 148 s = **32.75 s/frame** (was ~35 at -O2) — the spin is
ALGORITHMIC (record-loop), compiler levers don't fix it; S156 root-cause note
unchanged, frame_000 sha16 `11a38a5aeeff45a6`.

**§4.3 — unote (v30) full chain + the app's OWN sqlite (R4):** list UI →
`Add note` Button @(0,1794)+(360x126) → editor tree dumped with coordinates
(Title EditText (5,66)+(1070x127), Note EditText (0,259)+(1080x1535), Save
(0,1794)+(540x126), Return (540,1794)+(540x126)) → Save tap → back to list;
`databases/notes.db` created by the app's own helper with the REAL schema
(0 rows — the app's own validation rejects an empty save). Byte-identical ×2.

**§4.4 — honest gaps FILED (root-caused, not hidden):**
- opencalculator v53: full keypad renders (√ π ! AC ( ) % ÷ 7 8 9 × 4 5 6 −
  1 2 3 + 0 ⌫ =) but coordinate taps don't dispatch — EXP092 dump bounds are
  0x0 while the render is ~220x230 (measure/hit-test bounds gap). 5+3 chain
  FAILED twice; law candidate: re-run hit-test after the app's own layout pass.
- microtimer v8: keypad buttons have REAL bounds (355x210), listeners register
  ([EXP060-LISTENER] view_id=147), yet taps produce ZERO visual delta across
  25 frames (byte-identical frames) — display refresh path gap filed.
- unote typing: `--text` cannot inject in real-dalvik mode (S156-K).

## 5) THE 33-ITEM SESSION INVENTORY (each independently re-runnable)

| # | item | verdict |
|---|------|---------|
| 1 | 5th-environment re-validation (HEAD `be9329bb`, tree intact, binary build-current) | PASS |
| 2 | Battery A spot-check at session start: aggregate `d50dca1d…` + 5 pins EXACT | EXACT |
| 3 | canonical `-O2` binary backup (`work/s156/miniandroid_o2_canonical`) | PRESERVED |
| 4 | E2a build (S156-A): −21 %, pins EXACT | VERIFIED |
| 5 | E2a Battery A timed (141 s vs ~173 s baseline) | MEASURED |
| 6 | PGO instrumented build + 70 gcda | DONE |
| 7 | PGO profile runs (Battery A + 80 f launch-drain segment) | DONE |
| 8 | PGO use-build (S156-B): −27 % cum., pins EXACT | VERIFIED |
| 9 | PGO Battery A timed ×2 (131 s / 136 s post-rebuild) | MEASURED |
| 10 | PGO binary rebuild reproducibility (aggregate EXACT after fresh build) | VERIFIED |
| 11 | LTO+PGO conflict root-cause (S156-F, R6) | ROOT-CAUSED |
| 12 | gate-off law (S156-D): aggregate EXACT with gate disabled | VERIFIED |
| 13 | virtual-clock law (S156-C): `--frame-delay` = clock step | ROOT-CAUSED |
| 14 | P2 natural-drain census (130 f, drain1@75-76, no auto-serve 77-129) | VERIFIED |
| 15 | S156-I natural-drain law (ball 1 drains unaided) | VERIFIED |
| 16 | S156-G no-auto-serve law (bouncy v43) | VERIFIED |
| 17 | P3 cycle probe (serve2@81-82, drain2@117-118, queued serve3) | VERIFIED |
| 18 | S156-H serve-tap queue law | VERIFIED |
| 19 | P4 200 ms compression probe (events 5/6/29/30; 1,101 callbacks) | VERIFIED |
| 20 | P5 endgame run 1 (123 f on disk; drain2@77, serve3@86, ball3 alive@122) | RECORDED |
| 21 | P7 endgame run 2 (122 f; queued serve@78 → 79-84; gutter 115-121) | RECORDED |
| 22 | P8 endgame run 3 (127 f; physics events == P7; gutter to f126) | RECORDED |
| 23 | determinism cross-validation P5≡P7 frames 0-60 byte-exact | EXACT |
| 24 | ball 2 bumper scoring 600→2,100 pixel-proven (app's own scoring chain) | VERIFIED |
| 25 | 7-lever wall table (§3) + P8 final recipe (130 f) | MEASURED |
| 26 | resolution-crop law (S156-E, 810×1440 probe) | ROOT-CAUSED |
| 27 | 300 ms probe P6 (physics frame-identical, cost flat) | VERIFIED |
| 28 | corpus 8/8 restored (§4.1, SHA-256 registered) | RESTORED |
| 29 | corpus boot probes 8/8 (5 SUCCESS / 3 PARTIAL) | VERIFIED |
| 30 | unote full chain ×2 + notes.db real schema (R4) | VERIFIED |
| 31 | opencalculator keypad render + dispatch gap root-caused | FILED |
| 32 | microtimer listener/tap gap filed; dooz spin re-measured (32.75 s/f) | FILED |
| 33 | `p2_census.py` region-diff event tool built + used across 5 runs | DONE |

## 6) WHAT THIS COMMENT DOES NOT CLAIM

- The 3rd-ball endGame dialog is **NOT captured** — the wall is measured with
  the compiler levers stacked (§3); P8 is the final recipe for a ≥12-min
  environment. No fake success.
- No NEW engine source changes: every law above is build-flag/config/tooling
  level; the 12,401-path working tree is byte-identical to session start.
- opencalculator/microtimer interaction chains are FILED gaps, not fixes.
- The E2a/PGO binaries are experiment builds; the canonical `-O2` binary is
  backed up and restorable in one copy (item 3).

*— Coder 3 (issues-only channel; every number reproducible via §1)*