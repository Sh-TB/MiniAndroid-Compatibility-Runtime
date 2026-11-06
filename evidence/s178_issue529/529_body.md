# Coder D — Source Review Report: Critical Defects in MiniAndroid Dalvik Engine, Batch Interpreter, APK Parser, Text Shaper, and Supporting Modules

**Base:** source files provided in this session (no commit SHA available — see "Caveat" at end)
**Reviewer:** Coder D
**Protocol:** MINIANDROID Cross-Coder Collaboration, Incremental Delivery (Sections 4, 8, 10)
**Method:** line-by-line source review against AOSP/OpenJDK/spec. **No runtime execution performed** — statuses are capped at `SOURCE_VERIFIED` unless otherwise noted.

---

## ⚠️ Caveat (read first)

I do not have the live repository, so I cannot:
- run the reproduction commands I write below,
- compare against the main branch's HEAD,
- confirm that the line numbers I cite still match main after other coders' merges.

Every finding below is **derived from the source text you provided**. Treat the "Reproduction" fields as *prescriptions for the main coder to run*, not as evidence that I ran them. If any finding turns out to already be fixed in main, mark it `SUPERSEDED` in the ledger.

---

## P0 — CRITICAL: Undefined behavior / memory corruption on the hot path

---

### D-P0-1 — `pc_visit_count_` indexed without resize → heap buffer overflow in the interpreter hot loop

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik interpreter loop
**File:** `dalvik_engine.cpp` — `execute_method_internal` (variable init) + `fetch_decode_execute` (per-instruction use)
**Severity:** P0 (UB; likely to corrupt heap or crash on any real APK)

**A. Finding**
In `execute_method_internal`:
```cpp
pc_visit_count_.clear();
```
and in `fetch_decode_execute`, immediately after each instruction dispatch:
```cpp
pc_visit_count_[pc_]++;
if (pc_visit_count_[pc_] > config_.loop_visit_threshold) { ... }
```
`pc_visit_count_` is a `std::vector<uint32_t>` (declared in `dalvik_engine.h`). After `clear()`, its `size()` is 0. `operator[](pc_)` on an empty vector is **undefined behavior**.

**B. Root cause**
The header comment claims the vector is "Sized to `bytecode_.size()` at frame entry", but the actual entry code only calls `clear()`. The header was rewritten (in the batch you provided, `pc_visit_count_` became a flat `std::vector<uint32_t>` replacing the old `std::map`) without the resize being carried over from the comment's claim.

**C. Expected behavior**
A per-frame visitation counter must be a dense, indexed array of size ≥ `bytecode_.size()` (PCs can address every code unit). AOSP's ART interpreter tracks per-PC counts via a sparse table only for instrumentation; here the dense array is the correct representation.

