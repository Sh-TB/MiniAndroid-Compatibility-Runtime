# MiniAndroid Project State Audit

**Generated**: 2026-08-12  
**Purpose**: Complete repository inventory before GitHub migration  
**Status**: ✅ COMPLETE

---

## 1. Repository Status

### Current Directory
```
Path: /home/z/my-project
Type: Git repository (working tree clean)
```

### Git Status
```
Branch: main (HEAD)
Status: Working tree clean (nothing to commit)
Backup Branch: backup/exp023-pre-validation (exists)
```

### Existing Branches
| Branch | Type | Purpose |
|--------|------|---------|
| `main` | Active | Primary development branch |
| `backup/exp023-pre-validation` | Safety | Pre-validation checkpoint for EXP-023 |

### Commit History (Recent)
| Commit | Description |
|--------|-------------|
| `7ce4670` | HEAD - Latest commit on main |
| `30c326a` | backup/exp023-pre-validation checkpoint |
| `c6abf61` | Previous experiment state |
| ... | 22 total commits from Initial commit |

### Remote Configuration
```
Status: No remote configured
Action Required: Add GitHub remote before push
```

---

## 2. File Inventory

### SOURCE CODE (`src/`)
**Total Files**: 44 (42 .cpp/.h + 2 entry points)

#### Core Components
| Module | Files | Purpose |
|--------|-------|---------|
| **APK Parsing** | `apk_parser.cpp/h`, `manifest_reader.cpp/h` | APK extraction, AndroidManifest.xml |
| **DEX Engine** | `dex_parser.cpp/h`, `dex_interpreter.cpp/h`, `dex_interpreter_v2.cpp/h`, `class_resolver.cpp/h` | DEX format, bytecode interpretation |
| **Batch Processing** | `dex_interpreter_batch.cpp/h`, `dex_interpreter_exp018.cpp/h` | Multi-APK execution |
| **Runtime** | `execution_engine.cpp/h`, `application_runtime.cpp/h`, `object_model.h`, `runtime_integration_exp019.cpp/h` | Android runtime simulation |
| **Renderer** | `software_renderer.cpp/h` | View rendering pipeline |
| **Resources** | `resource_parser.cpp/h` | Android resource handling |
| **Diagnostics** | `trace_engine.cpp/h` | Execution tracing, debugging |
| **API Stubs** | `android_stubs.h` | Android API definitions |

#### Experiment Entry Points
| File | Experiment |
|------|-----------|
| `exp002_main.cpp` | EXP-002: Basic DEX parsing |
| `exp003a_main.cpp` | EXP-003a: Validation |
| `exp003a1_validate.cpp` | EXP-003a1: Extended validation |
| `exp003batch_main.cpp` | EXP-003 batch processing |
| `exp004_main.cpp` | EXP-004 |
| `exp005_main.cpp` | EXP-005 |
| `exp006_main.cpp` | EXP-006 |
| `exp007_012_megabatch_main.cpp` | EXP-007 to EXP-012 batch |
| `exp018_main.cpp` | EXP-018: Full execution |
| `exp019_main.cpp` | EXP-019: Runtime integration |
| `main.cpp` | Default entry point |

---

### BUILD ARTIFACTS (`build/`, `build_exp*/`)
**Total Size**: ~90MB (binary files)

| Directory | Size | Contents |
|-----------|------|----------|
| `build/` | 81MB | Main CMake build (object files, binaries) |
| `build_exp019/` | 2.6MB | EXP-019 specific build |
| `build_exp003a/` | 1.4MB | EXP-003a validation build |
| `build_exp002/` | 960KB | EXP-002 parser build |
| `build_exp006/` | 892KB | EXP-006 build |
| `build_exp004/` | 752KB | EXP-004 build |
| `build_exp003batch/` | 716KB | Batch processing build |
| `build_exp003a1/` | 516KB | EXP-003a1 build |
| `build_exp005/` | 292KB | EXP-005 build |

**Key Binaries**
- `build/miniandroid_megabatch` (22MB) - Main batch executor
- `build/exp018_test` (1.9MB) - EXP-018 test harness
- Various `.o` files (4-13MB each)

---

### SCRIPTS (`scripts/`)
**Total Files**: 15 Python scripts

| Script | Purpose | Lines |
|--------|---------|-------|
| `exp020_phase1_corpus.py` | Corpus collection | ~300 |
| `exp020_phase2_execution.py` | Execution testing | ~400 |
| `exp020_phase3_strict.py` | Strict validation | ~350 |
| `exp020_phase4_callback.py` | Callback analysis | ~280 |
| `exp020_phase5_resource.py` | Resource testing | ~320 |
| `exp020_phase6_failures.py` | Failure tracking | ~290 |
| `exp020_phase7_score.py` | Score calculation | ~250 |
| `exp021_phase1_interface.py` | Interface dispatch | ~380 |
| `exp021_phase2_return.py` | Return value handling | ~340 |
| `exp021_phase3_resource.py` | Resource integration | ~360 |
| `exp021_phase4_7_final.py` | Final phases 4-7 | ~900 |
| `exp022_corpus_audit.py` | Corpus transparency audit | ~900 |
| `exp023_master.py` | Master validation script | ~1200 |
| `exp023_phases5_17.py` | Phases 5-17 implementation | ~1500 |
| `generate_exp019_evidence.py` | Evidence generation | ~200 |

---

### DOCUMENTATION (`docs/`)
**Total Files**: 7 markdown documents

