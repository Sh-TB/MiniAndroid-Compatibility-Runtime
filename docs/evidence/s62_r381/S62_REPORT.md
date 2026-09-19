# S62 — R-NEW-381 measured bottleneck decomposition + F-107 A/B + F-109 + R-NEW-331 game consumers

Date: 2026-09-19 (S62). All runs on this machine (2 CPU, idle), dooz v23
`apk_cache/io.github.yamin8000.dooz_23.apk`, `--execution-mode real-dalvik`.

## 1. F-107 A/B (user directive D) — same machine, same day, 480s budgets

Pre-F-107 binary = `run/miniandroid.release.bak` (S60 build, no PERF-PHASE
strings, verified). Post = HEAD build (F-107 a/b/b2/c/c2/d landed).

| metric | pre-F-107 (run/s62_f107_ab_before) | post-F-107 (run/s62_f107_ab_after) |
|---|---|---|
| instructions @480s | 700,000 | ~690,000 (600K @377.1s; budget stopped before 700K) |
| avg inst/sec | 1,459 | ~1,437 |
| per-100K segment times | 26.7/58.1/60.7/66.7/52.5/92.9/111.3 s | 27.4/56.5/62.0/74.7/58.5/98.0 s |
| CLASS_INIT chains | 616 | 612 |
| frame outcome at budget stop | 0 non-white px, NO UC009-DRAW | **197 non-white px, UC009-DRAW fired (F-108 dispatchDraw-contract)** |

HONEST CONCLUSION: F-107 removed the measured evidence-machinery costs
(`__tcf_0` gone from the profile) but did NOT change instruction throughput
or the composition frontier on this workload (segments within noise). What
moved the frame 0→197 px was F-108's R8-rename identity law (draw-stage
dispatch at budget expiry), not F-107's throughput fixes.

## 2. R-NEW-381 measured bottleneck (S62 instrumentation)

Added (S62, env-gated MINIANDROID_PERF_PHASES=1): per-instruction bucket
rdtsc split `insn.pre / insn.sw_non / insn.sw_inv / insn.post` +
PERF-OPS/PERF-CI (existing). Runs: run/s62_buckets (91s), run/s62_opself
(60s, in-init suppression removed), run/s62_f109_measure (60s, post-F-109).

Buckets (90s run, TSC=3.20 GHz calibrated): insn.pre 0.026% of wall,
insn.post 0.084% — loop bookkeeping is CLEAN. class_init phase = 46.8% of
wall; PERF-CI warm=7527 skipfw=42 **cold=718**.

Per-clinit duration distribution (scripts/s62_clinit_costs.py over the
timestamped log): 245 paired chains = 42.9s; **top-10 chains = 74% of
class-init time, top-50 = 95%**. Heaviest: Lug0; (23 instr <clinit> → 7.1s),
Lqk; (117 → 6.3s), Lbl; (1004 → 6.3s), Ls02; (475 → 3.6s), Lv52; (5 → 1.4s).

