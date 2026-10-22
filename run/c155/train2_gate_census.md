# CONT-155 TRAIN 2 — Late-layer gate census: the replay leg never executes

Binary: f6b272ea24927363. APK: dooz v23. Live runs in run/c155/ (t2_*.log).

## Decisive live evidences
1. **METHOD-TRACE `Loz0;|a` = 0 lines** (run/c155/t2_oz0a.log, full 5-frame run):
   `Loz0;.a` NEVER EXECUTES. The entire lambda-replay leg of the Compose draw
   pipeline (layer callbacks em1.g/ff.g/sc0.g -> r1 -> fresh Loz0; -> oz0.a -> M0)
   is dead at runtime. All M0/T0 windows come from the root chain (el0.i -> kz0.d
   -> L0 -> M0).
2. **FIELD-TRACE `Lel0;.M` = 19 events** (t2_em.log): ALL puts from `Lel0;.<init>`,
   all value=1 (early obj#2039 + late obj#6300/6325/.../9xxx). The r1 in-method
   M-flag write (op5c at units 236/329) never fired — consistent with (1).
3. **FIELD-TRACE `Lpz0;.M` = 0 events** (t2_pm.log): M is an Lel0; field (layout
   node), not pz0 — first-guess corrected, trace re-run as (2).

## M0 fully decoded (120 insns, disasm in this file's companion session log)
pc0-1: `const/4 v0,#4; T0(4, this)` — kind-4 acceptance (TRAIN 8 law).
pc5-10: T0-null -> `h1` overlay fallthrough -> return (the blank face).
pc11-49: T0-hit -> node.s fetch, getSharedDrawScope, Leo;.S(g) time math,
   **`Lgl0;.c {v3..v9}` — the real content draw call**.
pc53-107: **THE CHAIN WALK**: loop { v11=(Lfw;)v1; v11 = v11.t? no — v11 = v1;
   v11.t fetch; if null break; v8 = v11.g (bitmask); if 0 skip; **v1 = v11
   (advance)**; Liw0; iterator (b()=next) for multi-child; **v11 = v11.j** (the
   chain LINK) } — tests every chain node's `.g` mask against kind-4.
pc114: Llo;.P.

## The completed F-NEW-481 law (TRAIN 1 + TRAIN 2, all machine-verified)
1. Per frame: dispatchDraw("AndroidOwner:draw") -> getRoot -> el0.i -> root.I ->
   kz0.d -> **ONE frozen pz0** -> L0 -> M0.
2. M0 walks the pz0's wt0 `.j` chain; draws content ONLY where kind-4 acceptance
   passes (TRAIN 8: h&4 and g&4).
3. The chain reachable from kz0.d contains ONLY early nodes (deliberate
   re-termination, TRAIN 7 CONT-153); bit-0x4-capable nodes live ONLY in late
   chains (TRAIN 9 census: 20/69 g-puts with 0x4, all obj#6xxx/9xxx).
4. The engine's second draw leg (layer-invalidate replay: em1.g/ff.g/sc0.g ->
   r1 -> fresh Loz0;(f,pz0) -> oz0.a -> M0) is **NEVER EXECUTED** (this file, (1)).
5. Composition DOES re-run: late draw lambdas are created with CORRECT late
   captures (TRAIN 1: 39 late Loz0; instances, zero invocations).

## Root-cause statement (engine-missed pipeline leg, app-independent)
The runtime implements ONLY the root-chain draw leg of Compose's draw pipeline.
The layer-invalidate replay leg — which on ART re-invokes the per-layer draw
lambdas (r1/oz0.a) that composition registers as scopes populate — is absent.
Result: every frame redraws the FROZEN early chain (kind-4 fails on every node
-> h1 overlay only -> blank face) while correctly-built late draw lambdas sit
uninvoked. This is the generic root for the 49-app APP_DRAW_OPS cohort.

## Fix lever (next train's single question)
Where does the engine's Choreographer/view draw loop end, and what structure
holds the created Loz0;/r1 callbacks? Candidate generic fixes (both
app-independent): (a) replay registered layer draw lambdas after dispatchDraw
(composition-ordered), or (b) rebuild/refresh the root chain head (kz0.d) when
late scopes register. Decision requires decoding who STORES the Loz0;/lambda
references post-<init> (they are strongly reachable — GC keeps them) — FIELD-TRACE
of the holder fields via allocation-site backtracking, or the engine-side
invalidation queue census.
