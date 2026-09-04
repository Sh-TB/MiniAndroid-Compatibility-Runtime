# MiniAndroid Runtime v0.1 - Runtime Status

**Generated:** 2026-08-12  
**Experiment:** EXP-013 REAL EXECUTION VALIDATION + GOLDEN CORPUS  
**Status: ⚠️ **VALIDATION COMPLETE - GAPS IDENTIFIED**

---

## EXP-013 Executive Summary

**Verdict: PARTIAL_PASS** - Infrastructure works, DEX execution is incomplete

### Critical Findings (Golden Debug Protocol Compliant)

| Question | Answer | Evidence |
|----------|--------|----------|
| **Is DEX bytecode really executed?** | PARTIALLY (20%) | Only const-string (1/5 opcodes in onCreate) |
| **Is Activity lifecycle real?** | NO - SIMULATED | State machine transitions, not DEX method calls |
| **Are Android APIs dispatched through runtime?** | NO - BYPASSED | All 12 API calls via direct C++ invocation |
| **Which parts are simulated?** | View creation, setText, lifecycle, layout, rendering | 6 bypass points documented |
| **Which APIs have highest priority?** | new-instance, invoke-direct, invoke-virtual, return-void | P0 blockers identified |

---

## Subsystem Status Summary (Post-Validation)

| Subsystem | Status | Real/Simulated | Implementation Notes |
|-----------|--------|----------------|---------------------|
| **APK Parser** | ✅ IMPLEMENTED | **REAL** | Full ZIP parsing, entry extraction |
| **Manifest Reader** | ✅ IMPLEMENTED | **REAL** | Binary AXML + Plain XML support |
| **DEX Parser** | ✅ IMPLEMENTED | **REAL** | Full header, class/method/string parsing |
| **Class Resolver** | ✅ IMPLEMENTED | **REAL** | Entry point detection, method resolution |
| **DEX Interpreter** | ⚠️ PARTIAL | **20% REAL** | ONLY const-string implemented. 219/220 opcodes unimplemented. |
| **Object Model** | ✅ IMPLEMENTED | **SIMULATED CREATION** | Objects exist but created via C++, not new-instance |
| **Resource Manager** | 🔶 PARTIAL | **PARTIAL** | XML resources working; ARSC basic support |
| **Layout Inflater** | 🔶 PARTIAL | **SIMULATED** | Layout parsed, Views created manually |
| **Software Renderer** | ✅ IMPLEMENTED | **DIRECT CALL** | Real pixel output but bypasses View.draw() |
| **ApplicationRuntime** | ✅ IMPLEMENTED | **COORDINATOR** | Unified pipeline with fallback simulation |
| **State Machine** | ✅ IMPLEMENTED | **TRACKING ONLY** | Records states but doesn't drive DEX execution |
| **API Intelligence DB** | ✅ IMPLEMENTED | **ANALYSIS** | 18 APIs tracked, 0 dispatched from DEX |

---

## Execution Path Reality (EXP-013 Audit)

```
STAGE                    STATUS      SOURCE
─────────────────────────────────────────────────────
APK Parsing              ✅ PASS      REAL - ApkParser
Manifest Resolution      ✅ PASS      REAL - ManifestReader  
DEX Loading              ✅ PASS      REAL - DexParser
Class Resolution         ✅ PASS      REAL - ClassResolver
onCreate Entry           ⚠️ ENTERED   REAL - Interpreter invoked
├─ const-string          ✅ EXECUTED  REAL DEX execution
├─ new-instance          ❌ HALTED    UNIMPLEMENTED
├─ invoke-direct         ⛔ NOT REACHED  Would call constructor
├─ invoke-virtual        ⛔ NOT REACHED  Would call setContentView/setText
└─ return-void           ⛔ NOT REACHED  Would complete method
[FALLBACK ACTIVATED]
View Creation             ⚠️ BYPASS    C++ heap_->create_text_view()
Text Assignment          ⚠️ BYPASS    Direct set_text() from resource parser
setContentView           ⚠️ BYPASS    Direct load_content_view() call
Lifecycle (onStart/Resume)⚠️ BYPASS   State machine transition_to() calls
Layout (measure/layout)  ⚠️ BYPASS    Hardcoded bounds assignment
Rendering                ⚠️ BYPASS    Direct renderer iteration of heap
Screenshot               ✅ OUTPUT    Real PNG generated
```

**Real Execution Percentage: ~15%** (APK→DEX→Interpreter entry is real; everything after first instruction is fallback)

---

## Detected Bypasses (run/bypass_detection.json)

| ID | Severity | Category | Impact |
|----|----------|----------|--------|
| BYPASS-001 | CRITICAL | DIRECT_VIEW_CREATION | TextView created without new-instance |
| BYPASS-002 | CRITICAL | HARDCODED_TEXT | Text set without invoke-virtual dispatch |
| BYPASS-003 | HIGH | MANUAL_LIFECYCLE | Lifecycle methods called directly |
| BYPASS-004 | HIGH | DIRECT_RENDERER | Renderer bypasses View.draw() chain |
| BYPASS-005 | MEDIUM | HARDCODED_LAYOUT | Dimensions are constants |
| BYPASS-006 | MEDIUM | RESOURCE_SHORTCUT | Resources loaded via C++ parser |

---

## Opcode Implementation Status

