# MiniAndroid Runtime v0.1 — Architecture Document

## Project Overview

**Experiment:** EXP-001 through EXP-013 (Real Execution Validation)  
**Goal:** Execute a minimal Android APK without full emulator  
**Philosophy:** Evidence-driven development, honest status reporting  
**Current Phase:** Validation complete - gaps identified and documented

---

## System Architecture (Post-EXP-013 Validation)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MiniAndroid Runtime v0.1                              │
│                  ⚠️ VALIDATION COMPLETE - SEE GAPS                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────────────┐   │
│  │   APK    │───▶│Manifest  │───▶│       Class Resolver             │   │
│  │  Parser  │    │ Reader   │    │   (REAL - finds onCreate)        │   │
│  └──────────┘    └──────────┘    └────────────┬─────────────────────┘   │
│       │               │                     │                          │
│       ▼               ▼                     ▼                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────────────┐   │
│  │   DEX    │───▶│DEX Interp.│───▶│     ⚠️ HALTS after 1 instruction │   │
│  │  Parser  │    │(const-   │    │     (only const-string works)     │   │
│  │          │    │ string)  │    └────────────┬─────────────────────┘   │
│  └──────────┘    └──────────┘                 │                          │
│       │               │                       │                          │
│       ▼               ▼                       ▼ [FALLBACK]              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              ApplicationRuntime (COORDINATOR)                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │  SIMULATION LAYER (activates when interpreter halts)         │ │  │
│  │  │  • Direct C++ object creation (bypasses new-instance)        │ │  │
│  │  │  • Direct API calls (bypasses invoke-virtual)                │ │  │
│  │  │  • State machine transitions (simulates lifecycle)           │ │  │
│  │  │  • Hardcoded layout geometry                                 │ │  │
│  │  │  • Direct renderer invocation                               │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │                                  │
│                                     ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    OUTPUT GENERATION                              │  │
│  │  Object Heap → View Tree → Software Renderer → Framebuffer → PNG │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Diagnostics Engine                             │  │
│  │  (Trace, Bypass Detection, API Tracking, Evidence Generation)    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure (Clean Architecture)

```
miniandroid/
├── src/                        # Production source code
│   ├── runtime/                 # Core runtime components
│   │   ├── application_runtime.h/cpp   # Central coordinator
│   │   ├── execution_engine.h/cpp      # Original engine (legacy)
│   │   └── object_model.h             # Android object model
│   │
│   ├── dex/                      # DEX parsing and interpretation
│   │   ├── dex_parser.h/cpp            # DEX format parser
│   │   ├── dex_interpreter.h/cpp       # Bytecode interpreter (EXP-003-A)
│   │   ├── dex_interpreter_batch.h/cpp # Batch interpreter (MEGA BATCH)
│   │   └── class_resolver.h/cpp        # Method resolution
│   │
│   ├── apk/                      # APK handling
│   │   ├── apk_parser.h/cpp            # ZIP extraction
│   │   └── manifest_reader.h/cpp       # XML/binary manifest parsing
│   │
│   ├── resources/                # Resource system
│   │   └── resource_parser.h/cpp       # ARSC + XML resource loading
│   │
│   ├── renderer/                 # Graphics output
│   │   └── software_renderer.h/cpp     # Software rendering pipeline
│   │
│   ├── diagnostics/              # Testing & tracing
│   │   └── trace_engine.h/cpp          # Unified diagnostic logging
│   │
│   ├── api/                      # Android framework stubs
│   │   └── android_stubs.h             # API declarations
│   │
│   └── experiments/              # Experiment entry points (preserved)
│       ├── exp002_main.cpp
│       ├── exp003a_main.cpp
│       ├── exp004_main.cpp
│       ├── exp005_main.cpp
│       ├── exp006_main.cpp
│       └── exp007_012_megabatch_main.cpp
│
├── tests/                       # Test suite
│   └── simple_test.cpp
│
├── tools/                       # Utility scripts
│   ├── gen_apk_fixed.py
│   └── generate_hello_world_apk.py
│
├── golden/                      # Expected outputs for regression
│   ├── expected_*.json (8 files)
│   └── corpus.json
│
├── run/                         # Generated evidence output
│   ├── *.json                   # All trace/evidence files
│   ├── screenshot.png           # Rendered output
│   ├── database/                # API/opcode databases
│   └── golden/                  # Corpus definitions
│
├── docs/                        # Documentation
│   ├── architecture.md          # This file
│   ├── runtime-status.md        # Live status (UPDATED EXP-013)
│   ├── execution-flow.md        # Pipeline flow documentation
│   ├── dependency-map.md        # Component dependencies
│   └── EXP_RULES.md             # Development rules
│
├── test_apks/                   # Test APK files
│   ├── HelloWorld.apk           # Primary test application
│   └── classes.dex              # Extracted DEX for analysis
│
├── third_party/                 # Dependencies
│   └── nlohmann_json/           # JSON library
│
├── build/                       # Build output (gitignored)
├── CMakeLists.txt               # Build configuration
└── Makefile                     # Alternative build
```

