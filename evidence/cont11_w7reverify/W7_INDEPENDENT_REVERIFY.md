# CONT-11 W7 RE-RUN — INDEPENDENT RE-VERIFICATION FROM A COLD CONTAINER RESET (2026-10-24)

## What this container was

This session started from a container reset at the **CONT-10 snapshot `e99c2fbd`**
(registry 566) — the remote main had already advanced through CONT-11 W7 → CONT-14
batches (registry 834, F-NEW-519 latest) → CONT-17/CONT-18h. The session therefore
**independently re-derived** the dooz draw-path chain without knowledge of the
remote's progress, then reconciled against origin/main at `2a2905b5`.

## What was independently reproduced (all CONFIRMED against the remote truth)

Remote authority: `evidence/cont11/CONT11_W7_DRAW_ROOT_CAUSE.md` + registry
**F-NEW-265** (re-rooted dooz first divergence; measure pass dies →
isPlaced=false). This re-run's findings MATCH it link-for-link:

| Link | Remote (F-NEW-265 chain) | This re-run (binary `e0a019853da44b8a`) |
|---|---|---|
| Lineage | rebuild byte-identical `aed46450c103f2ea` | cold rebuild; **5 anchors ×3 byte-identical** (opencalc a976d2f9fb675cb3 / chess b5a7a35d5fe0564b / dooz d602648e8e401895 / microtimer da73010a37dd0189 / unote 4f1a9e4e8f64fae8) — engine SEMANTIC-NEUTRAL (trace_exporter.o built -O1 after kernel OOM-kills; deviation recorded) |
| dispatchDraw | runs per frame, canvas holder swap, root.draw | `dispatched=YES ops=0`, traced pc=0..143 return-void; holder swap at pc=132-156 (Lt4;.w=Lhi; → Ly3;.a), root.draw(Ly3;) pc=184 |
| R8 map | Ly3;=AndroidCanvas via Lhi; CanvasHolder; Ljt1; = text-path forwarder (W6 face was a symptom) | SAME map corrections derived independently (disasm + per-instruction traces) |
| Draw walk | reaches InnerNodeCoordinator.performDraw; canvas.translate live | Lel0;.i ×164; Lpz0;.L0 path-B ×82 translate-pairs; M0 ×164; Ly3;.f ×164; Ly3;.p (drawRect) ×0 |
| Draw-node lookup | T0(4) = head(Nodes.Draw), 4 = 0b1<<2 (NodeKind.kt) | same; every visited chain lacks bit-4 masks (e.g. 5039275=0x4CE30B) |
| **The gate** | isPlaced never set on composed nodes | **Lel0;.I()Z = isPlaced: FALSE ×108 / TRUE ×18** — the remote's quantitative face REPRODUCES |
| Composition | healthy | Lel0;.<init> ×39, Lv02;.c ×94, Lel0;.B ×138, Lrr0;.h ×441, Ld;.i ×23 |

## Registry discipline

**root_registry.json was NOT modified.** An interim local registration
("F-NEW-261 = placement gate") collided with the remote's F-NEW-261 (S83-APXACT,
IMPLEMENTED+TESTED) and was dropped at reconciliation; the live root is and stays
**F-NEW-265** (with arm (c) = F-NEW-271). No root inflation.

## 40% old-apps block (at THIS re-run's binary — the CONT-10-era engine, i.e.
pre F-NEW-264/519; the remote's CONT-14-B4 binary carries more fixes, so these are
regression datapoints for the older binary, not the current one)

- forkgram (Telegram classic 12.10.8 vc709208): **REAL_APP_CONTENT ×2 byte-identical
  `cf4c41e62ceb6557`**; 44 in-flight exceptions past app frames (UnsatisfiedLinkError
  `ApplicationLoader;.onCreate` pc=0x128 native-lib; NPE family
  `Lorg/telegram/ui/ActionBar/d6;.b0/y3/x3` launch-layout init) — the honest remaining
  Telegram frontier at this binary.
- Old-games regression ×2 each, ALL REAL_APP_CONTENT: 2048 `59ca1526611c4622`,
  SnakeDeluxe `34a712689ce66e58`, MiniCraft `b0876952f41e4af2`, Tetris
  `f360daa244cfca8d`, SnakeNeon `24fb7694eb64634a`, gmdice `f3b483fe7b7cf51b`.

## Reusable tooling banked

- `scripts/cont11_disasm_dispatch.py` — per-method Dalvik disassembler (androguard;
  maps trace pcs to call targets)
- `scripts/cont11_buildloop.sh` — OOM-resilient single-thread build loop
- `scripts/cont11_baseline.sh` / `cont11_drawtrace.sh` — anchor + trace runners
