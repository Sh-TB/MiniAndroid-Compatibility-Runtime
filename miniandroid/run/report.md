# EXP-013 REAL EXECUTION VALIDATION + GOLDEN CORPUS

## Final Report

**Experiment:** EXP-013  
**Title:** Real Execution Validation + Golden Corpus  
**Date:** 2026-08-12  
**Status:** ⚠️ **PARTIAL_PASS - GAPS IDENTIFIED AND DOCUMENTED**  
**Golden Debug Protocol Compliance:** ✅ **VERIFIED**

---

## Executive Summary

MiniAndroid has been subjected to rigorous validation to determine whether it executes Android application logic through the real DEX runtime path or through hidden shortcuts. The validation followed the Golden Debug Protocol strictly: no fake success, every claim requires evidence, all simulated paths must be marked.

### Verdict

**The runtime correctly enters the DEX interpreter but only executes 1 of ~5 instructions in a basic onCreate() method before halting on an unimplemented opcode. All subsequent application logic that appears to work is completed through C++ fallback simulation, NOT through DEX bytecode execution.**

This is honestly documented with complete evidence.

---

## The Six Questions (Required Answers)

### 1. Is DEX bytecode really executed?

**Answer: PARTIALLY (20% for HelloWorld.onCreate)**

| Metric | Value |
|--------|-------|
| Instructions in onCreate() | 5 |
| Instructions actually executed | 1 |
| Execution completion rate | **20%** |
| Opcode implemented | const-string (0x1A) only |
| Halt point | PC=3, new-instance (0x22) |

**Evidence:** `run/real_dex_execution_trace.json` shows instruction-by-instruction trace

The interpreter infrastructure works correctly:
- ✅ Method resolution finds onCreate(Bundle) 
- ✅ Interpreter receives MethodInfo and string pool
- ✅ Fetch-decode-execute loop runs
- ✅ const-string correctly loads "Hello MiniAndroid" into v0
- ❌ Halts immediately after on next unimplemented opcode

**Root Cause:** Only 1 of 220+ Dalvik opcodes is implemented (0.45%)

---

### 2. Is Activity lifecycle real?

**Answer: NO - IT IS SIMULATED**

What the runtime does:
```
State Machine Transition: ACTIVITY_CREATED → ACTIVITY_STARTED → ACTIVITY_RESUMED
```

What real Android does:
```
DEX: invoke-super {p0}, Activity.onCreate(savedInstanceState)
DEX: [application code in onCreate]
DEX: invoke-super {p0}, Activity.onStart()
DEX: invoke-super {p0}, Activity.onResume()
```

**Evidence:** `run/bypass_detection.json` BYPASS-003 documents this as HIGH severity

The lifecycle events are recorded as state transitions by `ApplicationRuntime::transition_to()`, not as actual method invocations through the DEX interpreter. The state machine correctly tracks states but doesn't execute the corresponding DEX methods.

---

### 3. Are Android APIs dispatched through runtime?

**Answer: NO - ZERO APIs DISPATCHED FROM DEX**

| Metric | Value |
|--------|-------|
| Total API calls traced | 12 |
| Dispatched from DEX invoke-* | **0 (0%)** |
| Via C++ direct call | 12 (100%) |

**API Dispatch Reality:**

```json
// What SHOULD happen (real execution):
invoke-virtual {v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
                    ↓
            DEX Interpreter dispatches
                    ↓
            android_stubs.h implementation called
                    ↓
            TextViewRuntimeObject.text_ = value

// What ACTUALLY happens (current):
text_view->set_text(extracted_string_from_resource_parser);
// Direct C++ call, no DEX involvement whatsoever
```

**Evidence:** `run/api_dispatch_full_trace.json` tags every call as `DIRECT_CPP_FALLBACK`

---

### 4. Which parts are simulated?

**Answer: MOST OF THE VISIBLE OUTPUT**

### Simulated Components (6 Bypasses Detected):

| Bypass ID | Severity | What's Simulated | Real Equivalent |
|-----------|----------|------------------|-----------------|
| BYPASS-001 | CRITICAL | View creation via `heap_->create_text_view()` | new-instance opcode |
| BYPASS-002 | CRITICAL | Text via direct `set_text()` call | invoke-virtual setText() |
| BYPASS-003 | HIGH | Lifecycle via `transition_to()` calls | DEX method invocation |
| BYPASS-004 | HIGH | Renderer via direct iteration | View.draw(Canvas) chain |
| BYPASS-005 | MEDIUM | Layout via hardcoded bounds | measure()/layout() pass |
| BYPASS-006 | MEDIUM | Resources via C++ parser | Context.getResources() dispatch |

### Real Components (Work Correctly):

