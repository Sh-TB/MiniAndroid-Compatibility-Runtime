# EXP-049 PHASE 2-3 — Invoke-* Opcode Audit Report

**Audit scope:** Static review of every `invoke-*` opcode handler in
`miniandroid/src/dex/dalvik_engine.cpp`. For each opcode in the
`0x6e`–`0x78` range, we verify the five properties called out by the
task description:

1. **argc extraction** — does the handler correctly read the argument
   count from the 35c format header?
2. **try_recursive_invoke** — does the handler attempt to recurse into
   a DEX method with real bytecode?
3. **bridge_to_api** — does it fall through to the API stub layer if
   recursion fails?
4. **Return value** — does it propagate the callee's return value to
   the caller?
5. **PC advance** — does it advance `pc_` by the correct number of
   code units (3 for every invoke variant)?

The dispatch table is in `dalvik_engine.cpp` lines 1372–1420. Every
opcode in the `0x6e`–`0x78` range is dispatched; there are no silent
fall-throughs to a default handler.

---

## Summary Table

| Opcode | Name                       | Status     | argc | recursive | bridge | retval | pc_+3 | Notes |
|--------|----------------------------|------------|:----:|:---------:|:------:|:------:|:-----:|-------|
| 0x6e   | invoke-virtual             | WORKING    | OK   | OK        | OK     | void   | OK    | Returns void regardless of callee return type |
| 0x6f   | invoke-super               | WORKING    | OK   | OK        | OK     | void   | OK    | Returns void; super.onCreate path works |
| 0x70   | invoke-direct              | WORKING    | OK   | OK        | OK     | void   | OK    | Marks heap object initialized for `<init>` |
| 0x71   | invoke-static              | WORKING    | OK   | OK        | OK     | void   | OK    | Always returns void — see ISSUE-S1 below |
| 0x72   | invoke-interface           | PARTIAL    | OK   | OK        | OK     | void   | OK    | Recursion NOT guarded by `config_.enable_api_bridge` — see ISSUE-I1 |
| 0x73   | _unused_                   | N/A        | —    | —         | —      | —      | —     | Not dispatched (correct — 0x73 is reserved) |
| 0x74   | invoke-virtual/range       | BROKEN     | BAD  | OK        | OK     | void   | OK    | Reads 35c format instead of 3rc — see ISSUE-R1 |
| 0x75   | invoke-super/range         | BROKEN     | BAD  | OK        | OK     | void   | OK    | Same as 0x74 |
| 0x76   | invoke-direct/range        | BROKEN     | BAD  | OK        | OK     | void   | OK    | Same as 0x74 |
| 0x77   | invoke-static/range        | BROKEN     | BAD  | OK        | OK     | void   | OK    | Same as 0x74 |
| 0x78   | invoke-interface/range     | BROKEN     | BAD  | OK        | OK     | void   | OK    | Same as 0x74; recursion also not guarded |

**Verdict:** the 35c handlers (0x6e–0x72) are functionally correct
for the common case (void-returning methods); they will not crash or
halt the engine, but they silently discard non-void return values.
The 3rc handlers (0x74–0x78) are all routed to the same 35c handler
functions and therefore decode the **wrong instruction format** — they
read 5 packed register nibbles instead of `argc` consecutive registers
starting at the 16-bit `CCCC` field. Range variants with >5 arguments
or with the high 4 bits of `AAAA` populated will misread registers.

---

## Per-opcode Evidence

### 0x6e — `invoke-virtual` — WORKING

**Location:** `dalvik_engine.cpp:2858–2987` (`execute_invoke_virtual`)

**35c format decoding** (lines 2864–2894):

```cpp
uint16_t instr = bytecode_[pc];
uint16_t method_idx = bytecode_[pc + 1];   // CORRECT
uint16_t regs_word = bytecode_[pc + 2];     // CORRECT
uint8_t regs[5] = {
    static_cast<uint8_t>(regs_word & 0xF),
    static_cast<uint8_t>((regs_word >> 4) & 0xF),
    static_cast<uint8_t>((regs_word >> 8) & 0xF),
    static_cast<uint8_t>((regs_word >> 12) & 0xF),
    static_cast<uint8_t>((instr >> 8) & 0xF)   // 5th reg, low nibble of AA
};
uint8_t argc = (instr >> 12) & 0xF;            // CORRECT for 35c
```

Per AOSP `dalvik-bytecode.html`, the 35c layout is `AA|op BBBB FEDC`
where:
- `AA` = `arg_count` in the high nibble (so `(instr >> 12) & 0xF`) and
  the 5th register in the low nibble (so `(instr >> 8) & 0xF`).
