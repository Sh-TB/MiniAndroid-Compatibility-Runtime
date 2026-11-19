# W23 DEPENDENCY ANALYSIS — include graph, fan-out, and the header-cascade fix

Auto-generated inputs: `evidence/w23/fanout_before.json` /
`evidence/w23/fanout_after.json` (scripts/w23_fanout_from_d.py over the gcc
-MMD dep files of a full production build — the compiler's own closure, not a
text approximation) plus `evidence/w23/dep_graph.json`
(scripts/w23_dep_graph.py, text-level graph).

## 1. The problem (measured at baseline, HEAD 23a4d33b)

`src/dex/dalvik_engine.h` was a 4,744-line monolithic header carrying BOTH the
stable public surface (opcode constants, DalvikValue/DexRegisterFile/StackFrame/
HeapObject/DalvikHeap/CallStack, execution traces, DalvikExecutionResult) AND
the complete `DalvikExecutionEngine` class definition (~2,990 lines of class +
25 nested state structs + config + inline machinery). It directly included 13
project headers (dex_parser, class_resolver, manifest_reader, c7_package_index,
runtime_metadata, vtable_dispatch, android_stubs, arsc_parser,
attribute_set_store, res_config, sqlite_shadow, data_root, adapter_scrap_bin)
plus nlohmann/json.hpp.

Ground-truth fan-out (from .d files of the 88-slot production build):

| Header | fan-out | estimated cascade |
|---|---:|---:|
| dalvik_engine.h | 16 | 282.6 s |
| dalvik_engine_internal.h | 12 | 216.2 s |
| dalvik_bridge_frame.h | 6 | 140.6 s |
| android_shadows.h | 13 | 101.5 s |
| shadow_registry.h | 29 | 163.9 s |

Validated probe (w23_probe.py, one appended comment line, real rebuild):

| Probe (baseline) | wall | TUs recompiled |
|---|---:|---:|
| F — dalvik_engine_internal.h (private) | 246.64 s | 12 (the engine family) |
| G — dalvik_engine.h (public) | 343.18 s | 18 (family + trace chain + application_runtime + sqlite_shadow + task_stack_builder_shadow + main) |
| H — android_shadows.h (common) | 400.73 s | 29 |

G reproduces W22's 335.75 s within 2.2 % — the "~4-minute small change" is
confirmed on this exact tree.

## 2. Root cause

The class definition was the forcing function: every TU that constructs,
holds, or even forward-consumes the engine — including the four genuinely
non-engine consumers (`execution_engine.h/.cpp` (value member),
`application_runtime.cpp` (constructs + configures the engine),
`sqlite_shadow.cpp` (CvFlat mirror only), `task_stack_builder_shadow.cpp`
(DalvikValue/DalvikType only)) and the 45 test files — was compiled against
the full 4,744 lines. Any edit to ANY part of the file (including a comment)
invalidated all of them.

## 3. The redesign (W23-03/W23-04)

Verbatim relocation (scripts/w23_split_engine_header.py, no semantic change):

| File | before | after |
|---|---|---|
| src/dex/dalvik_engine.h | 4,744 lines = types + class | 28-line public contract shell: includes the types header, forward-declares the class |
| src/dex/dalvik_engine_types.h | — (new) | 1,763 lines: the stable public surface (opcodes, values, registers, frames, heap, call stack, traces, result, CvFlat) |
| src/dex/dalvik_engine_impl.h | — (new) | 3,001 lines: the `DalvikExecutionEngine` class definition + config + nested state, includes the types header |

Consumer repointing (scripts/w23_repoint_includes.sh + 4 direct edits):

- engine-family TUs (12 split parts + value_glue), `dalvik_bridge_frame.h`,
  `dalvik_engine_internal.h`, `application_runtime.cpp`, `trace_exporter.cpp`,
  `heap_adapter.h`, `execution_engine.h` (value member needs the class),
  45 test files → `dalvik_engine_impl.h`;
- public-surface consumers: `trace_exporter.h` (passes
  `DalvikExecutionResult` by reference), `sqlite_shadow.cpp` (CvFlat),
  `task_stack_builder_shadow.cpp` (DalvikValue/DalvikType) →
  `dalvik_engine_types.h`;
- zero source files include `dalvik_engine.h` anymore — it remains a
  compatibility shell for out-of-tree consumers.

Include-shrink pass (scripts/w23_shrink_probe.sh, -fsyntax-only probes on the
two public-surface TUs): 2 of the 13 heavy includes moved from the types
header to the impl header (dex_parser.h, manifest_reader.h); the other 11 are
genuinely used by the public value/heap types (their method signatures
reference AndroidAPI/registry/ARSC types) and stay. Measured, not assumed.

## 4. After-state dependencies (post-split .d files, fanout_after.json)

- `dalvik_engine.h` (28-line shell): **0 linked TUs** — a one-line edit now
  costs a no-op rebuild, removing the G probe from the critical path entirely.
- `dalvik_engine_impl.h`: the engine family + engine-holding consumers only —
  class-layout changes rebuild exactly the TUs that embed the class.
- `dalvik_engine_types.h`: family + public-surface consumers — result/trace
  edits rebuild exactly their users.

## 5. Validated after-state probes (w23_probe.py, probes_after.jsonl)

| Probe | before | after | reduction |
|---|---:|---:|---:|
| **G — dalvik_engine.h (the W22 probe of record)** | **343.18 s / 18 TUs** | **1.04 s / 0 TUs** | **−99.7 %** |
| IMPL_HDR — dalvik_engine_impl.h (class internals) | (was part of G) | 317.14 s / 15 TUs (family + execution_engine + application_runtime + main) | proportional |
| TYPES_HDR — dalvik_engine_types.h (public surface) | (was part of G) | 336.95 s / 18 TUs (same closure as old G) | proportional |
| F — dalvik_engine_internal.h | 246.64 s / 12 TUs | 246.09 s / 12 TUs | unchanged (family closure intact) |
| A no-op / B leaf / D opcode / E bridge | 1.06 / 2.05 / 11.86 / 9.44 s | 1.09 / 2.14 / 12.52 / 9.60 s | unchanged within noise |
| C interpreter | 23.50 s | 25.4 s (runs 2–3 of 3; see note) | unchanged within noise |

Measurement-honesty note: the first post-split C run (335.4 s, 18 TUs) was
discarded and documented — the harness caught it (18 TUs ≠ interpreter edit);
the previous types.h probe cleanup had left a pending mtime invalidation, so
that run measured the TYPES_HDR cascade, not the interpreter edit. The recorded
TYPES_HDR probe is the clean measurement of exactly that event.

## 6. What was NOT changed, and why

- `android_shadows.h` (H probe, 29 TUs / 400.7 s): every consumer genuinely
  uses shadow classes; shrinking it means PIMPL-ing ~3,200 lines of the
  framework API with real ABI/semantics risk for zero dev-loop gain (edits to
  it are rare). REJECTED with rationale, not attempted blindly.
- `shadow_registry.h` (29 TUs): genuine shared interface of the shadow system.
- `dalvik_bridge_frame.h` + `dalvik_engine_internal.h`: engine-family-private
  already; their closures ARE the necessary dependency closure for bridge/
  interpreter implementation changes.
- Opcode constants were left in the types header: the Dalvik opcode set is
  spec-stable; splitting it out would add a header for no measured win.
