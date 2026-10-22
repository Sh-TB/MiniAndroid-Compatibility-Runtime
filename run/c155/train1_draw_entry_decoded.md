# CONT-155 TRAIN 1 — Draw-entry enumeration map (F-NEW-481 refinement)

Binary: f6b272ea24927363 (deterministic rebuild #9, byte-identical). APK: dooz v23.
Baseline wall: 9/9 anchors MATCH before work (cont152_wall.sh).

## New tool
`scripts/cont155_methxref.py` — whole-dex invoke-site xref for one method, with
instruction-ALIGNED stepping (SIZES law ported verbatim from verified
cont151_disasm_regs.py), per-list-restart method_idx naming (cont153 verified law),
and class_data walk fixed to dex spec (field entries precede method entries; the
field-skip count is sf+ifc, NOT dm_s+dm_i — 4 walker bugs fixed en route:
class_def stride 32 not 4; sf+ifc skip count; opcode = LOW byte of LE unit;
midx diff-chain naming per list restart).

## The two call sites of Lel0;.i (whole-dex, instruction-aligned)
1. `Lt4;.dispatchDraw` unit 46 (pc=92) — THE per-frame view draw pass.
   Disasm proves: const-string "AndroidOwner:draw" -> Trace.beginSection ->
   Canvas fetch (y3.a/Canvas.a swap) -> `invoke Lt4;.getRoot` -> `Lel0;.i {root, canvas}`.
   **getRoot is re-read EVERY frame — the root is NOT snapshotted.**
2. `Lug0;.h1` unit 27 — the layout-bounds OVERLAY draw (correctly gated, TRAIN 8).

## REFUTATION (honest correction of CONT-154 TRAIN 2 structural law)
TRAIN 2 wrote: "draw loop iterates a scope list snapshotted at first layout".
FALSE at the root level: dispatchDraw calls getRoot per frame. The stale binding
lives DEEPER — inside the receiver chain and the layer callbacks (below).

## Receiver chain inside Lel0;.i (14 insns, fully decoded)
`this.I` (Lkz0;) -> `kz0.d` (Lpz0;) -> `Lpz0;.L0(pz0, pz0, canvas)`.
L0 (70 insns): owner flag guard (Lc31;.P) -> time math (0xFFFFFFFF mask nanos->ms)
-> `Ldi;.f` pre-hook -> **`Lpz0;.M0`** -> `Ldi;.f` post-hook. Single scope, no recursion.

## Lpz0;.M0 callers (whole-dex, exactly 2)
1. `Lpz0;.L0` unit 61 (root-chain entry, above).
2. **`Loz0;.a` unit 24** — Loz0; extends Lgk0; (lambda class), fields (I f, Lpz0; g),
   `a()` = state-switch: flag f -> packed-switch -> `M0(pz0.L, pz0)` or `Z0` fallback.

## Loz0; call graph (the draw-block lambda)
- Created in `Lpz0;.r1` unit 65: `Loz0;.<init>{v0, v12, v10}` — **v10 = the pz0
  currently being drawn**: each r1(pz0) invocation creates a FRESH lambda capturing
  THAT pz0, then `s1(v10)` + `oz0.a()` (units 231-241) -> M0.
- r1 callers (5): `Lpz0;.i1` pc=2, `Lpz0;.k1` pc=12, and the LAYER callbacks
  `Lem1;.g` pc=56, `Lff;.g` pc=46, `Lsc0;.g` pc=124.
- Layer-callback law (all three identical shape):
  iget-boolean `Lwt0;.e` -> if-nez gate -> `Llo;.T` -> iget-object `layer.t` (Lpz0;)
  -> `r1(t)`. **The drawn pz0 is the layer's FROZEN `.t` field.**
- `Lpz0;.e1` callers: `Lel0;.a` pc=46, `Lqz0;.b` pc=62 (the kz0 chain-build path).

## LIVE FIELD-TRACE (MINIANDROID_FIELD_TRACE='Loz0;.g', run/c155/t1_oz0g.log)
41 events, ALL `Loz0;.<init>` puts, ZERO rebinds:
- Early captures: obj#2356->2061, obj#2721->2717 (the two early scopes).
- **LATE captures DO happen: obj#6311->6309, #6336->6334, #6461->6459, #6481->6479,
  #6487->6485, #6512->6510, #7864->7862, #8983->8981 ... #9247->9245** —
  the engine re-runs the composition that creates late draw lambdas; the captures
  are CORRECT.
- T0-window census (TRAIN 7): receivers 2717 x54 / 2061 x54 / 2708 x30 / NULL x12 —
  zero late receivers. **The 2 early lambdas were replayed ~54x each; the ~39 late
  lambdas were invoked ZERO times.**

## Refined single question (TRAIN 2)
r1() creates the late lambdas AND (same method) calls oz0.a() — so a late r1 call
should produce late T0 windows. Since it does not, r1 must RETURN EARLY for late
pz0s. Both replay sites (unit 231-241 / 327-334) sit behind the `Z M` flag
(iput v1, v2, Z M at 236/329 — check-cast Lc31; P pattern). Next single question:
**the `M` flag and the `wt0.e` gate values on late pz0 layers** — who sets them,
when, and why late layers fail the gate. FIELD-TRACE targets: `Lpz0;.M`,
`Lc31;.P`, `Lwt0;.e`.