---

## Component Breakdown (With Validation Status)

### 1. APK Parser (`src/apk/`) ✅ REAL

**Responsibility:** Parse Android Package (APK) files

| Aspect | Status | Notes |
|--------|--------|-------|
| ZIP Parsing | ✅ IMPLEMENTED | Real extraction |
| Entry Listing | ✅ WORKING | Full entry map |
| Integrity Check | ✅ BASIC | ZIP signature verified |

**Validation Result:** Fully real implementation. No simulation detected.

---

### 2. DEX Parser (`src/dex/`) ✅ REAL

**Responsibility:** Parse Dalvik Executable format

| Aspect | Status | Notes |
|--------|--------|-------|
| Header Parsing | ✅ COMPLETE | All fields extracted |
| String Pool | ✅ WORKING | Full extraction |
| Type List | ✅ WORKING | Class references |
| Method List | ✅ WORKING | Signatures + offsets |
| Bytecode Access | ✅ WORKING | Raw bytes available |

**Validation Result:** Fully real implementation. Provides accurate data to downstream components.

---

### 3. DEX Interpreter (`src/dex/dex_interpreter.cpp`) ⚠️ 0.45% COMPLETE

**Responsibility:** Execute DEX bytecode instructions

| Opcode | Hex | Status | Priority |
|--------|-----|--------|----------|
| const-string | 0x1A | ✅ **IMPLEMENTED** | DONE |
| new-instance | 0x22 | ❌ UNIMPLEMENTED | **P0 BLOCKER** |
| invoke-direct | 0x70 | ❌ UNIMPLEMENTED | **P0 HIGH** |
| invoke-virtual | 0x6E | ❌ UNIMPLEMENTED | **P1 HIGH** |
| return-void | 0x0E | ❌ UNIMPLEMENTED | **P1 HIGH** |
| All others | ~215 | ❌ UNIMPLEMENTED | Various |

**Execution Flow (Validated):**
```
PC=0: const-string v0, "Hello MiniAndroid"  → ✅ EXECUTED (register v0 set)
PC=3: new-instance v1, TextView             → ❌ HALTED (unimplemented)
     ... (remaining instructions NOT REACHED)
```

**Validation Result:** Interpreter infrastructure is correct but only 1 opcode works. This is the PRIMARY bottleneck.

---

### 4. ApplicationRuntime (`src/runtime/application_runtime.cpp`) ⚠️ COORDINATOR + FALLBACK

**Responsibility:** Orchestrate the complete pipeline

**Dual Mode Operation:**

```cpp
// Pseudo-code of actual behavior:
bool ApplicationRuntime::execute_on_create() {
    // 1. Try real DEX execution
    auto trace = interpreter_->execute(entry_point, strings, config);
    
    if (trace.halted || trace.executed_instructions == 0) {
        // 2. FALLBACK: Simulate via direct C++ calls
        // This is where all bypasses occur:
        auto text_view = heap_->create_text_view(activity_id);  // BYPASS-001
        text_view->set_text(resource_parser->get_string(...));   // BYPASS-002
        load_content_view();                                     // BYPASS-003 variant
        // ... etc
    }
}
```

**Validation Result:** The coordinator correctly invokes the interpreter but then falls back to C++ simulation when it halts. This fallback is well-documented but means most "execution" is simulated.

---

### 5. Object Model (`src/runtime/object_model.h`) ✅ EXISTS

**Responsibility:** Represent Android objects in C++

| Class | Purpose | Creation Path |
|-------|---------|---------------|
| `RuntimeObject` | Base class | N/A |
| `ActivityRuntimeObject` | Activity instance | C++ fallback (should be DEX new-instance) |
| `ViewRuntimeObject` | View base | C++ fallback |
| `TextViewRuntimeObject` | Text display | C++ fallback |

**Validation Result:** Object model is well-designed but objects are created directly in C++, not through DEX object allocation.

---

### 6. Resource System (`src/resources/`) 🔶 PARTIAL

**Responsibility:** Load Android resources

