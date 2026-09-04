# MiniAndroid Project - AI Agent Context Document

**Document Purpose:** Authoritative context for future AI coding agents working on this project.
**Generated:** 2026-08-12T14:11:55.186426Z
**Experiment:** EXP-023 Knowledge Transfer
**Status:** AUTHORITATIVE

---

## 1. Project Purpose

MiniAndroid is an **Android application runtime simulator** written in C++ that can:
- Parse Android APK files (DEX format)
- Extract and analyze AndroidManifest.xml
- Interpret DEX bytecode instructions
- Dispatch Android framework API calls
- Simulate Activity lifecycle
- Create View hierarchy from layouts
- Render UI to framebuffer/screenshot

**Goal:** Achieve sufficient Android app compatibility to run real open-source applications.

**Current Maturity:** Early prototype - basic HelloWorld works, complex apps fail.

---

## 2. Current Architecture

### Runtime Pipeline (Actual Flow)

```
APK File (ZIP format)
    ↓
APK Parser → Extract classes.dex, resources.arsc, AndroidManifest.xml
    ↓
Manifest Parser → Identify launcher Activity, permissions, components
    ↓
DEX Parser → Parse bytecode into instruction stream
    ↓
Class Resolver → Map class descriptors to metadata
    ↓
DEX Interpreter (v2) → Execute instructions one-by-one
    ↓
API Dispatcher → Route framework calls to implementations
    ↓
Object Model → Manage Java object instances on heap
    ↓
Resource Manager → Resolve R.id.*, R.string.* references
    ↓
LayoutInflater → Convert XML to View objects
    ↓
View Tree → Hierarchical widget structure
    ↓
Software Renderer → Draw to pixel buffer
    ↓
Screenshot → PNG output
```

### Key Source Files

| Component | Header | Implementation | Status |
|-----------|--------|----------------|--------|
| DEX Parser | `src/dex/dex_parser.h` | `src/dex/dex_parser.cpp` | WORKING |
| DEX Interpreter v2 | `src/dex/dex_interpreter_v2.h` | `src/dex/dex_interpreter_v2.cpp` | WORKING (basic) |
| Class Resolver | `src/dex/class_resolver.h` | `src/dex/class_resolver.cpp` | PARTIAL |
| Execution Engine | `src/runtime/execution_engine.h` | `src/runtime/execution_engine.cpp` | BASIC |
| Object Model | `src/runtime/object_model.h` | N/A | STUB |
| Resource Parser | `src/resources/resource_parser.h` | `src/resources/resource_parser.cpp` | PARTIAL |
| Software Renderer | `src/renderer/software_renderer.h` | `src/renderer/software_renderer.cpp` | BASIC |
| Manifest Reader | `src/apk/manifest_reader.h` | `src/apk/manifest_reader.cpp` | WORKING |
| APK Parser | `src/apk/apk_parser.h` | `src/apk/apk_parser.cpp` | WORKING |
| Trace Engine | `src/diagnostics/trace_engine.h` | `src/diagnostics/trace_engine.cpp` | WORKING |

### Opcodes Implemented (~28-30)

**Control Flow:** if-eqz, if-nez, if-eq, if-ne, goto, goto/16, goto/32
**Method Invoke:** invoke-virtual, invoke-direct, invoke-static, invoke-interface (0x72)
**Data Movement:** move, move-result, move-result-object, move-result-wide, move-exception
**Object Operations:** new-instance, instance-of, check-cast
**Return:** return, return-object, return-wide, return-void
**Constants:** const-string, const/4, const/16, const
**Array:** array-length, new-array, filled-new-array, aget, aput
**Others:** iget, iput, sget, sput (basic field operations)

---

## 3. Experiment History (EXP-003 through EXP-022)

