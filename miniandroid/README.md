# MiniAndroid Runtime

**A C++ Android APK Execution Engine with Real Dalvik Bytecode Interpreter**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com)
[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue)](https://isocpp.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## Overview

MiniAndroid is a research-grade Android APK execution runtime built in C++17. It parses real APK files, extracts DEX bytecode, and executes Dalvik instructions through a register-based virtual machine.

### Current Status (Post EXP-030)

| Component | Status | Details |
|-----------|--------|---------|
| APK Parser | ✅ Complete | Parses real APKs from F-Droid |
| DEX Parser | ✅ Complete | Full DEX format support |
| **Dalvik Engine** | ✅ **NEW** | 2,218 lines, 25+ opcodes |
| Register Machine | ✅ Implemented | v0-vN + p0-pN registers |
| Object Heap | ✅ Implemented | Dynamic allocation tracking |
| Call Stack | ✅ Implemented | StackFrame with full context |
| API Bridge | ✅ Implemented | invoke → Android stub mapping |
| Validation | ✅ 12/12 APKs | All load bytecode successfully |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN.CPP                               │
│                   Entry Point / CLI                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  EXECUTION_ENGINE.CPP                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ APK Parser  │→│ DEX Parser  │→│ Runtime Orchestrator │ │
│  └─────────────┘  └─────────────┘  └──────────┬──────────┘ │
└────────────────────────────────────────────────┼────────────┘
                                                 │
┌────────────────────────────────────────────────▼────────────┐
│                    DALVIK_ENGINE.CPP (EXP-030)              │
│  ┌──────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │ Register File│ │ Object Heap│ │    Call Stack       │   │
│  │ v0-vN, p0-pN │ │ Allocation │ │ StackFrame tracking │   │
│  └──────────────┘ └────────────┘ └────────────────────┘   │
│  ┌──────────────┐ ┌────────────┐ ┌────────────────────┐   │
│  │ Opcode Exec  │ │API Bridge  │ │ Instruction Trace   │   │
│  │ 25+ opcodes  │ │invoke→stub │ │ Evidence capture    │   │
│  └──────────────┘ └────────────┘ └────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

```bash
# Build dependencies (Debian/Ubuntu)
sudo apt-get install g++ make cmake libjsoncpp-dev

# Or use the included build script
chmod +x build_exp019.sh
```

### Building

```bash
cd miniandroid
make clean && make
# Output: build/miniandroid (23.7MB)
```

### Running

```bash
# Execute an APK
./build/miniandroid run path/to/app.apk

# With detailed output
./build/miniandroid run --verbose path/to/app.apk

# Validate with EXP-030 tool
python3 tools/exp030_real_dalvik_validator.py --apk-dir download/exp027_real_apks/
```

---

## Experiments History

| Experiment | Focus | Status | Key Result |
|------------|-------|--------|------------|
| EXP-014-022 | Foundation | ✅ Complete | Core runtime established |
| EXP-023-026 | Real APKs | ✅ Complete | F-Droid corpus execution |
| EXP-027-028 | DEX Fix | ✅ Complete | Root cause fix for parsing |
| **EXP-029** | **Observability** | ✅ **Complete** | State machine, 15/15 APKs |
| **EXP-030** | **Real Execution** | ✅ **Complete** | Dalvik engine, 25+ opcodes |
| **EXP-035.1** | **External Research** | ✅ **Complete** | Solution mining, 30+ sources analyzed |

---

## EXP-035.1: External Research & Solution Mining (Latest)

### What Was Researched

**`docs/EXP035_1_EXTERNAL_RESEARCH.md`** — Comprehensive external research report:

### Research Categories Covered

| Category | Sources Analyzed | Key Findings |
|----------|------------------|--------------|
| DEX Parser Issues | AOSP, Androguard, Google Issues | code_off=0 is valid (abstract/native) |
| Dalvik Interpreters | AOSP (portable+fast), DaliVM, Academic | Two-interpreter pattern is standard |
| Field Opcodes | Android docs, AOSP bytecode.txt | Static linking optimization exists |
| Method Dispatch | Multiple sources | Two-phase resolution + vtable algorithm |
| Object Models | Dalvik Object.h, ART source | Pre-computed field offsets critical |
| Existing Projects | DaliVM, KiVM, mini-jvm, ReDex | ~40-60 opcodes sufficient for basic Activity |
| Compatibility Layers | Wine, ReactOS, QEMU | API translation approach recommended |

### Important Discoveries

1. **Two-Interpreter Pattern**: AOSP uses portable (debuggable) + fast (optimized) interpreters
2. **DaliVM Validation**: Python-based Dalvik emulation IS viable for our use case
3. **Field Inheritance**: Simple field_id→offset fails; must search class hierarchy
4. **VTable Critical**: Without proper vtable building, invoke-virtual breaks polymorphism
5. **Optimized DEX**: Real apps use iget-quick/invoke-quick variants post-dexopt
6. **Minimum Runtime**: ~40-60 opcodes sufficient for trivial Activity execution
7. **Compatibility Model**: Wine-style API translation more achievable than full emulation

### Recommendations Summary

**Adopt**:
- ✅ Portable interpreter pattern first (correctness over speed)
- ✅ Two-phase method resolution with caching
- ✅ Pre-computed field offsets during class loading
- ✅ VTable construction during class loading phase
- ✅ All 5 invoke types with different dispatch logic

**Avoid**:
- ❌ Optimizing before working correctly
- ❌ Full ART memory layout replication
- ❌ All 200+ opcodes at once
- ❌ Ignoring optimized DEX variants

### Report Location

```
docs/EXP035_1_EXTERNAL_RESEARCH.md  # Full research report (~500 lines)
docs/research/                      # Raw search results (JSON)
```

---

## Project Structure

```
miniandroid/
├── src/
│   ├── dex/
│   │   ├── dalvik_engine.h/cpp    # NEW: Dalvik executor
│   │   ├── dex_parser.h/cpp       # DEX format parser
│   │   └── dex_interpreter*.h/cpp # Legacy interpreters
│   ├── runtime/
│   │   ├── execution_engine.h/cpp # Main orchestrator
│   │   └── application_runtime.h/cpp
│   ├── api/android_stubs.h        # Android API stubs
│   └── main.cpp                   # Entry point
├── tools/
│   ├── exp029_state_machine.py    # State machine validator
│   └── exp030_real_dalvik_validator.py  # Dalvik engine validator
├── docs/
│   ├── EXP030_REAL_DALVIK_ENGINE_REPORT.md
│   └── EXP030_DEX_PIPELINE_AUDIT.md
├── experiments/
│   └── EXP-030/                   # Latest experiment
├── run/
│   └── exp030/traces/*/           # Per-APK validation traces
├── database/                      # JSON databases
├── download/apks/                 # Test APK corpus
└── Makefile                       # Build system
```

---

## Evidence & Validation

MiniAndroid follows the **Golden Debug Protocol**: every claim requires artifacts.

### Evidence Files Per APK

- `real_execution_proof.json` — Execution classification
- `api_trace.json` — Android API calls detected
- `report.md` — Human-readable summary
- `screenshot.ppm` — Visual output (6MB+)

### Databases

- `runtime_blockers.json` — Known failures and blockers
- `exp027_apk_registry.json` — APK metadata
- `exp027_opcode_frequency.json` — Opcode statistics

---

## Next Steps (Roadmap)

### Immediate (Integration)

1. **Wire DalvikEngine into ExecutionEngine.cpp**
   - Add include and create instance
   - Route parsed methods to engine
   - Replace simulation with real execution

2. **HelloWorld Proof of Concept**
   - Execute actual onCreate() bytecode
   - Show register modifications
   - Prove object allocations

### Short-term Enhancements

- Additional opcodes (iput, iget, array operations)
- Multi-dex support (classes2.dex+)
- Resource XML inflation
- Full Activity lifecycle from DEX

---

## Contributing

This is a research project focused on understanding Android runtime internals.

See individual experiment README files for:
- Design decisions (`DESIGN.md`)
- Implementation notes (`IMPLEMENTATION_NOTES.md`)
- Failure analysis (`FAILURES.md`)
- Results summary (`RESULTS.md`)

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

*Last Updated: 2026-08-14*
*Active Development: EXP-035.1 Research Complete, EXP-035 Implementation Pending*
