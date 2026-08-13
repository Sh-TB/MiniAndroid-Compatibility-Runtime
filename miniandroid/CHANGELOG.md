# Changelog

All notable changes to the MiniAndroid Runtime project.

## [EXP-030] - 2026-08-13 — Real Dalvik Execution Engine

### ✅ Added

#### Core Dalvik Engine (`src/dex/dalvik_engine.*`)
- **DalvikValue** type system with 15 value types (INT32, FLOAT32, STRING_REF, OBJECT_REF, etc.)
- **DexRegisterFile** virtual machine register file (v-registers + p-registers)
- **DalvikHeap** dynamic object allocation with unique IDs and class tracking
- **CallStack/StackFrame** method invocation context tracking
- **InstructionTrace** per-opcode evidence capture system
- **ApiCallTrace** Android API call logging with status tracking
- **DalvikExecutionResult** complete execution evidence container
- **Total: 2,218 lines of production C++ code**

#### Opcode Implementation (25+ Opcodes)
- **Constants**: const/4, const/16, const, const-string, const-class
- **Moves**: move, move-object, move-result, move-result-object
- **Objects**: new-instance, check-cast, instance-of
- **Invokes**: invoke-virtual, invoke-direct, invoke-static, invoke-interface
- **Returns**: return-void, return, return-object
- **Control Flow**: goto, if-eqz, if-nez

#### API Bridge System
- `bridge_to_api()` function for DEX invoke → Android API mapping
- Recognized patterns: TextView.setText, Activity.onCreate, Log.*
- Status tracking: IMPLEMENTED, STUBBED, MISSING, ERROR

#### Validation Tool
- `tools/exp030_real_dalvik_validator.py` (720 lines)
- 12 APK validation campaign
- Execution depth classification
- EXP-029 vs EXP-030 comparison generation

### 📝 Documentation
- `docs/EXP030_REAL_DALVIK_ENGINE_REPORT.md` — Comprehensive engine report
- `docs/EXP030_DEX_PIPELINE_AUDIT.md` — Architecture audit findings
- `experiments/EXP-030/README.md` — Experiment overview
- `README.md` — Project-level documentation (NEW)

### 📊 Output Artifacts
- `run/exp030/baseline_repository.json` — Pre-experiment state snapshot
- `run/exp030/execution_matrix.json` — 12 APK execution results
- `run/exp030/opcode_trace.json` — Global opcode statistics
- `run/exp030/progress_comparison.json` — EXP-029 vs EXP-030 comparison
- `run/exp030/traces/*/` — 12 per-APK trace directories

### 🔧 Modified Files
- `Makefile` — Added dalvik_engine.cpp to build
- `src/runtime/execution_engine.h/cpp` — Integration points ready
- Various database files updated with new metadata

---

## [EXP-029] - 2026-08-13 — Runtime State Machine & Observability

### ✅ Added
- **RuntimeStateMachine** — 11-state FSM with millisecond transitions
- **ValidationCampaign** — Multi-APK validation orchestrator
- **FailureIntelligenceSystem** — Classification and analysis
- **TimelineReportGenerator** — Prosper-style timeline output
- **RegressionVerifier** — Baseline comparison tool

### 📊 Results
- **15/15 APKs validated** (100% success rate)
- All reached `FIRST_FRAME_RENDERED` state
- Regression: PASS (HelloWorld baseline maintained)
- 0 blockers found in runtime_blockers.json

### 📁 New Files
- `tools/exp029_state_machine.py` (~1250 lines)
- `run/exp029/` — Complete trace directory for 15 APKs
- `docs/EXP029_REPORT.md` — Final report

---

## [EXP-028] - 2026-08-12 — DEX Parser Root Cause Fix

### 🔧 Fixed
- **DEX parse error**: "Invalid header size: 0" on all production APKs
- Root cause identified and corrected in dex_parser.cpp
- Result: Now loads 30+ real APKs successfully

### 📁 New Files
- `tools/exp028_forensic_analysis.py`
- `tools/exp028_dex_validator.py`
- `tools/exp028_finalizer.py`

---

## [EXP-027] - 2026-08-12 — Real World APK Corpus

### ✅ Added
- F-Droid real APK acquisition pipeline
- 30 production APKs downloaded and cataloged
- Real DEX bytecode analysis
- Failure intelligence database

### 📊 Results
- 30 APKs acquired from F-Droid
- Real opcode frequency analysis
- API usage statistics generated

---

## [EXP-026] - 2026-08-11 — True Execution Activation

### ✅ Achieved
- First real APK executions (not simulated)
- 10 test APKs through full pipeline
- Evidence-first compatibility scoring
- Screenshot capture working

---

## Earlier Experiments (EXP-001 to EXP-025)

Foundation work including:
- Initial APK parsing
- DEX format understanding
- Basic interpreter stubs
- Test framework establishment
- Corpus acquisition strategies

---

## Version History

| Version | Date | Experiment | Key Achievement |
|---------|------|------------|-----------------|
| 4.0.0 | 2026-08-13 | EXP-030 | Real Dalvik Engine (2,218 lines) |
| 3.0.0 | 2026-08-13 | EXP-029 | State Machine Observability |
| 2.5.0 | 2026-08-12 | EXP-028 | DEX Parser Fix |
| 2.0.0 | 2026-08-12 | EXP-027 | Real APK Corpus |
| 1.5.0 | 2026-08-11 | EXP-026 | True Execution |
| 1.0.0 | 2026-08-10 | EXP-014 | Foundation |

---

*Changelog maintained for GitHub preservation*
