# CONT-43 — "Cross the page": the calculator fix landed with zero drift,
# the dooz case-E frontier resolved (first real content frame ever), and
# an F-NEW-304-sourced csw regression exposed and rooted.

Date: 2026-10-11 · Session start: origin/main `b1668290` (CONT-42), container
recovered from a stale snapshot via `git fetch + reset --hard origin/main`
(fast-forward; the local tree had rolled back to a CONT-10-era image).
Registry 612 → 615. Final binary `3dab3038c222031e` (head b1668290 + this
wave's laws).

Directive: "برگرد به راه حل مشکلات خودمون — باید بتونی دوز و ماشین حساب رو
از اون صفحه رد بکنی" + "ادامه با تعداد بالای تسک همزمان" (continue with many
tasks in parallel). Both frontiers attacked in parallel; recovery + rebuild
+ all evidence below were produced this session.

---

## 1. Front A — the calculator (com.tananaev.calculator v1.10) crosses the
## FragmentTransaction page

CONT-42 left the tananaev blocker precisely recorded: the FragmentTransaction
drain (F-NEW-304) made the fragment machinery live (4 real preference entries
parsed, tree attached) but the frame stayed DEFAULT_BACKGROUND_ONLY
`d602648e8e401895` because platform wrap-content subtrees under a
DEX-measuring parent default-measured full-screen (the old
`getDefaultSize(spec)` law: AT_MOST → the FULL available size), and the
companion native class-measure law that fixed it deterministically moved the
opencalc golden and was REVERTED.

### 1.1 The re-landing (companion law + subtree-coherence fix)

The companion law is RE-LANDED at the two CONT-42 guarded insertion points
(`dalvik_engine.cpp`, S109 ROOT-042 bridge: the ROOT-045b descent lambda and
the top-level child loop). A no-DEX-override child now goes through
`ResourceRuntime::inflater().measure_view_spec(...)` — the honest AOSP
View.measure class dispatch (TextView shaping, LinearLayout weights, Frame-
Layout max-extent, TableLayout rows, ConstraintLayout anchors, RelativeLayout
dependency sort — the canonical laws inside `measure_node_raw`).

