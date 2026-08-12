# MiniAndroid Runtime

A lightweight Android APK execution runtime built in C++ for research, testing, and compatibility analysis.

## Overview

MiniAndroid is a from-scratch implementation of core Android runtime components designed to:

- Parse and execute DEX (Dalvik Executable) bytecode
- Simulate Android application lifecycle
- Render basic UI components
- Provide diagnostics and tracing capabilities
- Enable compatibility analysis across Android versions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MiniAndroid Runtime                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ APK     │  │ DEX      │  │ Runtime      │  │ Renderer │ │
│  │ Parser  │─▶│ Interpreter│─▶│ Engine       │─▶│ Software │ │
│  └─────────┘  └──────────┘  └──────────────┘  └──────────┘ │
│       │              │               │               │      │
│       ▼              ▼               ▼               ▼      │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐ │
│  │Manifest │  │ Class    │  │ Application  │  │ View Tree│ │
│  │ Reader  │  │ Resolver │  │ Runtime      │  │ Rendering│ │
│  └─────────┘  └──────────┘  └──────────────┘  └──────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌────────────┐  ┌─────────────────────┐  │
│  │ Resource     │  │ Diagnostics│  │    API Stubs        │  │
│  │ Parser       │  │ Trace Eng. │  │ (Android APIs)      │  │
│  └──────────────┘  └────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
miniandroid/
├── src/                 # C++ source code
│   ├── apk/            # APK parsing (manifest, resources)
│   ├── dex/            # DEX interpreter & parser
│   ├── runtime/        # Application runtime simulation
│   ├── renderer/       # Software rendering pipeline
│   ├── resources/      # Android resource handling
│   ├── diagnostics/    # Execution tracing & debugging
│   └── api/            # Android API stubs
├── scripts/             # Python automation scripts
├── docs/                # Documentation & architecture
├── database/            # JSON databases (APIs, opcodes, failures)
├── run/                 # Experiment outputs & evidence
├── tests/               # Unit tests
├── tools/               # Utility tools
├── test_apks/           # Test APK files
└── third_party/         # External dependencies
```

## Building

### Prerequisites

- C++17 compatible compiler (GCC 7+, Clang 5+)
- CMake 3.10+
- Make or Ninja build system

### Build Commands

```bash
# Main build (CMake)
cd miniandroid
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# Alternative: Using Makefile directly
cd miniandroid
make all
```

### Running

```bash
# Run with HelloWorld.apk
./build/miniandroid_megabatch test_apks/HelloWorld.apk

# Run specific experiment
./build_exp019/miniandroid_exp019 [args]
```

## Experiment History

This project has undergone extensive experimentation and validation:

| Experiment | Focus | Status |
|------------|-------|--------|
| EXP-002 | Basic DEX parsing | ✅ Complete |
| EXP-003a/b | Validation framework | ✅ Complete |
| EXP-004-006 | Feature extensions | ✅ Complete |
| EXP-007-012 | Batch processing | ✅ Complete |
| EXP-014 | Real DEX execution | ✅ Complete |
| EXP-015 | Bypass analysis | ✅ Complete |
| EXP-017 | API frequency analysis | ✅ Complete |
| EXP-018 | Full execution engine | ✅ Complete |
| EXP-019 | Runtime integration | ✅ Complete |
| EXP-020 | Corpus & compatibility | ✅ Complete |
| EXP-021 | Blocker removal | ✅ Complete |
| EXP-022 | Transparency audit | ✅ Complete |
| EXP-023 | Master validation | ✅ Complete |

See `docs/PROJECT_STATE_AUDIT.md` for complete inventory.

## Compatibility Score

Current real compatibility score: **55.2/100** (based on actual executed APKs)

- Initial baseline: 38/100
- After blocker removal (EXP-021): 55.2/100
- Based on: Real HelloWorld.apk execution + static analysis

## Key Features

1. **DEX Bytecode Interpreter**: Supports 70+ Dalvik opcodes
2. **APK Parser**: Extracts manifest, classes.dex, resources
3. **Runtime Simulation**: Activity lifecycle, intent handling
4. **Software Renderer**: Basic view tree rendering
5. **Diagnostics**: Full execution tracing and API dispatch logging
6. **Compatibility Analysis**: APK compatibility scoring system

## Golden Debug Protocol

All experiments follow strict rules:

- ❌ No fake PASS results
- ❌ No estimated APK names
- ✅ Separate static analysis from execution evidence
- ✅ Preserve all raw traces and proofs
- ✅ Report discrepancies honestly

See `docs/EXP_RULES.md` for complete protocol.

## License

Internal research project - See LICENSE file for details.

## Contributing

This is a research project. For experiment guidelines, see `docs/EXP_RULES.md`.
