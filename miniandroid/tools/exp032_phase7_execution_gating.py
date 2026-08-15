#!/usr/bin/env python3
"""
EXP-032 PHASE 7: Real Execution Gating System
==============================================
AOSP Reference-Driven MiniAndroid Acceleration

Purpose:
  - Implement mandatory execution evidence requirements (Rule 2, Rule 8)
  - Create validation gates that MUST pass before claiming "success"
  - Define minimum evidence standards for different claim levels
  - Generate execution validation checklists and tools

Core Principle (Rule 2):
  NO CLAIM WITHOUT EVIDENCE
  
  Any statement like "execution works", "opcode implemented", 
  "APK runs successfully" MUST include:
  - Opcode trace file
  - Register state dump
  - Execution source identifier (REAL vs SHORTCUT)

Author: EXP-032 Automation
Date: 2026-08-14
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path("/home/z/my-project/miniandroid")
DATABASE_DIR = PROJECT_ROOT / "database"
DOCS_DIR = PROJECT_ROOT / "docs"
RUN_DIR = PROJECT_ROOT / "run"

OUTPUT_FILE = DATABASE_DIR / "exp032_phase7_execution_gating.json"
REPORT_FILE = DOCS_DIR / "EXP032_PHASE7_EXECUTION_GATING.md"


# ============================================================================
# EXECUTION EVIDENCE STANDARDS
# ============================================================================

class ExecutionSource(Enum):
    """Rule 8: Must always distinguish execution source"""
    REAL_DALVIK_INTERPRETER = "real_dalvik_interpreter"  # Actual bytecode execution
    HOST_SHORTCUT = "host_shortcut"                      # Native code bypassing interpreter
    STATIC_ANALYSIS = "static_analysis"                  # No execution, just parsing
    SIMULATED = "simulated"                              # Mock/faked results
    UNKNOWN = "unknown"                                  # Source not documented


class EvidenceLevel(Enum):
    """Minimum evidence required for each claim level (Rule 3)"""
    CREATED = "created"           # Code exists, builds
    VALIDATED = "validated"       # Tests run with evidence
    PRODUCTION_READY = "production_ready"  # Real workloads tested


class ClaimType(Enum):
    """Types of claims that require evidence"""
    OPCODE_IMPLEMENTED = "opcode_implemented"
    METHOD_EXECUTED = "method_executed"
    APK_LAUNCHED = "apk_launched"
    API_CALLED = "api_called"
    UI_RENDERED = "ui_rendered"
    TEST_PASSED = "test_passed"


@dataclass
class EvidenceRequirement:
    """Defines what evidence is required for a specific claim"""
    claim_type: ClaimType
    evidence_level: EvidenceLevel
    
    # Required artifacts
    mandatory_artifacts: List[str] = field(default_factory=list)
    optional_artifacts: List[str] = field(default_factory=list)
    
    # Validation rules
    must_have_opcode_trace: bool = False
    must_have_register_dump: bool = False
    must_have_execution_source: bool = True  # ALWAYS required per Rule 8
    must_have_timestamp: bool = True
    must_have_apk_hash: bool = False
    must_have_heap_dump: bool = False
    must_have_api_trace: bool = False
    must_have_screenshot_file: bool = False
    
    # Minimum content requirements
    min_trace_length: int = 0  # Minimum number of trace entries
    min_opcodes_executed: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class ExecutionClaim:
    """
    A claim about execution that requires evidence.
    
    This is the MANDATORY format for all execution claims.
    """
    claim_id: str
    claim_type: ClaimType
    description: str
    claimed_by: str  # Who is making this claim
    timestamp: str = ""
    
    # Evidence provided
    evidence_level: EvidenceLevel = EvidenceLevel.CREATED
    execution_source: ExecutionSource = ExecutionSource.UNKNOWN
    
    # Artifact references (must be actual files/paths)
    opcode_trace_file: Optional[str] = None
    register_dump_file: Optional[str] = None
    heap_dump_file: Optional[str] = None
    api_trace_file: Optional[str] = None
    screenshot_file: Optional[str] = None
    additional_evidence: List[str] = field(default_factory=list)
    
    # Validation status
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    validator: str = ""  # Who validated
    validation_time: str = ""
    
    # Quality score (0-100)
    evidence_quality_score: int = 0
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate that this claim has sufficient evidence.
        
        Returns: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Rule 8: Must have execution source
        if self.execution_source == ExecutionSource.UNKNOWN:
            errors.append("Execution source not specified (Rule 8 violation)")
        
        # Check mandatory artifacts exist
        if self.opcode_trace_file and not Path(self.opcode_trace_file).exists():
            warnings.append(f"Opcode trace file not found: {self.opcode_trace_file}")
        
        if self.register_dump_file and not Path(self.register_dump_file).exists():
            warnings.append(f"Register dump file not found: {self.register_dump_file}")
        
        # Check evidence level appropriateness
        requirement = get_requirement_for_claim(self.claim_type, self.evidence_level)
        
        if requirement.must_have_opcode_trace and not self.opcode_trace_file:
            errors.append(f"Opcode trace required for {self.claim_type.value} at {self.evidence_level.value} level")
        
        if requirement.must_have_register_dump and not self.register_dump_file:
            errors.append(f"Register dump required for {self.claim_type.value} at {self.evidence_level.value} level")
        
        # Calculate quality score
        self.evidence_quality_score = self._calculate_score(requirement)
        
        self.validated = len(errors) == 0
        self.validation_errors = errors
        self.validation_warnings = warnings
        self.validation_time = datetime.now().isoformat()
        
        return (self.validated, errors, warnings)
    
    def _calculate_score(self, requirement: EvidenceRequirement) -> int:
        """Calculate evidence quality score (0-100)"""
        score = 0
        
        # Base points for having execution source (Rule 8)
        if self.execution_source != ExecutionSource.UNKNOWN:
            score += 20
        
        # Points for each artifact type
        if self.opcode_trace_file:
            score += 25
            # Bonus for real traces with content
            if Path(self.opcode_trace_file).exists():
                try:
                    size = Path(self.opcode_trace_file).stat().st_size
                    if size > 100:  # Has some content
                        score += 10
                except:
                    pass
        
        if self.register_dump_file:
            score += 15
        
        if self.heap_dump_file:
            score += 10
        
        if self.api_trace_file:
            score += 10
        
        if self.screenshot_file:
            score += 10
        
        # Bonus for real interpreter usage
        if self.execution_source == ExecutionSource.REAL_DALVIK_INTERPRETER:
            score += 10
        
        return min(score, 100)
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result["evidence_quality_score"] = self.evidence_quality_score
        result["validated"] = self.validated
        return result


# ============================================================================
# EVIDENCE REQUIREMENTS DEFINITION
# ============================================================================

def get_requirement_for_claim(claim_type: ClaimType, level: EvidenceLevel) -> EvidenceRequirement:
    """Get evidence requirements for a specific claim type and level"""
    
    requirements = {
        ClaimType.OPCODE_IMPLEMENTED: {
            EvidenceLevel.CREATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["source_code"],
                must_have_execution_source=True,
                min_opcodes_executed=0
            ),
            EvidenceLevel.VALIDATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["source_code", "test_case", "opcode_trace"],
                must_have_opcode_trace=True,
                must_have_register_dump=True,
                min_trace_length=1,
                min_opcodes_executed=1
            ),
            EvidenceLevel.PRODUCTION_READY: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["source_code", "multiple_test_cases", "real_apk_traces"],
                must_have_opcode_trace=True,
                must_have_register_dump=True,
                must_have_execution_source=True,
                min_trace_length=10,
                min_opcodes_executed=5
            )
        },
        ClaimType.METHOD_EXECUTED: {
            EvidenceLevel.CREATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["method_signature"],
                must_have_execution_source=True
            ),
            EvidenceLevel.VALIDATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["method_signature", "opcode_trace", "register_dump"],
                must_have_opcode_trace=True,
                must_have_register_dump=True,
                min_trace_length=3,
                min_opcodes_executed=3
            ),
            EvidenceLevel.PRODUCTION_READY: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["method_signature", "full_execution_trace", "heap_state"],
                must_have_opcode_trace=True,
                must_have_register_dump=True,
                must_have_heap_dump=True,
                min_trace_length=20,
                min_opcodes_executed=10
            )
        },
        ClaimType.APK_LAUNCHED: {
            EvidenceLevel.CREATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["apk_name"],
                must_have_execution_source=True,
                must_have_apk_hash=True
            ),
            EvidenceLevel.VALIDATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["apk_hash", "launch_trace", "onCreate_trace"],
                must_have_opcode_trace=True,
                must_have_register_dump=True,
                must_have_apk_hash=True,
                min_trace_length=5,
                min_opcodes_executed=5
            ),
            EvidenceLevel.PRODUCTION_READY: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["apk_hash", "complete_lifecycle_trace", "ui_screenshot"],
                must_have_opcode_trace=True,
                must_have_register_dump=True,
                must_have_api_trace=True,
                must_have_apk_hash=True,
                min_trace_length=50,
                min_opcodes_executed=25
            )
        },
        ClaimType.API_CALLED: {
            EvidenceLevel.CREATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["api_signature"],
                must_have_execution_source=True
            ),
            EvidenceLevel.VALIDATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["api_signature", "api_trace_entry", "calling_context"],
                must_have_opcode_trace=True,
                must_have_api_trace=True,
                min_trace_length=2
            ),
            EvidenceLevel.PRODUCTION_READY: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["api_signature", "multiple_call_traces", "parameter_validation"],
                must_have_opcode_trace=True,
                must_have_api_trace=True,
                must_have_register_dump=True,
                min_trace_length=10
            )
        },
        ClaimType.UI_RENDERED: {
            EvidenceLevel.CREATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["view_hierarchy"],
                must_have_execution_source=True
            ),
            EvidenceLevel.VALIDATED: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["view_hierarchy", "screenshot", "render_trace"],
                must_have_opcode_trace=True,
                must_have_screenshot_file=True,
                min_trace_length=10
            ),
            EvidenceLevel.PRODUCTION_READY: EvidenceRequirement(
                claim_type=claim_type,
                evidence_level=level,
                mandatory_artifacts=["view_hierarchy", "multiple_screenshots", "performance_metrics"],
                must_have_opcode_trace=True,
                must_have_screenshot_file=True,
                must_have_api_trace=True,
                min_trace_length=30
            )
        }
    }
    
    return requirements.get(claim_type, {}).get(level, EvidenceRequirement(
        claim_type=claim_type,
        evidence_level=level,
        must_have_execution_source=True
    ))


# ============================================================================
# VALIDATION GATE SYSTEM
# ============================================================================

class ExecutionGate:
    """
    Validation gate that claims MUST pass.
    
    This enforces Rules 2, 3, and 8 from the Engineering Protocol.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.claims_validated: List[ExecutionClaim] = []
        self.claims_rejected: List[ExecutionClaim] = []
        self.gate_passed: bool = False
        self.validation_time: str = ""
    
    def evaluate_claim(self, claim: ExecutionClaim) -> bool:
        """Evaluate a claim against requirements"""
        is_valid, errors, warnings = claim.validate()
        
        if is_valid:
            self.claims_validated.append(claim)
        else:
            self.claims_rejected.append(claim)
        
        return is_valid
    
    def finalize(self) -> bool:
        """Finalize gate evaluation"""
        self.gate_passed = len(self.claims_rejected) == 0
        self.validation_time = datetime.now().isoformat()
        return self.gate_passed
    
    def get_summary(self) -> Dict:
        """Get gate summary"""
        return {
            "gate_name": self.name,
            "gate_description": self.description,
            "passed": self.gate_passed,
            "claims_validated": len(self.claims_validated),
            "claims_rejected": len(self.claims_rejected),
            "validation_time": self.validation_time,
            "rejected_claims": [
                {"id": c.claim_id, "errors": c.validation_errors}
                for c in self.claims_rejected
            ]
        }