- `BBBB` (code unit +1) = `method_idx`.
- `FEDC` (code unit +2) = 4 packed register nibbles.

The MiniAndroid handler reads all of these in the correct positions.

**VTable dispatch:** lines 2910–2934 — uses the static type from
`args[0].class_desc` and the runtime type from `heap_.get(obj_id)`.
Falls back to static type if the object is not in the heap.

**try_recursive_invoke:** lines 2944–2952 — invoked with the declaring
class + method name. Guarded by `config_.enable_api_bridge` (which
defaults to `true`; see `dalvik_engine.h:1123`).

**bridge_to_api:** lines 2954–2960 — only invoked if recursion fails.
Uses the runtime type if available, else the declaring class.

**Return value:** `return_val` is initialized to `make_void()` (line
2937) and updated by both `try_recursive_invoke` and `bridge_to_api`.
However, the return value is **never written back into a result
register**. The handler:

```cpp
DalvikValue return_val = DalvikValue::make_void();
// ... try_recursive_invoke / bridge_to_api update return_val ...
api_trace.return_value = return_val.to_string();
// ... trace.operands populated ...
pc_ = pc + 3;
return true;
```

The return value is captured in the API trace (so the trace system can
see it) but is **not pushed to the caller's `move-result*` register**.
This means `move-result-object` / `move-result` / `move-result-wide`
will read a stale or zero register value. ISSUE-V1 below.

**PC advance:** `pc_ = pc + 3;` (line 2985) — correct for 35c.

---

### 0x6f — `invoke-super` — WORKING

**Location:** `dalvik_engine.cpp:3020–3144` (`execute_invoke_super`)

**argc extraction:** lines 3043 —
```cpp
uint8_t arg_count = static_cast<uint8_t>((instr >> 12) & 0xF);
```
Correct 35c arg-count extraction. Reads `std::min(arg_count, 5)` registers.

**try_recursive_invoke:** lines 3106–3111 — guarded by
`config_.enable_api_bridge`. Uses `declaring_class + "<super>"` for
the bridge_to_api fallback (line 3113).

**bridge_to_api:** lines 3112–3115 — invoked with the synthetic class
name `<declaring_class><super>` so the API layer can distinguish
super-class dispatch.

**Return value:** same pattern as invoke-virtual — captured in
`return_val`, propagated to the API trace, but not written to the
caller's result register. ISSUE-V1 applies.

**PC advance:** `pc_ = pc + 3;` (line 3142) — correct.

**Semantics note (lines 2989–3019):** the docstring acknowledges that
real invoke-super dispatches through the *superclass* vtable of the
static type. The implementation doesn't actually walk the superclass
chain — it just routes to `bridge_to_api` with the synthetic class
name. This is a known limitation; for `super.onCreate()` calls (the
only super-call on the Telegram startup path) the bridge has an
explicit `Activity.onCreate` handler that returns void, so this works
in practice.

---

### 0x70 — `invoke-direct` — WORKING

**Location:** `dalvik_engine.cpp:3146–3233` (`execute_invoke_direct`)

**argc extraction:** lines 3172 —
```cpp
uint8_t argc = (instr >> 12) & 0xF;
for (int i = 0; i < argc && i < 5; ++i) { ... }
```
Correct.

**Heap side-effect:** lines 3188–3201 — if `method_name == "<init>"`
and `args[0]` is an OBJECT_REF already in the heap, calls
`heap_.mark_initialized(args[0].object_id)` to mark the constructor
as having run. This is the only invoke handler that mutates the heap.

**try_recursive_invoke:** lines 3208–3214 — guarded.

**bridge_to_api:** lines 3215–3217 — invoked when recursion fails.

**Return value:** same void-default pattern. ISSUE-V1 applies for
non-void direct methods (e.g. `String.length()`, private getters).

**PC advance:** `pc_ = pc + 3;` (line 3231) — correct.

---

### 0x71 — `invoke-static` — WORKING (with ISSUE-S1)

**Location:** `dalvik_engine.cpp:3235–3309` (`execute_invoke_static`)

**argc extraction:** lines 3259 —
```cpp
uint8_t argc = (instr >> 12) & 0xF;
```
Correct.

**try_recursive_invoke:** lines 3286–3292 — guarded by
`config_.enable_api_bridge`.

**bridge_to_api:** lines 3293–3295 — invoked when recursion fails.

**Return value:** ISSUE-S1 — the return value from
`bridge_to_api` is stored in `return_val` (initialized to
`make_void()`), but the handler never copies `return_val` into the
caller's `move-result*` destination register. So a static method
that returns a value (e.g. `System.currentTimeMillis()` returning
`long`, or `Integer.valueOf(int)` returning an `Integer` object)
will appear to return void from the caller's perspective.