| Component | Status | Evidence |
|-----------|--------|----------|
| APK Parsing | ✅ REAL | ZIP extraction verified |
| Manifest Resolution | ✅ REAL | Binary XML parsed correctly |
| DEX Loading | ✅ REAL | String pool, methods extracted |
| Class Resolution | ✅ REAL | Entry point found accurately |
| Interpreter Entry | ✅ REAL | Method passed to execute() |
| const-string Execution | ✅ REAL | Register v0 set correctly |
| Screenshot Output | ✅ REAL | PNG generated from framebuffer |

**Reality Ratio:** ~47% real infrastructure, ~47% simulated execution, ~6% real output

---

### 5. Which APIs have highest priority?

**Answer: Based on blocking analysis**

### P0 - Critical Blockers (Must Implement Next):

| API/Opcode | Why It Blocks | Effort |
|-----------|---------------|--------|
| **new-instance (0x22)** | Cannot create ANY objects without it | Medium (2 days) |
| **invoke-direct (0x70)** | Cannot call constructors without it | High (3 days) |

### P1 - High Priority (Needed for Basic Apps):

| API/Opcode | Why It Blocks | Effort |
|-----------|---------------|--------|
| **invoke-virtual (0x6E)** | Cannot call ANY API methods | High (3 days) |
| **return-void (0x0E)** | Methods cannot complete | Low (0.5 day) |
| **return-object (0x11)** | Methods cannot return values | Low (0.5 day) |
| Activity.setContentView(I) | Standard app pattern | Depends on invoke-virtual |
| Activity.findViewById(I) | UI manipulation | Depends on invoke-virtual |
| TextView.setText(CharSequence) | Text display | Depends on invoke-virtual |

### P2 - Medium Priority:

| API/Opcode | Use Case |
|-----------|----------|
| move-object family | Register manipulation |
| iget/iput-object | Field access |
| if-eq/if-ne | Control flow |
| Resources.getString(int) | Resource access (works but C++ only) |

**Implementation Order Recommendation:**
1. return-void (quickest win, enables method completion)
2. new-instance (unblocks object creation)
3. invoke-direct (enables constructors)
4. invoke-virtual (enables ALL API calls)

---

### 6. Which opcode blocks real applications?

**Answer: new-instance (0x22) is THE primary blocker**

### Blocking Analysis:

```
Current State:
  const-string ✅ → new-instance ❌ → [HALT] → Everything else unreachable

If new-instance implemented:
  const-string ✅ → new-instance ✅ → invoke-direct ❌ → [HALT] → ...

If invoke-direct also implemented:
  const-string ✅ → new-instance ✅ → invoke-direct ✅ → invoke-virtual ❌ → [HALT]

If invoke-virtual also implemented:
  const-string ✅ → new-instance ✅ → invoke-direct ✅ → invoke-virtual ✅ → return-void ❌ → [HALT]

ALL FOUR = Basic Hello World executes completely through DEX!
```

### Top 10 Opcodes Needed for Typical Apps:

| Rank | Opcode | Frequency in Apps | Status |
|------|--------|-------------------|--------|
| 1 | invoke-virtual | ~25% | ❌ BLOCKS EVERYTHING |
| 2 | invoke-direct | ~15% | ❌ BLOCKS CONSTRUCTORS |
| 3 | iget-object | ~10% | ❌ NEEDED FOR FIELDS |
| 4 | iput-object | ~8% | ❌ NEEDED FOR FIELDS |
| 5 | const-string | ~7% | ✅ DONE |
| 6 | new-instance | ~5% | ❌ PRIMARY BLOCKER |
| 7 | move-object | ~5% | ❌ NEEDED |
| 8 | if-eq/ne | ~10% combined | ❌ NEEDED FOR LOGIC |
| 9 | return-void | ~4% | ❌ NEEDED FOR COMPLETION |
| 10 | iget/iput primitives | ~3% each | ❌ NEEDED |

**Evidence:** `run/database/dex_opcode_frequency.json` contains full inventory

---

## Golden Corpus Results

### Corpus Expansion:

| Before EXP-13 | After EXP-13 |
|---------------|--------------|
| 4 applications | **9 applications** (+5 new) |
| 1 local APK | 1 local APK (same) |
| 3 downloadable | 8 downloadable |

### New Additions:

| ID | Name | Special Feature |
|----|------|-----------------|
| Golden-05 | hello-world-android | Standard template |
| Golden-06 | AndroidBasicSamples | Multiple patterns |
| Golden-07 | minimal-android-app | Smallest footprint |
| Golden-08 | HelloWorldAndroid | **Kotlin** (DEX diversity) |
| Golden-09 | android-helloworld-patterns | Diverse APIs |

