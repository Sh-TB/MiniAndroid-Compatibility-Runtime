# cont375 CONT-2 — F-NEW-084 closeout + baseline reconciliation at binary e2b948d4b11dc45e

## STATUS — RESULT — EVIDENCE

**F-NEW-084 (fairymahjong interpreter halt) — ROOT-CAUSED-FIXED (3 generic laws + resource knob)**

- RESULT: interpreter halt GONE on fairymahjong; game init completes measured-bounded at ~177.4M instructions (deterministic [PROGRESS] evidence, RSS 344MB real decode); the game advances into its own async board pipeline. Probe 3/3 PASS ×3 byte-identical. Zero drift on all recorded anchors.
- EVIDENCE:
  - Law v3 (frame-level forward-progress): visit counting restored on EVERY pc (branch-free spin evidence: ECJ compiles `while(k==5){k=5;}` to `0x49 nop / 0x4a goto -1`); halt decision is frame-level — every conditional-branch (0x32..0x3d) operand-signature CHANGE anywhere in the frame bumps frame_progress_epoch_; a pc over the 50k stale window halts only when the epoch is unchanged across the checkpoint. Per-branch law (v2) false-positived at fairymahjong `Lw4;.<init>` pc=0x99 `if-lt v14,v7` (16<0) — loop-INVARIANT branch, real exit `if-ge v1,v3` advances. Raw-visit law (v0) false-positived at the 50,001st visit (recorded face).
  - Caught-halt resume: at EXC-PROPAGATE handler-found, the callee-originated engine halt clears halted_/halted_on_return_ (pending_exception_ + move-exception armed) — else the caller fetch loop exits and the app catch never runs (probe-proven).
  - `--max-instructions` session RESOURCE knob (default 100M unchanged; distinct from the semantic law) — rationale in-code.
  - Probe: fixtures/f084_loop_probe (APK a7ebf47e…) — P1 60k progressing loop completes sum=30000; P2 nested 40×1250 completes total=6239400; N1 stalled-spin callee halted via catchable java.lang.VirtualMachineError — ×3 byte-identical.
  - Disasm tooling: scripts/cont375_f084_full_ladder.py (correct dalvik size table; op = LOW byte; invoke-range 3 units).

**NEW generic law — android.util.AtomicFile (AOSP AtomicFile.java)**

- RESULT: fairymahjong practice-board DataStore chain (Lq1;.run) no longer NPEs on `File.exists()` (getBaseFile()==null stub); ctor/getBaseFile/startRead(+.bak crash-recovery)/openRead/startWrite/.new/finishWrite(rename-over-base)/failWrite/delete implemented; streams registered in the SAME open_assets_/open_writers_ maps as the FileInputStream/FileOutputStream laws.
- EVIDENCE: run/cont375/fairy_v4_run2 — [R347-FILE-CTOR] practice-board.json(.bak) caller=Lq1;.run; game proceeds to its own BoardShape build.

**NEXT frontier — F-NEW-235 registered (OBSERVED)**

- RESULT: the game's own layout generator/validator throws `IllegalArgumentException: "Duplicate tile position"` (Lg0;.a ← Lm;.<init> BoardShape parser, 696-insn ctor with java.util.regex Matcher.matches token parse ← Lo;.<clinit> ← Lm2;.b ← Lq1;.run) — regex/token-parse or Set-dedup divergence; generic law pending; no package conditional.
- EVIDENCE: [THROWABLE-MSG] IAE "Duplicate tile position" caller=Lg0;.a pc=2 depth=5; [EXC-PROPAGATE] APP BOUNDARY at MainActivity.onCreate invoke_pc=56; run/cont375/fairy_v4_run2.

**Baseline reproduced at binary e2b948d4b11dc45e (final binary of this wave)**

- Battery: ALL PASS (114 stages; s106 text2 14/14 after DroidSansMono restore db19a1fd…; density-matrix 11/11 after resource_trace relink 2d364c50…; EXT-01 9/9 + EXT-02 interaction after fixture refetch APK 009b4671… + ref PNG 121d479c…).
- Anchors 5/5 ×3 BYTE-IDENTICAL to recorded shas: opencalc e364b001…, chess b5a7a35d…, dooz d602648e…, microtimer da73010a…, unote 4f1a9e4e….
- Gate A probe: 95 PASS / 0 FAIL / 2 INFO (fresh at this binary).
- Negatives: 17/17 PASS (fresh; N-08 family harvested from the freshly-run gate_a_results.jsonl).
- Reinstall matrix 8/8 + REINSTALL-IDENTITY ALL PASS (source SHA == installed base.apk SHA == pkgaudit live re-hash for all 5).
- Multi-app installed-environment: 5/5 ALL PASS (incl. render-FAIL blockblast honesty case).
- NATX 10/10 ×3 byte-identical (results sha 4d7761f7… ×3; libprobe.so rebuilt d5ec1f57… = recorded; probe APK e50d3b40…).
- Agent Skill selftest: 13/13 PASS.
- Container-reset repairs all SHA-exact: 5 wave APKs (fossifyclock 43cf9f0e…, fairymahjong 88a4cbbe…, sudokusolver d114d479…, blockblast 64589a3a…, memory 830798a6…), font, EXT fixtures, native probe lib.

**Registry: 540 roots** — F-NEW-084 ROOT-CAUSED-FIXED; F-NEW-235 OBSERVED; R-NEW-464 stays ROOT-CAUSED-FIXED; no duplicate IDs (cross-matched vs R-NEW-361 dooz hash-probe family: distinct).

**Commits**: b9e43b95 (CONT-2, pushed; includes the back-filled CONT-1 worklog entry). Worklog: cont375-CONT-1 (back-fill) + cont375-CONT-2.