### Status Legend
- ✅ **CONFIRMED REAL**: Actually executed, verified with trace evidence
- ⚠️ **PARTIALLY REAL**: Some parts real, some simulated
- 🔸 **SIMULATED**: Evidence generated but not from actual execution
- 📝 **STATIC ANALYSIS ONLY**: APK analyzed but not executed
- 📊 **PROJECTED**: Estimated/theoretical numbers
- ❌ **UNKNOWN**: Insufficient data to verify

---

### EXP-003 through EXP-012 (Megabatch Era)

**Objective:** Initial DEX parsing and interpretation implementation
**Implementation:** Core interpreter, opcode handlers, basic execution loop
**Evidence:** Basic execution traces, simple test cases
**Verified Facts:**
- DEX parsing works for simple APKs
- ~18 opcodes implemented initially
- HelloWorld.apk can be loaded and parsed
**Known Limitations:**
- No control flow (branches/jumps)
- Limited method dispatch
- No return value handling
**Status:** 📝 STATIC ANALYSIS ONLY / 🔸 SIMULATED for execution claims

---

### EXP-013 through EXP-014 (Intermediate Development)

**Objective:** Enhanced execution, view system basics
**Implementation:** setContentView support, TextView creation, basic rendering
**Evidence:** View tree traces, screenshot generation
**Verified Facts:**
- TextView.setText works
- Basic layout inflation possible
- Screenshot output generated
**Known Limitations:**
- Only trivial apps possible
- No event handling
**Status:** ⚠️ PARTIALLY REAL (HelloWorld trace exists)

---

### EXP-015 (Golden Corpus Validation)

**Objective:** Validate against 12+ corpus APKs
**Implementation:** Corpus analysis pipeline, execution matrix
**Evidence:** `run/golden/corpus_exp015.json`, `run/corpus_execution_matrix.json`
**Verified Facts:**
- Corpus of 12 APKs defined (1 real + 11 projected)
- Opcode coverage analyzed: 7/220 implemented (3.2%)
- Strict mode validation created
**Simulated Behavior:**
- Most "execution results" are projections
- Real execution only confirmed for HelloWorld
**Status:** 📝 STATIC ANALYSIS ONLY / 📊 PROJECTED for pass rates

---

### EXP-016 (Not found in records)

**Note:** No dedicated EXP-016 artifacts found. May have been skipped or merged.

---

### EXP-017 (API Intelligence Mining)

**Objective:** Discover most-used Android APIs from real applications
**Implementation:** APK analysis pipeline, frequency database
**Evidence:** `database/android_api_frequency_v2.json` (245 APIs), `database/api_priority.json`
**Verified Facts:**
- 100 APK entries analyzed (13 real-ish + 87 projected)
- Top APIs: onCreate (100%), setContentView (98%), TextView.setText (85%)
- Priority tiers: P0 (5 APIs), P1 (15 APIs), P2 (35 APIs), P3 (190 APIs)
**Known Limitations:**
- Most corpus entries are projections, not real APK analysis
- Frequency counts may be inflated
**Status:** 📝 STATIC ANALYSIS ONLY / 📊 PROJECTED statistics

---

### EXP-018 (Real Execution Core Batch)

**Objective:** Increase real APK execution capability based on EXP-017 data
**Implementation:** 
- Control flow engine (16 branch/jump opcodes)
- Return value system (move-result*)
- Static dispatch (invoke-static + 25 methods)
- Interface dispatch (invoke-interface + OnClickListener)
**Evidence:** Control flow traces, register traces, static/interface dispatch traces
**Verified Facts:**
- Total opcodes: ~28-30 (up from 7)
- Opcode coverage: ~29.5%
- Control flow: FULLY IMPLEMENTED
- Return values: IMPLEMENTED
- Static dispatch: 25+ methods
- Interface dispatch: Basic OnClickListener support
**Simulated Behavior:**
- "Projected APK pass rate: ~65-70%" - this is ESTIMATED, not measured
- "Overall grade: B+ (82/100)" - theoretical score
**Status:** ⚠️ PARTIALLY REAL (implementations exist, metrics projected)

---

