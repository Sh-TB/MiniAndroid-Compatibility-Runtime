# [CONT-131b addendum] Row #25 root DECODED one level deeper — the UP→onClick chain dies on a WILD `aput` index inside the Kotlin MapBuilder SWAR scan (`Lbw0;.a` → index 373,496,216 into a length-7 array) → catch-all → coroutine job cancellation

Follow-up on the CONT-131 wave (comment 6792937042): the POST tap run's console forensics localize the gesture-coroutine death to an exact instruction — this is the row #24 core / #25 mechanism, now with DEX truth.

## The measured chain (POST tap run, binary `4d9087c60482042b`, #573 recipe)

1. `[UI-EVENT] TOUCH action=1 … arm=dispatchTouchEvent attached=1` — the UP dispatch re-enters `Lt4;.dispatchTouchEvent` clean (no gate artifact — the soft-stop law held).
2. The UP is **DISPATCHED and CONSUMED** (`[UI-EVENT] event=TOUCH action=1 result=DISPATCHED consumed=true`).
3. `[EXP090-DRAIN] Invoking Runnable id=1255 class=Lh9;` — the AndroidUiDispatcher trampoline IS invoked (the dispatcher wake-up works).
4. `[QUEUE] Runnable id=67393 enqueued (delay=50ms, source=View.post)` — the PerformClick-family post happens (a View.post with 50ms delay lands in the queue).
5. **`[SYNTH-EXC] aput-oob: Ljava/lang/ArrayIndexOutOfBoundsException; (length=7; index=373496216) method=Lbw0;.a pc=8 → uncaught`** — a WILD index (373,496,216 = 0x16400A28) into a length-7 `Object[]`.
6. `[EXC-PROPAGATE]` ×3 through catch-all handlers (`Lwi1;.i` → `Lj50;.a` → `Lne;.g`) into the coroutine machinery: `_handled$volatile` / `_resumed$volatile` field offsets resolved (R337-REFLECT/UNSAFE rows), then **`"Parent job is Cancelling"` / `"kp1" is cancelling` / `"rg1" is cancelling`** string-concat bursts — **the coroutine JOB is CANCELLED** by the wild exception.
7. The gesture chain (detectTap → onTap → PerformClick → onClick → `viewModel.onNewGameClicked()`) therefore never completes: **0 `onClick` rows in the whole 30 MB log** — the dice `delay(100ms)`×5 chain is never scheduled, the interactive-clock law legitimately arms 0×, the board never materializes.

## DEX truth (androguard, canonical `dooz_23_toplevel.apk`, single classes.dex)

`Lbw0;` **is the Kotlin stdlib `MapBuilder`** (the open-addressing hash map behind `buildMap`/`HashMap` builders): fields `a [J` (SWAR control-word array), `b [Ljava/lang/Object;` (slots), `c/d/e I` (capacity-mask/size/state), initial capacity 6.

The dying instruction (`aput-object v4, v2, v1` in `Lbw0;.a(Ljava/lang/Object;)Z` — the `put` path) stores into `b[index]` where **index = return value of `Lbw0;.d(Ljava/lang/Object;)I` (findKey)**. `d` is the classic Kotlin MapBuilder SWAR probe:

```
0:  move-object/from16 v0, v34            # this
8:  if-eqz v1, +7                          # k == null?
12: invoke-virtual v1, Ljava/lang/Object;->hashCode()I
24: const v4, -862048943                   # hash spread (Murmur-ish)
30: mul-int/2addr v3, v4
32: shl-int/lit8 v5, v3, 16
36: xor-int/2addr v3, v5
38: ushr-int/lit8 v5, v3, 7
42: and-int/lit8 v3, v3, 127               # 7-bit control value
50: and-int v7, v5, v6                     # bucket = hash & capacity-mask
72: aget-wide v12, v9, v10                 # SWAR: read the control long
76: ushr-long/2addr v12, v11               # ← DYNAMIC long shift (0..56)
90: shl-long v9, v15, v9                   # ← DYNAMIC long shift (64-shift)
124: mul-long v17, v11, v13                # 0x0101010101010101 (SWAR broadcast)
170: invoke-static v2, v3, Ljava/lang/Long;->numberOfTrailingZeros(J)I
182: add-int v17, v7, v17
186: and-int v17, v17, v6                  # masked slot index → returned to put()
```

**The suspect set is small and engine-side**: the wild index can only come from (a) the dynamic long-shift pair (`ushr-long/2addr` with shift 0..56, `shl-long` with 64-shift) inside the SWAR scan, (b) the SWAR arithmetic chain (`mul-long` with `0x0101010101010101`, `neg-long`, `not-long`, `sub-long`, `or-long`, `and-long`, `cmp-long`), or (c) `Long.numberOfTrailingZeros(J)I` (the engine's static dispatch of it). Any of these mis-evaluating turns the masked-slot invariant (`and-int v17, v17, v6`) into garbage — the OOB index is 0x16400A28, exactly the shape of a corrupted long→int truncation.

## Why this matters for the whole ladder

Every Kotlin `buildMap`/`HashMap`-builder put inside coroutine/compose machinery takes this `d()` path — a mis-evaluated SWAR step kills ANY tap-driven recomposition with a cancellation storm, not just dooz. This is a PLATFORM bug on the interpreter's long-op family, not an app bug: fixing it (micro-proof fixture first, per the fixtures law) is the row #25 fix candidate that un-gates #22 end-to-end AND the compose white-screen frontier's next layer.

**Next wave plan (CONT-132)**: micro-proof fixture reproducing the `d()` SWAR chain (dynamic long shifts + `0x0101…01` mul-long + `numberOfTrailingZeros`) → engine A/B on the failing op → fix → re-run the cont131 tap battery (expect: 0 `aput-oob`, onClick lands, dice chain schedules, clock arms >0, row #22 closes).

— CONT-131b addendum, the platform lane. Generator: `scripts/cont131_dump.py` (androguard-backed, committed locally with the wave).