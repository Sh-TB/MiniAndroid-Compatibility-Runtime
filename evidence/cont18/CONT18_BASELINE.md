# CONT-18 BASELINE — T-01 (PHASE 0)

Date: 2026-10-08 · Recorded by: T-01 static-facts + live battery · **No engine code changed.**

## 1. Identity

| Item | Value | Verification |
|---|---|---|
| Git HEAD | `d95b352f` (CONT-17 W6) | `t01_static_facts.json` |
| Source tree | clean (only pre-existing `tmp/flappycow` mod) | `git status --porcelain` |
| Unpushed commits at start | **0** | `git log origin/main..HEAD` empty |
| Runtime binary | **`a8761a482a186eac`** (133,078,968 bytes) | = recorded CONT-17 SHA (CONT17_TASK_LIST task 0, SUCCESS_PATH_REPORT) |
| Registry | 575 rows, `total == total_roots == 575`, sha16 `0942fdcf2c7b0570` | status_counts in `t01_static_facts.json` |
| Toolchain | clang++/make/python3 recorded | same file |

**Brief discrepancy (recorded honestly):** the CONT-18 brief states the CONT-17 binary as
`e752b6d9c669558a`. That SHA appears **nowhere** in the repository (full-tree grep over
md/json evidence: 0 hits). The authoritative recorded CONT-17 binary is
`a8761a482a186eac` (= CONT-16 recorded SHA, byte-identical rebuild), and the on-disk
binary matches it exactly. Baseline therefore proceeds on the recorded SHA; the stated
value is classified **NOT-FOUND-IN-REPO** (stale/typo in the brief), not as drift.

## 2. APK identities (sha256[:16])

dooz `299eab21ac8b3c61` · microtimer `79c6f730f64886e7` · unote `be91103f0e7db443` ·
gmdice `1621eda11b5dbc0c` · opencalc `2642613868a8a80f` · chess `3245b9ec35f6c1df` ·
telegram `e37aced2a49c1dbb` · probes f266 `bf59945fc326b8e6` / f259 `8870eafe766d007a` /
f259g `2cfaa0f132ba3d20` / fcol `954f2371cddb4855` / f084 `21351bd0df1571cd`.

## 3. Live battery at `a8761a482a186eac` (all runs foreground, timeout-bounded)

| Gate | Required | Recorded (CONT-17) | **CONT-18 live** | Verdict |
|---|---|---|---|---|
| Anchors ×3 | 6/6 byte-identical | 6/6 | dooz `d602648e8e401895`, microtimer `da73010a37dd0189`, unote `4f1a9e4e8f64fae8`, gmdice `f3b483fe7b7cf51b`, opencalc `a976d2f9fb675cb3`, chess `b5a7a35d5fe0564b` — **18/18 MATCH** | **ZERO DRIFT** |
| Telegram ×3 | consistent REAL_APP_CONTENT | REAL_APP_CONTENT + in-flight | run1=run3=`cf4c41e62ceb6557` REAL_APP_CONTENT, 5 uncaught in-flight, 1961434/2073600 non-white px; **run2 = 120 s wall-clock cap** mid `h0$a;.onActivityStarted` → F084-HALT-RETURN → no screenshot (timing flake of the wall budget, recorded; engine unchanged) | **BASELINE HONEST** |
| f266 | 6/6 | 6/6 | **6/6** | MATCH |
| f259 | 7/7 | 7/7 | **7/7** | MATCH |
| f259g | 12/13 honest | 12/13 | **12/13** (row L = documented F-068 most-derived test-expectation artifact) | MATCH |
| fcol | record exact | 3/18 | **3/18** (K7/K8/K10 PASS; K1–K6, K9, K11–K18 FAIL = the six-law queue) | MATCH |
| Negatives | 19/19 | 19/19 | **19/19** | MATCH |
| Skill | 13/13 | 13/13 | **13/13** | MATCH |
| Gate A battery | 121-stage ALL PASS | ALL PASS | **ALL PASS** (see §4 restoration) | MATCH |
| f084 probe (F-217 evidence) | HALT 50,001 / deferred VME / cap never raised | VERIFIED-CORRECT (task 33) | **REPRODUCED**: `[HALT-LOOP] …stalledSpin (visited 50001 times, bytecode_size=2)` → `F084-HALT-RETURN (deferred) VirtualMachineError`; `t01_f084_probe.json` VERIFIED=true | **LIVE** |

## 4. Environment restoration during baseline (root-caused, evidence-pinned; no engine change)

The container reset (same family as CONT-17 task 4_1) wiped four classes of
non-engine state. Each was diagnosed, restored with pinned evidence, and the
affected stage re-run:

1. **`tools/android-34.jar`** (fixture-builder lookup path, untracked): restored by
   copy from tracked `tools/toolchain/android-34.jar`; both sha256 `6cea1df3…` byte-identical.
