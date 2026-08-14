# EXP-034 BASELINE — Real APK Compatibility Foundation

**Generated**: 2026-08-14T09:00:00Z  
**Previous Commit**: e903ca9 (EXP-033: AOSP/Dalvik Architecture Research)  
**Branch**: main  
**Status**: ✅ Clean working tree, ready for EXP-034

---

## 1. Current State Summary

### 1.1 DEX Parser Status
| Component | Status | Evidence |
|-----------|--------|----------|
| Header parsing | ✅ PASS | `dex_parser.h` lines 1-150 |
| String IDs | ✅ PASS | Validated with 15+ real APKs |
| Type IDs | ✅ PASS | Full type resolution |
| Proto IDs | ✅ PASS | Method prototypes |
| Method IDs | ✅ PASS | Method resolution |
| Class Definitions | ✅ PASS | ClassDef extraction |
| Code Items | ✅ PASS | Bytecode extraction |
| Instruction decoding | ✅ PASS | 28 opcodes decoded |

### 1.2 Dalvik Interpreter Status
| Component | Status | Opcodes |
|-----------|--------|---------|
| Constant loading | ✅ PASS | 6/12 (const/4, const/16, const, const/high16, const-string, const-class) |
| Move operations | ✅ PARTIAL | 4/13 (move, move-object, move-result, move-result-object) |
| Return operations | ✅ PASS | 3/4 (return, return-object, return-void) |
| Instance operations | ✅ PARTIAL | 3/4 (new-instance, instance-of, check-cast) |
| Array operations | ❌ MISSING | 0/19 (new-array, aget, aput all missing) |
| Field operations | ❌ MISSING | 0/28 (iget, iput, sget, sput all missing) |
| Invoke operations | ✅ PARTIAL | 3/12 (invoke-virtual, invoke-direct, invoke-static) |
| Method operations | ❌ MISSING | 0/6 (invoke-interface, invoke-polymorphic missing) |

**Total Coverage**: 28/210 opcodes (13.33%)

### 1.3 Object Model Status
| Component | Status | Implementation |
|-----------|--------|----------------|
| RuntimeObject base | ✅ PASS | `object_model.h` lines 50-120 |
| ClassMetadata | ✅ PARTIAL | Basic class info, no VTable |
| Object Heap | ✅ PASS | ID-based allocation |
| Type System | ✅ PASS | Primitive + reference types |
| Field Storage | ⚠️ PROTOTYPE | String-keyed map (not offset-based) |
| Static Fields | ⚠️ PROTOTYPE | Per-class string maps |
| Inheritance | ✅ PARTIAL | Single inheritance supported |

### 1.4 Known Blockers (from EXP-033 Research)

#### 🔴 CRITICAL Blockers (Block Real APK Execution)
1. **Field Operations Not Implemented**
   - Impact: ~14% of real bytecode uses iget/iput/sget/sput
   - Evidence: `opcode_coverage.json` shows 0/28 field opcodes
   - Root Cause: No field resolution system exists

2. **No VTable / Virtual Dispatch**
   - Impact: invoke-virtual cannot resolve methods at runtime
   - Evidence: `research/miniandroid_vs_dalvik.md` gap analysis
   - Root Cause: ClassInfo lacks method dispatch table

3. **String-Keyed Field Maps**
   - Impact: Cannot support DEX field_idx-based access
   - Evidence: Phase 4 object model improvement report
   - Root Cause: Prototype design never upgraded

#### 🟡 HIGH Priority Gaps
4. **Array Operations Missing** (0/19)
5. **Math Operations Missing** (0/32)
6. **No Proper ClassLoader Chain**

---

## 2. Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MiniAndroid Runtime v0.2                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐ │
│  │ APK Parser  │───▶│ DEX Parser  │───▶│  Class Resolver │ │
│  └─────────────┘    └─────────────┘    └────────┬────────┘ │
│                                                  │          │
│                                                  ▼          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Dalvik Engine (dalvik_engine.h)         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │ Registers│  │  Stack   │  │  Opcode Executor  │   │  │
│  │  │ (256 v)  │  │  Frames  │  │  (28 opcodes)     │   │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                             │                               │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Object Model (object_model.h)               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │  Heap    │  │  Class   │  │  Field Storage   │   │  │
│  │  │ Manager  │  │ Metadata │  │  (string-keyed)  │   │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                             │                               │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Bridge (android_stubs.h)            │  │
│  │  Activity / View / TextView / Log / ...             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Test Infrastructure Status

