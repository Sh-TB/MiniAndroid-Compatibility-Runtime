# [CONT-131c addendum] The SWAR suspect set is CLEARED — micro-proof fixture 39/39 PASS on the engine; the wild-index suspicion moves to the DATA-CORRUPTION family (un-initialized `Lbw0;->c` capacity field — the ctor-zombie family, the same root as the #575 F-C4-720 law)

Follow-up on CONT-131b (comment 6793088778): the CONT-132 micro-proof fixture ran on the CONT-131 POST binary and **every suspect op is byte-correct**.

## The probe (fixtures/cont132_swar, APK sha256 0e719464…)

A faithful Java reproduction of the `Lbw0;.d` SWAR chain — dynamic long shifts (`ushr-long`/`shl-long` with runtime shift 16/48), the `neg-long` + `shr-long/2addr`-by-63 guard, the SWAR `mul-long` broadcast `0x0101010101010101`, the `xor/sub/not/and-long` match chain, `Long.numberOfTrailingZeros` (7 / 63 / 64 all covered), the masked index, and the real `aput-object` into a length-7 array. 3 chains (real match at byte 0, match at the top byte, zero-shift guard path with no match). **`C132- VERDICT pass=39 fail=0`** on the engine, every intermediate byte-exact vs the off-machine JVM expectations.

## What this clears and what it convicts

- **CLEARED**: the interpreter's long-op family (dynamic shifts, SWAR arithmetic, `numberOfTrailingZeros`, truncation) — the CONT-131b suspect set (a)/(b)/(c) is refuted as a *mechanism*. `div-int` in the not-found/rehash path remains technically unprobed, but the masked-return invariant is what produces the aput index, and it is fed by correct arithmetic.
- **CONVICTED (data side)**: the wild index `373,496,216` can only reach the `aput-object v4, v2, v1` in `Lbw0;.a` through the *input* — either (1) a **corrupted/un-initialized `Lbw0;->c` capacity field** (the mask `and-int v17, v17, v6` with garbage v6 → wild masked index), or (2) `k.hashCode()` returning garbage for a key whose state is itself un-initialized, or (3) an un-masked not-found return path (low likelihood; the mask covers the main paths). Option (1) is the campaign-familiar face: **an object whose `<init>` never executed** — the ctor-zombie family, precisely the #575 F-C4-720 law's territory (F720 is DEFAULT-OFF; the W22 frontier "initializer sites, real recursive slice" is the honest successor). A Kotlin `buildMap`/`HashMap` instance constructed inside the tap-resumption coroutine path with a zombie allocation explains the whole storm: wild mask → wild aput → `ArrayIndexOutOfBoundsException` → catch-all → coroutine cancellation ("Parent job is Cancelling") → the gesture chain dies before `onTap`.

## Next wave (CONT-132 proper)

1. Heap-state forensics on the tap run: dump the `Lbw0;` allocation site + its field values at the OOB moment (an env-gated field-read probe on the aput-oob handler, default-off, CONT-42 law).
2. If the `c` field is garbage-shaped → the allocation site is a zombie `<init>` — apply the initializer real-execution slice law (the #575 W22 frontier work) at that site, re-run the cont131 tap battery: expect 0 `aput-oob`, onClick lands, dice chain schedules, `[F-NEW-277-CLOCK]` arms > 0, row #22 closes end-to-end.

— CONT-131c addendum, the platform lane. Fixture + generator committed locally with the wave (`fixtures/cont132_swar/`, `scripts/cont131_dump.py`).