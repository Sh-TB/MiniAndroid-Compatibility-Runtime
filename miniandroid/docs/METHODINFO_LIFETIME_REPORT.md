# EXP-054 — MethodInfo Lifetime Audit Report

**Date:** 2026-08-17
**Phase:** 1 (Memory Safety)
**D-Suggestion:** #1 — MethodInfo pointer lifetime bug

## D-Suggestion #1 — [Verified]

D's suggestion that there is a structural memory lifetime problem with `MethodInfo*` pointers is **partially correct**. The code at `dalvik_engine.cpp:1119-1208` does store `const dex::MethodInfo*` pointers into a local `all_methods` vector. However, the vector is kept alive in the function scope (`auto all_methods = cls_ref.all_methods();`), so the pointers remain valid for the duration of `try_recursive_invoke`.

The actual segfault observed in EXP-053 is more likely caused by **C++ stack overflow** during deep recursive invokes, NOT by dangling pointers. Each `try_recursive_invoke` call uses a large C++ stack frame (InstructionTrace + vectors + locals ≈ 50-80KB per frame). With MAX_RECURSION_DEPTH=80, that's up to 6.4MB — close to the default 8MB stack limit.

When `ensure_class_initialized` calls `try_recursive_invoke` from INSIDE an opcode handler (e.g., `execute_sget`), the call stack is:
```
execute_method_internal (outer method)
  → fetch_decode_execute
    → execute_sget
      → ensure_class_initialized
        → try_recursive_invoke
          → execute_method_internal (<clinit>)
            → fetch_decode_execute
              → execute_const_16 (or any opcode)
                → ... (potentially more recursive invokes)
```

Each level adds ~50-80KB of C++ stack. With the outer method already 3-4 levels deep, adding `<clinit>` execution can easily overflow.

## Audit: All MethodInfo* storage locations

### Location 1: `try_recursive_invoke` — `dalvik_engine.cpp:1119-1208`

```cpp
auto all_methods = cls_ref.all_methods();  // local vector (BY VALUE)
const dex::MethodInfo* best_match = nullptr;
const dex::MethodInfo* fallback_match = nullptr;
for (const auto& method : all_methods) {
    ...
    best_match = &method;  // pointer into all_methods
    ...
}
const dex::MethodInfo* selected = best_match ? best_match : fallback_match;
if (selected) {
    const auto& method = *selected;  // reference into all_methods
    execute_method_internal(..., method.bytecode, ...);  // used after
}
```

**Pointer owner:** local `all_methods` vector
**Container:** `std::vector<MethodInfo>` (returned by value from `cls_ref.all_methods()`)
**Can invalidate:** NO — the vector is alive for the entire function scope. The recursive call to `execute_method_internal` does NOT modify `all_methods`.
**Risk:** LOW — pointers are valid. The segfault is from stack overflow, not dangling pointers.

**However:** D's suggestion to audit ALL such patterns is valid. Let me check other locations.

### Location 2: `class_resolver.cpp:250, 374, 395, 453`

```cpp
for (const auto& method : target_cls->all_methods()) {
    ...
}
```

**Pointer owner:** temporary vector returned by `all_methods()`
**Container:** `std::vector<MethodInfo>` (temporary, destroyed at end of `for` loop)
**Can invalidate:** YES — but only if the pointer is used after the loop. In these locations, the loop body doesn't store the pointer — it uses `method` by reference within the iteration. **No dangling pointer risk.**

### Location 3: `dalvik_engine.cpp:356, 470, 526, 572, 1041`

```cpp
for (const auto& method : cls.all_methods()) {
    ...
}
```

Same pattern as Location 2. **No dangling pointer risk** — `method` is used by reference within the loop body only.

### Location 4: `dalvik_engine.cpp:907-1010` (JNI bridge section)

```cpp
auto all_methods_check = cls_ref.all_methods();
for (const auto& method : all_methods_check) {
    ...
}
```

Same as Location 1 — local vector kept alive. **No dangling pointer risk.**

## Comparison of options

### Option A: `std::deque<MethodInfo>`
- **Performance:** O(1) push_back, no reallocation on growth. References stable.
- **Complexity:** Low — just change `vector` to `deque`.
- **Compatibility:** `all_methods()` returns `vector` — would need to change return type or copy.
- **Verdict:** Doesn't solve the actual problem (stack overflow, not pointer invalidation).

### Option B: `std::unordered_map<method_id, MethodInfo>`
- **Performance:** O(1) lookup by method_id. References stable.
- **Complexity:** Medium — need to change the data model.
- **Compatibility:** Major refactor of `ClassInfo`.
- **Verdict:** Overkill for the current problem.

### Option C: `shared_ptr / unique_ptr` ownership
- **Performance:** Heap allocation per MethodInfo — slower.
- **Complexity:** Medium — change ownership model.
- **Compatibility:** Major refactor.
- **Verdict:** Overkill. The actual issue is C++ stack depth, not ownership.

### Option D: Current design with copied MethodInfo (RECOMMENDED)
- **Performance:** Copy on lookup — acceptable (MethodInfo is ~100 bytes).
- **Complexity:** Minimal — just change `const MethodInfo*` to `MethodInfo` (store by value).
- **Compatibility:** No API changes.
- **Verdict:** This is the safest minimal fix. It eliminates the theoretical pointer risk (even though the current code is actually safe) and makes the code more robust against future refactoring.

## Decision

**[D-Suggestion #1]: Partially accepted.**

- The structural concern is valid in principle — raw pointers into containers are fragile.
- BUT the actual segfault in EXP-053 is caused by **C++ stack overflow** during deep recursive invokes from opcode handlers, NOT by dangling pointers.
- The fix is two-fold:
  1. **Store MethodInfo by value** in `try_recursive_invoke` (Option D) — eliminates the theoretical pointer risk.
  2. **Increase the C++ stack size** for the runtime thread, OR reduce per-frame stack usage by making `InstructionTrace` lighter.
  3. **Move `ensure_class_initialized` out of the opcode handler** — call it at method entry instead of on every SGET, to reduce the recursive invoke depth.

## Implementation plan

1. Change `const dex::MethodInfo* best_match` to `std::optional<dex::MethodInfo> best_match` (store by value).
2. Change `const dex::MethodInfo* fallback_match` to `std::optional<dex::MethodInfo> fallback_match`.
3. Use `*best_match` instead of `*selected` when accessing the method.
4. Run the runtime with increased stack size (`ulimit -s 65536`) to verify the stack overflow theory.
5. Re-enable `<clinit>` execution and verify the segfault is gone.