| Document | Purpose |
|----------|---------|
| `AI_AGENT_CONTEXT.md` | Authoritative AI agent context |
| `EXP_RULES.md` | Experiment rules and guidelines |
| `architecture-current.md` | Current architecture map |
| `architecture.md` | Original architecture design |
| `dependency-map.md` | Component dependencies |
| `execution-flow.md` | Execution pipeline flow |
| `runtime-status.md` | Runtime status report |

---

### DATABASE (`database/`)
**Total Files**: 14 JSON databases

| Database | Purpose | Records |
|----------|---------|---------|
| `runtime_failures.json` | Aggregated failure data | ~50 entries |
| `apk_storage_policy.json` | Storage management rules | Policy doc |
| `exp022_corpus_inventory.json` | EXP-022 corpus metadata | 36 APKs |
| `exp022_real_api_frequency.json` | Real API frequency data | API stats |
| `exp023_database_reconciliation.json` | DB reconciliation results | Analysis |
| `exp023_opcode_priority_real.json` | Real opcode priorities | Rankings |
| `exp023_opcode_frequency.json` | Opcode statistics | Frequency data |
| `exp023_evidence_audit.json` | Evidence verification | Audit trail |
| `exp023_storage_policy.json` | Storage policies | Rules |
| `exp023_real_corpus.json` | Real corpus metadata | APK list |
| `exp023_runtime_failures.json` | Real failures DB | Failure records |
| `exp023_api_frequency.json` | API usage stats | Frequency data |
| `exp023_api_priority_real.json` | API priority rankings | Top 100 |

---

### RUN OUTPUTS (`run/`)
**Total Files**: 95+ evidence/output files

#### Categories:
- **Execution Traces**: ~30 JSON trace files
- **Experiment Reports**: EXP-015 through EXP-023 reports (.md)
- **Database Outputs**: `database/` subfolder with 13 files
- **Validation Results**: Golden tests, matrices, scores
- **Screenshots**: `screenshot.png` (1.1MB)
- **Execution Proofs**: `apk_execution_proofs/` folder
- **EXP-023 Outputs**: Classification, compatibility, regression data

#### Key Output Files:
| File | Significance |
|------|-------------|
| `compatibility_score.json` | Overall compatibility metrics |
| `golden_end_to_end.json` | End-to-end test proof |
| `exp021_matrix.json` | Before/After improvement matrix |
| `exp022_report.md` | Transparency audit findings |
| `exp023_report.md` | Master validation report |

---

### TEST FILES (`tests/`)
| File | Purpose |
|------|---------|
| `simple_test.cpp` | Basic unit test |

---

### TOOLS (`tools/`)
| File | Purpose |
|------|---------|
| `apk_corpus_miner.py` | APK corpus mining utility |
| `gen_apk_fixed.py` | Fixed APK generation |
| `generate_hello_world_apk.py` | HelloWorld.apk generator |

---

### THIRD PARTY (`third_party/`)
| Library | License | Purpose |
|---------|---------|---------|
| `nlohmann/json.hpp` | MIT | JSON parsing library |

---

### TEST APKS (`test_apks/`)
| File | Size | Purpose |
|------|------|---------|
| `HelloWorld.apk` | 1.4KB | Golden test APK |
| `classes.dex` | 530B | Extracted DEX |

---

## 3. Experiment History Summary

| Experiment | Focus | Status | Key Output |
|------------|-------|--------|------------|
| EXP-002 | Basic DEX parsing | ✅ Complete | Parser foundation |
| EXP-003a/b | Validation | ✅ Complete | Validation framework |
| EXP-004 | Extension | ✅ Complete | Component added |
| EXP-005 | Feature | ✅ Complete | New capability |
| EXP-006 | Enhancement | ✅ Complete | Improvement |
| EXP-007-012 | Megabatch | ✅ Complete | Batch processing |
| EXP-013 | (Not in src) | 📋 Referenced | Intermediate |
| EXP-014 | DEX Execution | ✅ Complete | Real execution engine |
| EXP-015 | Bypass Analysis | ✅ Complete | bypass_analysis JSON |
| EXP-017 | API Frequency | ✅ Complete | API stats database |
| EXP-018 | Full Execution | ✅ Complete | Full results JSON |
| EXP-019 | Runtime Integration | ✅ Complete | Runtime integration |
| EXP-020 | Corpus & Compatibility | ✅ Complete | 35-APK corpus |
| EXP-021 | Blocker Removal | ✅ Complete | 38→55.2 score |
| EXP-022 | Transparency Audit | ✅ Complete | Honest assessment |
| EXP-023 | Master Validation | ✅ Complete | Real APK validation |

---

## 4. Risk Assessment

### High-Risk Items
1. **Build Artifacts (90MB)**: Large binary files that shouldn't be in repo
2. **No Remote Configured**: Need to add GitHub remote
3. **Screenshot Binary**: 1.1MB PNG in run/ directory
4. **APK Files**: Test APKs need proper handling

### Safe Items
- All source code (text, versionable)
- Documentation (markdown)
- Scripts (Python)
- Database JSON files
- Experiment reports

---

## 5. Recommended Actions

### Before Push
- [ ] Create proper `.gitignore` for build artifacts
- [ ] Consider Git LFS for large binaries if needed
- [ ] Add GitHub remote
- [ ] Create logical commit history

### Exclusions
- `build/` directories (rebuildable)
- `build_exp*/` directories (rebuildable)
- `temp_apk_downloads/` (empty, transient)
- `node_modules/` (already in .gitignore)
- `skills/` (external)

---

**Audit Completed By**: Super Z AI Agent  
**Verification Timestamp**: 2026-08-12T14:25:00Z  
**Next Step**: Proceed to Phase 2 - Git Safety Check
