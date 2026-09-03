# Upstream reference — AOSP ART aput semantics (UNIFIED_014 / DEX-APUT-BOUNDS)

**Fetched:** 2026-09-03, from `android.googlesource.com/platform/art` `refs/heads/main`
(`?format=TEXT` base64 endpoint; saved locally under `/home/z/my-project/ws/aosp_*.cc/.h`
during the session). Purpose: canonical oracle for the aput fix — MiniAndroid test-green
alone is not acceptance (master directive rule 4).

## Files + exact functions verified

| AOSP file | Function | Line(s) | Semantics confirmed |
|---|---|---|---|
| `runtime/interpreter/interpreter_switch_impl-inl.h` | `HandleAPut<ArrayType,T>(T value)` | ~525–541 | null array → `ThrowNullPointerExceptionFromInterpreter()`, pending exception, NO store; `CheckIsValidIndex(index)` false → pending exception (AIOOBE), NO store; only then `SetWithoutChecks(index, value)`. **Array length is never mutated by aput.** |
| `runtime/interpreter/interpreter_switch_impl-inl.h` | `APUT_OBJECT` | ~1092–1106 | same null/index checks + `CheckAssignable(val)` (ArrayStoreException — see "not ported") |
| `runtime/interpreter/interpreter_switch_impl-inl.h` | APUT_BOOLEAN/BYTE/CHAR/SHORT/()/_WIDE | 1068–1091 | all primitive forms route through `HandleAPut<T>` — bounds/null semantics identical for every width |
| `runtime/mirror/array-inl.h` | `Array::CheckIsValidIndex` | 58–66 | OOB iff `static_cast<uint32_t>(index) >= static_cast<uint32_t>(GetLength())` — i.e. `index < 0 || index >= len` (negative index is OOB) |
| `runtime/mirror/array.cc` | `Array::ThrowArrayIndexOutOfBoundsException` | 134–136 | delegates to `art::ThrowArrayIndexOutOfBoundsException(index, GetLength())` |
| `runtime/interpreter/interpreter_common.cc` | `ThrowNullPointerExceptionFromInterpreter` | 56–58 | plain NPE from current DexPC |

## Message formats

- AIOOBE: ART's runtime thrower formats `length=<len>; index=<idx>` (canonical visible
  in ART/libcore test expected output and real device logcat:
  `java.lang.ArrayIndexOutOfBoundsException: length=3; index=3`).
  `runtime/exceptions.cc` itself could NOT be re-fetched this session
  (googlesource rate-limited after 6 successful fetches) — format recorded from the
  `ThrowArrayIndexOutOfBoundsException(index, GetLength())` signature plus the
  universally observed ART message shape; corroborated (not proven from local file).
  MiniAndroid pre-existing aget used `"length N; index M"` — aligned to the canonical
  `length=…; index=…` in this batch (message text only; type unchanged).
- NPE (null array): `ThrowNullPointerExceptionFromInterpreter()` throws with **no
  detailed message** (`ThrowNullPointerExceptionFromDexPC()`); MiniAndroid uses the
  classic dalvik/libcore detail string `"Attempt to write into null array"` as an
  additive detail (type is what fixtures assert).

## Mapping to MiniAndroid (src/dex/dalvik_engine.cpp ARRAY_PUT_CASE)

| AOSP | MiniAndroid (engine reality) |
|---|---|
| null reference → NPE, no store | `arr_val.type == NULL_REF \|\| arr_val.is_null` → `raise_synthetic_exception("Ljava/lang/NullPointerException;", …, "aput-null")`; pc not advanced (handler/unwind machinery takes over) |
| `CheckIsValidIndex` → AIOOBE | effective length chain (identical to aget's): `__array_length__` → `__new_array_length__` → register `int_val`; if effective len > 0 (CONFIRMED array): `idx < 0 \|\| idx >= len` → AIOOBE `length=…; index=…` (`aput-oob`); NO store, length untouched |
| `SetWithoutChecks` | `heap_.set_object_field(arr, "array[idx]", src)` |
| length immutable | auto-grow **removed** for confirmed arrays (the DEX-APUT-BOUNDS drift: aput past end grew `__array_length__` to idx+1 → phantom tail for array-length/loops) |

## Conservative tiers preserved (engine boundaries, documented — NOT fake passes)

- **length 0 / unknown** (field missing or 0; conflates genuine empty arrays):
  legacy store + grow — mirrors the UNIFIED_011.2 aget gate (`arr_len == 0 may mean
  "length unknown"`). Bridges that fill arrays aput-by-aput with no recorded length
  keep working. Documented engine boundary shared with aget.
- **non-OBJECT_REF / heap-missing register**: legacy silent skip (unchanged).
- **NOT ported:** `CheckAssignable` (ArrayStoreException) — needs a per-array
  component-type model in the heap; recorded as a follow-up finding, not faked.
  `TransactionChecker` — N/A (no transactions).

## Provenance

- Finding: `MASTER_CURRENT_GAP_MATRIX.md` DEX-APUT-BOUNDS (UNIFIED_011.2 audit;
  DEFERRED with regression-risk note) — this batch resolves it.
- Sibling fixed half: DEX-AGET-OOB-LIVELOCK (@2f05134) — aput now matches aget's
  confirmed-OOB policy, completing the array-bounds chain.
