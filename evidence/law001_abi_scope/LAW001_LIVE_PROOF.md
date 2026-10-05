# LAW-001 LIVE PROOF — FIRST TEST LAW: ABI SCOPE (x86 / x86_64 ONLY)

Adopted: 2026-10-06 (project owner directive) · Session: CONT-6 (post-CONT-5)
Head at adoption: `6bc15a99` (evidence generated on this working tree)

---

## 1. The law (exact owner statement)

> Every app or game that is loaded and executed must be executable on the
> host CPU: it is either pure-DEX (no native libraries — ABI-neutral) or it
> ships x86 / x86_64 native libraries. An APK whose native trees contain
> no x86/x86_64 ABI (ARM32 / ARM64 / other) is OUT OF SCOPE: it is recorded
> with the verdict `ABI_OUT_OF_SCOPE` (SKIP) — NEVER counted as
> "MiniAndroid could not run the game".

* ARM is **deferred, not deleted** — removed from the failure criteria only;
  ABI translation may become a separate future project/phase once the core
  runtime matures (instruction translation, syscall/ABI compat, JNI
  bridging, alignment — a separate large layer deliberately kept out of the
  current mission).
* Main test path: x86/x86_64 or pure-DEX → DEX → Framework → Lifecycle →
  UI → Rendering → Input → State → Filesystem → DB → …
* Sub-laws: LAW-001a check order (FIRST, before install/launch, from real
  `lib/<abi>/` entries) · LAW-001b honest statistics (separate SKIP bucket)
  · LAW-001c deferred-not-deleted · LAW-001d pure-DEX always in scope ·
  LAW-001e mixed APKs in scope · LAW-001f no abuse as a failure escape
  hatch (real ABI evidence required).

Full text: [CONSTITUTION_V2.md → LAW-001](../../CONSTITUTION_V2.md) ·
Main-page banner: [README.md](../../README.md) ·
Profile binding: `docs/ENVIRONMENT_PROFILE.json` ENV-005 `scope_law`.

## 2. Implementation (files changed at this head)

| File | Change |
|---|---|
| `CONSTITUTION_V2.md` | LAW-001 section inserted after MISSION (before CORE PRINCIPLE) with 6 sub-laws |
| `README.md` | LAW-001 banner + two-path scope table on the main page |
| `scripts/unknown_apk_preflight.py` | 16-verdict contract 1.1: `ABI_OUT_OF_SCOPE` verdict, early scope gate before install/launch, `verdict_class` / `in_current_test_scope` / `counts_as_failure` fields, VERDICT_CLASS statistics map |
| `scripts/cont5_gate_matrix.py` | verdict list + per-row `verdict_class` + `statistics.json` (PASS/SKIP/FINDING/BLOCKED buckets) |
| `docs/ENVIRONMENT_PROFILE.json` | ENV-005 `scope_law` + updated `abi_selection_law` |
| `docs/execution-skill/SKILL.md` | verdict list 1.1 + LAW-001 as gate law (0) |
| `fixtures/arm_only_scope_probe/` | ARM-only fixture source (manifest + res + `MainActivity` + deterministic 64-byte `lib/armeabi-v7a` / `lib/arm64-v8a` stub payloads via `make_arm_stubs.py`) |

## 3. Live proof — ARM-only fixture through the REAL gate

Fixture: `fixtures/arm_only_scope_probe/` → built with the committed
aapt2/ECJ/D8 harness (`scripts/build/build_fixture_apk.sh`):

* APK: `run/law001/arm_only_scope_probe.apk`
* SHA-256: `4ce8b0dbf8a87697f133709210f6d21df60134b1e09a9532c0316881f48e4af1`
  (`apk_sha256_16` = `4ce8b0dbf8a87697`)
* native trees: `lib/armeabi-v7a/`, `lib/arm64-v8a/` (no x86 tree)

