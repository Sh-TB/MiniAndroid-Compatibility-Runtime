# S56 — F-084 HALT-RETURN Containment + dooz v23 face refinement

## F-084 fix (generic engine law)

**Law**: a callee frame that exits via the loop-detector/instruction-budget
halt has NO defined return value. The pre-fix engine blanket-cleared
`halted_` at the invoke boundary (dalvik_engine.cpp, execute_invoke path)
and handed the STALE `last_invoke_return_` to the caller's move-result.
ART law: a method that cannot complete never returns a value.

**Discriminator**: `halted_ && !halted_on_return_` — every NORMAL return
also sets `halted_` (execute_return* sets both as a pair); only the
abnormal halts (HALT-LOOP, instruction budget, invalid goto) set `halted_`
without `halted_on_return_`. The fix escalates the halt to the caller as a
deferred `Ljava/lang/VirtualMachineError;` (origin `F084-HALT-RETURN`),
so enclosing catch-alls see a real exception instead of garbage.

**Proof**:
- regression battery `BATTERY GATE: ALL PASS (96 stages)` at this HEAD
  (F-084 shipped with zero stage regressions; the first attempt without
  the normal-return discriminator broke corpus stages 59-63 and was fixed
  before commit — the failure mode itself re-confirmed that `halted_` is
  set on every normal return).
- simplestopwatch corpus run rc=0 with zero F084 fires (normal apps never
  hit the discriminator).
- dooz v23: the pre-fix face `aput-oob length=15; index=-733270216`
  (garbage word from the halted `Lbw0;.d` consumed as a ScatterMap slot
  index by `Lbw0;.a` pc=8) is GONE; the halt now surfaces as
  `VirtualMachineError (F084 interpreter halt in callee ...)` and unwinds
  with real exception semantics.

## dooz v23 post-F-083/F-084 face (R-NEW-344 refinement)

R-NEW-361 no longer appears in v23 (F-083 deep-stack fix holds). The run
now reaches Recomposer/ControlledComposition internals:

1. `Lnb0;` = Recomposer (strings: "Compose:recompose",
   "Reentrant composition is not supported"), `Lwo;` = ControlledComposition
   (holds two `Lbw0;` maps as `l`/`m` — dirty-scope tracking),
   `Ldw0;.e:Lbw0;` wrapper chain.
2. `Lbw0;` = androidx.collection ScatterMap/ScatterSet (fields
   `a:[J` metadata + `b:[Ljava/lang/Object;` values + `c` capacity +
   `d` size + `e` free-budget; helpers `Lmg1;.a` = loadedCapacity,
   `Lmg1;.b` = nextCapacity `cap*2+1`).
3. Observed full lifecycle (SHA-traced stderr below): construction
   `<init>(6)` → `f(6)` (cap 7, budget e=6) → 6 inserts → grow at e=0 via
   `f(15)` (resize #1 correct: new metadata o4644, cap 15, budget
   e=loaded(15)-6=8) → 8 more inserts (size 14) → grow check at e=0
   entered the (R8-inlined) resize, but the conversion pass
   (`convertMetadataForCleanup` — Full→Deleted, value 0xfefefefefefe80fe
   written at d pc=235, bit-exact vs upstream source) re-filled the SAME
   arrays (no new allocation, newCap stayed 15: the resize epilogue wrote
   e=0 = loaded(15)-14) → table 15/15 with zero EMPTY metadata bytes →
   the probe loop in `d(Object)I` never terminates (HALT-LOOP after 2.4M
   instructions at pc=28 iget-object).
4. With F-084, the halt now propagates honestly; the app-facing crash
   (AIOOBE) is contained. The root (why the second grow computed
   newCap=15 instead of nextCapacity(15)=31) is the pinned next step.

## Key trace excerpts

```
[SYNTH-EXC] F084-HALT-RETURN (deferred): Ljava/lang/VirtualMachineError; (F084 interpreter halt in callee (no return value): Infinite loop at PC=0x1c in Lbw0;.d (visited 50001 times in this frame, bytecode_size=671, op_at_pc=0x0x0054).) method=Lbw0;.d pc=28 → uncaught (deferred frame unwind + propagate)
[EXCEPTION] method=Lnb0;.n pc=162 exception=Ljava/lang/VirtualMachineError; msg="F084 interpreter halt in callee ..." try_range=[156,163) handler=FOUND handler_addr=64 catch_type=<catch-all>
```

Pre-fix face (for contrast, from miniandroid/run/s56_dooz23_refix/stderr2.log):
```
[SYNTH-EXC] aput-oob: Ljava/lang/ArrayIndexOutOfBoundsException; (length=15; index=-733270216) method=Lbw0;.a pc=8 → uncaught (frame unwind + propagate)
[EXC-PROPAGATE] Ljava/lang/ArrayIndexOutOfBoundsException; uncaught at caller Lio/github/yamin8000/dooz/ui/MainActivity;.onCreate invoke_pc=317 → APP BOUNDARY unwind
```

## Budget-counter evidence (MINIANDROID_FIELD_TRACE=e, obj#2658)

```
put Lbw0;.f Lbw0;.e obj#2658 value=6      ; f(6): cap 7, budget loaded(7)-0 = 6
get d e value=6 / put d e value=5         ; insert #1 (two reads, one decrement)
... 5,4,3,2,1,0 ...
get d e value=0 ; put Lbw0;.f e value=8   ; grow at e=0: f(15) ran, cap 15, budget 8 = loaded(15)-6
... 7,6,5,4,3,2,1,0 (inserts 8..15) ...
get d e value=0                           ; insert #16: grow check fires again
(c=15/a[] read storm = inlined resize entry-copy walk, 14 entries)
put Lbw0;.d Lbw0;.e value=0               ; epilogue e = loaded(newCap)-14 = 0 ⇒ newCap = 15 (BUG: must be 31)
```

## Environment

- HEAD at capture: S56 working tree (F-084 + S56 diagnostics), engine
  rebuilt clean (`Build complete`), battery 96/96 ALL PASS.
- Repro: `MINIANDROID_LOOP_LOCALS_DIAG=1 MINIANDROID_META_STORE_TRACE=1
  ./miniandroid/build/miniandroid run apk_cache/io.github.yamin8000.dooz_23.apk`