| Feature | Status | Notes |
|---------|--------|-------|
| XML Resources | ✅ WORKING | strings.xml, layouts.xml |
| ARSC Parsing | 🔶 BASIC | Header + string table |
| Resource ID Resolution | ✅ WORKING | @string/*, @layout/* |
| Config Qualifiers | ❌ NOT | No locale/density support |

**Validation Result:** Works for simple cases but called from C++, not via `getResources()` DEX dispatch.

---

### 7. Renderer (`src/renderer/`) ✅ DIRECT CALL

**Responsibility:** Generate pixel output

| Feature | Status | Notes |
|---------|--------|-------|
| Clear/Fill | ✅ WORKING | Background color |
| Rectangle | ✅ WORKING | View backgrounds |
| Text | ✅ BASIC | Bitmap font rendering |
| PNG Output | ✅ WORKING | screenshot.png generated |

**Validation Result:** Produces real output but invoked directly, not through `View.draw(Canvas)` dispatch chain.

---

### 8. Diagnostics (`src/diagnostics/`) ✅ COMPREHENSIVE

**Responsibility:** Trace, log, and validate everything

**EXP-013 Additions:**
- Execution path audit (14 stages classified as REAL/SIMULATED)
- Bypass detection (6 bypass points identified)
- API dispatch source tracking (all 12 calls tagged)
- Instruction-level trace with real/simulated markers

---

## Data Flow Reality (EXP-013 Validated)

### What Actually Happens When You Run an APK:

```
1. APK Parser extracts classes.dex                    ← REAL
2. ManifestReader identifies .MainActivity            ← REAL
3. DexParser loads string pool, methods                ← REAL
4. ClassResolver finds onCreate(Bundle) method         ← REAL
5. DexInterpreter.execute(onCreate) entered           ← REAL
6. const-string executes, "Hello MiniAndroid" → v0     ← REAL (ONLY THIS)
7. Interpreter halts on new-instance                   ← REAL HALT
8. ApplicationRuntime detects halt, activates fallback ← DOCUMENTED
9. TextView created via heap->create_text_view()       ← BYPASS #1
10. Text set via direct set_text() call                ← BYPASS #2
11. Layout loaded via C++ resource parser              ← BYPASS #3
12. State machine records lifecycle transitions        ← BYPASS #4
13. Hardcoded bounds assigned to Views                ← BYPASS #5
14. Renderer draws directly from object heap           ← BYPASS #6
15. Screenshot saved as PNG                            ← REAL OUTPUT
```

**Real Execution: Steps 1-7 (47%)**  
**Simulated Fallback: Steps 8-14 (47%)**  
**Real Output: Step 15 (6%)**

---

## Interface Boundaries

### Where Real Meets Simulated:

```
┌─────────────────────────────────────────────────────────────┐
│                    REAL ZONE                                 │
│  APK → Manifest → DEX → ClassResolver → Interpreter Entry  │
└────────────────────────────────┬────────────────────────────┘
                                 │
                       Interpreter Halts
                        (new-instance unimplemented)
                                 │
┌────────────────────────────────▼────────────────────────────┐
│                  SIMULATION ZONE                             │
│  C++ Object Creation → API Calls → Layout → Rendering       │
└────────────────────────────────┬────────────────────────────┘
                                 │
                        Real Output Generated
                        (screenshot.png)
```

---

## Build System

### CMake Configuration (Current)

```cmake
cmake_minimum_required(VERSION 3.16)
project(MiniAndroid VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Core library sources
set(MINIANDROID_SOURCES
    src/apk/apk_parser.cpp
    src/apk/manifest_reader.cpp
    src/dex/dex_parser.cpp
    src/dex/class_resolver.cpp
    src/dex/dex_interpreter.cpp
    src/dex/dex_interpreter_batch.cpp
    src/runtime/application_runtime.cpp
    src/runtime/execution_engine.cpp
    src/resources/resource_parser.cpp
    src/renderer/software_renderer.cpp
    src/diagnostics/trace_engine.cpp
)

add_library(miniandroid_core STATIC ${MINIANDROID_SOURCES})

# MEGA BATCH executable
add_executable(miniandroid_megabatch
    src/exp007_012_megabatch_main.cpp
)
target_link_libraries(miniandroid_megabatch PRIVATE miniandroid_core)

# Dependencies
find_package(ZLIB REQUIRED)
target_link_libraries(miniandroid_core PRIVATE ZLIB::ZLIB)
```

---

## Technology Stack

| Component | Technology | Version | Status |
|-----------|------------|---------|--------|
| Language | C++17 | - | ✅ Active |
| Build System | CMake | 3.16+ | ✅ Working |
| Compiler | Clang/GCC | 11+ | ✅ Tested |
| Compression | zlib | 1.2+ | ✅ Integrated |
| JSON | nlohmann/json | 3.x | ✅ Integrated |
| Image Output | Custom PNG writer | - | ✅ Working |
| Testing | Manual + JSON evidence | - | ✅ EXP-013 validated |

---

## Milestone Status (Updated)

### M0 — Project Builds ✅
**Evidence:** `build/miniandroid_megabatch` binary exists

### M1 — APK Parser Works ✅
**Evidence:** `application_runtime.json` shows parsed APK info

### M2 — DEX Metadata Loaded ✅
**Evidence:** DEX report shows 8 strings, 4 methods

### M3 — HelloWorld "Executes" ⚠️ PARTIAL
**Evidence:** `screenshot.png` shows "Hello MiniAndroid"
**Caveat:** Output is correct but achieved via C++ fallback, not full DEX execution

### M4 — API Tracing Works ✅
**Evidence:** `api_dispatch_full_trace.json` shows 12 traced calls

### M5 — **NEW: Real Execution Validated** ⚠️ INCOMPLETE
**Evidence:** `execution_path_audit.json`, `oncreate_execution_proof.json`
**Status:** Only 20% of onCreate method actually executes via DEX

---

## Golden Debug Protocol Compliance

### Rules (from docs/EXP_RULES.md):

1. **Never hide failures** ✅
   - All 6 bypasses documented in `bypass_detection.json`
   
2. **No silent fake returns** ✅
   - Every simulated path explicitly tagged as SIMULATED
   
3. **Evidence required** ✅
   - 7 new evidence files generated for EXP-013
   
4. **Trace everything** ✅
   - Instruction-level trace with register state snapshots

### EXP-013 Specific Compliance:

| Requirement | Status | Evidence File |
|-------------|--------|---------------|
| No fake success | ✅ PASS | `runtime-status.md` honestly reports PARTIAL |
| Every PASS requires evidence | ✅ PASS | All claims backed by JSON files |
| Simulated paths marked | ✅ PASS | `execution_path_audit.json` tags each stage |
| Missing execution documented | ✅ PASS | `real_dex_execution_trace.json` shows what didn't run |
| Previous artifacts preserved | ✅ PASS | All EXP-007→012 files intact |

---

## Future Roadmap (Adjusted for Reality)

### Phase 1 — Complete Basic Opcodes (Immediate)

**Goal:** Execute a real onCreate() method end-to-end

**Tasks:**
1. Implement return-void (0x0E) - 2 hours
2. Implement return-object (0x11) - 2 hours
3. Implement new-instance (0x22) - 1 day
4. Build object heap bridge - 1 day
5. Implement invoke-direct (0x70) - 2 days
6. Implement invoke-virtual (0x6E) - 3 days
7. Build API stub dispatch bridge - 2 days

**Estimated Time:** 2 weeks  
**Expected Result:** HelloWorld.apk executes entirely through DEX interpreter

### Phase 2 — Control Flow & Fields

**Goal:** Support if/else, loops, field access

**Tasks:**
1. Implement if-eq/if-ne family - 2 days
2. Implement move/move-object family - 1 day
3. Implement iget/iput-object - 2 days
4. Implement sget/sput-object - 1 day

**Estimated Time:** 1 week

### Phase 3 — Remove Simulation

**Goal:** Eliminate all C++ fallback paths

**Tasks:**
1. Disable fallback when DEX execution succeeds
2. Make simulation opt-in for debugging
3. Add strict mode that fails on any fallback

### Phase 4 — Corpus Expansion

**Goal:** Run 9+ diverse APKs successfully

**Tasks:**
1. Download/build corpus APKs
2. Fix app-specific issues
3. Achieve >80% corpus pass rate

---

## Key Architectural Decisions (Documented)

### Decision 1: Fallback Simulation
**Context:** Interpreter only implements 1 opcode  
**Decision:** Allow C++ fallback after interpreter halt  
**Rationale:** Enables pipeline testing while opcodes are developed  
**Risk:** May hide opcode implementation need  
**Mitigation:** EXP-013 validation exposes all fallback points  

### Decision 2: Separate Interpreter Versions
**Context:** Opcodes namespace conflicts between interpreters  
**Decision:** Keep `dex_interpreter.h` (single) and `dex_interpreter_batch.h` (batch) separate  
**Rationale:** Avoid breaking existing experiments  
**Future:** Unify when batch interpreter reaches feature parity  

### Decision 3: JSON Evidence Format
**Context:** Need machine-readable + human-readable output  
**Decision:** Use nlohmann/json for all evidence files  
**Rationale:** Easy parsing, good tooling support, git-diffable  

---

*Document Version: 3.0-EXP013*  
*Last Updated: EXP-013 Real Execution Validation Complete*
*Architecture Status: VALIDATED with documented gaps*
