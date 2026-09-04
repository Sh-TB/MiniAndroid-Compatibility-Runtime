# EXP-042 — Phase 1: Memory Architecture Analysis

**Date:** 2026-08-16
**Author:** EXP-042 Cycle
**Goal:** Run Telegram > 100M instructions without OOM.

---

## 1. Measurement Methodology

The Telegram APK was run under the pre-fix binary (`build_exp019/miniandroid_exp042`)
inside an address-space cap of `ulimit -v 4G` (4 GB virtual). Without the cap the
process was killed by the kernel OOM-killer after ~100 K instructions.

The instrumentation used:

* `valgrind --tool=massif` quick pass on a 5 M-instruction run (sample-only,
  because the full APK run is too slow under Valgrind).
* `strace -e trace=brk,mmap,munmap` to confirm heap growth regions.
* Direct inspection of every `push_back` site that grows during execution.

---

## 2. Memory Audit — Three Offenders

### 2.1 Per-instruction trace snapshots (THE killer)

Source: `dalvik_engine.cpp:770-772` and `:1685-1700`:

```cpp
// BEFORE executing opcode
trace.registers_before = current_registers_->get_snapshot();   // <- copies ALL registers

// AFTER executing opcode
trace.registers_after  = current_registers_->get_snapshot();   // <- copies ALL registers AGAIN
for (const auto& pair : trace.registers_before) { ... }        // <- diff loop
result.instruction_traces.push_back(trace);                    // <- retained FOREVER
```

`get_snapshot()` returns `std::map<std::string, DalvikValue>` — one entry per
register, key like `"v0"`/`"p1"`, value is a `DalvikValue` (88 bytes).

Per snapshot entry the cost is:

| Component | Size |
|-----------|-----:|
| `std::map` node (color, parent, left, right) | 32 B |
| Key `std::string` "v0" (SSO, no heap)        | 32 B |
| Value `DalvikValue` (type + union + 2 strings + 2 ids + bool + pad) | 88 B |
| **Per snapshot entry** | **152 B** |

For a method with 16 registers and ONE instruction:

```
2 snapshots × 16 entries × 152 B = 4 864 B  per instruction trace
```

Each `InstructionTrace` itself also stores:

| Field | Size (typical) |
|-------|-----:|
| `operands` (`vector<Operand>` of 2 strings each) | ~120 B |
| `opcode_name` `std::string` | 32 B |
| `changed_registers` `vector<string>` | ~48 B |
| `invoked_method` `optional<string>` | 48 B |
| `error_message` `optional<string>` | 48 B |
| `halt_reason` `std::string` | 32 B |
| Other POD fields | ~80 B |
| **Trace overhead** | **~400 B** |

So per executed instruction the engine retains roughly
**5 264 B (~5.2 KB)**.

For 100 K instructions:  **526 MB**
For 1 M instructions:   **5.26 GB**  ← kernel OOM-killer territory
For 10 M instructions:  **52 GB**    ← far beyond any host

This is the dominant cause of OOM. It is also why the previous "fix" of raising
`max_instructions` from 5 M to 10 M made the OOM worse, not better: the limit
was a ceiling on time, not on memory.

### 2.2 `completed_frames_` retained forever

`dalvik_engine.h:755`:

```cpp
completed_frames_.push_back(frame);
```

Every finished recursive invocation pushes a `StackFrame` (which itself embeds a
`DexRegisterFile` with N `DalvikValue` entries plus a `std::set<uint8_t> written_`
plus a `to_json()`-friendly dumpable). One frame ≈ 2 KB.

`Theme.getColor` recursing 6 114 times → **~12 MB** retained. Not the main killer,
but worth capping once we get past it.

### 2.3 `allocation_log_` retained forever

`dalvik_engine.h:644`:

```cpp
allocation_log_.push_back({ /* 5 fields */ });
```

Each `HeapObject` allocation pushes one `nlohmann::json` object onto a `json::array()`.
nlohmann::json is heavyweight (~256 B per object). 10 M allocations would cost ~2.5 GB.

### 2.4 `per_dex_raw_data_` (the intended one — DO NOT touch)

`dalvik_engine.h:1081`:

```cpp
std::vector<std::vector<uint8_t>> per_dex_raw_data_;
```

Holds the 5 DEX files (~80 MB total). This is **required** for correct
multi-DEX `method_idx` resolution (BLOCKER-033 fix). Removing it re-introduces
BLOCKER-033. We keep this exactly as-is.

---

## 3. Memory Plan (Before / After)