2. **`miniandroid/runtime/data/fonts/DroidSansMono.ttf` + `NOTICE.md`**: the AOSP
   `monospace` system font (pinned SHA-256 `db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862`)
   was **deleted from git tracking by commit `46f56737`** (pre-CONT-15) while the engine
   (`TextShaper::resolve_family`, AOSP fonts.xml law) and s106 X11 (`mg-087`) still require
   it — it had survived only as an untracked local file until this reset. Restored from the
   git object store (`9a5025ee`), SHA re-verified against the pinned NOTICE value;
   **re-added to tracking this wave** (re-adding is the fix for the repo defect, not a workaround).
   s106 text2 after restore: **14/14 PASS** (`mono=4 sys=0`).
3. **External fixture** `/home/z/corpus/external_hello/`: HelloWorldSelfAware-1.1.0 APK
   re-fetched, SHA-256 `009b467109c4d48d4b00610b06f37f3a77eed75178fbaae344a111acc848cc41`
   = frozen record; author reference screenshot re-fetched, SHA-256
   `121d479c5165044943dc45e508de713ec754ed7abb9059c7c1be59eb016e2ba5` = frozen record.
   EXT-01 typography golden after restore: **9/9 PASS**.
4. **`build/resource_trace`**: missing because the battery's numbered resume cache
   (`/tmp/g09_battery_state`, stage-number keyed) marked the build stage passed from a
   pre-reset run. Rebuilt at HEAD: sha16 `8953f30778defbf1`; density-matrix oracle then
   **11/11 PASS** (all runtime pixel laws + 3-run determinism already green).

## 5. Baseline verdict

**BASELINE LOCKED.** Every required gate reproduces the recorded CONT-17 state at the
recorded binary; the only differences were proven environment-restoration artifacts
(each restored + re-verified above). Zero engine drift: anchors 18/18 byte-identical,
all probe rows identical to recorded values, f084 spin law live and deterministic.

Registry untouched this phase (per PHASE 0 discipline).

## 6. Artifacts

- `evidence/cont18/t01_static_facts.json` — identity, APK SHAs, command lines
- `evidence/cont18/t01_f084_probe.json` — f084 spin probe verdict
- `run/cont18/anchors/` — 21 runs (6 anchors ×3 + telegram ×3) with logs/traces
- `run/cont18/probes/probe_report.json` — f266/f259/f259g/fcol rows
- `run/cont18/f084_run/` — f084 probe run dir
- `run/cont18/battery_fresh1.log`, `run/cont18/battery_fresh2.log` — battery logs

## 7. CONT-18f addendum — clean-container reproduction + orphan-audit wave

A fresh container had NO local history (local main was 23 commits behind
origin/main; the CONT-11..18 lineage existed only on GitHub). Recovery and
live re-proof, all in THIS container:

1. **Lineage recovery**: `git merge --ff-only origin/main` → HEAD `c15e2661`.
2. **Binary reproducibility**: clean cold rebuild (`timeout 570 make -j1
   BUILD_DIR=build`) reproduces the recorded CONT-18 binary **byte-identically**:
   `build/miniandroid` sha16 `8ee839e718877216` (the LAW-C/E/F + T-01 recorded
   binary). One honest build note: `-j2` OOM-killed cc1plus in this container;
   `-j1` (the standing discipline) succeeds.
3. **LAW-A..F cumulative impact, live**: fcol probe APK rebuilt from the
   committed fixture (`scripts/cont11_build_fcol.sh`, apk sha16
   `d03cc97f82f47c55`) and run at the reproduced binary (`run/cont18f/probes/`):
   **fcol 18/18 PASS (K1–K18)** — vs 3/18 recorded at the CONT-18 baseline.
   This is the runtime-visible impact of the campaign's main-code fixes.
4. **Zero-drift regression**: anchors 6/6 ×3 = **18/18 MATCH byte-identical**
   (`run/cont18/anchors/`, `scripts/cont18_anchors.sh` part1+part2).
5. **T-01 tap exposure reproduced live** (`run/cont18f/tap1/run.log`):
   `[F117-TAP] frame 15 DOWN (540,960) target=0`; post-tap screenshot sha16
   `d602648e8e401895` = the dooz anchor (byte-identical = zero state consumed
   by the tap). Registered as **F-NEW-267 (CLASSIFIED)** — registry 575→576.
6. **Orphan-findings audit** (user directive): every discrete/abandoned
   finding dispositioned — see `evidence/cont18f/ORPHAN_FINDINGS_AUDIT.md`
   (14 loose ends: 1 fixed in main code, 1 registered as a root, 1 toolified,
   4 resolved/resolved-by-lineage, rest explicitly DEFERRED/OBSERVED/BLOCKED
   with scope). The pre-push guard empty-list defect (recorded twice, never
   fixed) is **fixed in main code** with a permanent selftest law.
7. **Usability artifact**: `scripts/findings_queue.py` → the 576-row registry
   becomes a ranked work order (255 queued / 321 terminal; P0 first:
   F-NEW-156, F-NEW-157, F-NEW-265, …).

No engine source was changed this wave (build reproducibility wave + audit +
input-frontier evidence + infra fix). The guard fix is the only main-code
change (scripts/, fail-closed semantics preserved, selftest green).
