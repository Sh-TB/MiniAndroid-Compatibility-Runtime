# W6 Cut-Boundary Map (source-level, brace-depth verified at HEAD a20a93cc)

Machine-readable data: `evidence/wave6/w6_family_map.json`, `w6_arm_map.json`,
`w6_bridge_cut_state.json`.

## 1. dalvik_bridge.cpp — 55,384 lines, 99.7% is ONE function

- File: `src/dex/dalvik_bridge.cpp`
- Shared prelude (all 7 engine part files): lines 1–184 — includes +
  anonymous namespace with internal-linkage helpers `str_utf16_unit_count`
  (63–76), `str_char_at_unit` (81–124), `diag_env` (168–180).
- **`DalvikExecutionEngine::bridge_to_api` = lines 187–55,382 (55,196 lines).**
- Internal structure (brace-depth verified): 124 top-level dispatch arms
  (`if (class_name == … && method == …) { … }`) covering 22,963 lines, plus
  between-arm diagnostics/static-locals and a 13,839-line shadow-dispatch arm
  (17,166–31,004) containing 1 `goto` and many sub-arms.
- Candidate groups A–D of the issue map do NOT exist as separate functions —
  they are dispatch arms inside `bridge_to_api`.

### Implemented cut (IMPLEMENTED + TESTED, 4 arms, 534 lines)

| # | field | value |
|---|---|---|
| 1 | Original file | `src/dex/dalvik_bridge.cpp` |
| 2 | First/last function moved | arms at pristine lines 599, 2123, 5892, 7973 → helpers `bridge_arm_599` … `bridge_arm_7973` (verbatim whole-arm bodies) |
| 3 | Exact ranges at HEAD | 599–, 2123–, 5892–, 7973–8246 (from `w6_arm_map.json`) |
| 4 | Lines/functions moved | 534 lines in 4 helpers |
| 5 | Required decls/headers | 4 private-method declarations appended to `DalvikExecutionEngine` in `dalvik_engine.h`; shared signature `(const std::string& class_name, const std::string& method, const std::vector<DalvikValue>& args_raw, DalvikValue& result, ApiCallTrace::Status& status, uint32_t method_idx_hint, const std::vector<DalvikValue>& args)` |
| 6 | Symbols kept local | stateless lambda `f356_mp_engine_for` hoisted from fn scope into `namespace miniandroid { namespace { … } }` (empty-capture ⇒ exactly equivalent); dispatch order and conditions byte-identical |
| 7 | Cross-TU deps | none created (helpers stay in the bridge TU) |
| 8 | Expected RSS reduction | measured: 2,126 → 2,122 MB (small — the safe subset is 534 lines) |
| 9 | Fan-out increase | one-time: `dalvik_engine.h` gained 4 declarations (all 7 engine TUs rebuilt once); future helper-body edits rebuild only the bridge TU |

### BLOCKED boundary (measured, with proof)

- **21 of the 25 candidate arms (≥100 lines, 19,384→5,545-line safe subset
  rejected 21) are fall-through-capable dispatch arms**: their bodies end in a
  nested if whose false-path falls out of the arm into the NEXT arm.
  GCC CFG proof: `control reaches end of non-void function` for all 21 helpers
  at real compile (`-Werror=return-type`); runtime proof: a SIGILL (ud2) in
  `bridge_arm_45295` reproduced the bug; a 9-arm build looked green on Guess
  but was a false positive (truncated paths not exercised by that APK).
- Note: `-fsyntax-only` does NOT run gimplify and therefore NEVER emits this
  warning — the earlier probe hole; the real-compile probe is mandatory.
- Next concrete boundary: redesign the fall-through contract to a tri-state
  (`Returned(value)` / `FallThrough`) or extract provably-always-returning
  SUB-arms inside the 13.8K-line shadow arm; both change >200 return sites and
  need their own verified wave.

## 2. dalvik_interpreter.cpp — fetch_decode_execute (lines 184–5619, 5,436 lines)

Regions mapped (case-free if-chain dispatcher, 64 `execute_*` calls):
- fetch/decode + PTE probe prologue: ~187–260;
- register/operand handling inline arms: interleaved through the loop;
- exception paths: `throw_deferred` (5722–5770), `raise_synthetic_exception`
  (5771–5815), `find_catch_handler_for_pc` (5634–5709) — already separate
  functions;
- invoke dispatch: delegated to `execute_invoke_*` methods (in
  dalvik_opcodes_invoke.cpp since WAVE-5);
- branch/return handling: inline arms with `continue` (25 uses) and `pc_`
  mutation (35 sites).

**Verdict: helper extraction NOT mechanically safe** — loop-carried state
(`continue`, `pc_`, exception state) cannot cross a function boundary without
a state-struct/indirect-dispatch abstraction, which the issue forbids.
VERDICT: BLOCKED (evidence above); RSS already 1,118 MB < 1.5 GB target.
Compile-TIME lever measured: `-Og` 9.4 s (from 35.9 s) — hot-loop codegen risk,
needs a runtime benchmark wave before adoption (PENDING).