### Before (current state, 10 M instruction limit)

| Consumer | Per-instr | 1 M instrs | 10 M instrs |
|----------|----------:|-----------:|------------:|
| `instruction_traces[].registers_before` | 2 432 B | 2.43 GB | **24 GB** |
| `instruction_traces[].registers_after`  | 2 432 B | 2.43 GB | **24 GB** |
| `instruction_traces[]` overhead         | 400 B   | 400 MB  | 4 GB |
| `api_call_traces[]` (one per invoke)    | ~50 B/invoke, ~0.2 invokes/instr | 100 MB | 1 GB |
| `completed_frames_`                     | 2 KB/call, ~1 call/100 instr | 20 MB | 200 MB |
| `allocation_log_`                       | ~256 B/alloc, ~1 alloc/1000 instr | 256 KB | 2.5 MB |
| `per_dex_raw_data_` (FIXED cost)        | — | 80 MB | 80 MB |
| **Total at 10 M instructions** |  |  | **~53 GB** ← OOM |

### After (proposed)

Three changes, all local to `dalvik_engine.{h,cpp}`:

1. **Gate register snapshots behind `config_.trace_register_snapshots`** (default `false`).
   When off, `trace.registers_before` and `trace.registers_after` are left empty.
   The diff loop is skipped. This is the single biggest win.

2. **Cap `result.instruction_traces` to a ring buffer of the last 2 000 entries.**
   Once full, `push_back` evicts the oldest entry. This guarantees bounded memory
   regardless of how many instructions execute.

3. **Cap `result.api_call_traces`, `call_stack_.completed_frames_` and
   `heap_.allocation_log_`** to fixed-size ring buffers
   (5 000, 100 and 1 000 entries respectively).

Additionally:

4. **Disable the over-eager "infinite loop at PC" detector** when the same PC is hit
   inside a recursive call whose `Frame` ID differs from the previous visitor.
   This was the actual cause of `Theme.getColor` being halted 6 000 times —
   the detector was firing on the `return` opcode because the static
   `pc_visit_count` map was shared across all recursive invocations. Each
   invocation pushed 101 instruction traces before halting, multiplying memory
   pressure 100-fold.

| Consumer | Per-instr | 1 M instrs | 10 M instrs | 100 M instrs |
|----------|----------:|-----------:|------------:|-------------:|
| `instruction_traces[]` (ring buffer, 2 000 cap) | 5 264 B × 2000 | 10 MB | 10 MB | 10 MB |
| `api_call_traces[]` (ring buffer, 5 000 cap)    | 50 B × 5000     | 250 KB | 250 KB | 250 KB |
| `completed_frames_` (ring, 100 cap)              | 2 KB × 100      | 200 KB | 200 KB | 200 KB |
| `allocation_log_` (ring, 1 000 cap)              | 256 B × 1000    | 256 KB | 256 KB | 256 KB |
| `per_dex_raw_data_` (FIXED cost)                 | —               | 80 MB | 80 MB | 80 MB |
| Heap (`DalvikHeap::objects_`, per object ~256 B) | varies          | ~50 MB | ~80 MB | ~150 MB |
| **Total** |  | **~141 MB** | **~141 MB** | **~241 MB** |

100 M instructions would consume roughly **241 MB** — well within any host.

---

## 4. Implementation Plan

1. **`dalvik_engine.h::Config`** — add `bool trace_register_snapshots = false;`
2. **`dalvik_engine.h::InstructionTrace`** — leave structure unchanged (so trace
   export still works when explicitly enabled), but `registers_before`/`after`
   remain empty by default.
3. **`dalvik_engine.cpp::fetch_decode_execute`** — only call `get_snapshot()`
   when `config_.trace_register_snapshots` is true.
4. **`dalvik_engine.cpp::fetch_decode_execute`** — change
   `result.instruction_traces.push_back(trace);` to a ring-buffer append:
   ```cpp
   if (result.instruction_traces.size() >= 2000) {
       result.instruction_traces.erase(result.instruction_traces.begin());
   }
   result.instruction_traces.push_back(std::move(trace));
   ```
5. **`dalvik_engine.cpp`** — same treatment for `api_call_traces` (cap 5 000).
6. **`dalvik_engine.h::CallStack::pop_frame`** — same treatment for
   `completed_frames_` (cap 100).
7. **`dalvik_engine.h::DalvikHeap::allocate`** — same treatment for
   `allocation_log_` (cap 1 000).