Causal chain inside the 7.1s chain (engine M3 METHOD-TRACE, run/s62_lbl_trace):
Lug0; → Lqk; → Lbl; → **1,024 invocations of Lnd1;.c** (bytecode 180) — the
register names ("Display P3", "NTSC (1953)", "SMPTE-C RGB", "scRGB
IEC 61966-2-2:2003") identify the androidx **ColorSpace Rgb transfer-table**
static init. 1,024×180 = 184K of the ~205K instructions executed in the 90s
run (90%).

Op self-time (60s, in-init suppression removed): sget-object 0x62 = 23.3 ms
per cold-init trigger (37% of wall), new-instance 0x22 = 9.4 ms (14.5%),
sget 0x60 = 88 ms (235 calls), sget-wide = 14.5 ms; ALL simple ops (iget,
return-*, move) are µs-fast. Total = **~69% of wall is first-touch
sget/new-instance carrying full cold-init subtrees of REAL interpreted work**.

ROOT CAUSE (S62 statement): composition volume = real androidx work
(ColorSpace transfer tables + Kotlin/ScatterMap statics) executed at
~1,459 inst/s average; the engine needs ~700K instructions to reach
composition completion, i.e. ~480s+ at the current per-op/per-invoke
constant costs — the composition does not complete inside practical budgets.
F-109a/c (this session: written-set bitmap + strcmp arith dispatch) improved
the early rate ~9-10% (100K @ 25.0s vs 27.4s) — honest: marginal; the
frontier is unchanged. Next measured lever (registered, not guessed): the
per-invoke constants (tri.resolve 15.8µs + em.setup 22.7µs measured) and
DalvikValue copy cost (2×std::string per register read/write).

## 3. R-NEW-331 — fragment host attach law: 3 NEW game consumers

Runs: run/s62_game_mines (minesweeper), run/s62_probe_org.secuso.privacyfriendlymemory,
run/s62_probe_org.secuso.privacyfriendly2048 — ALL die at the same first
failure: `[EXC-PROPAGATE] IllegalStateException "FragmentManager has not been
attached to a host."` from Landroidx/fragment/app/FragmentManager;.ensureExecReady
(pc=24) at the app's Splash/Main onCreate → APP BOUNDARY unwind.

S62 precision (run/s62_mines_trace.log): the FULL real androidx chain runs as
DEX — FragmentActivity.<init>, FragmentActivity$HostCallbacks.<init>,
FragmentController.createController, FragmentHostCallback.<init>,
FragmentManagerImpl.<init>, FragmentActivity.onCreate (16 units) →
ComponentActivity.onCreate → SavedStateRegistryController.performRestore —
all return OK — yet FragmentController.attachHost never dispatches (no
METHOD-IN; the APK string pool contains "attachHost", so the method exists).
First-engine face: the real lifecycle chain runs but the attachHost leg of
the upstream contract never executes in-engine → mHost stays null.

Upstream law (androidx fragment): FragmentActivity.onCreate calls
`mFragments.attachHost(null)` (≤1.3) before any transaction can execute;
ensureExecReady throws exactly this ISE when mHost == null (upstream
FragmentManager.java). Engine-side candidate law: when dispatching an
activity whose superclass chain contains androidx FragmentActivity, ensure
the real FragmentController.attachHost leg executes on the activity's own
mFragments object before app onCreate proceeds.

## 4. Games Spotlight — bouncy L6 (input → state → render, real DEX)

Run: run/s62_bouncy_l6 (com.dozingcatsoftware.bouncy, --click-count 6, 300s).
- Input: 6/6 clicks dispatched (U0113-XMLCLICK → REAL app DEX handlers on
  BouncyActivity obj#7: scoreViewClicked, doPreviousTable, doQuit,
  hideHighScore, ...). Also --tap pipeline verified (G06-TAP DOWN/UP law).
- State→render: 7 frames recorded; frame SHAs 0-2 = 4219c5116ea2,
  3-6 = 52e4ddacc8ac — a real render-state transition after click #3
  (dialog ink; visible_texts unchanged — TextView layer same, pixel layer
  changed). Representative frames committed:
  docs/evidence/s62_r381/bouncy_frame0_menu.png (35.5 KB) and
  bouncy_frame4_after_state_change.png (20 KB).
- L-level: **L6 (input → callback → state transition → render change)**.
  Honest: not claimed L7 (no multi-round game-loop interaction proof yet).

## 5. Search tools (real use, S62 ledger rows)

- zoekt-index v16: indexed miniandroid/src + docs → 117 + 963 files,
  shards 7.9 MB + 30.3 MB (overhead 2.9x), ~7s. Query "attachHost" →
  0 rows displayed (zoekt CLI; recorded under-reporting limitation).
- csearch (cindex over miniandroid/src + docs): query "ensureExecReady"
  → 2ms, hits docs/evidence/mc4_telegram/tg_run1_distilled.log — the same
  ISE face in the Telegram golden = 4th consumer of the R-NEW-331 law
  (cross-corpus reuse recorded; duplicate research avoided).