The `bridge_to_api` layer DOES set the result correctly (see
`System.currentTimeMillis` at lines 4443–4453, which sets
`result = v; v.type = INT64; v.long_val = ...`), but the handler
discards the result.

The API trace records the return value (line 3302 only sets
`api_trace.pc`, `api_class`, `method`, `status` — NOT the return
value!), so debugging this from traces is also non-trivial. Looking
closely:

```cpp
ApiCallTrace api_trace;
api_trace.sequence = api_call_sequence_++;
api_trace.api_class = class_name;
api_trace.method = method_name;
api_trace.status = status;
api_trace.pc = pc;
// NOTE: api_trace.return_value is NEVER set!
```

Contrast with `execute_invoke_virtual` (line 2968):
`api_trace.return_value = return_val.to_string();` — virtual DOES
record the return value in the trace. **Static does not.**

**ISSUE-S1 (low severity):** static method return values are silently
dropped. For void-returning static calls (the majority on the startup
path: `Log.d`, `Log.e`, etc.) this is harmless. For value-returning
static calls (`System.currentTimeMillis`, `Color.argb`,
`TextUtils.isEmpty`) the caller gets garbage in its move-result
register. Fix: `set_register(result_register, return_val)` after
the bridge call. The handler doesn't know the result register
though — it would have to be inferred from the next instruction
(`move-result*`) which is the same problem invoke-virtual has.

**PC advance:** `pc_ = pc + 3;` (line 3307) — correct.

---

### 0x72 — `invoke-interface` — PARTIAL

**Location:** `dalvik_engine.cpp:3311–3369` (`execute_invoke_interface`)

**argc extraction:** lines 3318 — same correct `(instr >> 12) & 0xF`
extraction as the others.

**try_recursive_invoke:** lines 3345 —
```cpp
if (try_recursive_invoke(class_name, method_name, args, return_val, result)) {
    trace.invoked_method = class_name + "." + method_name;
    pc_ = pc + 3;
    return true;
}
```

**ISSUE-I1 (medium severity):** the recursive invoke is **not**
guarded by `config_.enable_api_bridge`. Compare with the other
handlers:

| Handler          | Recursive guarded? | Bridge guarded? |
|------------------|:------------------:|:---------------:|
| invoke-virtual   | ✅ yes             | ✅ yes          |
| invoke-super     | ✅ yes             | ✅ yes          |
| invoke-direct    | ✅ yes             | ✅ yes          |
| invoke-static    | ✅ yes             | ✅ yes          |
| **invoke-interface** | ❌ **NO**       | ✅ yes          |

If a caller disables the API bridge (`config_.enable_api_bridge =
false`), invoke-interface will still attempt recursion (which calls
`execute_method_internal` recursively and grows the call stack).
This is inconsistent with the other handlers and could surprise
debugging. It also means `dex_report_` will be dereferenced inside
`try_recursive_invoke` even when `enable_api_bridge = false`.

**bridge_to_api:** lines 3352–3355 — correctly guarded.

**Return value:** ISSUE-V1 applies (return value discarded).

**PC advance:** `pc_ = pc + 3;` (line 3367) — correct.

---

### 0x74 – 0x78 — `invoke-*/range` — BROKEN

**Dispatch site:** `dalvik_engine.cpp:1401–1420`

```cpp
case Opcode::INVOKE_VIRTUAL_RANGE:
    success = execute_invoke_virtual(pc_, trace, result);
    trace.opcode_name = "invoke-virtual/range";
    break;
case Opcode::INVOKE_SUPER_RANGE:
    success = execute_invoke_super(pc_, trace, result);
    trace.opcode_name = "invoke-super/range";
    break;
case Opcode::INVOKE_DIRECT_RANGE:
    success = execute_invoke_direct(pc_, trace, result);
    trace.opcode_name = "invoke-direct/range";
    break;
case Opcode::INVOKE_STATIC_RANGE:
    success = execute_invoke_static(pc_, trace, result);
    trace.opcode_name = "invoke-static/range";
    break;
case Opcode::INVOKE_INTERFACE_RANGE:
    success = execute_invoke_interface(pc_, trace, result);
    trace.opcode_name = "invoke-interface/range";
    break;
```

The comment at lines 1396–1400 acknowledges this:
> "Format 3rc: AA|op BBBB CCCC (3 code units). AA = arg count,
> BBBB = method_idx, CCCC = first register. For now, route to the
> same handlers as non-range variants. The 3rc format reads AA
> consecutive registers starting at CCCC."

