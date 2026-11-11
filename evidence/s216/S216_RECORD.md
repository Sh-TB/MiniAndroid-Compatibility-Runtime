# S216 — CONT-131 WAVE RECEIPT + THE CONT-132 SOFT-STOP RETURN-VALUE LAW

Binary (post-law): `74f1d2c24cb8e40b` (full -O2, -j1 foreground chunks; provenance-only)
Base: main `01586a17` (S215d tip) + R14 superclass-first class-init law (A-R3 #580, 42 lines) + the CONT-131 wave parts 1-4.

## 1. The CONT-131 wave application (T21/T22 verified)

| part | file | declared sha16 | recomputed | apply |
|---|---|---|---|---|
| 1/4 | dalvik_engine.h (76 lines) | `4204890f8f935a17` | `4204890f8f935a17` | CLEAN |
| 2/4 | dalvik_engine.cpp (171 lines) | `b14853c9059728bf` | `b14853c9059728bf` | CLEAN (after source restore, see §1a) |
| 3/4 | execution_engine.h (30 lines) | `f44512952585dded` | `f44512952585dded` | CLEAN |
| 4/4 | execution_engine.cpp (105 lines) | `a7d6b3c77ac9e6bd` | `a7d6b3c77ac9e6bd` | CLEAN |

**§1a The reconciliation law**: the local tree carried a partial hand-written
soft-stop implementation (from the interrupted pre-recycle S216 instance) that
collided with part2's hunks at dalvik_engine.cpp:17475/21009. Resolution: the
four source files were restored to `01586a17`, the instance's OWN R14 law was
replayed from the saved diff (evidence/s216/r14_replay.diff, 49 hunk lines),
then the four wave parts applied in order. The hand-written fragments were
discarded in favor of the lane's byte-exact delivery (T21/T22 discipline).

## 2. The CONT-131 battery on this line (scripts/s216_cont131_battery.py)

### Golden (no-tap, default geometry) — the row-#21 contract

| run | face | vsync ticks | choreo | wall |
|---|---|---|---|---|
| g1 | `a0fae9072313e2d1` | 6 | 25 | 196.7s |
| g2 | `a0fae9072313e2d1` | 6 | 25 | 197.7s |
| g3 | `a0fae9072313e2d1` | 6 | 25 | 199.4s |

**GOLDEN ×3 BYTE-EXACT HOLD — the four laws are byte-inert for the golden;
the vsync drip is LIVE (6 ticks = the lane's own POST number).**

### Tap run (#573 recipe `765,1830@6 + 540,960@10`, 16 frames)

| row | pre-law binary (3c3c4aa8) | post-law binary (74f1d2c2) |
|---|---|---|
| aput-oob storm | 12-15 per run (`Lbw0;.a` pc=8 / `Lbw0;.k` pc=6 / `Lso1;.b` pc=29, wild index = the raw key hash: -879540352 / 832694404 / -2087608294 …) | **0** |
| "Parent job is Cancelling" | storm present | **0** |
| uncaught | 2 | **0** |
| final face chain | … → eccabf41 (white) | … → eccabf41 → **10d4a156** (NEW face — deeper than any pre-law run) |
| soft-stop rows | 1 | 1 |
| hard / backstop | 0 / 0 (R14-off) | 0 / 0 |

The pre-law A/B was run with `MINIANDROID_R14_SUPER_INIT=0` (the R14 law
default-ON): poison 32,717 / oob 15 / uncaught 2 — the R14 delta is NOT the
OOB cause (verified).

## 3. THE CONT-132 ROOT (evidence-complete, the #25 core law)

**The CONT-131 wave's soft draw-window stop breaks the fetch loop BEFORE any
return instruction; the F-084 HALT-RETURN contamination discriminator
(`halted_ && !halted_on_return_`) cannot see a soft exit (both flags false),
so `try_recursive_invoke` handed `last_invoke_return_` — the callee's LAST
INTERNAL invoke result — to the caller's move-result.** Live face: the dying
`Lbw0;.d` (the compose ScatterMap probe) had just computed the key hashCode
(its first internal invoke, DEX-verified at pc 6-9 via androguard); the
soft-stop broke the frame mid-probe; the caller `Lbw0;.a` pc=8 `aput-object
v4, v2, v1` consumed the raw hash as the slot index → ArrayIndexOutOfBounds →
catch-alls → coroutine job cancellation ("Parent job is Cancelling") → the
gesture chain died before onClick. This is the F-084 comment's own historical
face (`-733270216`, "dooz v23 observed the downstream face") returning through
the NEW soft channel — and it is S211's "scan-claim state interleaving under
engine re-entrancy schedule" resolved to an exact mechanism.

APUT-OOB register dump (MINIANDROID_LOOP_LOCALS_DIAG, trace10 run): receiver
o15283 `Lbw0;` c=7 e=6 d=0, b[7] all-zero, control words all-empty + 0xFF
terminator — the receiver is a CLEAN freshly-initialized map (the lane's
ctor-zombie theory is NOT this face's mechanism on this line; the corruption
was in the CALLER's consumed register, not the map state).

### The law (7 edit sites, `soft_stopped_no_return_` member)

1. `dalvik_engine.h` — the member + law comment.
2. `execute_method_internal` frame entry — per-frame reset.
3. + 4. The fetch-loop soft break AND the deadline-hit break set the flag.
5. `try_recursive_invoke` save set — the flag saved with the EXP-054/055 set.
6. The post-call discriminator: `else if (soft_stopped_no_return_)` →
   `return_val = make_null(); last_invoke_return_ = make_null();` (the
   DEFINED polymorphic zero — the soft channel's graceful-unwind contract
   means the interrupted callee never feeds the caller a value; the caller's
   own loop breaks at the next soft check and never consumes it).
7. The restore block — the flag restored with the saved set.

The diff ships in this commit (`evidence/s216/cont132_soft_stop_return_law.diff`).

## 4. FULL 6-PIN GATE on the post-law binary 74f1d2c2 — ALL HOLD

| pin | face | verdict |
|---|---|---|
| bouncy | `8a6c24ac8a7d718e` | HOLD |
| unote | `3b8dcb0adbbc17a9` | HOLD |
| dooz (15s golden) | `a0fae9072313e2d1` | HOLD |
| gmdice ×2 | `3891679dff449331` | HOLD, rerun-identical |
| microtimer | `b39665f68f3938e6` | HOLD, 0 uncaught |
| ttt ×3 | `7354c1b231cd581d` | HOLD, deterministic ×3, 0 uncaught |

`make test` 4/4. Evidence: evidence/s216/S216_GATE.json + gate_runs/.
All faces' PNG sizes < 800KB (the S214 noise heuristic: 0 NOISE-SUSPECT rows).

## 5. THE DOOZ180 COVERAGE GAP (honest finding for the lane)

The CONT-131 wave battery measured golden/tap/ttt but NOT the dooz180
standing gate. On the post-wave binary the 180s-budget boot does NOT
complete: 84.9M instructions executed (~470k/s), F084 wall-stop mid-boot,
final face = the white `a0fae907` (want `4f32f50fd55ccf90`). Verified NOT
the R14 law (R14-off reproduces) and NOT the keep-alive pump
(`MINIANDROID_VSYNC_KEEPALIVE=0` reproduces); the composition IS still
progressing (21,078 F-NEW-297/DRAWWIN rows, RSS 73→252MB). The boot's total
instruction need grew ~3.4x vs the CONT-43 record (~25M@80s) — the
soft-channel by-return unwind + F-C4-543 re-entry compounding is the named
suspect. The opt-out env laws exist but neither restores the pin. The
dooz180 gate is the lane's next re-pin decision (this receipt supplies the
PRE/POST numbers on the integration line).

## 6. Queue + sweep state (S216)

- Sweep pass 2 (scripts/s216_sweep2.py, edit-detection against the 08:54Z
  snapshot): 11 NEW comments (the CONT-131 wave/b/c/honesty on #573; the
  SIM-L3 verdict on #492), **0 EDITED** — the full snapshot baseline for the
  next cycle is evidence/s216/s216_full_snapshot.json.
- SIM-L3 (Coder-3, #492): patch extracted `evidence/s216/s216_c3_sim_l3.patch`
  (sha256-16 `df4355a758ddd372` == declared), `git apply --check` rc=0 ON TOP
  of the wave+R14 tree — QUEUED (not landed this cycle; the dooz A/B ran on a
  SIM-L3-free tree).
- W21 part 17/17: formal request posted on #575 (comment `6797337480`) —
  cross-linked to the CONT-131b/c conviction per the queue-discipline law.
