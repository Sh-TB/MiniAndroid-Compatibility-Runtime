# CURRENT_HEAD_BASELINE — REUSE-FIRST CAMPAIGN §1

All values below are from commands executed THIS session (2026-09-05),
not inherited from any prior report. Build ran from `make clean`.

## Record

```text
HEAD:            a3c3aded (main)
Branch:          main (worktree clean after commit)
Origin:          https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git
Remote main:     ad95d92876a355a719d2a8959053f8a47c2b1e79 (UNRELATED rebuilt history; 28 local commits ahead)
Push status:     PUSH_BLOCKED — "fatal: could not read Username for 'https://github.com'":
                 no gh CLI, no ~/.ssh, no ~/.netrc, no token env vars (probed this session)
Build:           PASS — make clean + make -j (binary 60,183,232 B)
Semantic tests:  PASS — long/cmp/conv 14 · switch parse-neg 25 · pass3 bridge 57 (= 96/96)
MUTF-8 battery:  PASS — 7/7 (FIND-REUSE-001 shared primitive)
Hello World:     PASS — helloworld_golden 26/26 checks, RESOURCE-BACKED (§36.E):
                 aapt2-linked APK 3cf76fb7…, strings in resources.arsc and ABSENT
                 from classes.dex, screenshot a61f5b22… 1080×1920, run B byte-identical
Tic-Tac-Toe:     PASS — tictactoe_golden 8/8 checks: 9/9 clicks, "X to move"→"O to move"
                 →"X WINS", 4 X + 3 O marks, marks in cells 2..8 only, glyph ink >100 px,
                 10 frames byte-identical across runs (§29/§16 satisfied on this HEAD)
Corpus:          simplestopwatch exit=0 + screenshot; gmdice exit=0 + screenshot
                 (visually verified: history list + hints + button bar);
                 microtimer exit=0 + screenshot. APKs from tests/corpus/apks.json
                 registry with SHA256 HASH MATCH (F-Droid), cache outside repo.
Rendering:       goldens render 1080×1920 PNG (ctype 2), no composited frames
Interaction:     real DEX click listeners (tictactoe state machine), EXT-AOSP-001/002
                 dispatch evidence in helloworld log
Replay:          byte-identical screenshots across two runs for both goldens AND
                 deterministic fixture APK builds (aapt2/repackager pin 1980 epoch)
Gate:            scripts/run_test_battery.sh → BATTERY GATE: ALL PASS (11 stages)
```

## Commands (verbatim)

```bash
git remote -v && git branch -vv && git status --short && git log --oneline -10
git ls-remote origin                    # → ad95d928… ≠ local a3c3aded
git push origin main                    # → could not read Username (PUSH_BLOCKED)
make clean && bash scripts/run_test_battery.sh   # (from /home/z/my-project)
# battery → 11 stages ALL PASS (build, 3 links, 3 semantic, mutf8, 2 goldens)
python3 miniandroid/scripts/download_test_apks.py --only SimpleStopwatch,gmdice,MicroTimer
./build/miniandroid run <apk> -o <dir>  # ×3 corpus apps, exit 0 each
```

## Known gaps recorded at this HEAD (not regressions)

- FIND-GRAVITY-VERTICAL — LinearLayout container gravity vertical axis
  top-aligns (see docs/evidence/GOLDEN_HELLOWORLD.md).
- Corpus cache is external and was empty at session start; re-fetch via
  the registry downloader (zero-APK-in-repo policy intact).
- EXP092 legacy `resource_values.json` warning still prints when the
  ARSC-first path is active — misleading diagnostic, cleanup queued.
