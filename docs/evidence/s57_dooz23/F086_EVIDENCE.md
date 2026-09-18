# S57 — R-NEW-344 Closure: F-086 Long.compare Bridge Law + dooz v23 ScatterMap 15→31

## Root cause (generic engine law — F-086)

`java.lang.Long.compare(JJ)I` / `compareUnsigned(JJ)I` had NO handler in the
native bridge (`bridge_to_api`). The call therefore fell to the STUBBED
typed-zero exit (`make_int(0)` for return type `I`), and the caller's
`move-result` received 0.

**Why this killed dooz v23 (androidx.collection ScatterMap 1.4.x, R8-inlined
into `Lbw0;.d`):** the second-table growth decision compiles Kotlin's
load-factor check into the standard unsigned-compare idiom:

```
; d() growth branch (androground disasm, scripts/s57_andro_lbw0.py)
pc= 174 iget      v2, v0, Lbw0;->d I          ; size
pc= 179 int-to-long v3, v2
pc= 182 mul-long  v3, v3, 32                  ; size * 32
pc= 184 int-to-long v1, v1                   ; capacity
pc= 187 mul-long  v1, v1, 25                  ; capacity * 25
pc= 189 const-wide/high16 v17, 0x8000000000000000
pc= 191 xor-long  v3, v3, v17                ; unsigned-compare lowering
pc= 193 xor-long  v1, v1, v17
pc= 195 invoke-static Long.compare(v3, v1)
pc= 199 if-gtz    v1, ->494                  ; → f(Lmg1;.b(cap)) = f(cap*2+1)
; fall-through pc=201..482: convertMetadataForCleanup + same-capacity refill
```

Correct math at the second grow (cap 15, size 14): `448^MIN > 375^MIN` →
**+1** → resize to `nextCapacity(15) = 15*2+1 = 31`. The STUB returned 0 →
`if-gtz` not-taken → cleanup branch converted Full→Deleted
(`0xFEFEFEFEFEFEFEFE` written at pc=235, bit-exact vs S56 evidence) and
re-filled the SAME capacity-15 arrays → zero EMPTY metadata bytes → the probe
loop in `d` never terminates → HALT-LOOP → F-084 honest escalation → blank
first frame.

**Why only the SECOND grow failed:** the cap-7 grow never reaches the compare
— `if-le capacity, 8 → pc=491` branches straight into the resize path
(pc=494-506). The compare is only consulted for capacity ≥ 9, so grow #1
(f(15)) was always correct.

## Fix

`miniandroid/src/dex/dalvik_engine.cpp` — F-055 Long block, S57 addition:
`compare` (signed 64-bit, OpenJDK `Long.java` law) and `compareUnsigned`
(unsigned domain) return -1/0/+1 from full `int64_t` args. Corpus-generic:
any Kotlin/R8 unsigned-compare idiom and any sorted-structure comparator
needs this surface.

## Runtime proof (§6 criteria)

`MINIANDROID_FIELD_TRACE=c` on the ScatterMap capacity field, obj#2658
(the same instance family as the S56 budget-counter evidence):

```
[FIELD-TRACE] put Lbw0;.f Lbw0;.c obj#2658 value=7     ; initializeStorage(6)
[FIELD-TRACE] put Lbw0;.f Lbw0;.c obj#2658 value=15    ; grow #1: f(15)
[FIELD-TRACE] put Lbw0;.f Lbw0;.c obj#2658 value=31    ; grow #2: f(31)  ← 15→31
```

- capacity 7 → resize → 15 ✓
- capacity 15 → growth threshold → resize → 31 ✓
- NO infinite probe (HALT-LOOP: 0), NO fake return (F084-HALT-RETURN: 0),
  NO aput-oob (garbage-index face gone) ✓

Post-fix the run advances into the **R-NEW-376** ctor-climb family
(`Lgz1;.<init>` depth=2048 self-delegation ×3, `Lbp1;.<init>` ×1) — the
already-pinned frontier, observed now on BOTH v18 and v23 (§37 alias rule;
no new ID).

## Regression

`miniandroid/tests/semantic_long_cmp_conv_test.cpp` — F-086 group, 6 checks
(includes the bit-exact dooz23 growth idiom `compare(448^MIN, 375^MIN)==+1`,
signed negatives, LONG_MIN vs LONG_MAX, equal, compareUnsigned).
**20/20 PASS** (battery stage "semantic long/cmp/conv (expect 20)").

## Repro commands

```bash
# pre-fix face (HEAD 28b644b7 + S56 tree): HALT-LOOP in Lbw0;.d pc=28
./miniandroid/build/miniandroid run apk_cache/io.github.yamin8000.dooz_23.apk -o run/s57_r344_repro
# post-fix proof: capacity 7→15→31
MINIANDROID_FIELD_TRACE=c ./miniandroid/build/miniandroid run \
  apk_cache/io.github.yamin8000.dooz_23.apk -o run/s57_r344_proof2
# regression
./build/semantic_long_cmp_conv_test   # RESULT: 20 passed, 0 failed
```

## SHA256SUMS

See `SHA256SUMS` in this directory (raw run logs stay outside the repo per
the zero-APK/no-raw-logs law; key excerpts above are the committed record).