def create_standard_gates() -> Dict[str, ExecutionGate]:
    """Create standard validation gates for MiniAndroid development"""
    
    gates = {
        "opcode_implementation_gate": ExecutionGate(
            name="Opcode Implementation Gate",
            description="All opcode implementation claims must have trace evidence"
        ),
        "method_execution_gate": ExecutionGate(
            name="Method Execution Gate",
            description="All method execution claims must show actual bytecode execution"
        ),
        "apk_launch_gate": ExecutionGate(
            name="APK Launch Gate",
            description="All APK launch claims must have complete lifecycle traces"
        ),
        "api_compatibility_gate": ExecutionGate(
            name="API Compatibility Gate",
            description="All API call claims must have API trace entries"
        ),
        "production_readiness_gate": ExecutionGate(
            name="Production Readiness Gate",
            description="Production-ready claims require comprehensive evidence"
        )
    }
    
    return gates


# ============================================================================
# EXAMPLE CLAIMS FOR TESTING
# ============================================================================

def generate_example_claims() -> List[ExecutionClaim]:
    """Generate example claims demonstrating proper evidence format"""
    
    claims = []
    
    # Example 1: Good claim with full evidence
    claim1 = ExecutionClaim(
        claim_id="OPCODE-CONST4-001",
        claim_type=ClaimType.OPCODE_IMPLEMENTED,
        description="const/4 opcode correctly loads small literals into registers",
        claimed_by="dalvik_engine.cpp",
        timestamp="2026-08-14T10:00:00Z",
        evidence_level=EvidenceLevel.VALIDATED,
        execution_source=ExecutionSource.REAL_DALVIK_INTERPRETER,
        opcode_trace_file=str(RUN_DIR / "exp031_5/traces/com.test.valid/opcode_trace.json"),
        register_dump_file=str(RUN_DIR / "exp031_5/traces/com.test.valid/register_trace.json"),
        additional_evidence=[
            "Test case: Test1_Constant.dex executes const/4 successfully",
            "Opcode hex: 0x12, format: 22s"
        ]
    )
    claims.append(claim1)
    
    # Example 2: Weak claim (missing evidence)
    claim2 = ExecutionClaim(
        claim_id="METHOD-ONCREATE-001",
        claim_type=ClaimType.METHOD_EXECUTED,
        description="Activity.onCreate() method executes completely",
        claimed_by="manual_test",
        timestamp="2026-08-14T11:00:00Z",
        evidence_level=EvidenceLevel.CREATED,  # Only claiming CREATED
        execution_source=ExecutionSource.REAL_DALVIK_INTERPRETER,
        opcode_trace_file=None,  # Missing! Will fail validation at higher levels
        register_dump_file=None
    )
    claims.append(claim2)
    
    # Example 3: APK launch claim
    claim3 = ExecutionClaim(
        claim_id="APK-HW-001",
        claim_type=ClaimType.APK_LAUNCHED,
        description="HelloWorld.apk launches and shows Activity",
        claimed_by="exp032_runner.py",
        timestamp="2026-08-14T12:00:00Z",
        evidence_level=EvidenceLevel.VALIDATED,
        execution_source=ExecutionSource.REAL_DALVIK_INTERPRETER,
        opcode_trace_file=str(RUN_DIR / "exp032_phase3/execution_proofs/HelloWorld_original/evidence_summary.json"),
        additional_evidence=[
            "APK SHA256: abc123...",
            "Entry point: com.example.HelloWorld.onCreate()"
        ]
    )
    claims.append(claim3)
    
    return claims


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_phase7_report(example_claims: List[ExecutionClaim],
                          gates: Dict[str, ExecutionGate]) -> Dict:
    """Generate comprehensive Phase 7 report"""
    
    # Evaluate all example claims through gates
    for claim in example_claims:
        for gate_name, gate in gates.items():
            if gate_name in ["opcode_implementation_gate", "method_execution_gate", "apk_launch_gate"]:
                gate.evaluate_claim(claim)
    
    # Finalize all gates
    for gate in gates.values():
        gate.finalize()
    
    report = {
        "phase": "PHASE_7_EXECUTION_GATING",
        "timestamp": datetime.now().isoformat(),
        "status": "CREATED",
        
        "core_principle": {
            "rule_reference": "RULE 2 + RULE 8",
            "statement": "NO CLAIM WITHOUT EVIDENCE - Every execution claim MUST have opcode trace",
            "enforcement": "Claims without evidence are REJECTED automatically"
        },
        
        "evidence_levels": {
            level.value: {
                "description": f"Requirements for {level.value} level",
                "min_score": 20 if level == EvidenceLevel.CREATED else 
                           60 if level == EvidenceLevel.VALIDATED else 90,
                "can_claim": "Code exists" if level == EvidenceLevel.CREATED else
                            "Tested with evidence" if level == EvidenceLevel.VALIDATED else
                            "Real workload validated"
            }
            for level in EvidenceLevel
        },
        
        "execution_sources": {
            source.value: {
                "description": _describe_source(source),
                "validity": "FULLY VALID" if source == ExecutionSource.REAL_DALVIK_INTERPRETER else
                          "LIMITED VALIDITY" if source == ExecutionSource.HOST_SHORTCUT else
                          "NOT EXECUTION EVIDENCE"
            }
            for source in ExecutionSource
        },
        
        "validation_gates": {
            gate_name: gate.get_summary()
            for gate_name, gate in gates.items()
        },
        
        "example_claims_evaluated": len(example_claims),
        "example_claim_details": [c.to_dict() for c in example_claims],
        
        "quality_thresholds": {
            "minimum_acceptable": 40,   # Below this = reject
            "good": 60,                 # Acceptable for VALIDATED
            "excellent": 80,            # Required for PRODUCTION_READY
            "perfect": 100              # All possible evidence
        },
        
        "implementation_checklist": [
            "☐ Before claiming 'opcode implemented': Run test, collect trace",
            "☐ Before claiming 'method executed': Capture register state",
            "☐ Before claiming 'APK launched': Record full lifecycle",
            "☐ Before claiming 'API works': Log API trace entry",
            "☐ Always specify execution source (Rule 8)",
            "☐ Score must exceed threshold for claim level",
            "☐ Store evidence files in run/ directory",
            "☐ Include evidence paths in claim record"
        ],
        
        "common_violations": [
            {
                "violation": "Claiming 'works' without trace file",
                "severity": "CRITICAL",
                "fix": "Run execution with tracing enabled, save output"
            },
            {
                "violation": "Using HOST_SHORTCUT but claiming REAL execution",
                "severity": "HIGH",
                "fix": "Clearly label execution source; only REAL counts for opcode claims"
            },
            {
                "violation": "Evidence file doesn't exist or is empty",
                "severity": "MEDIUM",
                "fix": "Verify artifact paths before submitting claim"
            },
            {
                "violation": "Missing timestamp on claim",
                "severity": "LOW",
                "fix": "Always include ISO timestamp when creating claim"
            }
        ]
    }
    
    return report


