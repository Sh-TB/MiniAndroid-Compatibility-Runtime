# CONT-38 Wave Ledger — 2026-10-26

User directive: «گیت هاب به روز رسانی ادامه ادامه تا هدف نهایی» — GitHub
self-update, then continue to the final goal (dooz+telegram کامل کامل,
the «حداقل ۳ تا برنامه دیگر کامل لود» criterion, the census wagons).

## PHASE 0 — self-update (honest)

Local container AT origin/main (68fbcd8f = CONT-37) — zero drift at wave
start (the CONT-37 wave itself performed the 331-commit catch-up). Binary
reproduced the CONT-37 lineage: sha256(256MB binary) prefix a95136b836bbb0bc
matches the recorded final binary; dooz 90s anchor 851cc1761a1dfcdf
reproduced pre-wave. Registry 834. Consumed the CONT-37 ledger + the named
next-wave items (the Lho1;.b ~pc2 same-site re-entry family, the
destination parent-chain walk, the boot-representation lever, the
tri.resolve/em.setup throughput lever).

## LAW F-NEW-543 — the M3-19 re-entry budget (ROOT-CAUSED-FIXED)

The named CONT-37 frontier (the same-site ~pc2 re-entry family, 6 kills)
root-caused with a new env-gated instrument (MINIANDROID_M3_CALLER=1 —
caller-chain dump at the kill site):

- dooz kill chain (depth=24): Lho1;.b (the snapshot observer-dispatch
  loop) → Li7;.h → Lto1;.c (CAS invalidation-queue drain) → Lso1;.a →
  Lww;.i → Lww;.h (the snapshot ADVANCE) → Lkc0;.m → Lho1;.c → the killed
  b — SEVEN upstream frames between the outer same-key frame and the
  re-entry.
- opencalc kills (depth=16): LN1/d;.b / LN1/g;.b re-entered across a
  NINE-frame handler walk (Looper dispatch → choreographer → view tree →
  Runnable → the SAME call site pc=44).

Both are upstream-legal REENTRANT-MONITOR nestings (compose snapshot lock
+ Looper dispatch are reentrant in ART; the nested dispatch observes the
DRAINED state). LAW: for a complete-payload same-key re-entry, execute
real DEX while the same-key ACTIVE depth < 2; stub at >= 2 (genuine cycles
still terminate at the budget). Per-key depth map replaces raw
set-membership; the set erases only when the LAST same-key frame leaves.

EFFECT: dooz kills 2 → 0 ([M3-19-REENTRY] releases: Lho1;.b#532 +
Lo52;.c); opencalc kills 2 → 0; BOTH anchors byte-exact.

## R-NEW-546 — the dooz board frontier moved a level deeper (REGISTERED)

Post-543 the board still does not paint (600s rc=0 run, anchor
byte-exact). Three new env-gated instruments + the corrected static
scanner pinned the frontier COMPOSITION-SIDE:

- [DRAWWIN-IN census] (cap env-tunable): the draw cascade RUNS —
  Lpz0;.L0 x1555, M0 x1769, Luc0;.g x205, rc0.e x203, rc0.c x971 (the
  draw-block INVOCATION fires 971x for other nodes) — Lz6;/Lmy;/Loc0; = 0.
- [L0-TRACE]: 22 of 25 Lpz0; nodes have P=NULL (the InnerNodeCoordinator
  is created ONLY in Lpz0;.r1 — the draw-block installer; nodes without an
  r1 install draw as childless arm-2 translations).
- [NEW-WATCH]: Lz6; (the board Canvas lambda) NEVER allocated in a whole
  run; METHOD-IN 1.09M entries: Lel0;.<init> x90, r1 x105, Luc0;.<init>
  x19, **Lz6;.<init> = 0**.
- Corrected static scan: exactly 4 allocation sites
  (Lcx0;.p / Le7;.b / Lfn0;.f / Lqu0;.q) — ALL never execute.

