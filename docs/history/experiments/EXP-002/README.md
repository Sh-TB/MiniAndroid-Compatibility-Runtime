# EXP-002: Basic DEX Parsing Foundation

## Goal
Establish foundational DEX (Dalvik Executable) file parsing capabilities for the MiniAndroid runtime.

## Implemented
- DEX file format parser (`src/dex/dex_parser.cpp`)
- Header extraction (string_ids, type_ids, proto_ids, field_ids, method_ids, class_defs)
- Basic bytecode disassembly
- APK container parsing (`src/apk/apk_parser.cpp`)
- AndroidManifest.xml reader

## Source Files
- `src/exp002_main.cpp` - Experiment entry point
- `src/dex/dex_parser.cpp/h` - Core DEX parser
- `src/apk/apk_parser.cpp/h` - APK ZIP extraction
- `src/apk/manifest_reader.cpp/h` - XML manifest parsing

## Evidence
- Build artifact: `build_exp002/miniandroid_exp002`
- Validation traces in `run/` directory

## False Assumptions Corrected
1. Initially assumed all DEX files would have standard header offsets - added validation
2. Assumed APKs would always contain classes.dex - added multi-dex awareness

## Remaining Blockers
- Full method body parsing needed
- Instruction decoding incomplete
- No execution capability yet

## Status
✅ **COMPLETE** - Foundation for all subsequent experiments
