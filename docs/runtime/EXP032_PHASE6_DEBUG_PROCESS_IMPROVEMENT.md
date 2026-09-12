# EXP-032 Phase 6: Debug Process Improvement

**Generated**: 2026-08-14T10:46:14.056250
**Status**: CREATED
**Goal**: Implement Golden Debug Protocol for evidence-based debugging

---

## Overview

This phase establishes **standardized debugging procedures** that MUST be followed for all MiniAndroid bug fixes.

### Why This Matters

Without structured debugging:
- ❌ Fixes address symptoms, not root causes
- ❌ Same bugs reappear repeatedly  
- ❌ Knowledge is lost when developers change
- ❌ No evidence fixes actually work

With Golden Debug Protocol:
- ✅ Every fix has documented root cause
- ✅ Patterns emerge from tracked hypotheses
- ✅ New developers can understand past decisions
- ✅ Evidence proves correctness

---

## The Golden Debug Protocol Phases

### EVIDENCE COLLECTION: Evidence Collection

**Rule Reference**: RULE 4.1

Collect logs, traces, dumps, and reproduction cases BEFORE changing code

**Required Output**: ['instruction_trace.json', 'register_dump.json', 'error_log.txt']

---

### HYPOTHESIS FORMATION: Hypothesis Formation

**Rule Reference**: RULE 4.3

Form clear hypothesis about root cause

**Required Output**: DebugHypothesis record with status tracking

---

### AOSP REFERENCE CHECK: AOSP Reference Check

**Rule Reference**: RULE 6

Consult AOSP source code to understand correct behavior

**Required Output**: Reference comparison document

---

### ROOT CAUSE IDENTIFICATION: Root Cause Identification

**Rule Reference**: RULE 4.2

Identify actual cause, not just symptom

**Required Output**: Root cause description with evidence

---

### FIX IMPLEMENTATION: Fix Implementation

**Rule Reference**: Best Practice

Implement minimal fix addressing root cause

**Required Output**: Code changes with clear commit message

---

### REGRESSION TESTING: Regression Testing

**Rule Reference**: RULE 4.2

Verify fix doesn't break existing functionality

**Required Output**: Test results showing pass/fail

---

### DOCUMENTATION: Documentation

**Rule Reference**: RULE 5

Document findings, lessons learned, prevention measures

**Required Output**: Updated experiment docs + worklog

---

## Debug Templates

Use these templates when creating new debug sessions:

| Template | For | Severity |
|----------|-----|----------|
| `Opcode Template` | Opcode implementation bugs | HIGH |
| `Parse Template` | DEX parsing errors | HIGH |
| `Object_model Template` | Object model / field access issues | HIGH |
| `Api_bridge Template` | Android API stub behavior | HIGH |

## AOSP Reference Quick Guide

| Component | Dalvik Source | ART Source | Usage |
|-----------|---------------|------------|-------|
| Opcode Interpreter | `dalvik/vm/Interp.c` | `art/runtime/interpreter/interpreter.cc` | Main interpreter switch statement |
| Opcode Assembly | `dalvik/vm/mterp/` | `art/runtime/interpreter/mterp/` | Assembly-optimized opcode implementations |
| Dex Format | `dalvik/libdex/DexFile.cpp` | `art/libdexfile/dex_file.cc` | DEX file format structures and parsing |
| Dex Structures | `dalvik/libdex/DexProto.h` | `art/libdexfile/dex_file_structs.h` | DEX structure definitions (header, class_def, etc.) |
| Object Model | `dalvik/vm/oo/Object.h` | `art/runtime/mirror/object.h` | Runtime object representations |
| Field Access | `dalvik/vm/oo/Object.h (Field struct)` | `art/runtime/art_field.h (ArtField)` | Field offset resolution and access |
| Class Loader | `dalvik/vm/Reflect.h` | `runtime/class_linker.h` | Class loading and resolution |
| Method Dispatch | `dalvik/vm/oo/Object.h (vtable)` | `art/runtime/art_method.h` | Virtual method dispatch mechanism |

## Debug Checklists

### Before Changing Code (MANDATORY)

☐ Issue reproducible (not one-time flake)
☐ Evidence collected BEFORE code changes
☐ Root cause identified (not just symptom fixed)
☐ Fix is minimal (no unnecessary changes)
☐ Changes don't break existing functionality
☐ Tests added for the specific issue
☐ Documentation updated
☐ Commit message explains 'why' not just 'what'

### Opcode-Specific Checklist

☐ Captured full instruction trace showing failure
☐ Identified exact opcode hex value causing issue
☐ Recorded PC (program counter) at time of failure
☐ Dumped register state before and after opcode
☐ Verified bytecode is valid (not corrupted)
... (see full checklist in JSON)

## Implementation Status

| Item | Status |
|------|--------|
| Protocol Documented | ✅ |
| Templates Created | ✅ |
| Checklists Available | ✅ |

### Next Steps

- [ ] Create new DebugSession for each bug using templates
- [ ] Follow phases sequentially (no skipping!)
- [ ] Store completed sessions in experiments/ directory
- [ ] Review sessions in team meetings for pattern detection
- [ ] Update templates based on lessons learned

---

## Appendix: Creating a New Debug Session

```python
# Example usage (see DebugSession class definition above)
session = DebugSession(
    session_id="MYBUG-001",
    title="Brief description of issue",
    severity=Severity.HIGH,
    category=IssueCategory.OPCODE_ERROR,
    problem_description="Detailed description...",
    reproduction_steps=["Step 1", "Step 2", ...],
    expected_behavior="What should happen",
    actual_behavior="What actually happens"
)

# Add hypothesis
session.hypotheses.append(DebugHypothesis(
    id="H1",
    description="My guess about the cause",
    category=IssueCategory.OPCODE_ERROR,
    proposed_cause="Root cause theory",
    proposed_fix="How to fix it"
))

# Save session (example - see documentation above)
# json.dump(session.to_dict(), open('experiments/DEBUG_SESSION.json', 'w'), indent=2)
```

---

*Protocol established by EXP-032 Phase 6*
*All future debugging MUST follow this process*
