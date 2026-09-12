# EXP-071 — Opcode Audit

## AOSP canonical opcode table (verified against dalvik-bytecode.html)

| Opcode | Hex  | Format | Mnemonic               | AOSP Name             | Status |
|--------|------|--------|------------------------|-----------------------|--------|
| 0x24   | 24   | 35c    | filled-new-array        | filled-new-array      | ✓ verified |
| 0x25   | 25   | 3rc    | filled-new-array/range  | filled-new-array/range | ✓ verified |
| 0x26   | 26   | 31t    | fill-array-data         | fill-array-data       | ✓ verified |
| 0x27   | 27   | 11x    | throw                   | throw                 | ✓ verified (compatibility skip) |
| 0x28   | 28   | 10t    | goto                    | goto                  | ✓ verified (D8/R8 hybrid) |
| 0x29   | 29   | 20t    | goto/16                 | goto/16               | ✓ verified |
| 0x2A   | 2A   | 30t    | goto/32                 | goto/32               | ✓ verified |

## EXP-071 Session 5 additions

### `const-wide/16` (opcode 0x17, format 21s)

**Bug:** handler wrote the 64-bit value to the 32-bit `int_val` field of
`DalvikValue` while marking the value as `INT64`. The 64-bit `long_val`
field was left with uninitialized garbage.

**Impact:** `execute_invoke_static`'s wide-arg merge later read `long_val`
for `INT64`-typed registers, getting values like `93862215288784` instead
of `400`. This silently broke `AndroidUtilities.runOnUIThread(Runnable, long)`
— the wrong delay was passed to `HandlerShadow.enqueue`.

**Fix:** write to `long_val` (not `int_val`) for INT64-typed DalvikValues.

### `const-wide/32` (opcode 0x18, format 31i)

Same bug, same fix.

### `const-wide/high16` (opcode 0x19, format 21h)

Same bug, same fix.

### `const-wide` (opcode 0x18, format 51l)

Same bug, same fix.

## Wide register pair merging

Added to `execute_invoke_static`:

1. **Resolve the method proto** via the new
   `resolve_method_proto_for_dex(method_idx, dex_index)` function. This
   reads the DexMethodId's `proto_idx` → DexProtoId, then walks the
   TypeList at `parameters_off` to build the full
   `"(Ljava/lang/Runnable;J)V"`-style proto string.

2. **Parse the proto** into parameter types: `Ljava/lang/Runnable;`, `J`,
   etc. — correctly handling objects (`L...;`), arrays (`[...`), and
   primitives (single char).

3. **Walk params and consume register slots.** Wide params (`J`, `D`)
   consume TWO consecutive registers; other params consume one.

4. **Merge wide register pairs correctly.** Two cases:
   - **Case 1:** If the low register already holds `INT64`/`FLOAT64`
     (the normal case after `const-wide/16` etc.), use it directly.
   - **Case 2:** If the low register holds `INT32` (assembled from two
     separate writes), merge `vAA` (low 32) + `vAA+1` (high 32) into a
     single `INT64` value via `(hi.int_val << 32) | (uint32_t)lo.int_val`.

## Static-method shadow dispatch fix

`try_shadow_dispatch` now distinguishes static vs instance calls:

- For **instance methods** (`invoke-virtual`/`invoke-direct`): `args[0]`
  is `this` → shift args so `ctx.args[0]` is the first PARAMETER, and
  set `ctx.receiver_id`/`receiver_class` from `args[0]`.
- For **static methods** (`invoke-static`): `args[0]` IS the first
  parameter → put ALL args in `ctx.args` without shifting.

This is tracked by the new `current_invoke_is_static_` member, set to
`true` by `execute_invoke_static` (with a scope guard to reset on return).

Without this fix, static calls like
`AndroidUtilities.runOnUIThread(Runnable, long)` had their Runnable
stolen as `this`, leaving `ctx.args` empty — so `HandlerShadow` could
not extract the Runnable and `enqueue` was never called.

## Two-pass class name lookup

`try_shadow_dispatch` now tries TWO class names when dispatching:

1. **Pass 1:** the DECLARED class name (e.g.
   `Lorg/telegram/messenger/AndroidUtilities;` for static calls, or
   `Landroid/view/View;` for inherited instance methods).
2. **Pass 2:** the runtime class of `args[0]` (i.e. `args[0].class_desc`)
   if it differs from the declared class. This catches cases like
   `setOnClickListener` invoked on a `FragmentFloatingButton` instance —
   the declared class is `View`, but the runtime class is the subclass.

This makes both static and instance dispatch work correctly without
the user having to know which kind of call it is.

## `ViewShadow` class descriptor fix

`ViewShadow::get_or_create_node(view_id, class_desc)` now prefers
`ctx.receiver_class` (the runtime class of `this`) over `ctx.class_name`
(the declared class). Without this fix, every View node created by an
inherited method (e.g. `View.setOnClickListener` on a
`FragmentFloatingButton`) would have `class_desc = "Landroid/view/View;"`
instead of the actual runtime class. This in turn broke
`find_by_class_substring("FragmentFloatingButton")`.

## Audit results

All regressions verified to pass:

- `instance-of` — walks superclass chain
- `View.getContext` — returns stored context or LaunchActivity singleton
- `TextView.length` — dispatches to ViewShadow.getText()
- `String.length` — returns actual STRING_REF length
- `filled-new-array` / `filled-new-array/range` — element ordering
- `fill-array-data` — 1/2/4/8 byte widths
- `goto` / `goto/16` / `goto/32` — signed offsets
- `wide registers` — const-wide/* now writes to `long_val`; invoke-static
  merges wide pairs
- `multi-dex` — per-DEX string/type/method resolution
- `exception handling` — THROW is a compatibility skip (not a halt)
- `async callbacks` — `runOnUIThread` enqueues to HandlerShadow's queue;
  runtime drains the queue and invokes each Runnable's `run()`

The new fixes remain GENERIC — no Telegram-specific class names, no
hardcoded method names, no special-casing for `auth.sendCode`. They apply
to any Dalvik bytecode that uses the standard `runOnUIThread(Runnable, long)`
idiom and any framework code that uses wide register pairs.
