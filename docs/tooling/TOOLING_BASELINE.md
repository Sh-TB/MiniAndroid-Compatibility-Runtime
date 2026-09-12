# TOOLING BASELINE — PHASE 0 REPORT (brief §45)

HEAD at report: `bcfd4405` (post-worklist) · CPU-only: **YES** · Offline: **YES** ·
API key: **NONE** · VPS: **NONE** · New mandatory dependencies: **ZERO** (stdlib-only tools)

## Existing tools (inventory, versions real)

| Tool | Version/Path | Role |
|---|---|---|
| g++/gcc | 14.2.0-19 | runtime build (Makefile) |
| make | 4.4.1 | build graph |
| OpenJDK | 21.0.12.1 | D8/ECJ fixture builds |
| aapt2 | 2.20-14304508 (`tools/aapt2/`) | APK compile/link/badging (fixture authority, D-04) |
| r8.jar / D8 | `tools/d8/r8.jar` | DEX build |
| ecj.jar | `tools/ecj/ecj.jar` | Java compile |
| android-34.jar | `tools/android-34.jar` | compile stubs |
| python3 | 3.12.14 + PIL 11.3.0 | tooling + screenshot metrics |
| git | 2.47.3 | evidence/churn |
| zip/unzip, objdump/readelf/nm/strings | system | APK/ELF inspection |
| repo disassemblers | `scripts/forensic/minidump_dex.py`, `f023_disasm.py`, `exp059_disasm.py`, `m6_*` | DEX ground-truth forensics (proven in every F-law) |
| runtime binary | `miniandroid/build/miniandroid` | real-APK execution + screenshot pipeline |
| sqlite3 | system lib | storage shadow evidence |

ABSENT (honest): clang/clang++, cmake, ninja, javac, adb, aapt2-on-PATH, baksmali/smali, androguard.

## New tools (this phase — all stdlib-only, no new deps)

| Tool | Command | What it removes |
|---|---|---|
| Shared APK/DEX/ARSC artifact factory | `python3 tools/verify/apk_artifacts.py <apk>` | repeated APK parsing; ONE parse → N root queries (cache key sha256+toolver) |
| Central root probe runner | `python3 tools/verify/verify.py --root R-NEW-XXX / --batch / --cluster apk\|source\|shot\|symbols / --list` | 30-grep investigations → 1 structured call |
| Evidence bundle collector | `python3 tools/verify/evidence.py <id> [--apk p] -- <cmd>` | manual log/sha/manifest collection (brief §7 schema) |
| Stub radar probe | `verify.py --cluster source` | manual TODO/REC-MISS/fail-soft hunting (POTENTIAL GAP verdicts only) |
| Screenshot metrics probe | `verify.py --cluster shot` | manual pixel forensics (w/h/colors/mean/SHA; re-proved golden 11e0056… from disk) |
| Symbol index probe | `verify.py --cluster symbols` | repeated tree walks (5,824 symbols at HEAD) |
| Doctor (health check) | `tools/doctor.sh [--json]` | manual tool-environment checks (17 components, all OK) |
| Agent index | `docs/agent-index/{REPO_MAP.md, SYMBOL_INDEX.json, HOTSPOTS.json, ROOT_GRAPH.json, TEST_GRAPH.json, API_COVERAGE.json, BUILD_GRAPH.json}` | per-session repo rediscovery |
| Root registry (machine-readable) | `root_registry.json` (286 roots) | status lookup without reading prose docs |
| Benchmark harness | `tools/verify/benchmark.py` → `benchmark_results.json` | unmeasured speed claims |

## Verified usable (proof-of-use, evidence-pinned)

- apk_artifacts.py: dooz d81292cd… → 106 entries / 19,385 methods / 4,596 classes / ARSC 143,884 B / badging OK; cold MISS 62 ms, warm HIT 25 ms (factory-internal), tool-call warm 38.7 ms median.
- verify.py fast path: R-NEW-246 package 575 B structured in 1 call (vs 4 greps, 1,023 B).
- screenshot-metrics probe: re-verified hello_color golden SHA 11e0056320d8546d… from disk (1.4 s PIL scan, 1,737,849 non-white px).
- doctor.sh: 17/17 components OK (JSON + text modes).
- Battery gate unchanged: 91/91 ALL PASS at the merged HEAD (no tooling regression).

## Rejected tools (with reasons — brief §37)

See `docs/root-searchlight/ROOT_TOOL_MATRIX.md`: Androguard/apktool/jadx (RESEARCH-ONLY — absent offline, same questions served by proven repo path), emulator/adb (REJECT — no substrate), Ghidra/radare2 (REJECT for DEX scope), bundletool (REJECT — no AAB corpus demand).

## Benchmark (REAL measurements, 3 runs, same machine/commit bcfd4405 — `tools/verify/benchmark_results.json`)

| Task | Manual baseline | Tool-assisted | Verdict |
|---|---|---|---|
| APK inspection (dooz) wall-clock | 22.5 ms median | cold 62.2 ms / cached 38.7 ms | **NO MATERIAL GAIN (0.6× — python startup dominates at 20 ms scale)** |
| Root investigation package (R-NEW-246) wall-clock | 14.1 ms (grep chain) | 22.1 ms (1 call) | **NO MATERIAL GAIN (0.6×)** |
| Root investigation tool-CALL count | 4 calls | 1 call | **4 calls → 1 call** |
| Root investigation context bytes | 1,023 B grep noise | 575 B structured | **44% context reduction** |
| APK inspection context bytes | 11,610 B dumps | 900 B summary (+cached JSON artifacts) | **92% context reduction** |
| Large-APK (73 MB-class) cache benefit | — | — | **UNMEASURED (no large APK in container)** |
| Shared-artifact reuse | parse per root | 1 parse serves 18 roots (cluster plan) | structural win, wall-clock UNMEASURED at corpus scale |

**Honest headline: the PHASE-0 fast path does NOT yet beat raw shell commands in
wall-clock on micro-tasks. Its proven value is evidence structuring, cache reuse,
tool-call/context reduction, and the registry fast path — measured as above, with
negative results recorded per brief §5/§39.** Future: batch runner amortization and
runtime-trace aggregation are where wall-clock wins are expected (UNMEASURED).

## Shared artifact / cache / batch / parallel status

- Shared artifacts: `artifacts/apk/<cache-key>/` (zip_index, dex_index, arsc_summary, badging, manifest).
- Cache: sha256(apk)+tool-version key; HIT/MISS recorded in manifest; invalidation by key change.
- Batch: `verify.py --batch` + `--cluster` (18 roots served by one parse).
- Parallel: NOT implemented (deliberate — safe-parallelism needs isolation analysis; UNMEASURED).

## Evidence status vocabulary

Enforced in evidence.py: RESEARCHED/IMPLEMENTED/TESTED/OBSERVED/VERIFIED/REGRESSION/FAILED/FALSE_LEAD/BLOCKED/UNPROVEN — never mixed; tool output ≠ root-proof.

## What the 278-root audit inherits (BEFORE → AFTER)

BEFORE: 278 roots × (manual investigation + repeated APK parsing + repeated source
search + repeated runtime setup + manual evidence collection).
AFTER: 286 registered roots → registry fast path (1 call each) → shared cached
APK/DEX/ARSC artifacts → cluster probes (apk/source/shot/symbols) → evidence
bundles → manual deep-dive ONLY for what tools cannot classify (brief §50).