```
IMPLEMENTED (1):
  ✅ const-string (0x1A) - Working correctly

UNIMPLEMENTED BLOCKERS:
  ❌ new-instance (0x22)     - P0: Blocks ALL object creation
  ❌ invoke-direct (0x70)    - P0: Blocks constructor calls  
  ❌ invoke-virtual (0x6E)   - P1: Blocks API method calls
  ❌ return-void (0x0E)      - P1: Blocks method completion

UNIMPLEMENTED (~215): Remaining Dalvik opcodes
```

**Progress: 0.45% (1/220 opcodes)**

---

## Golden Corpus Status

| ID | Name | Local APK | Tested | Result |
|----|------|-----------|--------|--------|
| Golden-01 | android-HelloWorld | ✅ Yes | ✅ Yes | PARTIAL_PASS |
| Golden-02 | hello-android | ❌ No | - | SKIPPED |
| Golden-03 | android-hello-world | ❌ No | - | SKIPPED |
| Golden-04 | MinimalDroid | ❌ Placeholder | - | INVALID |
| Golden-05 | hello-world-android | ❌ No | - | SKIPPED |
| Golden-06 | AndroidBasicSamples | ❌ No | - | SKIPPED |
| Golden-07 | minimal-android-app | ❌ No | - | SKIPPED |
| Golden-08 | HelloWorldAndroid (Kotlin) | ❌ No | - | SKIPPED |
| Golden-09 | android-helloworld-patterns | ❌ No | - | SKIPPED |

**Test Coverage: 11.1% (1/9 APKs available locally)**

---

## API Dispatch Reality

```
Total APIs Tracked: 18
Dispatched from DEX: 0 (0%)
Via C++ Fallback: 12 (67%)
Via Lifecycle Simulation: 2 (11%)
Never Called: 4 (22%)
```

**Critical Insight**: The runtime has ZERO DEX-to-API dispatch. Every API call that appears to work is actually a C++ function call made directly by ApplicationRuntime after the interpreter halts.

---

## Known Limitations (Updated)

### P0 - Blocking for ANY Real Execution
1. **Only 1 opcode implemented**: Cannot execute real application logic
2. **No object creation via DEX**: new-instance not implemented
3. **No method invocation via DEX**: invoke-* family not implemented
4. **No method completion**: return-* not implemented

### P1 - Required for Basic Apps
5. **All API calls are simulated**: No DEX dispatch bridge exists
6. **Lifecycle is state tracking only**: Not real method execution
7. **Layout geometry is hardcoded**: No measure/layout pass

### P2 - Important for Complex Apps
8. **ARSC parser basic**: No full binary resource table decoding
9. **Single activity only**: No fragments/services/receivers
10. **No control flow**: if/jump/switch opcodes not implemented

### P3 - Nice to Have
11. **No hardware acceleration**: Software renderer only
12. **No animation system**
13. **No touch/input handling**

---

## Evidence Output Location (EXP-013 New Files)

All evidence files in `run/`:

**New Validation Files:**
- `execution_path_audit.json` - Complete pipeline audit (14 stages)
- `real_dex_execution_trace.json` - Instruction-level trace with real/simulated tags
- `oncreate_execution_proof.json` - onCreate entry path verification
- `api_dispatch_full_trace.json` - 12 API calls with dispatch source
- `bypass_detection.json` - 6 detected bypasses with severity
- `corpus_results.json` - Corpus validation results
- `regression_matrix.json` - Automated test matrix definition

**Updated Database Files:**
- `database/android_api_frequency.json` - Expanded to 18 APIs with dispatch reality
- `database/dex_opcode_frequency.json` - Full opcode inventory with priorities
- `golden/corpus.json` - Expanded to 9 applications (5 new)

---

## Recommended Next Steps (Priority Order)

### Immediate (Unblocks Basic Execution)

1. **Implement return-void (0x0E)** 
   - Effort: Low (simple PC adjustment)
   - Impact: Methods can complete

2. **Implement new-instance (0x22)**
   - Effort: Medium (object heap integration)
   - Impact: Objects can be created via DEX

3. **Implement invoke-direct (0x70)**
   - Effort: High (method resolution + argument passing)
   - Impact: Constructors can execute

4. **Implement invoke-virtual (0x6E)**
   - Effort: High (vtable lookup + API stub bridge)
   - Impact: ALL Android APIs become callable from DEX

### Short-term (Enables Real Apps)

5. **Build DEX-to-C++ dispatch bridge**
   - Connect invoke-* to android_stubs.h implementations
   - Enable real API dispatch chain

6. **Implement move-object and iget/iput-object**
   - Enable register manipulation and field access

7. **Download/build corpus APKs**
   - Increase test coverage beyond single HelloWorld

### Medium-term (Completes MVP)

8. **Implement if-eq/if-ne for control flow**
9. **Real measure/layout pass**
10. **Remove fallback simulation paths**

---

## Success Condition (From EXP-013 Spec)

> "MiniAndroid must know exactly what is real and what is simulated."

**STATUS: ✅ ACHIEVED**

We now have complete visibility into:
- Which stages are real vs. simulated
- Exactly which instructions executed
- Where every bypass occurs
- What each API call's true dispatch source is
- What opcodes block real execution

The runtime is **honest about its limitations**. No fake success claims.

---

*Status Document Version: 2.0-EXP013*  
*Generated by: EXP-013 Real Execution Validator*
*Golden Debug Protocol Compliance: VERIFIED ✅*