Registered with the full tooling bank (9 decode/scan scripts, 9 run dirs).

## R-NEW-547 — the telegram envelope attribution CORRECTED (REGISTERED)

New [BOOT-RSS] per-stage instrument (default-on, zero behavior change;
first cut misread statm field 1 = VmSize 5936MB, corrected to VmRSS):

- load_apk 72MB → parse_dex 146MB (**+74MB — NOT the bulk!**) →
  load_classes 159MB → execute_application 2869MB (**+2710MB during
  execution**), render 2883MB.
- [HEAP-CENSUS] at 50K-insn ticks: live_objects 10.3K → 13.4K over 14.4M
  insns — the interpreter heap is NEGLIGIBLE.

The F-NEW-542 "GC lever is dead" conclusion STANDS; its "boot-representation
bulk" naming does NOT: the ~1.9GB accrues in the FIRST ~100K instructions
(engine-side first-touch class materialization — ~19KB/insn). The next
wave owns the allocation attribution inside execute_application. The
telegram envelope itself holds: the 60s window was OOM-killed by the 3GB
sandbox ceiling; the 22s window reaches LaunchActivity.onCreate REAL UI
draw dispatch (c4;.dispatchDraw, F084 budget-bound, RSS flat 2849MB).

## REGRESSION WALL at the final binary (sha256 prefix 7927c7c82a9c66d4)

- anchors 6/6 BYTE-EXACT: opencalc 63020bc7334048fe / chess 3f7e670759b7c6a8
  / microtimer bbd350b6c14fbd52 / unote 7481e9b468eaa376 /
  tower3d 11a38a5aeeff45a6 / dooz 851cc1761a1dfcdf
- games 7/7 EXACT-TO-PIN: g2048 f43face08299ffc6 / tetris b818a6a7016bea8e
  / snake_deluxe 5235683fc7b1f04b / snakeneon 2617c81c9e72b195 /
  ttt_deluxe db1d633d77b5819a / minicraft e77a073f733255eb /
  gmdice 3891679dff449331
- negatives 19/19 PASS; reinstall matrix 8/8 PASS; skill 13/13 PASS
- batch-50 census 50/50 rows — 13/13 content rows BYTE-EXACT RETAINED
  (evidence/cont38/batch50_census.json): librecontacts 1214501px /
  bouncy 1137140 / balance 500130 / peri 325303 / netguard 324655 /
  airlyrics 243000 / fossify_math 192398 / fossify_calendar 192024 /
  listai 73635 / starlingmap 58612 / wocheneinkauf 44227 / uturn 10782 /
  aat 5285. The «حداقل ۳ تا برنامه دیگر کامل لود» criterion remains MET
  with the same 5 complete-first-launch-UI titles (visual evidence at
  run/cont37_batch50/r_*/screenshot.png; no new crossings this wave —
  honestly recorded).

## REGISTRY 834 → 837 (id-unique)

F-NEW-543 ROOT-CAUSED-FIXED; R-NEW-546 REGISTERED (dooz composition
frontier + instruments); R-NEW-547 REGISTERED (BOOT-RSS instrument +
F-NEW-542 envelope correction). Canonical projection regenerated
id-for-id.

## NEXT WAVE (named, evidence-backed)

1. R-NEW-546: the four Lz6; allocation-site invokers (Le7;.b /
   Lcx0;.p / Lfn0;.f / Lqu0;.q) — who should dispatch them, why the
   destination composition stops before the Canvas block materializes.
2. R-NEW-547: allocation attribution inside execute_application — the
   1.9GB/100K-insns allocator named with per-subsystem counters or a
   heap-profile run; then the structural cut (interning/lazy
   materialization) to bring telegram inside the 3GB sandbox for the 60s+
   windows.
3. The Lo52;.c WindowInsets re-entry walk decode (if it resurfaces).
4. The deferred-UI family re-test (chess/klondike/tripeaks/flappycow/
   ballbreak) + fossify_math/calendar damaged faces.
