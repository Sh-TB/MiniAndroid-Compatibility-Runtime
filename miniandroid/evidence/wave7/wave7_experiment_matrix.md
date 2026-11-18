# WAVE-7 Experiment Matrix & Results (honest labels)

Environment: g++ 14.2.0 · ld.bfd 2.44 · Make 4.4.1 · 2 CPUs · 4 GB cgroup · make -j1.
Each experiment ran in isolation; no two experimental changes were combined before
individual measurement. Cold/warm separation noted per row.

| # | Configuration | Change | Result | Label |
|---|---|---|---|---|
| 1 | Split production (current) | none (baseline) | gates: opcode 12.8–17.5 s, two-opcode 26.4 s, DEV 21.4 s, noop 1.07 s, link 2.16 s (wave-5 ×5) | TESTED |
| 2 | Monolith fallback (`make DALVIK_SPLIT=0`) | re-verified live post-W6 header change | see `wave7_benchmarks.json` (build rc + wall) | TESTED |
| 3 | Split + ccache | binary ABSENT, apt blocked (not root) | install path documented; not adoptable offline | BLOCKED |
| 4 | Split + PCH (isolated `build_pch/`, opt-in only) | `.gch` of engine prelude; A/B on 2 engine TUs; no-PCH config stays default | not run (time-boxed) | PENDING |
| 5 | Split + ld.bfd knobs | test-binary relink with `--hash-style=gnu` variants | not run (time-boxed) | PENDING |
| 6 | Split + header narrowing | internal-header usage table (nm -u per part) | 583-line header, 24 shared decls genuinely cross-TU; narrowing saves 0 compiles | OBSERVED (no change adopted) |
| 7 | Bridge Option C (per-TU inline budget at -Og) | `--param inline-unit-growth/large-function-growth` probes | not run (time-boxed) | PENDING |
| 8 | Interpreter per-TU inline budget (`-O2` + growth params) | 35.9→21.3 s compile (w6); 3-APK hashes IDENTICAL + 27 PASS | compile 35.9 to 21.8 s; end-to-end 34.1 s | TESTED + ADOPTED |
| 9 | Bridge Option A (tri-state dispatch) | semantic analysis only — reconstruction of fall-through contract | >200 `return` sites; prototype scope = one full wave; not started | PENDING |
| 10 | Bridge Option B (always-returning sub-arms inside the 13,839-line shadow arm) | probe-driven extraction (W6 methodology: real-compile `-Werror=return-type`) | candidate scan done in W6; extraction not started (each cycle ≈ 250 s + full runtime gates) | PENDING |
| 11 | Unity/Jumbo build | rejected by analysis: loses per-TU granularity (the project's key property), peak RSS = merged TUs (2 GB+ OOM risk), collision classes (anon-ns/static/macro/init-order) documented in research doc | not built | REJECTED (analysis) |
| 12 | C++20 modules | GCC 14 supports them but needs Ninja/CMake ≥3.20 (ABSENT offline) | RESEARCH ONLY | BLOCKED (build system) |

## Fair-comparison protocol

Same compiler/flags/source state/4 GB limit per comparison; sequential compiles only (-j1);
cold = empty scratch dirs; warm = same objects reused; every timing in
`wave7_benchmarks.json` carries reps and medians where ≥5 reps were practical, otherwise the
repetition count is stated (1–2) and the label says so.