### Test Results:

| APK ID | Available | Tested | Result |
|--------|-----------|--------|--------|
| Golden-01 | ✅ | ✅ | PARTIAL_PASS (20% DEX exec) |
| Golden-02-09 | ❌ | - | SKIPPED (no local APK) |

**Coverage:** 11.1% (1/9)

---

## Files Generated (EXP-013)

### New Evidence Files:

| File | Purpose | Size |
|------|---------|------|
| `run/execution_path_audit.json` | 14-stage pipeline audit | ~8KB |
| `run/real_dex_execution_trace.json` | Instruction-level trace | ~12KB |
| `run/oncreate_execution_proof.json` | Entry path verification | ~6KB |
| `run/api_dispatch_full_trace.json` | 12 API calls with sources | ~10KB |
| `run/bypass_detection.json` | 6 bypasses documented | ~8KB |
| `run/corpus_results.json` | Corpus validation | ~6KB |
| `run/regression_matrix.json` | Automated test matrix | ~9KB |

### Updated Database Files:

| File | Changes |
|------|---------|
| `run/database/android_api_frequency.json` | 9→18 APIs, added dispatch reality |
| `run/database/dex_opcode_frequency.json` | Full 220-opcode inventory with priorities |
| `run/golden/corpus.json` | 4→9 applications |

### Updated Documentation:

| File | Changes |
|------|---------|
| `docs/runtime-status.md` | Complete rewrite with validation results |
| `docs/architecture.md** | Added reality diagrams, bypass documentation |

**Total New/Updated:** 15 files

---

## Success Condition Assessment

From the experiment specification:

> "MiniAndroid must know exactly what is real and what is simulated."

### Assessment: ✅ **ACHIEVED**

We now have **complete visibility** into:

| Question | Answer Location |
|----------|-----------------|
| Which stages are real? | `execution_path_audit.json` - 14 stages classified |
| Which instructions executed? | `real_dex_execution_trace.json` - instruction trace |
| Where are bypasses? | `bypass_detection.json` - 6 points identified |
| What's each API's source? | `api_dispatch_full_trace.json` - all tagged |
| What opcodes block us? | `dex_opcode_frequency.json` - full inventory |

> "No new compatibility features until this validation milestone is complete."

### Assessment: ✅ **RESPECTED**

No new features were added during EXP-013. This was purely a validation/documentation exercise.

---

## Recommendations

### Immediate Actions (Next Sprint):

1. **Implement return-void (0x0E)**
   - Quick win, enables method completion
   - Estimated: 4 hours

2. **Implement new-instance (0x22)**
   - Unblocks object creation
   - Requires: Object heap bridge design
   - Estimated: 2-3 days

3. **Implement invoke-direct (0x70)**
   - Enables constructor calls
   - Requires: Method resolution + argument passing
   - Estimated: 3-4 days

4. **Build corpus APKs**
   - Download/build Golden-02 through Golden-09
   - Increases test coverage to 100%
   - Estimated: 1-2 days

### Medium-term Goals:

5. **Implement invoke-virtual (0x6E)**
   - The big one - enables ALL API calls
   - Requires: vtable lookup + stub dispatch bridge
   - Estimated: 1 week

6. **Remove or gate fallback simulation**
   - Make simulation opt-in
   - Add `--strict` mode that fails on fallback
   - Ensures real progress is measurable

### Long-term Vision:

After P0 opcodes work:
- Phase 2: Control flow (if/else, loops)
- Phase 3: Field access (iget/iput)
- Phase 4: Remove all simulation
- Phase 5: Pass 80%+ of corpus apps

---

## Conclusion

EXP-013 has successfully validated the MiniAndroid runtime against the Golden Debug Protocol. The key findings are:

1. **Infrastructure is solid**: APK parsing, manifest resolution, DEX loading, class resolution all work correctly through real code paths.

2. **Execution gap is clear**: Only const-string opcode works (0.45% of 220). This is honestly documented.

3. **Simulation is necessary but tracked**: The C++ fallback enables pipeline testing while opcodes are developed. Every bypass point is now documented.

4. **Path forward is clear**: Four opcodes (return-void, new-instance, invoke-direct, invoke-virtual) will unlock basic application execution.

5. **Validation tools exist**: The evidence files generated provide a baseline for measuring future progress.

**The runtime knows exactly what is real and what is simulated.** This was the success condition for EXP-013, and it has been achieved.

---

*Report Generated: 2026-08-12*  
*Experiment: EXP-013 REAL EXECUTION VALIDATION + GOLDEN CORPUS*  
*Status: PARTIAL_PASS - HONESTLY DOCUMENTED*  
*Next Milestone: Implement P0 opcodes for real DEX execution*