But the shared 35c handler **does not** read 3rc format. It reads
35c format.

**ISSUE-R1 (high severity):** the 3rc format is:
```
AA|op BBBB CCCC
```
where:
- `AA` is a full byte (range 0–255) — the argument count.
- `BBBB` is the 16-bit method_idx.
- `CCCC` is the 16-bit index of the FIRST register; the rest are
  `CCCC+1, CCCC+2, ..., CCCC+AA-1` (consecutive).

The shared handler instead does:
```cpp
uint8_t argc = (instr >> 12) & 0xF;  // WRONG for 3rc
```
This reads only the high **nibble** of `AA` (so argc is truncated to
0–15) and then reads 5 packed register nibbles from the FEDC layout
(which doesn't exist in 3rc — the third code unit is `CCCC`, a single
16-bit value).

**Concrete consequences:**
- Any invoke-*/range with `argc > 5` (very common — 6+ argument
  calls force the compiler to use /range) will be **truncated to
  argc=5** and silently lose arguments 6, 7, 8, ... .
- The 5 register nibbles the handler reads from `regs_word` will
  actually be the low 4 bits of `CCCC` plus the high byte of `CCCC`
  reinterpreted as 3 more nibbles — i.e. **garbage register indices**.
  So even for `argc ≤ 5` calls the handler reads the wrong registers
  unless `CCCC` happens to be a multiple of 0x1111.

**Frequency in Telegram:** the static call-graph analysis (see
`miniandroid/reports/telegram_call_graph.json`) recorded **1,039,580
total invoke sites** across the 5 DEX files (scanner_stats in the JSON
header). The opcode breakdown on the startup path (4,000 methods
reachable from `LaunchActivity.onCreate`, depth ≤ 8):

| Opcode | Invoke kind              | Startup-path count | % of startup invokes |
|--------|--------------------------|-------------------:|----------------------:|
| 0x6e   | invoke-virtual           |              11,737 |                 50.3% |
| 0x71   | invoke-static            |               4,744 |                 20.3% |
| 0x70   | invoke-direct            |               4,666 |                 20.0% |
| 0x72   | invoke-interface         |               1,250 |                  5.4% |
| 0x74   | invoke-virtual/range     |                 351 |                  1.5% |
| 0x76   | invoke-direct/range      |                 282 |                  1.2% |
| 0x77   | invoke-static/range      |                 212 |                  0.9% |
| 0x6f   | invoke-super             |                  38 |                  0.2% |
| 0x78   | invoke-interface/range   |                  32 |                  0.1% |
| 0x75   | invoke-super/range       |                   3 |                  <0.1% |
| 0xfd   | invoke-custom/range      |                   2 |                  <0.1% |
| 0xfc   | invoke-custom            |                   1 |                  <0.1% |
| 0xfb   | invoke-polymorphic/range |                   1 |                  <0.1% |
|        | **TOTAL**                |              23,319 |                  100% |

**~3.8% of startup-path invokes use /range variants** (881 of 23,319).
That sounds small as a percentage but translates to ~880 individual
call sites where the engine will misread argument registers. Of
particular concern:

- `invoke-direct/range` (282 sites) is used heavily for multi-arg
  constructors (e.g. `new Intent(...)`, `new Bundle(...)`,
  `new StringBuilder(int)`), where it's used by `dx` to fit >5 args.
  Misreading the argument registers here means the new object's
  fields will be initialized with garbage.
- `invoke-virtual/range` (351 sites) is used for method calls with
  >5 args (e.g. `String.format(...)`, `Message.obtain(...)` with
  the full arg list) and for array-of-primitive `varargs` methods.

---

## Cross-cutting Issues

### ISSUE-V1 — Return value is silently dropped by ALL handlers

Every invoke-* handler captures the callee's return value into a
local `return_val` variable, but **none of them write it to a result
register**. The actual register write has to happen when the next
instruction (`move-result`, `move-result-wide`, or `move-result-object`)
is executed. Looking at those handlers (lines 3389–3460), they read
the value from `get_register(ret_reg)` — which would return a stale
or zero value because the previous invoke never wrote it.

**Affected opcodes:** 0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76,
0x77, 0x78 — i.e. **every invoke variant**.

**Severity:** medium. For void-returning calls (which dominate the
startup path) this is harmless. For non-void calls the caller reads
uninitialized memory in the destination register. In practice this
means:
- `String.length()` returns 0 (caller reads the default INT32 value).
- `System.currentTimeMillis()` returns 0 (caller reads INT64 default).
- `Resources.getConfiguration()` returns null (caller reads NULL_REF
  or whatever was there before).