**D. Implementation**
At the top of `execute_method_internal`, replace:
```cpp
pc_visit_count_.clear();
```
with:
```cpp
pc_visit_count_.assign(bytecode_.size() + 1, 0);   // +1 for PC == size at end-of-method
pc_branch_sig_.assign(bytecode_.size() + 1, 0);
pc_branch_sig_seen_.assign(bytecode_.size() + 1, 0);
```
(The two `pc_branch_sig_*` vectors are in the same family and are used identically — if they exist in your current header, they need the same treatment. If they don't exist, drop those two lines.)

**E. Reproduction**
Any APK run with `--max-instructions > 1`. The first `fetch_decode_execute` iteration will write to `pc_visit_count_[0]` on an empty vector. Under ASan: `heap-buffer-overflow` or `container-overflow`. Without ASan: silent corruption; usually survives because `std::vector` capacity is often retained across `clear()` — but not guaranteed, and not correct.

**F. Integration guidance**
This patch is completely isolated: one line in `execute_method_internal`. It cannot conflict with any other coder's work. It unblocks every APK run and must be merged **before** any APK-level verification is trusted.

---

### D-P0-2 — `move/16` (0x03) truncates 16-bit registers to `uint8_t`

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik interpreter — `move/16` opcode handler
**File:** `dalvik_engine.cpp` — `Opcode::MOVE_16` case in `fetch_decode_execute`
**Severity:** P0 (silent register corruption on any method with >255 registers — i.e. most R8-minified Compose and Telegram methods)

**A. Finding**
```cpp
case Opcode::MOVE_16: {
    if (pc_ + 2 >= bytecode_.size()) return false;
    uint16_t src  = bytecode_[pc + 1];
    uint16_t dest = bytecode_[pc + 2];
    DalvikValue val = get_register(static_cast<uint8_t>(src));   // ← truncation
    set_register(static_cast<uint8_t>(dest), val);               // ← truncation
    ...
}
```

**B. Root cause**
Two independent bugs:
1. `static_cast<uint8_t>(...)` collapses any register ≥ 256 to `reg & 0xFF`.
2. The 32x format decode is wrong even ignoring the cast: AOSP 32x is `[AAAA] [op] [BBBB] [BBBB]` where `AAAA = cu[0] >> 8 | (cu[1] & 0xFF) << 8` and `BBBB = ((cu[1] >> 8) & 0xFF) | (cu[2] & 0xFF) << 8`. The current code reads `src` from `cu[1]` whole and `dest` from `cu[2]` whole — both wrong.

**C. Expected behavior**
Per AOSP `dalvik-bytecode.html` (format 32x):
```
AAAA|op BBBB|BBBB
AAAA = first (destination) register, split across cu[0] high and cu[1] low byte
BBBB = second (source) register, split across cu[1] high byte and cu[2] low byte
```

**D. Implementation**
Replace the handler with:
```cpp
case Opcode::MOVE_16: {
    if (pc_ + 2 >= bytecode_.size()) return false;
    uint16_t aaaa = static_cast<uint16_t>((bytecode_[pc] >> 8) |
                    ((bytecode_[pc + 1] & 0xFF) << 8));
    uint16_t bbbb = static_cast<uint16_t>(((bytecode_[pc + 1] >> 8) & 0xFF) |
                    ((bytecode_[pc + 2] & 0xFF) << 8));
    DalvikValue val = get_register(bbbb);
    set_register(aaaa, val);
    trace.opcode_name = "move/16";
    pc_ += 3;
    break;
}
```
This depends on `D-P0-3` being fixed first (register API must accept `uint16_t`).

**E. Reproduction**
Any DEX from an R8-minified APK (Compose, Telegram) that contains a method with >255 registers. Cross-check the execution trace's `move/16` destinations against `dexdump -d` output. Mismatch on the first `move/16` whose `AAAA != (BBBB & 0xFF)`.

**F. Integration guidance**
Isolated. Does not conflict. **Must be merged with D-P0-3**; the two are one semantic unit.

---

### D-P0-3 — `set_register` / `get_register` / `register_name` take `uint8_t` while `DexRegisterFile::write_v` takes `uint16_t`

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik interpreter — register API surface
**Files:** `dalvik_engine.h` (declarations), `dalvik_engine.cpp` (definitions)
**Severity:** P0 (defeats `DexRegisterFile`'s own `uint16_t` widening — every register ≥ 256 is silently aliased onto a lower register)

**A. Finding**
`dalvik_engine.h`:
```cpp
void set_register(uint8_t reg, const DalvikValue& value);
DalvikValue get_register(uint8_t reg) const;
std::string register_name(uint8_t reg) const;
```
but `DexRegisterFile::write_v` / `read_v` in the *current* header are `uint16_t`:
```cpp
void write_v(uint16_t reg, const DalvikValue& value);
DalvikValue read_v(uint16_t reg) const;
```
Consequence: any call path that goes through `set_register`/`get_register` truncates the register number before it reaches `write_v`. The `uint16_t` widening in `DexRegisterFile` is *invisible* to the interpreter because the interpreter never passes anything wider than `uint8_t`.

**B. Root cause**
Partial refactor: the header was updated to widen `DexRegisterFile`'s API (the comment in `DexRegisterFile::write_v` explicitly says "DEX register numbers are UNSIGNED 16-BIT"), but the façade functions were left narrow.

**C. Expected behavior**
Register numbers in DEX `32x` / `3rc` / `22x` / `21t` formats address up to 65535. The façade must accept `uint16_t` end-to-end.

**D. Implementation**
Three files to touch, mechanically:
1. `dalvik_engine.h`: change all three declarations to `uint16_t`.
2. `dalvik_engine.cpp`: change all three definitions to `uint16_t` (currently `uint8_t`).
3. `dalvik_engine.cpp`: remove every `static_cast<uint8_t>(...)` on a register argument to these three functions. Search for `static_cast<uint8_t>(` in the register-dispatch region — most of them are truncation bugs of this exact class (see `D-P0-2` above; `D-P0-4` below; also `MOVE_FROM16` and `MOVE_WIDE_FROM16` are already correct).

**E. Reproduction**
Same as `D-P0-2`. After applying this, `D-P0-2` becomes meaningful. Before applying this, `move/16` and everything else that relies on ≥256 registers will still truncate.

**F. Integration guidance**
Mechanical patch; no semantic conflict. **Merge as one commit with `D-P0-2`** so reviewers can validate the pair atomically.

---

### D-P0-4 — `execute_invoke_static` reads `regs[5]` when `reg_idx == 4` (out-of-bounds stack read)

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik interpreter — `invoke-static` wide-argument merge
**File:** `dalvik_engine.cpp` — `execute_invoke_static`, the `param_types` walk near the top
**Severity:** P0 (stack OOB read; also wrong long/double value → corrupted argument to callee)

**A. Finding**
```cpp
uint8_t regs[5] = { ... };
for (size_t p = 0; p < param_types.size() && reg_idx < 5 && (int)reg_idx < argc; ++p) {
    const std::string& pt = param_types[p];
    if (pt == "J" || pt == "D") {
        DalvikValue lo = get_register(regs[reg_idx]);
        ...
        DalvikValue hi = get_register(regs[reg_idx + 1]);   // ← reg_idx==4 → regs[5]
```
The loop condition permits `reg_idx == 4`; inside, a wide parameter (`J` or `D`) unconditionally accesses `regs[5]`. The array has 5 elements (`regs[0..4]`).

**B. Root cause**
The `35c` format packs at most 5 registers. A wide (`J`/`D`) parameter is 2 DEX register slots, so it can never legally start at the last slot — but the code does not verify the DEX invariant, so a hostile or corrupt DEX (or a caller-side bug producing an inconsistent `param_types`/`argc`) reaches `regs[5]`.

**C. Expected behavior**
On ART this is a verify-time rejection (`VerifyError` at class load). On the engine, the correct behavior when the DEX passes verification but the wide parameter has no room is to abort the invoke with a `VerifyError` (deferred exception) — never to read past the array.

**D. Implementation**
Inside the loop, before `get_register(regs[reg_idx + 1])`:
```cpp
if (reg_idx + 1 >= 5) {
    throw_deferred("Ljava/lang/VerifyError;",
                   "wide argument at register slot 4 (35c limit)",
                   "INVOKE-STATIC-WIDE");
    break;
}
```

**E. Reproduction**
Construct a synthetic DEX where `invoke-static {v0, v1, v2, v3, v4}, M(J)V` passes a wide (J) parameter in slot 4. Under ASan (with `array-bounds` sanitizer): stack-buffer-overflow. Without ASan: `regs[5]` reads the first byte of the next stack local (unspecified).

**F. Integration guidance**
Isolated. Depends on `throw_deferred` already existing in this header (it does). Merge with `D-P0-2` / `D-P0-3` as a "register-width + invoke-arg sanity" cluster.

---

### D-P0-5 — `Opcode::MOVE_WIDE_16` (0x06) is undefined; interpreter reaches `handle_unimplemented` on any method that uses it

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik opcode table
**File:** `dalvik_engine.h` — `namespace Opcode`
**Severity:** P0 (any method with >255 registers and a `move-wide/16` instruction halts)

**A. Finding**
```cpp
constexpr uint16_t MOVE_WIDE = 0x04;
constexpr uint16_t MOVE_WIDE_FROM16 = 0x05;
// 0x06 is missing
constexpr uint16_t MOVE_OBJECT = 0x07;
```
`0x06` is not defined anywhere in the header. The `switch` in `fetch_decode_execute` therefore has no case for it.

**B. Root cause**
Not an opcode-value error; an omission. The AOSP opcode table has `0x06 = move-wide/16` in the 32x format (same shape as `move/16`).

**C. Expected behavior**
`move-wide/16 vAAAA, vBBBB` — copy 64-bit value from `BBBB` to `AAAA` (2 code units).

**D. Implementation**
Add to `namespace Opcode`:
```cpp
constexpr uint16_t MOVE_WIDE_16 = 0x06;
```
Add to the dispatch switch:
```cpp
case Opcode::MOVE_WIDE_16: {
    if (pc_ + 2 >= bytecode_.size()) return false;
    uint16_t aaaa = static_cast<uint16_t>((bytecode_[pc] >> 8) |
                    ((bytecode_[pc + 1] & 0xFF) << 8));
    uint16_t bbbb = static_cast<uint16_t>(((bytecode_[pc + 1] >> 8) & 0xFF) |
                    ((bytecode_[pc + 2] & 0xFF) << 8));
    DalvikValue val = get_register(bbbb);
    if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
        val = DalvikValue::make_long(
            static_cast<int64_t>(static_cast<uint32_t>(val.int_val)));
    }
    set_wide_pair(aaaa, val);
    trace.opcode_name = "move-wide/16";
    pc_ += 3;
    break;
}
```
(Reuses `set_wide_pair` from the existing header — this is the correct opcode for exactly that law.)

**E. Reproduction**
Disassemble any DEX containing `move-wide/16` (`dexdump -d | grep 'move-wide/16'`). Under the current source, the trace will show `UNIMPLEMENTED 0x0006` at the first occurrence.

**F. Integration guidance**
Depends on `D-P0-3`. Does not conflict with any coder. Merge with the register-width cluster.

---

## P1 — HIGH: Silent wrongness in the batch interpreter and the API dispatcher

---

### D-P1-1 — `DexInterpreterBatch::resolve_method` ignores `method_idx`; every invoke resolves to the first matching name it finds

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Batch interpreter (`EXP-003-BATCH` fixture)
**File:** `dex_interpreter_batch.cpp` — `DexInterpreterBatch::resolve_method`
**Severity:** P1 (every `invoke-*` in the batch interpreter — which is the fixture used to demonstrate `onCreate` — resolves to the wrong method for any class that declares multiple methods of the same name, or for any `invoke` whose target is not one of `onCreate` / `<init>` / `setText`)

**A. Finding**
```cpp
std::pair<std::string, std::string> DexInterpreterBatch::resolve_method(
    uint16_t method_idx, const DexReport& dex_report) const {
    ...
    if (method_idx < dex_report.classes.size()) {   // ← compares method_idx to classes.size()
        for (const auto& cls : dex_report.classes) {
            for (const auto& m : cls.all_methods()) {
                if (m.name == "onCreate") { ... goto found; }
                else if (m.name == "<init>") { ... goto found; }
                else if (m.name == "setText") { ... goto found; }
```
There is no lookup into `dex_report.method_ids` at all. The `if (method_idx < dex_report.classes.size())` comparison mixes index spaces (`method_idx` indexes `method_ids`, not `classes`).

**B. Root cause**
The `DexReport` didn't expose `method_ids` when the batch interpreter was written; the current header now does (`std::vector<DexMethodId> method_ids`). The workaround (heuristic "find the first method named X") was never replaced with a real lookup.

**C. Expected behavior**
```cpp
if (method_idx >= dex_report.method_ids.size()) return {"<unknown>", "<unknown>"};
const auto& mid = dex_report.method_ids[method_idx];
```
then resolve `mid.class_idx` → `dex_report.types[...]` and `mid.name_idx` → `dex_report.strings[...]`.

**D. Implementation**
Full replacement in `dex_interpreter_batch.cpp`:
```cpp
std::pair<std::string, std::string> DexInterpreterBatch::resolve_method(
    uint16_t method_idx, const DexReport& dex_report) const {
    if (method_idx >= dex_report.method_ids.size())
        return {"<unknown>", "<unknown>"};
    const auto& mid = dex_report.method_ids[method_idx];
    const std::string cls = (mid.class_idx < dex_report.types.size())
        ? dex_report.types[mid.class_idx] : "<bad class>";
    const std::string name = (mid.name_idx < dex_report.strings.size())
        ? dex_report.strings[mid.name_idx] : "<bad name>";
    return {cls, name};
}
```

**E. Reproduction**
Run the batch interpreter on any APK with more than one method named `<init>` (every APK). Trace the `invoked_method` field. Under the current source, every `<init>` invoke logs the *first* `<init>` in class order, regardless of `method_idx`.

**F. Integration guidance**
Isolated to `dex_interpreter_batch.cpp`. This is the fixture's correctness floor. **Merge before using the batch interpreter as a "Dalvik ran" evidence source** — otherwise the evidence is fabricated.

---

### D-P1-2 — Batch interpreter advances `pc_ += 3` for 2-unit opcodes (`const-string`, `new-instance`)

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Batch interpreter
**Files:** `dex_interpreter_batch.cpp` — `execute_const_string`, `execute_new_instance`
**Severity:** P1 (the interpreter reads PC one unit too far after every `const-string` / `new-instance`; decoded opcodes after the first are garbage)

**A. Finding**
```cpp
bool DexInterpreterBatch::execute_const_string(uint32_t pc, InstructionTraceEntry& entry) {
    ...
    pc_ += 3;   // ← 21c is 2 code units
```
```cpp
bool DexInterpreterBatch::execute_new_instance(uint32_t pc, InstructionTraceEntry& entry, ...) {
    ...
    pc_ += 3;   // ← 22c is 2 code units
```
`invoke-*` (35c) and `filled-new-array` (35c) and `fill-array-data` (31t) are 3 units. `const-string` (21c) and `new-instance` (22c) are 2.

**B. Root cause**
Copy-paste of the `invoke` length (3) into the handler bodies. Not a decode error — a PC-advance error.

**C. Expected behavior**
`pc_` advances by the exact code-unit count of the instruction format:
- `const-string` (21c): 2 units (`op`+`vAA` | `string@BBBB`)
- `new-instance` (22c): 2 units (`op`+`vAA` | `type@BBBB`)

**D. Implementation**
In both handlers, change `pc_ += 3;` to `pc_ += 2;`.

**E. Reproduction**
```bash
./miniandroid run --apk fixture.apk --batch-interpreter
```
Trace PC after the first `const-string`. Compare against `dexdump -d`. Mismatch is off-by-one at the first such instruction; every subsequent opcode is decoded from the wrong offset.

**F. Integration guidance**
Isolated. Fix `D-P1-1` first so the batch's dispatch is meaningful at all; then this fix makes the trace trustworthy.

---

### D-P1-3 — `ApiDispatcher::dispatch` never increments `successful_calls_`

**Status:** `SOURCE_VERIFIED`
**Subsystem:** API dispatcher statistics
**File:** `api_dispatcher.cpp` — `ApiDispatcher::dispatch`
**Severity:** P1 (coverage report claims 0% success on every run regardless of actual behavior; downstream triage is misled)

**A. Finding**
```cpp
switch (result.status) {
    case Observatory::ApiImplementationStatus::FOUND_AND_EXECUTED:
        successful_calls_ ;   // ← bare expression, no effect
        break;
```
`successful_calls_` is never incremented on this branch. The other branches (`failed_calls_`, `stubbed_calls_`, `critical_missing_calls_`) are also bare expressions. So **all four counters stay at 0 forever**.

**B. Root cause**
Missing `++`. Likely a typo during initial authoring; the compiler doesn't warn because `successful_calls_ ;` is a valid (if pointless) statement.

**C. Expected behavior**
`++successful_calls_;` on `FOUND_AND_EXECUTED`, etc.

**D. Implementation**
```cpp
switch (result.status) {
    case Observatory::ApiImplementationStatus::FOUND_AND_EXECUTED:
        ++successful_calls_;
        break;
    case Observatory::ApiImplementationStatus::FOUND_BUT_FAILED:
        ++failed_calls_;
        break;
    case Observatory::ApiImplementationStatus::MISSING_STUB:
        ++stubbed_calls_;
        break;
    case Observatory::ApiImplementationStatus::MISSING_CRITICAL:
        ++critical_missing_calls_;
        missing_critical_apis_.push_back(context);
        break;
    default:
        break;
}
```

**E. Reproduction**
Run any APK. `ApiDispatcher::generate_coverage_report()` output will show `Total: N, Successful: 0, Failed: 0, Stubbed: 0, Critical Missing: 0` — the four counters sum to zero while `total_calls_` is nonzero.

**F. Integration guidance**
Isolated. Fix in the same commit as `D-P1-1` and `D-P1-2` (batch interpreter + dispatcher correctness cluster).

---

### D-P1-4 — `CallStack::dump_current_stack` is a use-after-free (dangling `const Frame*` into `temp`'s popped node)

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik call-stack diagnostics — invoked on halt / crash
**File:** `dalvik_engine.h` — `CallStack::dump_current_stack`
**Severity:** P1 (the tool that is supposed to explain a halt is itself UB when the halt happens deep in the stack; can crash or produce garbage — exactly when you need it most)

**A. Finding**
```cpp
json dump_current_stack() const {
    json arr = json::array();
    std::vector<const Frame*> frames;
    auto temp = stack_;
    while (!temp.empty()) {
        frames.push_back(&temp.top());   // pointer into temp's node
        temp.pop();                       // node destroyed
    }
    for (auto it = frames.rbegin(); it != frames.rend(); ++it) {
        arr.push_back((*it)->to_json());  // dereference dangling pointer
    }
    return arr;
}
```
`std::stack::pop()` destroys the top element (for the default `std::deque`/`std::vector` it is `pop_back` on the underlying container, followed by size decrement). The pointer stored in `frames` is therefore pointing at freed memory by the time the reverse pass runs.

**B. Root cause**
Confusion between "copy the stack" and "keep pointers into the copy". `std::stack` does not expose references on `pop()` (only on `top()`), so the correct pattern is a **by-value** copy of the frames before `pop()` destroys them.

**C. Expected behavior**
Return a JSON array of frames in the same order (root → top) built from value-copies. This is exactly what `peek_frames_top_first` already does correctly (it uses `std::vector<StackFrame>` by value).

**D. Implementation**
```cpp
json dump_current_stack() const {
    json arr = json::array();
    std::vector<Frame> frames;                 // by value
    auto temp = stack_;
    while (!temp.empty()) {
        frames.push_back(temp.top());           // deep copy
        temp.pop();
    }
    for (auto it = frames.rbegin(); it != frames.rend(); ++it) {
        arr.push_back(it->to_json());
    }
    return arr;
}
```

**E. Reproduction**
Trigger any halt (loop-detector, unimplemented opcode, max-instructions) in a stack with depth ≥ 2. Under ASan: heap-use-after-free inside `dump_current_stack`. Without ASan: garbage frame names in the trace, sometimes crash.

**F. Integration guidance**
Isolated. Correctness-of-evidence fix — must be merged before any crash report from the interpreter is treated as evidence.

---

## P2 — MEDIUM: Correctness and safety in specific paths

---

### D-P2-1 — `HeapObject::set_field` allows unbounded `array_store` growth → trivial DoS / OOM

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik heap
**File:** `dalvik_engine.h` — `HeapObject::set_field`
**Severity:** P2 (a hostile or buggy APK writing `array[2000000000] = v` allocates ~16 GB; any single DEX byte can trigger a process OOM)

**A. Finding**
```cpp
int32_t ai;
if (parse_array_index(name, ai)) {
    ...
    if (ai >= array_length) {
        array_length = ai + 1;
        if ((int32_t)array_store.size() < array_length)
            array_store.resize(array_length);   // no cap
    }
    array_store[ai] = value;
```
No upper bound; `resize()` on a `std::vector<DalvikValue>` of ~1e9 elements.

**B. Root cause**
The array store was designed for real-app-sized arrays (the comment cites Telegram's MB-scale buffers). No defensive cap was added.

**C. Expected behavior**
AOSP's `NewArray` throws `OutOfMemoryError` when the array can't be allocated. The engine should **refuse** with a bounded exception rather than take the process down.

**D. Implementation**
```cpp
static constexpr int32_t kMaxArrayLength = 64 * 1024 * 1024;   // 64M elements ≈ 1 GiB at 16 B/elem
if (ai >= kMaxArrayLength) {
    throw std::length_error(
        "HeapObject::set_field: array index " + std::to_string(ai) +
        " exceeds runtime cap (" + std::to_string(kMaxArrayLength) + ")");
}
```

**E. Reproduction**
Synthetic DEX with `const/4 v0, #0; new-array v0, v1, [I; const v1, #2000000000; aput v0, v0, v1`. Under the current source: OOM kill (OOMKiller or `bad_alloc`).

**F. Integration guidance**
Isolated to `HeapObject`. Does not conflict with other coders.

---

### D-P2-2 — `parse_array_index` accepts `array[]` and `array[abc]` (no endptr check); silently aliases them onto `array[0]`

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik heap
**File:** `dalvik_engine.h` — `HeapObject::parse_array_index`
**Severity:** P2 (silent misbehavior; `set_field("array[]", v)` writes `array[0]`)

**A. Finding**
```cpp
static bool parse_array_index(const std::string& name, int32_t& out) {
    if (name.size() < 7 || name.compare(0, 6, "array[") != 0)
        return false;
    if (name.back() != ']') return false;
    out = (int32_t)strtol(name.c_str() + 6, nullptr, 10);
    return true;
}
```
`"array[]"` has length 7 → passes the size check → `strtol("")` returns 0 with `endptr == begin` (not checked) → `out = 0`. `"array[abc]"` similarly passes and `out = 0`.

**B. Root cause**
No `endptr` capture and no "all bytes between `[` and `]` consumed" assertion.

**C. Expected behavior**
`parse_array_index` should return `false` on any input that is not exactly `array[<decimal int>]`.

**D. Implementation**
```cpp
static bool parse_array_index(const std::string& name, int32_t& out) {
    static constexpr const char* kPrefix = "array[";
    static constexpr size_t kPrefixLen = 6;
    if (name.size() <= kPrefixLen + 1) return false;             // must have ≥1 digit
    if (name.compare(0, kPrefixLen, kPrefix) != 0) return false;
    if (name.back() != ']') return false;
    const char* begin = name.c_str() + kPrefixLen;
    char* end = nullptr;
    long v = std::strtol(begin, &end, 10);
    if (end == begin) return false;                               // no digits
    if (end != name.c_str() + name.size() - 1) return false;      // trailing junk before ']'
    if (v < 0 || v > INT32_MAX) return false;
    out = static_cast<int32_t>(v);
    return true;
}
```

**E. Reproduction**
Unit-test `parse_array_index` with `"array[]"`, `"array[abc]"`, `"array[12x]"`, `"array[12]"` — only the last should return `true`.

**F. Integration guidance**
Isolated. Merge with `D-P2-1`.

---

### D-P2-3 — `DexParser::parse_class_defs` silently discards `parse_class_data` failure

**Status:** `SOURCE_VERIFIED`
**Subsystem:** DEX parser
**File:** `dex_parser.cpp` — `parse_class_defs`
**Severity:** P2 (a partially-parsed class is injected into `report.classes` with empty `direct_methods`/`virtual_methods`; downstream `try_recursive_invoke` silently returns `false`; the failure surface is a missing-method error, not a parse error)

**A. Finding**
```cpp
if (class_def.class_data_off != 0 && class_def.class_data_off < current_size_) {
    parse_class_data(data, class_def, info);   // return value ignored
}
```

**B. Root cause**
No `if (!parse_class_data(...))` guard.

**C. Expected behavior**
Either (a) propagate a parse error up so the whole class is skipped and reported, or (b) at minimum emit a structured log line so downstream `REC-MISS` events can be traced back to the parse failure.

**D. Implementation**
```cpp
if (class_def.class_data_off != 0 && class_def.class_data_off < current_size_) {
    if (!parse_class_data(data, class_def, info)) {
        log("WARN: class_data parse failed for " + info.name +
            " — class will be present with empty method/field lists");
        // Optionally: report.classes.push_back(info); continue;  // skip
    }
}
```

**E. Reproduction**
Corrupt a class_def by 1 byte in a fixture DEX; run the parser with `--verbose`; observe that the class is present in `report.classes` with empty method tables but no error was logged.

**F. Integration guidance**
Isolated. Merge with `D-P2-1` and `D-P2-2` as the "defensive bounded parsing" cluster.

---

### D-P2-4 — `dalvik_engine.cpp` shell-injects `path` into `popen("unzip -p ...")`

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Asset loader
**File:** `dalvik_engine.cpp` — `cached_asset_bytes` (the `unzip -p` path)
**Severity:** P2 (asset name comes from the DEX string pool; a hostile DEX can execute arbitrary shell commands as the user running MiniAndroid)

**A. Finding**
```cpp
std::string cmd = "unzip -p '" + apk_path_ + "' 'assets/" + path + "' 2>/dev/null";
FILE* pipe = popen(cmd.c_str(), "r");
```
`path` is a DEX string (`const-string` operand). It is concatenated into a shell command with single-quote delimiters. A DEX string containing `'` terminates the quote, allowing arbitrary shell injection (`x'; rm -rf ~; '`).

**B. Root cause**
`popen` invokes `/bin/sh -c <cmd>`; single quotes are the only thing separating the caller-controlled bytes from shell metacharacters.

**C. Expected behavior**
Either (a) invoke `unzip` (or a built-in libarchive reader) via `execve` with an `argv[]` (no shell), or (b) reject any `path` containing `'`, `;`, `` ` ``, `$`, `\`, `\n`, `&`, `|`, `<`, `>` before building the command.

**D. Implementation (immediate mitigation)**
```cpp
static bool asset_path_is_safe(const std::string& p) {
    for (char c : p) {
        if (c == '\'' || c == ';' || c == '`' || c == '$' || c == '\\' ||
            c == '\n' || c == '&' || c == '|' || c == '<' || c == '>')
            return false;
    }
    return true;
}
```
Then before `popen`:
```cpp
if (!asset_path_is_safe(path)) {
    last_error_ = "unsafe asset path: " + path;
    return empty;
}
```
(Long-term: replace `popen` with `execve("/usr/bin/unzip", argv, envp)` and `read()` from a pipe — no shell involvement.)

**E. Reproduction**
Synthetic DEX with `const-string v0, "x'; touch /tmp/pwned; '"` followed by `AssetManager.open(v0)`. After the run: `/tmp/pwned` exists.

**F. Integration guidance**
Isolated. This is a security fix and should be merged **before** any corpus-wide APK execution campaign.

---

### D-P2-5 — `dex_parser.cpp` truncates the `tries[]` + handler list to 4 KiB → catch handlers silently break

**Status:** `SOURCE_VERIFIED`
**Subsystem:** DEX parser
**File:** `dex_parser.cpp` — `parse_code_item`
**Severity:** P2 (methods with large `encoded_catch_handler_list` — nested try/catch, coroutine state machines — will have their handler data truncated; `find_catch_handler_for_pc` then reads past the end or reads stale bytes)

**A. Finding**
```cpp
size_t max_catch_data = 4096;
size_t available = current_size_ - tries_start;
size_t to_copy = std::min(available, tries_bytes + max_catch_data);
method.tries_data.resize(to_copy);
```
Any handler list longer than 4096 bytes is truncated. There is no sentinel or "truncated" flag emitted.

**B. Root cause**
Defensive size cap chosen by hand; the correct cap is `current_size_ - tries_start` (the rest of the file — the handler list is the last thing in a `code_item`, and the next `code_item` belongs to a different method, so there is no correct "end" other than the file end without re-parsing the map).

**C. Expected behavior**
Copy the full remainder of the file; the decoder uses the *length* of `current_tries_data_size_` as its bound (which it already does, correctly).

**D. Implementation**
```cpp
size_t available = current_size_ - tries_start;
if (tries_start + tries_bytes <= current_size_) {
    method.tries_data.assign(data + tries_start, data + current_size_);
} else {
    log("  ⚠️ tries[] extends beyond file — skipping tries capture");
}
```
(i.e. drop the `max_catch_data` cap; the file-end bound is already the correctness bound.)

**E. Reproduction**
Any APK with a method whose handler list is > 4 KiB (coroutine-heavy Compose methods are the common case). After the fix, `[EXCEPTION] → jumping to handler` appears for a catch that previously fell through to "unhandled".

**F. Integration guidance**
Isolated. Merge with `D-P2-3` as the "DEX parser soundness" cluster.

---

### D-P2-6 — `execute_return_wide` zero-extends instead of sign-extending when the source register is `INT32`

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik interpreter — `return-wide`
**File:** `dalvik_engine.cpp` — `execute_return_wide`
**Severity:** P2 (a negative `int32_t` in a `long` return is widened to a positive `int64_t`)

**A. Finding**
```cpp
if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
    int64_t coerced = static_cast<int64_t>(static_cast<uint32_t>(val.int_val));
    val = DalvikValue::make_long(coerced);
}
```
`static_cast<uint32_t>(val.int_val)` converts `-1` to `0xFFFFFFFF`; then `int64_t` yields `4294967295`, not `-1`.

**B. Root cause**
The `uint32_t` cast was presumably meant to normalize the union, but it erases the sign. This is the same class of bug as `D-P0-2` (truncation via cast).

**C. Expected behavior**
`return-wide` of an `INT32`-tagged register is a verifier-level impossibility in real DEX (the register should be `INT64` after a `const-wide`), but the *defensive* widening — which is what the code intends — must be sign-preserving:
```cpp
val = DalvikValue::make_long(static_cast<int64_t>(val.int_val));
```

**D. Implementation**
One-line fix (remove the `uint32_t` cast).

**E. Reproduction**
Method with `const/4 v0, #-1; return-wide v0` (illegal DEX but reachable after any previous corruption). Trace shows `RETURN_WIDE -1L` after fix, `RETURN_WIDE 4294967295L` before.

**F. Integration guidance**
Isolated. Merge with the batch-interpreter cluster or as a standalone one-liner.

---

### D-P2-7 — `SharedPreferencesEditor::apply()` uses a discarded `std::async` future; blocks on destruction and skips listener notification

**Status:** `SOURCE_VERIFIED`
**Subsystem:** `SharedPreferences` (used by `ApplicationContext` used by the Android framework layer)
**File:** `shared_prefs.cpp` — `SharedPreferencesEditor::apply`
**Severity:** P2 (contradicts the documented non-blocking contract; if `prefs_ptr` is destroyed before the async task starts, use-after-free; listeners never observe `apply()` changes)

**A. Finding**
```cpp
void SharedPreferencesEditor::apply() {
    ...
    std::async(std::launch::async, [prefs_ptr, puts_copy, ...]() {
        std::lock_guard<std::shared_mutex> lock(prefs_ptr->m_rw_lock);
        ...
        prefs_ptr->saveToFile();
        // ... For safety, we skip listener notification in async mode
    });
}
```
Three problems:
1. The `std::future` returned by `std::async(std::launch::async, ...)` is discarded. Its destructor **blocks** until the task completes — so `apply()` is *synchronous in practice*, contradicting the documented contract.
2. `prefs_ptr` is a raw pointer; if the parent `SharedPreferences` is destroyed before the async task starts, the task dereferences a dangling pointer.
3. Listeners are not called, breaking the documented `apply()` contract (`onSharedPreferenceChanged` must fire on the main thread after `apply()` — see AOSP `SharedPreferencesImpl`).

**B. Root cause**
Attempted async, but the future lifetime and pointer ownership were not designed.

**C. Expected behavior**
The minimal honest fix is to make `apply()` **explicitly synchronous** (call the same code path as `commit()`, including listener notification, but without the boolean return value). This is documented in Android's `SharedPreferences` javadoc as "the actual write is asynchronous"; the engine doesn't have a message queue for the async write to land in.

**D. Implementation**
```cpp
void SharedPreferencesEditor::apply() {
    // Engine has no background write thread; apply() == commit() without return.
    (void)commit();
}
```
Then remove the `std::async` include if unused.

(Long-term, if `Handler`-based async is desired: capture a `std::shared_ptr<SharedPreferences>` and queue through the existing `HandlerShadow`.)

**E. Reproduction**
Call `prefs.edit().putString("k","v").apply()`. Before fix: listener callbacks are never invoked, and — if the `SharedPreferences` object is a local — the process aborts with a use-after-free under ASan. After fix: listener fires.

**F. Integration guidance**
Isolated to `shared_prefs.cpp`. Does not conflict with other coders.

---

### D-P2-8 — Hardcoded Telegram-specific static keys in the generic engine

**Status:** `SOURCE_VERIFIED`
**Subsystem:** Dalvik engine — `bridge_to_api` and `bind_manifest_application`
**Files:** `dalvik_engine.cpp` (multiple sites), `dalvik_engine.h` (`bind_manifest_application`)
**Severity:** P2 (pollution of the general runtime with per-app state; a second APK with a coincidentally-same class name will receive the state)

**A. Finding**
```cpp
static_field_storage_["Lorg/telegram/messenger/ApplicationLoader;.applicationContext"] = ...
```
```cpp
static_field_storage_["Lorg/telegram/messenger/NativeLoader;.nativeLoaded"] = ...
```
And in the batch-interpreter `resolve_method`: literal `"onCreate"`, `"<init>"`, `"setText"` matches.

**B. Root cause**
The engine was validated against Telegram first; app-specific seeds were added inline as unblockers. The protocol (Section 5) explicitly forbids this: "Never add an application-specific condition merely to make one screenshot pass."

**C. Expected behavior**
App-specific seeds should live in a `TelegramProfile` class that is **only** instantiated when running a Telegram APK (detected by `package_name` in the `ApkInfo`). The engine core must contain zero `Lorg/telegram/` literals.

**D. Implementation**
1. Add `class AppProfiles` with a virtual `seed_static_fields(DalvikExecutionEngine&)` and a `TelegramProfile` subclass.
2. Look up the profile by `package_name` in `execute_apk_with_activity`.
3. Remove every `Lorg/telegram/` literal from `dalvik_engine.cpp` and `dalvik_engine.h`.

**E. Reproduction**
Run any non-Telegram APK. Search the static-storage dump for `Lorg/telegram/` — under the current source it will be populated even for unrelated packages.

**F. Integration guidance**
Larger refactor; schedule as a separate wave. Log as `DISCOVERED` and follow the 30–50% rule: deliver the `AppProfiles` skeleton first, then migrate one literal per handoff.

---

## P3 — LOW: Quality/consistency

### D-P3-1 — `save_to_directory` reports success even when no file was written
`execution_observatory.cpp`: `saved_ = true; return true;` is reached after `if (json_file.is_open())` branches that fall through on open failure. Fix: track a `bool ok` across all four `ofstream`s and `return ok`. Merge with `D-P1-3`.

### D-P3-2 — Batch interpreter off-by-one: `pc + 2 >= bytecode_.size()` rejects the last valid instruction
For a 2-unit instruction at `pc`, the last valid `pc` is `size - 2`. The condition `pc + 2 >= size` returns `false` (rejects) exactly at `pc == size - 2`. Use `pc + 1 >= size` for 2-unit opcodes. Merge with `D-P1-2`.

### D-P3-3 — "D8/R8 hybrid goto" (opcode 0x28 read as both 10t and 20t) is not AOSP behavior
`dalvik_engine.cpp::execute_goto`: the extra `if (offset == 0 && pc + 1 < size)` branch invents a 2-unit interpretation. Either D8/R8 produce malformed DEX (unlikely — `dexdump` accepts them) or the original malformation was a different bug surfacing at this site. Recommend: remove the hybrid branch, and add a corpus-wide `dexdump`-vs-engine PC-advance check. Log as `DISCOVERED`, not `SOURCE_VERIFIED` — this needs empirical verification before a fix is written.

### D-P3-4 — `generate_trace = true` with `trace_cap = 0` (config inconsistency)
`dalvik_engine.h::Config`. Downstream consumers that check only `generate_trace` will expect traces that are never produced. One-line consistency fix.

---

## Summary table for the ledger

| ID | Status | Severity | Subsystem | One-line |
|---|---|---|---|---|
| D-P0-1 | SOURCE_VERIFIED | P0 | interpreter | `pc_visit_count_` not resized → OOB write |
| D-P0-2 | SOURCE_VERIFIED | P0 | interpreter | `move/16` truncates to `uint8_t` + wrong 32x decode |
| D-P0-3 | SOURCE_VERIFIED | P0 | interpreter | register API façade is `uint8_t`, defeats `uint16_t` widening |
| D-P0-4 | SOURCE_VERIFIED | P0 | interpreter | `invoke-static` reads `regs[5]` when `reg_idx==4` |
| D-P0-5 | SOURCE_VERIFIED | P0 | opcode table | `MOVE_WIDE_16 = 0x06` undefined |
| D-P1-1 | SOURCE_VERIFIED | P1 | batch interp | `resolve_method` ignores `method_idx` |
| D-P1-2 | SOURCE_VERIFIED | P1 | batch interp | `pc_ += 3` for 2-unit opcodes |
| D-P1-3 | SOURCE_VERIFIED | P1 | API dispatcher | counters never incremented |
| D-P1-4 | SOURCE_VERIFIED | P1 | call-stack diag | `dump_current_stack` use-after-free |
| D-P2-1 | SOURCE_VERIFIED | P2 | heap | unbounded array growth |
| D-P2-2 | SOURCE_VERIFIED | P2 | heap | `parse_array_index` no endptr check |
| D-P2-3 | SOURCE_VERIFIED | P2 | DEX parser | `parse_class_data` failure silent |
| D-P2-4 | SOURCE_VERIFIED | P2 | asset loader | shell injection via `popen` |
| D-P2-5 | SOURCE_VERIFIED | P2 | DEX parser | tries data truncated to 4 KiB |
| D-P2-6 | SOURCE_VERIFIED | P2 | interpreter | `return-wide` zero-extend on `INT32` |
| D-P2-7 | SOURCE_VERIFIED | P2 | SharedPrefs | `apply()` blocks + skips listeners |
| D-P2-8 | SOURCE_VERIFIED | P2 | engine | Telegram-specific hardcoding |
| D-P3-1 | DISCOVERED | P3 | observatory | false-success on save |
| D-P3-2 | SOURCE_VERIFIED | P3 | batch interp | off-by-one in `pc + 2 >= size` |
| D-P3-3 | DISCOVERED | P3 | interpreter | hybrid `goto` is not AOSP — needs empirical verification |
| D-P3-4 | SOURCE_VERIFIED | P3 | config | `generate_trace=true` + `trace_cap=0` |

**Counts:** P0 = 5, P1 = 4, P2 = 8, P3 = 4. Total = 21.

---

## Integration order recommendation (to main coder)

1. **Cluster A (merge together, first commit):** `D-P0-3` + `D-P0-2` + `D-P0-5` — register-width widening. Without this, nothing else about register handling can be trusted.
2. **Cluster B (second commit):** `D-P0-1` — one-line, zero-conflict, prevents heap corruption from every subsequent run.
3. **Cluster C (third commit):** `D-P0-4` — 6 lines, prevents stack OOB in every invoke.
4. **Cluster D (fourth commit):** `D-P1-1` + `D-P1-2` + `D-P1-3` + `D-P3-2` — batch-interpreter correctness. Must land before the batch is used as evidence.
5. **Cluster E:** `D-P1-4` — crash-evidence correctness. Must land before any crash report is trusted.
6. **Cluster F:** `D-P2-4` — security fix. Must land before any corpus run.
7. **Cluster G:** the remaining P2 and P3 items, in any order.

---

## What I did NOT verify (honest gaps)

- I did not run any of the reproduction commands. Statuses are `SOURCE_VERIFIED`, not `UNIT_TESTED` or `HARNESS_TESTED`.
- `D-P3-3` (hybrid `goto`) is logged as `DISCOVERED` — it needs empirical comparison against `dexdump` before a fix is prescribed.
- `encoded_value.h::VALUE_CHAR` — I did not find a bug, but the reading of the spec leaves ambiguity that needs an AOSP `DexSwapVerify` comparison. Not logged as a defect; log as `DISCOVERED` for the next coder who reviews that file.
- `http_client.cpp` HTTP/2 absence is a documented limitation, not a defect. Not logged.
- `text_shaper.cpp` — I flagged one suspicious pattern (`result.width += ait->second - g.x_advance` appearing identically in both branches of an `if`), but the preceding `if/else` differs in a way I could not fully validate without running HarfBuzz. Log as `DISCOVERED` for a dedicated text-shaper review; do not merge a fix without HarfBuzz verification.

---

*End of report. Coder D — for review by main coder and coder peers.*