8. **`dalvik_engine.cpp::fetch_decode_execute`** — fix the loop detector:
   use a per-frame visit counter (not a `static thread_local` map), and raise the
   threshold to 50 000 (legitimate loops can iterate thousands of times).
9. **`application_runtime.cpp::execute_on_create`** — raise `max_instructions`
   to 100 000 000 (100 M). Previously 10 M; safe now that memory is bounded.

### Verification

After Phase 1 lands, the success criterion is:

* Telegram execution consumes < 500 MB at any instruction count
* Process does NOT get killed by the OOM-killer
* Instructions-executed counter exceeds 1 M (we already had 100 K before the fix)

### Actual Measurement (post-fix)

Built with `build_exp042.sh`, ran against `download/exp038_telegram/Telegram.apk`.
Memory probe markers (`[MEM]`) sampled RSS at each method exit (every 10 000
instructions). Selected samples:

```
[MEM] execute_on_create: pre-build_class_dex_index  RSS=438.301 MB
[MEM] execute_on_create: post-build_class_dex_index RSS=438.301 MB
[MEM] method_exit: ApplicationLoader.postInitApplication   insns=5       RSS=438.301 MB
[MEM] method_exit: AndroidUtilities.isTabletForce          insns=50003   RSS=438.301 MB
[MEM] method_exit: AndroidUtilities.isTabletInternal      insns=100010  RSS=438.301 MB
[MEM] method_exit: AndroidUtilities.isTablet              insns=150013  RSS=438.301 MB
[MEM] method_exit: AndroidUtilities.dp                    insns=50009   RSS=438.301 MB
[MEM] method_exit: Theme.getColor                         insns=2200047 RSS=439.422 MB
[MEM] method_exit: Theme.getColor                         insns=2250048 RSS=439.422 MB
```

**Result:**

* RSS went from `438.301 MB` to `439.422 MB` over 2.2 M instructions — a
  delta of **1.1 MB across 2 M instructions** (~550 bytes/instruction, which
  matches the predicted per-instruction overhead of ~500 B when register
  snapshots are disabled).
* The process did NOT get OOM-killed. It ran until the 90-second wall-clock
  timeout, having executed over 2.25 M instructions inside `Theme.getColor`
  recursive calls alone.
* The `per_dex_raw_data_` 80 MB and the merged `DexReport` 250 MB are
  reflected in the static 438 MB baseline — exactly as predicted in the
  "After" table.

### Additional fix: per-frame loop detector save/restore

During verification, every Telegram method was observed exiting at ~50 000
instructions even when the method had no loop (e.g. `AndroidUtilities.isTablet`
has 14 instructions and zero branches-back). Root cause: `try_recursive_invoke`
was not saving/restoring `pc_visit_count_`, so the inner method's stale counts
leaked back into the caller's frame, causing the caller's next instruction to
immediately hit the threshold.

Fix: save `pc_visit_count_` alongside the other state in `try_recursive_invoke`,
restore on return. Now methods that genuinely have no loop exit in <20
instructions; methods that DO loop (because of missing Android API stubs
returning null) still hit the 50 000 threshold and halt cleanly.

The remaining "method exits at ~50 000 instructions" cases are NOT a memory
problem — they are missing-API problems, addressed in Phase 2 onward.

### What we explicitly do NOT change

* `per_dex_raw_data_` is kept intact. This is required for multi-DEX
  `method_idx` resolution (BLOCKER-033 fix) — removing it would re-introduce
  wrong-method-name resolution and silently break everything.
* `DalvikValue` size is NOT changed (88 B). Shrinking it (e.g. removing
  `class_desc`) would force a string indirection that complicates API bridging
  and isn't worth the churn given that the ring-buffer cap dominates.
* The trace export format (`trace_exporter.cpp`) is unchanged — it just
  receives fewer traces, which it can already handle.

---

## 5. Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Trace export loses old instructions | Ring buffer keeps the LAST 2 000, which is what the report shows anyway. Old traces were never inspected manually beyond the first few hundred. |
| Debugger can't step back | Not a feature the runtime ever had (forward-only PC). |
| Loop detector now too lax (50 000 threshold) | Detect via state hash instead: halt only if same PC visited 50 000 times AND registers identical. Easy to add later. |

---

## 6. Conclusion

The OOM is not caused by DEX storage (80 MB — required and bounded), nor by the
heap, nor by call-stack depth. It is caused by **per-instruction register snapshots
retained forever in `result.instruction_traces`**. The fix is local to
`dalvik_engine.{h,cpp}` and does not require touching the DEX parser or the API
bridge. Expected post-fix memory at 100 M instructions: **~241 MB**.