Gate result (`arm_only_probe_gate_verdict.json`):

```json
{"schema": "MINIANDROID_UNKNOWN_APK_PREFLIGHT/1.1",
 "verdict": "ABI_OUT_OF_SCOPE", "verdict_class": "SKIP",
 "in_current_test_scope": false, "counts_as_failure": false,
 "install": null, "launch": null,
 "is_environment_prerequisite": true, "elapsed_s": 0.0,
 "apk_abis": ["arm64-v8a", "armeabi-v7a"],
 "abi_scope": "OUT_OF_SCOPE (LAW-001)"}
```

LAW-001a proof: `install` and `launch` are **null** — the gate exited from
the ABI scope check BEFORE any install/launch attempt (elapsed 0.0 s).
LAW-001b proof: `counts_as_failure=false`, `verdict_class=SKIP`.

## 4. Control — the law works in BOTH directions

x86_64 native probe fixture (`native_probe_apk_fixture.apk`, trees
`lib/x86_64/`) through the same gate
(`x86_64_control_gate_verdict.json`):

* verdict `RUNTIME_ROOT` (the fixture's own deliberate `NativeMissing`
  negative-control arm recording an UnsatisfiedLinkError divergence —
  pre-existing fixture behavior, not a regression), `verdict_class=FINDING`,
  `in_current_test_scope=true`, install OK, launch reached.
* → x86 APKs are NOT skipped; the scope law relabels nothing in scope.

## 5. Unit sweep — classify() verdict order (8/8)

| Case | Verdict |
|---|---|
| arm64-v8a + armeabi-v7a only | `ABI_OUT_OF_SCOPE` |
| armeabi-v7a only | `ABI_OUT_OF_SCOPE` |
| mixed x86_64 + arm64-v8a | `PREFLIGHT_PASS` (in scope) |
| x86 only | `PREFLIGHT_PASS` (in scope) |
| pure-DEX (no libs) | `PREFLIGHT_PASS` (in scope) |
| arm-only AND install-failed | `ABI_OUT_OF_SCOPE` (LAW-001 preempts) |
| parse-failed | `UNKNOWN` (no ABI evidence → no scope relabel, LAW-001f) |
| x86 but minSdk 40 > host 34 | `ENVIRONMENT_BLOCKED` (unrelated prereq intact) |

## 6. Full gate-matrix rerun — zero drift

`scripts/cont5_gate_matrix.py` rerun at this head over the whole local
corpus + negatives (62 rows): **53/53 rows present in both the previous
committed matrix and this run carry IDENTICAL verdicts** (the 3 label-only
negative renames map 1:1 to the same verdicts: UNKNOWN / UNKNOWN /
RESOURCE_BLOCKED; 9 rows are newly added corpus titles, not drift).

Post-LAW-001 statistics (`matrix_statistics_after_law001.json`):
`PASS=3 · SKIP(out-of-scope)=0 · FINDING=56 · BLOCKED(could-not-run)=3`
— the SKIP bucket is zero because the local corpus currently contains
**zero ARM-only APKs** (58 pure-DEX + 11 x86/x86_64 + negatives); the
bucket is now live-proven via the fixture above and will absorb future
ARM-only titles honestly.

Corpus ABI census at this head: 69 distinct APKs scanned → 0 ARM-only,
11 x86/x86_64, 58 pure-DEX (ABI-neutral).

## 7. Reproduce

```bash
python3 fixtures/arm_only_scope_probe/make_arm_stubs.py fixtures/arm_only_scope_probe/lib
bash scripts/build/build_fixture_apk.sh fixtures/arm_only_scope_probe run/law001/arm_only_scope_probe.apk
python3 scripts/unknown_apk_preflight.py run/law001/arm_only_scope_probe.apk --json /tmp/v.json   # → ABI_OUT_OF_SCOPE
python3 scripts/cont5_gate_matrix.py                                                              # full matrix + statistics
```