### EXP-019 (Runtime Integration)

**Objective:** Connect all subsystems into unified runtime
**Implementation:** RuntimeIntegrationExp019 class with 7 phases
**Evidence:** Phase 1-7 JSON traces, compiled object file
**Verified Facts:**
- Resource Pipeline: getResources(), getString(), getIdentifier()
- View Tree: setContentView(), LayoutInflater, findViewById()
- Event System: Button, setOnClickListener()
- Lifecycle: All via DEX dispatch (not C++ direct calls)
- Intent System: Constructor, putExtra/getExtra, startActivity()
- Compilation: runtime_integration_exp019.o compiled successfully
**Known Limitations:**
- Integration tested via simulation, not real multi-APK batch
**Status:** ⚠️ PARTIALLY REAL (code compiles, integration simulated)

---

### EXP-020 (Real APK Validation Batch)

**Objective:** Validate EXP-019 against 35 real open-source APKs
**Implementation:** 7-phase validation pipeline
**Evidence:** 
- `run/exp020_corpus_inventory.json` (35 APKs claimed)
- `run/exp020_execution_matrix.json` (7 PASS, 4 PARTIAL, 24 FAIL)
- `run/compatibility_score.json` (38.0/100 Grade F)
- `database/runtime_failures.json` (83 failures classified)
**Verified Facts:**
- Corpus inventory lists 35 APKs across 7 categories
- Execution matrix has per-APK results
- Failure database classifies issues by type
- Score calculation formula documented
**CRITICAL FINDING (from EXP-022 audit):**
- **Only 1 APK (HelloWorld.apk) actually exists as a file**
- Other 34 are corpus PROJECTIONS, not real executable APKs
- The "7 PASS, 24 FAIL" matrix contains projected/simulated results
- Compatibility score 38/100 is THEORETICAL, not empirically measured
**Status:** 📝 STATIC ANALYSIS ONLY / 📊 PROJECTED (claims need verification)

---

### EXP-021 (Top Blockers Removal)

**Objective:** Fix top 3 blockers from EXP-020 to increase compatibility
**Implementation:**
- Phase 1: invoke-interface (0x72) with imtable
- Phase 2: move-result-object pipeline completion
- Phase 3: BYPASS-006 removal, resource DEX routing
**Evidence:**
- `run/exp021_interface_trace.json` (3/3 callback tests passing)
- `run/exp021_return_trace.json` (4/5 return value tests)
- `run/exp021_resource_trace.json` (3/4 resource tests)
- `run/exp021_report.md` (Before 38 → After 55.2)
**Verified Facts:**
- invoke-interface code EXISTS and passes unit tests
- move-result-object code EXISTS and passes tests
- Resource routing changed (BYPASS-006 removed)
**SIMULATED/PROJECTED BEHAVIOR:**
- "17/35 APKs now PASS" - this is ESTIMATED improvement
- "Score improved to 55.2" - CALCULATED ESTIMATE, not re-measured
- Assumes fixes unblock specific categories without real testing
**Status:** ⚠️ PARTIALLY REAL (code changes real, impact projected)

---

### EXP-022 (Corpus Audit)

**Objective:** Transparent audit of all APKs used in experiments
**Implementation:** 8-phase audit process
**Evidence:**
- `run/exp022_report.md` (comprehensive audit findings)
- `database/exp022_corpus_inventory.json`
- `run/exp022_claim_validation.json`
**VERIFIED FACTS (HONEST ASSESSMENT):**
- **Only 1 real APK executed:** HelloWorld.apk (com.example.helloworld)
- **34+ entries are STATIC ANALYSIS ONLY** (94.4%)
- **Popular apps NOT tested:** WhatsApp NO, Telegram NO, TikTok NO
- **EXP-021 score validity:** THEORETICAL ESTIMATE
- **Honesty rating:** HIGH - discrepancies documented
**Status:** ✅ CONFIRMED REAL (audit findings are accurate)

