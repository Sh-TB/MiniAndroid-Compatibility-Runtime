# EXP-032 Phase 7: Real Execution Gating System

**Generated**: 2026-08-14T10:50:46.084205
**Status**: CREATED
**Purpose**: Enforce evidence-based claims for all execution statements

---

## ⚠️ MANDATORY REQUIREMENT (Rule 2)

### NO CLAIM WITHOUT EVIDENCE

The following statements are **FORBIDDEN** without supporting evidence:

| Statement | Requires | Minimum Level |
|-----------|----------|---------------|
| "Opcode X works" | Opcode trace file | VALIDATED |
| "Method Y executed" | Trace + register dump | VALIDATED |
| "APK Z launches" | Full lifecycle trace | VALIDATED |
| "API W called" | API trace entry | VALIDATED |
| "UI rendered" | Screenshot + view tree | VALIDATED |

---

## Execution Source Classification (Rule 8)

Every diagnostic event **MUST** identify its source:

### REAL DALVIK INTERPRETER

Actual DEX bytecode executed by DalvikEngine interpreter

**Validity**: ✅ FULLY VALID

---

### HOST SHORTCUT

Native code bypassing bytecode interpretation

**Validity**: ⚠️ LIMITED VALIDITY

---

### STATIC ANALYSIS

DEX parsed but no execution occurred

**Validity**: ❌ NOT EXECUTION EVIDENCE

---

### SIMULATED

Results fabricated or mocked

**Validity**: ❌ NOT EXECUTION EVIDENCE

---

### UNKNOWN

Execution method not documented

**Validity**: ❌ NOT EXECUTION EVIDENCE

---

## Validation Gates

Claims must pass these gates before acceptance:

| Gate | Passed | Validated | Rejected |
|------|--------|-----------|----------|
| Opcode Implementation Gate | ❌ | 2 | 1 |
| Method Execution Gate | ❌ | 2 | 1 |
| APK Launch Gate | ❌ | 2 | 1 |
| API Compatibility Gate | ✅ | 0 | 0 |
| Production Readiness Gate | ✅ | 0 | 0 |

## Evidence Quality Scoring

Claims are scored 0-100 based on evidence completeness:

| Score Range | Rating | Can Claim |
|-------------|--------|-----------|
| 0-39 | ❌ INSUFFICIENT | Nothing (auto-reject) |
| 40-59 | ⚠️ MINIMAL | CREATED only |
| 60-79 | ✅ GOOD | VALIDATED |
| 80-99 | ✅✅ EXCELLENT | Production candidate |
| 100 | ✅✅✅ PERFECT | Fully documented |

### Scoring Criteria

| Evidence Type | Points |
|---------------|--------|
| Execution source specified | +20 |
| Opcode trace file (exists) | +25 (+10 if has content) |
| Register dump file | +15 |
| Heap state dump | +10 |
| API trace log | +10 |
| Screenshot captured | +10 |
| Real interpreter used | +10 |

---

## Example Claims Evaluated

### OPCODE-CONST4-001: const/4 opcode correctly loads small literals into registers

| Attribute | Value |
|-----------|-------|
| **Type** | ClaimType.OPCODE_IMPLEMENTED |
| **Level** | EvidenceLevel.VALIDATED |
| **Source** | ExecutionSource.REAL_DALVIK_INTERPRETER |
| **Score** | 80/100 |
| **Status** | ✅ PASS |

### METHOD-ONCREATE-001: Activity.onCreate() method executes completely

| Attribute | Value |
|-----------|-------|
| **Type** | ClaimType.METHOD_EXECUTED |
| **Level** | EvidenceLevel.CREATED |
| **Source** | ExecutionSource.REAL_DALVIK_INTERPRETER |
| **Score** | 30/100 |
| **Status** | ✅ PASS |

### APK-HW-001: HelloWorld.apk launches and shows Activity

| Attribute | Value |
|-----------|-------|
| **Type** | ClaimType.APK_LAUNCHED |
| **Level** | EvidenceLevel.VALIDATED |
| **Source** | ExecutionSource.REAL_DALVIK_INTERPRETER |
| **Score** | 65/100 |
| **Status** | ❌ FAIL (1 errors) |

**Errors:**
- Register dump required for apk_launched at validated level

## Implementation Checklist

Before making ANY execution claim:

☐ Before claiming 'opcode implemented': Run test, collect trace
☐ Before claiming 'method executed': Capture register state
☐ Before claiming 'APK launched': Record full lifecycle
☐ Before claiming 'API works': Log API trace entry
☐ Always specify execution source (Rule 8)
☐ Score must exceed threshold for claim level
☐ Store evidence files in run/ directory
☐ Include evidence paths in claim record

## Common Violations to Avoid

### 🔴 Claiming 'works' without trace file

**Fix**: Run execution with tracing enabled, save output

---

### 🟡 Using HOST_SHORTCUT but claiming REAL execution

**Fix**: Clearly label execution source; only REAL counts for opcode claims

---

### 🟠 Evidence file doesn't exist or is empty

**Fix**: Verify artifact paths before submitting claim

---

### 🟠 Missing timestamp on claim

**Fix**: Always include ISO timestamp when creating claim

---

## Integration Requirements

To use this gating system:

1. **Import ExecutionClaim class** in your test/validation code
2. **Create claim** with all evidence artifacts referenced
3. **Call validate()** to check sufficiency
4. **Check score** meets threshold for your desired level
5. **Store claim** in experiments/ directory with evidence

### Quick Start Example

```python
from exp032_phase7_gating import ExecutionClaim, ClaimType, EvidenceLevel, ExecutionSource

claim = ExecutionClaim(
    claim_id="MY-TEST-001",
    claim_type=ClaimType.OPCODE_IMPLEMENTED,
    description="My new opcode works correctly",
    claimed_by="my_test.py",
    execution_source=ExecutionSource.REAL_DALVIK_INTERPRETER,
    evidence_level=EvidenceLevel.VALIDATED,
    opcode_trace_file="run/my_test/trace.json",
    register_dump_file="run/my_test/registers.json"
)

is_valid, errors, warnings = claim.validate()  # claim defined above
print(f"Score: {claim.evidence_quality_score}/100")
print(f"Valid: {is_valid}")

if not is_valid:
    print("Missing:", errors)
```

---

*Gating system established by EXP-032 Phase 7*
*All future claims MUST pass through this validation*
*Violations will be flagged in code review*
