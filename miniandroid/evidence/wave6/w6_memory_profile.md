# W6 Memory Profile — measured per-TU compiler footprint (g++ 14.2.0, -j1, 4 GB cgroup)

Method: each TU compiled with its EXACT make flags to a scratch object; peak RSS via
RUSAGE_CHILDREN in a fresh interpreter per compile (not estimated from object size or
system RAM); wall/CPU via rusage; functions via `nm --print-size --size-sort -C`.

## Ranked table (peak RSS)

| TU | peak MB | wall s | CPU s | lines | obj MB | text MB | syms | hdr deps | flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| dalvik_bridge.cpp | **2126** (was) | 41.9 | 41.9 | 55384 | 6.56 | 6.2 | 6039 | 12 | -Og -g0 |
| dalvik_engine.cpp (monolith) | 2867 | 219.7 | 219.7 | 94201 | – | – | – | – | -O2 -g0 |
| dalvik_interpreter.cpp | 1118 | 35.9 | 35.8 | 6300 | 0.89 | 0.8 | 704 | 12 | -O2 -g0 |
| dalvik_engine_core.cpp | 1115 | 22.4 | 22.4 | 9457 | 1.37 | 1.3 | 842 | 12 | -O2 -g0 |
| dalvik_engine_invoke.cpp | 1027 | 23.4 | 23.4 | 12091 | 1.42 | 1.4 | 901 | 12 | -O2 -g0 |
| dalvik_opcodes_invoke.cpp | 973 | 14.6 | 14.6 | 6757 | 0.86 | 0.8 | 614 | 12 | -O2 -g0 |
| dalvik_opcodes.cpp | 929 | 10.3 | 10.3 | 4286 | 0.49 | 0.4 | 442 | 12 | -O2 -g0 |
| dalvik_engine_tail.cpp | 845 | 7.5 | 7.4 | 600 | 0.23 | 0.2 | 74 | 12 | -O2 -g0 |
| webview_engine.cpp | 834 | 20.5 | 20.4 | 6589 | 18.69 | 18.4 | – | – | -O2 -g |
| html_dom.cpp | 360 | 4.6 | 4.5 | 762 | 4.09 | 4.0 | – | – | -O2 -g |

(All remaining ~72 TUs measured in `w6_memory_profile.json`; none exceeds the dalvik set above.
Full JSON: `evidence/wave6/w6_memory_profile.json` with per-TU top functions and flags.)

## Findings

1. **The only TU above 1.5 GB is `dalvik_bridge.cpp` (2,126 MB at -Og; OOM-killed ~3,087 MB at
   -O2, rc=1 — re-measured at this HEAD).** Its 55,384 lines are 99.7% ONE function:
   `DalvikExecutionEngine::bridge_to_api` (lines 187–55,382). GCC's peak scales with the
   single function's GIMPLE, so file-level cuts cannot shrink it without touching the
   function body (see cut-boundary map).
2. All other engine TUs are already below 1.5 GB (max 1,118 MB).
3. Interpreter compile TIME (35.9 s) is front-end/GIMPLE-bound: `-Og` cuts it to 9.4 s but
   RSS stays 1,071 MB — and changes hot-loop codegen (rejected without runtime proof).
4. GGC tuning on the bridge (`--param ggc-min-expand=5/10 ggc-min-heapsize=1024/2048`)
   measured 1,796–1,829 MB with **object bytes sha256-identical to baseline** (codegen-
   neutral) but +10–18 s wall — documented as an optional RAM mitigation, not adopted.

## Experiments (measured, OBSERVED)

| experiment | rc | wall s | peak MB | note |
|---|---:|---:|---:|---|
| bridge -Og + GGC(10/2048) | 0 | 51.4 | 1829 | obj identical to baseline |
| bridge -Og + GGC(5/1024) | 0 | 59.5 | 1796 | obj identical to baseline |
| bridge -O2 + GGC | 1 | 73.4 | 3087 | still does not fit |
| interpreter -O2 + inline budget params | 0 | 21.3 | 1070 | -41% wall; codegen changes — needs runtime proof |
| interpreter -Og | 0 | 9.4 | 1071 | codegen changes — hot-loop risk |
| interpreter -fno-ipa-cp / -fno-ipa-sra | 0 | 34.5 / 37.2 | 1118/1117 | no effect |

## Header fan-out (from -MMD dep graphs, `header_fanout` in JSON)

shadow_registry.h: 29 objects · nlohmann/json.hpp: 17+13 · dex_parser.h: 14 ·
class_resolver.h: 13 · android_shadows.h: 13 · android_stubs.h / manifest_reader.h /
c7_package_index.h: 12 each · the 7 engine TUs each carry 12 header deps; touching
`dalvik_engine_internal.h` rebuilds exactly those 7 TUs (158.2 s, wave-5 measurement).
