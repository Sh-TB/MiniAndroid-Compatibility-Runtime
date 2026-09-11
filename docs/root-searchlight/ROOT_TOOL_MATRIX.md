# ROOT TOOL MATRIX (brief §36) — filled from PROVEN tools only

Rule: no guesses. Every row cites a Proof-of-Use in this repo. Tool output =
EVIDENCE, never root-proof (§2). Tool adoption decisions: DECISION_LEDGER + TOOLING_BASELINE.

| Root family / cluster | Best tool/probe (proven) | Proof-of-Use |
|---|---|---|
| APK structure / manifest / ZIP (R-NEW-033/045/064/081/086/087) | `tools/verify/apk_artifacts.py` (zip_index + aapt2 badging, cached) | dooz d81292cd: 106 entries, badging OK, cache HIT 25 ms (2026-09-11) |
| DEX index / counts (R-NEW-122/123/124/135/139) | `apk_artifacts.py` dex_index.json + repo `scripts/minidump_dex.py`, `scripts/f023_disasm.py`, `scripts/exp059_disasm.py` | dooz: 1 dex, 19,385 methods, 4,596 classes; every F-law diagnosis used the disassemblers |
| ARSC / resources (R-NEW-031/033/034/090) | `apk_artifacts.py` arsc_summary + runtime ARSC parser + aapt2-built fixtures | hello_color end-to-end golden (F-053 evidence) |
| Source stub/gap discovery (R-NEW-164/165/172) | `verify.py --cluster source` (stub radar) | generated POTENTIAL-GAP inventory at HEAD (see run below) |
| Screenshot / pixel evidence (R-NEW-077/270-278) | `verify.py --cluster shot` (PIL metrics + SHA) | re-verified hello_color golden SHA 11e0056320d8546d… from disk |
| Symbol discovery (R-NEW-016/027/051/127) | `verify.py --cluster symbols` + `docs/agent-index/SYMBOL_INDEX.json` | 5,824 symbols indexed at HEAD |
| Root lookup / investigation package (ALL) | `verify.py --root R-NEW-XXX` (registry fast path) | R-NEW-246 package returned in one call |
| Build graph (R-NEW tooling) | `docs/agent-index/BUILD_GRAPH.json` (Makefile objects) | generated from miniandroid/Makefile |
| Test graph / regression (ALL) | `docs/agent-index/TEST_GRAPH.json` + `scripts/run_test_battery.sh` | 91/91 ALL PASS at HEAD 0383f19f |
| Runtime trace (R-NEW-001/242/256-261) | runtime's own env-gated traces (`[COMPOSE-TRY]`, `[M3-19-THROWTRACE]`, WIDE-DIAG, TAG-TRACE) | M8/M9 session evidence chains |
| Root candidates awaiting a probe (rest) | registry fast-path package → manual deep-dive ONLY when tools cannot classify (brief §50) | `root_registry.json` |

## Rejected / research-only OSS tools (proof-of-use absent in this environment)

| Tool | Verdict | Reason (evidence-based) |
|---|---|---|
| Androguard | RESEARCH-ONLY | not installed in container; offline pip install unverified; our own aapt2+minidump_dex path already proven for the same questions |
| apktool / jadx / baksmali | RESEARCH-ONLY | absent from PATH (doctor.sh); ECJ+D8+aapt2 covers the fixture-authority path; disassembly covered by repo scripts |
| Android emulator / adb | REJECT (main path) | no device/emulator substrate in container; screenshots via software renderer proven |
| Ghidra / radare2 | REJECT for DEX scope | heavyweight binary RE tooling; DEX ground truth already served by repo disassemblers |
| bundletool | REJECT for now | no AAB corpus demand (R-NEW-082 NOT-APPLICABLE) |