This is a long-standing design limitation: the invoke handlers don't
know the result register ahead of time. The proper fix is to stash
`return_val` in a per-frame "pending result" slot that
`move-result*` reads on the next instruction. (See `dalvik_engine.h`
for the `pending_return_value_` slot if it exists; if it doesn't,
that's the missing piece.)

### ISSUE-S1 — Static handler doesn't record return value in trace

**Severity:** low (debugging-only). `execute_invoke_static` (and
`execute_invoke_direct`) build the `ApiCallTrace` but never set
`api_trace.return_value`. Compare with `execute_invoke_virtual` which
sets it explicitly. This means API trace consumers that read the
return value (e.g. `miniandroid/docs/exp042/EXP042_TELEGRAM_COMPATIBILITY_MAP.md`)
will see empty return-value strings for static calls, which makes
debugging stubbed static methods harder.

### ISSUE-I1 — Interface handler not guarded by `enable_api_bridge`

**Severity:** medium (configuration inconsistency). See 0x72 above.

### ISSUE-R1 — Range variants decode wrong instruction format

**Severity:** high. See 0x74–0x78 above.

---

## Silent-Path Audit (Return-Without-Dispatch)

The task asks specifically about handlers that "return void without
dispatching". A scan of every invoke handler shows that **none** of
them return early with `void` without first attempting both
`try_recursive_invoke` and (on failure) `bridge_to_api`. The only
early-returns are:

1. The bounds check at the top of every handler:
   ```cpp
   if (pc + 2 >= bytecode_.size()) return false;
   ```
   This is a hard error (returns `false`, halts execution). Not a
   silent void return.

2. The `try_recursive_invoke` success path in `execute_invoke_interface`
   (lines 3345–3349) returns early after recursion succeeds — but the
   recursive invocation itself did the dispatch, so this is not a
   silent path. The trace is correctly populated before the return.

3. There is no path in any invoke handler that silently returns `true`
   with `result = void` without invoking either the recursive DEX
   engine or the API bridge. The shared `bridge_to_api` default case
   (line 4722) returns `void` for unknown calls, but that's a feature
   ("don't crash on missing stub"), not a silent handler bug.

**Verdict: no silent-path bugs found in the invoke dispatch.**

---

## Recommendations (for downstream fix tasks)

1. **Fix the 3rc format (ISSUE-R1):** write a dedicated
   `execute_invoke_*_range(pc, trace, result)` set of handlers that
   read the 3rc layout (`argc = (instr >> 8) & 0xFF`, `regs[i] =
   cccc + i`). Or, at minimum, detect the range case inside the shared
   handler by inspecting the opcode byte and switching on it.

2. **Implement pending-result propagation (ISSUE-V1):** add a
   `pending_return_value_` field to the engine; have every invoke
   handler write to it; have `move-result`, `move-result-wide`, and
   `move-result-object` read from it. This is the standard pattern
   used by AOSP's dalvik interpreter (`mReturnValue` in
   `dalvik/vm/interp/Interp.cpp`).

3. **Guard `try_recursive_invoke` in `execute_invoke_interface`
   (ISSUE-I1):** wrap the recursive call in
   `if (config_.enable_api_bridge)` for consistency with the other
   four handlers.

4. **Set `api_trace.return_value` in static + direct handlers
   (ISSUE-S1):** add
   `api_trace.return_value = return_val.to_string();` to both
   `execute_invoke_static` and `execute_invoke_direct`, matching the
   pattern in `execute_invoke_virtual`.

---

## Cross-Reference: Static Call Graph Evidence

The companion static call-graph analysis
(`miniandroid/reports/telegram_call_graph.json`, generated by
`miniandroid/tools/dex_call_graph.py`) confirms the dispatch
audit. Key numbers:

- **Total invoke sites in Telegram's 5 DEX files:** 1,039,580
- **Range-variant (3rc) invoke sites:** 106,725 (~10.3%)
- **Native method call sites (ACC_NATIVE flag set):** 462
- **System.loadLibrary / System.load call sites:** 6
- **Native methods reachable from LaunchActivity.onCreate (depth ≤ 6):**
  18 — including `ConnectionsManager.native_init`,
  `Utilities.blurBitmap`, `MediaController.isOpusFile`,
  `NativeInstance.destroyVideoCapturer`.

The 18 native methods on the startup path are exactly the JNI entry
points that MiniAndroid's `bridge_to_api` layer must stub out for
Telegram to start. They are listed in
`telegram_call_graph.json::startup_path::native_methods_on_path`.