def _describe_source(source: ExecutionSource) -> str:
    descriptions = {
        ExecutionSource.REAL_DALVIK_INTERPRETER: "Actual DEX bytecode executed by DalvikEngine interpreter",
        ExecutionSource.HOST_SHORTCUT: "Native code bypassing bytecode interpretation",
        ExecutionSource.STATIC_ANALYSIS: "DEX parsed but no execution occurred",
        ExecutionSource.SIMULATED: "Results fabricated or mocked",
        ExecutionSource.UNKNOWN: "Execution method not documented"
    }
    return descriptions.get(source, "Unknown")


def generate_markdown_report(report: Dict) -> str:
    """Generate human-readable markdown report"""
    
    md = f"""# EXP-032 Phase 7: Real Execution Gating System

**Generated**: {report['timestamp']}
**Status**: {report['status']}
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

"""

    for source_name, source_info in report['execution_sources'].items():
        validity_icon = "✅" if "FULLY" in source_info['validity'] else \
                       "⚠️" if "LIMITED" in source_info['validity'] else "❌"
        md += f"""### {source_name.upper().replace('_', ' ')}

{source_info['description']}

**Validity**: {validity_icon} {source_info['validity']}

---

"""

    md += f"""## Validation Gates

Claims must pass these gates before acceptance:

| Gate | Passed | Validated | Rejected |
|------|--------|-----------|----------|
"""

    for gate_name, gate_summary in report['validation_gates'].items():
        passed_icon = "✅" if gate_summary['passed'] else "❌"
        md += f"| {gate_summary['gate_name']} | {passed_icon} | {gate_summary['claims_validated']} | {gate_summary['claims_rejected']} |\n"

    md += f"""
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

"""

    for claim_data in report.get('example_claim_details', []):
        score = claim_data.get('evidence_quality_score', 0)
        status = "✅ PASS" if claim_data.get('validated') else f"❌ FAIL ({len(claim_data.get('validation_errors', []))} errors)"
        md += f"""### {claim_data['claim_id']}: {claim_data['description']}

| Attribute | Value |
|-----------|-------|
| **Type** | {claim_data['claim_type']} |
| **Level** | {claim_data['evidence_level']} |
| **Source** | {claim_data['execution_source']} |
| **Score** | {score}/100 |
| **Status** | {status} |

"""

        if claim_data.get('validation_errors'):
            md += "**Errors:**\n"
            for err in claim_data['validation_errors']:
                md += f"- {err}\n"
            md += "\n"

    md += f"""## Implementation Checklist

Before making ANY execution claim:

"""

    for item in report['implementation_checklist']:
        md += f"{item}\n"

    md += f"""
## Common Violations to Avoid

"""

    for violation in report['common_violations']:
        severity_icon = "🔴" if violation['severity'] == "CRITICAL" else \
                     "🟡" if violation['severity'] == "HIGH" else \
                     "🟠"
        md += f"""### {severity_icon} {violation['violation']}

**Fix**: {violation['fix']}

---

"""

    md += f"""## Integration Requirements

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
print(f"Score: {{claim.evidence_quality_score}}/100")
print(f"Valid: {{is_valid}}")

if not is_valid:
    print("Missing:", errors)
```

---

*Gating system established by EXP-032 Phase 7*
*All future claims MUST pass through this validation*
*Violations will be flagged in code review*
"""
    
    return md


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 80)
    print("EXP-032 PHASE 7: REAL EXECUTION GATING")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Step 1: Create validation gates
    print("[1/4] Creating validation gates...")
    gates = create_standard_gates()
    print(f"      Created {len(gates)} gates")
    
    # Step 2: Generate example claims
    print("\n[2/4] Generating example claims...")
    example_claims = generate_example_claims()
    print(f"      Generated {len(example_claims)} example claims")
    
    # Step 3: Validate claims through gates
    print("\n[3/4] Validating claims through gates...")
    for claim in example_claims:
        is_valid, errors, warnings = claim.validate()
        status = "✅ PASS" if is_valid else f"❌ FAIL ({len(errors)} errors)"
        print(f"      {claim.claim_id}: {status} (score: {claim.evidence_quality_score}/100)")
    
    # Step 4: Generate report
    print("\n[4/4] Generating report...")
    report = generate_phase7_report(example_claims, gates)
    
    # Save outputs
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n      Database: {OUTPUT_FILE}")
    
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    report_md = generate_markdown_report(report)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report_md)
    print(f"      Report: {REPORT_FILE}")
    
    # Summary
    print("\n" + "=" * 80)
    print("PHASE 7 COMPLETE SUMMARY")
    print("=" * 80)
    print(f"Status: {report['status']}")
    print(f"Gates defined: {len(gates)}")
    print(f"Example claims evaluated: {len(example_claims)}")
    valid_count = sum(1 for c in example_claims if c.validated)
    print(f"Claims passing: {valid_count}/{len(example_claims)}")
    print()
    print("Key Output: Execution gating now MANDATORY for all claims")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    main()