---

## 4. Explicit Application Compatibility Statement

### Applications CONFIRMED TESTED (Real Execution)

| Application | Package | Status | Evidence |
|-------------|---------|--------|----------|
| HelloWorld | com.example.helloworld | ✅ PASS | DEX trace, screenshot |

### Applications NOT Tested (No Execution Evidence)

| Application | Status |
|-------------|--------|
| WhatsApp | ❌ NOT TESTED |
| Telegram | ❌ NOT TESTED |
| TikTok | ❌ NOT TESTED |
| Instagram | ❌ NOT TESTED |
| Facebook | ❌ NOT TESTED |
| Netflix | ❌ NOT TESTED |
| Spotify | ❌ NOT TESTED |
| Any commercial app | ❌ NOT TESTED |

> **RULE:** Do NOT claim compatibility with any named application unless its actual APK was executed and execution proof exists in `run/apk_execution_proofs/`.

---

## 5. Current Blockers (Preventing MVP)

Based on EXP-020 failure analysis:

1. **ListView/RecyclerView** (affects 8+ APKs) - Complex widget not implemented
2. **SharedPreferences** (affects 10+ APKs) - Persistence not implemented
3. **colors.xml parsing** (affects 15+ APKs) - Incomplete resource handling
4. **invoke-static for Toast/Log** (affects 6+ APKs) - Partial static dispatch
5. **Intent/startActivity navigation** (affects 5+ APKs) - Multi-activity not working
6. **Complex layouts** (ConstraintLayout, CoordinatorLayout) - Not supported
7. **Fragment support** - Not implemented
8. **AsyncTask/Coroutines** - Threading not supported

---

## 6. What Works (Verified)

1. ✅ DEX file parsing (classes.dex extraction)
2. ✅ AndroidManifest.xml parsing (launcher activity detection)
3. ✅ Basic opcode execution (const-string, new-instance, invoke-virtual, return-void)
4. ✅ Control flow (if-eqz, if-nez, goto variants)
5. ✅ Activity.onCreate dispatch
6. ✅ setContentView(int) for simple layouts
7. ✅ TextView creation and setText
8. ✅ Button creation and setOnClickListener (invoke-interface)
9. ✅ findViewById with move-result-object
10. ✅ Resources.getString via DEX routing
11. ✅ Screenshot generation (software renderer)
12. ✅ Trace/logging infrastructure

---

## 7. Development Guidelines for Future Agents

### Do's
- Read source code before trusting documentation
- Run HelloWorld regression after any change
- Generate trace evidence for every claim
- Use EXP-022 audit findings as baseline truth
- Preserve ALL historical evidence files
- Be explicit about REAL vs PROJECTED vs SIMULATED

### Don'ts
- Don't fabricate execution results
- Don't claim app compatibility without real APK test
- Don't overwrite previous experiment outputs
- Don't commit secrets/tokens/APK binaries
- Don't implement features outside current experiment scope
- Don't use synthetic benchmarks as real validation

### File Naming Convention
- Experiment outputs: `expXXX_<description>.json/md`
- NEVER reuse filenames from previous experiments
- If conflict, create EXP-023-specific variant

---

## 8. Quick Reference

### Key Commands
```bash
# Build
cd miniandroid && bash build_exp019.sh

# Run HelloWorld test
cd miniandroid && ./build_exp019/miniandroid_exp019

# Generate evidence
python scripts/generate_exp019_evidence.py
```

### Important Paths
```
/home/z/my-project/miniandroid/
├── src/           # C++ source code
├── run/           # Experiment evidence (NEVER delete)
├── database/      # Analysis databases
├── golden/        # Expected outputs for comparison
├── docs/          # Documentation
├── scripts/       # Python automation scripts
├── test_apks/     # Test APK files (HelloWorld.apk only)
└── tools/         # Utility tools
```

---

*Document generated by EXP-023 Phase 1*
*This is the authoritative context - update when significant changes occur*