**The CONT-42 opencalc breakage is root-caused and fixed — it was a
SPLIT-BRAIN MEASURE, not a law conflict.** The native class law measures the
whole subtree COHERENTLY (its own container law computes weights/table cells/
anchor edges and writes every descendant's `measured_width/height`), but the
engine's ROOT-045b descent then RESET each node's `dex_measure_valid` and
re-measured subtree members at cruder per-node specs — opencalc's pad got
cell widths overwritten while the row law's x-pitch survived → overlapping
digit labels ("98" superimposed; zoom evidence
`evidence/cont43_opencalc_pad_zoom.png`). The fix: nodes measured by a native
class-law subtree pass are MARKED (`f304_native_subtree`), the descent
defers (no reset, no re-measure) for the pass.

### 1.2 The A/B verdict

| binary | tananaev ×3 | opencalc ×3 |
|---|---|---|
| PRE (CONT-42 source, rebuilt `5b7cb20a2c17441c`) | `d602648e8e401895` rc=1 | `a976d2f9fb675cb3` |
| POST (companion law, no coherence) `130c665a1f257fc3` | `0f649804d6e0486d` **rc=0 SUCCESS** | `0a0b26cf69b0f378` (the CONT-42 break, reproduced exactly) |
| POST+coherence (final `3dab3038c222031e`) | `0f649804d6e0486d` **rc=0 ×3** | **`a976d2f9fb675cb3` — the exact golden RESTORED** |

The coherent honest dispatch is semantically neutral for opencalc by
construction — zero drift AND the calculator fix, in one law.

The tananaev fix face `0f649804d6e0486d` (rc=0): 4 REAL preference entries
parsed (`addPreferencesFromResource 0x7f110000 → 4 entries (res/SF.xml)` with
the real titles "Notification settings" / "Ongoing notification" / "Lock
screen notification"), rows measured 1080×44 at real y-pitch, tree attached
(view#456 into container#379), full drain ladder fired, run completes clean.

**Honest remaining leg (F-NEW-305)**: the rows render UNDER the appcompat
action-bar band — the frame shows the gray ActionBarContainer band + tinted
background, 0 dark pixels (no row text visible). AOSP law:
ActionBarOverlayLayout's action-bar inset dispatch positions content BELOW
the bar (non-overlay mode); the engine hosts the real appcompat classes
(C013-HIER confirms ActionBarOverlayLayout/ActionBarContainer) but leaves
the content at y=0 and the bar band's z-order overdraws rows 0..~176.
Root-caused, PENDING fix — the fragment/preference family's slice 2.

## 2. Front B — dooz v23 case-E resolved; the first real content frame

### 2.1 The discriminating measurement (zero engine change)

CONT-40's open question: is the 14.3M-instruction composition at the wall
halt PROGRESSING or CYCLING? Answered by a budget ladder (identical binary,
`--trace` + `MINIANDROID_CANVAS_DRAW_WIN_TRACE`):

| budget | instructions | app-owned draw ops (RENDER_OK) |
|---|---|---|
| 15 s | 4.7M | **155** |
| 45 s | 13.7M (×2.9) | **659** (×4.25) |

OPS GROW WITH BUDGET; the `[PROGRESS]` tail methods differ between the two
halts; the rate is a steady ~300k insns/s. **The composition PROGRESSES —
case E is a boot-cost root, not a hidden spin.** Mechanism note: the wall
clock is a `static thread_local` deadline from the FIRST DEX instruction of
the run — after it passes, every later window halts immediately (266
`[WALL-STOP]`s in one run). The F-NEW-298 frame-honesty law then keeps the
white `31ddd4d5b8e6d18e`.

### 2.2 The boot completes — the REAL Dooz scaffold renders

With a fair budget the boot composition COMPLETES and the run ENDS (no
halt): 90 s (25.4M insns, wall 82 s) and 180 s (51.6M insns, wall 76 s) both
produce the same deterministic frame **`6841d52a20e6597e`** — locked ×5
(x3 + x2 on the final binary; now a standing gate, `cont37_regression.sh
dooz180` ×3 MATCH):

- 2,073,600/2,073,600 non-white pixels (100% — the white-screen era is over)
- Material3 surface (250,248,254) 88.7% + secondary band (237,237,246)
- accent pill (185,203,255) 25k px, **15,876 black glyph/icon pixels** —
  the top-bar action icons, the bottom app bar's FAB circle and rounded
  pill button (render `evidence/cont43_dooz_ext180_frame.png`)
- all 5 frames byte-identical (steady state from frame 0)
- the run's uncaught exceptions drop 23 → 12; stub-census 472k → 5.44M
  IMPLEMENTED (the app executes ~11× more real surface)

**Honest residual (F-NEW-307)**: the frame census still reports
`app_draw_ops=0 / VIEWTREE_NO_APP_PIXELS / first_missing_stage=APP_DRAW_OPS`
despite the rendered app content — the census's draw-window attribution does
not count the Compose paint path that actually painted (the [CDW-OP] trace
caps at 400 lines and stays silent). Fixing the attribution flips dooz to
REAL_APP_CONTENT honestly. The boot cost itself (25M instructions for the
first frame) is the perf frontier. The CONT-40 identity-hash
interleaving-sensitivity probe remains the prerequisite for any engine
change on this path.

## 3. Front C — the csw regression EXPOSED (F-NEW-304's own, not this wave's)

The full gate caught composeStopwatch drifted `3442d9a9dc0fa0f9` →
`5c4a0172628849ba` (deterministic ×3) — `5c4a0172` being the exact
"single-color, text lost" face CONT-40 recorded under the PARKED
getWindowToken law. Isolation:

| binary | csw ×3 |
|---|---|
| CONT-41 source tree, THIS environment (`7063c7238e0de79b`) | `3442d9a9dc0fa0f9` — the healthy face |
| CONT-42 source (F-NEW-304), no companion law (`5b7cb20a2c17441c`) | `5c4a0172628849ba` |
| CONT-42 + this wave's laws (`3dab3038c222031e`) | `5c4a0172628849ba` |

**The regression is F-NEW-304's own (the CONT-42 wave never ran the target
case); the CONT-43 delta is exonerated.** First divergence decoded: the
androidx LifecycleDispatcher ReportFragment (`Li01;`, tag
`androidx.lifecycle.LifecycleDispatcher.report_fragment_tag`) now DRAINS
through real DEX (clean — zero exceptions in the drain window); the compose
boot then takes a different interleaving in which `Laj0;.n`
(performMeasureAndLayout, the "unattached/unplaced root" guards) dispatches
`isEmpty()` on a NULL state object (`Lgi0;.f` — and `Lgi0;` is NEVER
ALLOCATED per `MINIANDROID_ALLOC_TRACE`: the content-state object graph
never forms); the catch-all NPE at `Lh4;.onMeasure` degrades the boot from
4.4M to 600k instructions (no dialog/choreo content). This is the same
identity-hash interleaving knife-edge family CONT-40 flagged — the
discriminating-probe prerequisite applies. Registry F-NEW-306 (P0); the csw
anchor expectation STAYS `3442d9a9` (content must be REGAINED, not
re-baselined down); the target case now carries the full analysis comment.

## 4. Zero-drift regression (final binary `3dab3038c222031e`)

- **anchors 27/27 ×3 byte-identical** (the 8 recorded apps + tananaev newly
  pinned at `0f649804d6e0486d`; opencalc golden RESTORED by the coherence
  fix; dooz 15 s white face retained) — the full battery ran three complete
  rounds (81 runs), zero DRIFT.
- **dooz180 ×3 MATCH** `6841d52a20e6597e` (new standing content gate).
- **probes == records exactly**: fcol 140/0, f259 49/0, f259g 84/7 (known
  rows), f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0,
  ckey 105/0, cpipe 119/0, fnew302 48/24 (documented), fnew252 56/0,
  fnew290..296 == records, fnew297 42/0, fnew298 19/0 KEEP=5 corner=PASS.
- frag_tx_probe 12/0 ×3; notif_builder_probe 56/0 ×3.
- simplecalc ×3 rc=0 `7960bce447ac6d8f` (APK re-fetched SHA-exact
  `68da25fd9fdf54b4`; composeStopwatch_1009011 re-fetched SHA-exact
  `dbf937ebbe7c0b3d`; tananaev calculator_11 re-fetched SHA-exact
  `294a68bd00debbdc` — all lost to the container reset, all restored and
  verified against the recorded SHAs).
- target csw: 5c4a0172 — the EXPOSED pre-existing regression above (rooted,
  gated red deliberately until F-NEW-306's fix).

## 5. Registry + artifacts

- F-NEW-304 refreshed: companion law re-landed + coherence fix + tananaev
  frontier PARTIAL → rc=0 SUCCESS.
- F-NEW-305 (P1): tananaev visible-rows leg — ActionBarOverlayLayout inset
  law missing (content at y=0 under the bar band).
- F-NEW-306 (P0): csw content-state regression sourced to F-NEW-304's drain
  interleaving (first divergence decoded; fix next wave).
- F-NEW-307 (P1): dooz case-E resolved (progressing-not-stalled; boot
  completes ~80 s / 25M insns; content face `6841d52a20e6597e`) + the census
  attribution gap.
- Registry 612 → 615 (`scripts/cont43_registry.py`).
- Evidence images: `evidence/cont43_dooz_ext180_frame.png`,
  `evidence/cont43_dooz_ext180_small.png`, `evidence/cont43_tananaev_frame.png`,
  `evidence/cont43_opencalc_pre_post.png`, `evidence/cont43_opencalc_pad_zoom.png`.
- Wave scripts: `scripts/cont43_csw_decode.py` (the Laj0;/Ly9;/Lgi0; DEX
  decode), `scripts/cont43_registry.py`; run artifacts under `run/cont43/`.

## 6. Next wave (priority order)

1. **F-NEW-306 (P0)**: regain csw's visible content — the CONT-40
   discriminating probe (progressing vs cycling + oid/hash order) first,
   then the fix on the drain/interleaving path.
2. **F-NEW-305 (P1)**: the ActionBarOverlayLayout inset law — tananaev's
   rows become visible below the bar band (the calculator page fully
   rendered).
3. **F-NEW-307 (P1)**: the frame-census Compose-paint attribution — dooz
   flips to REAL_APP_CONTENT at the `dooz180` gate; then the boot-cost
   perf decode.