### 3.1 Available Test APKs
| Source | Count | Location | Validation Status |
|--------|-------|----------|-------------------|
| EXP-025 Downloaded | 15 | `download/apks/` | ✅ DEX extracted |
| EXP-027 Generated | 30 | `download/exp027_real_apks/` | ✅ Synthetic |
| EXP-031.5 Unit Tests | 5 | `test_apks/exp031_5/` | ✅ Targeted tests |
| HelloWorld Original | 1 | `test_apks/HelloWorld.apk` | ✅ Reference |

### 3.2 Evidence Collection Locations
| Evidence Type | Location | Count |
|---------------|----------|-------|
| Execution Traces | `run/exp032_phase3/` | 17 trace files |
| Opcode Analysis | `database/exp032_*.json` | 8 analysis files |
| Research Notes | `research/*.md` | 2 documents |
| Experiment Reports | `docs/EXP032_*.md` | 7 reports |

---

## 4. GitHub Preservation Status

### 4.1 Last Commit Details
```
Commit: e903ca9
Message: EXP-033: AOSP/Dalvik Architecture Research Phase (Pre-Implementation Study)
Author: Sh-TB
Date: 2026-08-14
Push Status: ✅ SUCCESS (pushed to origin/main)
```

### 4.2 Files in Last Commit
- `docs/EXP033_RESEARCH_REPORT.md`
- `research/dalvik_architecture_notes.md`
- `research/miniandroid_vs_dalvik.md`
- Updated `README.md`, `CHANGELOG.md`, `worklog.md`

---

## 5. EXP-034 Scope Definition

### 5.1 IN SCOPE (This Experiment)
✅ **Real APK Bytecode Pipeline Validation**  
✅ **Runtime Metadata Design** (ClassInfo, MethodInfo with proper structure)  
✅ **Field System Implementation** (offset-based iget/iput/sget/sput)  
✅ **VTable Dispatch Design** (invoke-virtual through runtime resolution)  
✅ **Real Execution Evidence** (traces from actual APK execution)

### 5.2 OUT OF SCOPE (Future Work)
❌ Adding more opcodes beyond field/vtable requirements  
❌ Array operation implementation  
❌ Math operation implementation  
❌ Performance optimization  
❌ Multi-dex support  
❌ Resource system expansion  

---

## 6. Success Criteria for EXP-034

### 6.1 MUST Have (for Completion)
- [ ] **Real APK validated**: At least 5 real APKs fully parsed to instruction level
- [ ] **ClassInfo designed**: Documented structure matching AOSP ClassObject
- [ ] **MethodInfo designed**: Documented structure with code_item reference
- [ ] **Field system implemented**: iget/iput/sget/sput with evidence
- [ ] **VTable designed**: Virtual dispatch mechanism documented
- [ ] **Evidence collected**: Real execution traces showing field access
- [ ] **GitHub commit**: All changes pushed with hash

### 6.2 NICE to Have (Stretch Goals)
- [ ] Real invoke-virtual through VTable traced
- [ ] Field offset calculation validated against AOSP
- [ ] Performance baseline measured

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Real APKs use unsupported opcodes | HIGH | MEDIUM | Focus on subset that works; document failures |
| Field resolution complexity underestimated | MEDIUM | HIGH | Follow AOSP patterns exactly; don't innovate |
| VTable construction has edge cases | MEDIUM | MEDIUM | Test with inheritance hierarchies |
| Git push fails | LOW | HIGH | Push frequently; keep local backups |

---

## 8. Next Steps (PHASE 1+)

See subsequent phase documents for detailed implementation plan.

**Immediate Action**: Begin PHASE 1 — Validate REAL APK bytecode pipeline with evidence collection.

---

*Baseline established: 2026-08-14T09:00:00Z*  
*Ready for EXP-034 implementation phases*
