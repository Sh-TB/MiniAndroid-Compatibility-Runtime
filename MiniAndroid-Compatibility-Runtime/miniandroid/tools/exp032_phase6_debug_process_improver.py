#!/usr/bin/env python3
"""
EXP-032 PHASE 6: Debug Process Improvement Tool
===============================================
AOSP Reference-Driven MiniAndroid Acceleration

Purpose:
  - Implement Golden Debug Protocol (from Engineering Continuity Protocol)
  - Create standardized debug workflow: Search AOSP → Compare → Fix → Regress Test
  - Generate debug templates and checklists
  - Document debugging patterns for common issues

Evidence Protocol Compliant (Rule 2, Rule 4):
  - All fixes require root cause identification
  - Hypotheses must be tracked
  - Evidence collected before code changes

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


# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path("/home/z/my-project/miniandroid")
DATABASE_DIR = PROJECT_ROOT / "database"
DOCS_DIR = PROJECT_ROOT / "docs"
TOOLS_DIR = PROJECT_ROOT / "tools"

OUTPUT_FILE = DATABASE_DIR / "exp032_phase6_debug_process_improvement.json"
REPORT_FILE = DOCS_DIR / "EXP032_PHASE6_DEBUG_PROCESS_IMPROVEMENT.md"
TEMPLATE_DIR = PROJECT_ROOT / "templates"  # Debug templates


# ============================================================================
# GOLDEN DEBUG PROTOCOL IMPLEMENTATION
# ============================================================================

class DebugPhase(Enum):
    """Phases of the Golden Debug Protocol"""
    EVIDENCE_COLLECTION = "evidence_collection"     # Step 1: Collect logs/traces/dumps
    HYPOTHESIS_FORMATION = "hypothesis_formation"   # Step 2: Form hypothesis
    AOSP_REFERENCE_CHECK = "aosp_reference_check"   # Step 3: Check AOSP source
    ROOT_CAUSE_IDENTIFICATION = "root_cause_identification"  # Step 4: Find root cause
    FIX_IMPLEMENTATION = "fix_implementation"       # Step 5: Implement fix
    REGRESSION_TESTING = "regression_testing"       # Step 6: Regression test
    DOCUMENTATION = "documentation"                 # Step 7: Document findings


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"      # Blocks all progress
    HIGH = "high"             # Blocks major feature
    MEDIUM = "medium"         # Feature partially broken
    LOW = "low"               # Minor issue or enhancement
    COSMETIC = "cosmetic"      # Visual/polish only


class IssueCategory(Enum):
    """Categories of debug issues"""
    OPCODE_ERROR = "opcode_error"           # Opcode implementation wrong
    PARSE_ERROR = "parse_error"             # DEX parsing incorrect
    OBJECT_MODEL = "object_model"           # Object model mismatch
    TYPE_SYSTEM = "type_system"             # Type handling wrong
    MEMORY = "memory"                       # Memory management issue
    API_BRIDGE = "api_bridge"               # API stub behavior wrong
    CONTROL_FLOW = "control_flow"           # Branch/jump logic error
    PERFORMANCE = "performance"             # Slow/crash under load
    UNKNOWN = "unknown"                     # Not yet categorized


@dataclass
class DebugHypothesis:
    """Tracked hypothesis during debugging (Rule 4.3)"""
    id: str
    description: str
    category: IssueCategory
    proposed_cause: str
    proposed_fix: str
    
    # Tracking
    created_time: str = ""
    status: str = "PENDING"  # PENDING, TESTING, CONFIRMED, REJECTED
    test_performed: str = ""
    test_result: str = ""  # PASS, FAIL, INCONCLUSIVE
    evidence_collected: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class DebugSession:
    """
    Complete debug session following Golden Debug Protocol.
    
    This is the MANDATORY format for all debugging activities.
    """
    session_id: str
    title: str
    severity: Severity
    category: IssueCategory
    
    # Problem description
    problem_description: str
    reproduction_steps: List[str] = field(default_factory=list)
    
    # Evidence (Step 1 - collected BEFORE any changes)
    initial_evidence: Dict[str, Any] = field(default_factory=dict)
    logs_collected: List[str] = field(default_factory=list)
    traces_collected: List[str] = field(default_factory=list)
    
    # Current state when bug found
    expected_behavior: str = ""
    actual_behavior: str = ""
    
    # Hypotheses tracking (Rule 4.3)
    hypotheses: List[DebugHypothesis] = field(default_factory=list)
    
    # Root cause (Step 4)
    root_cause_identified: bool = False
    root_cause_description: str = ""
    aosp_reference_checked: bool = False
    aosp_source_file: str = ""
    aosp_behavior_differs: bool = False
    difference_description: str = ""
    
    # Fix (Step 5)
    fix_implemented: bool = False
    fix_description: str = ""
    files_changed: List[str] = field(default_factory=list)
    lines_changed: int = 0
    
    # Regression (Step 6)
    regression_tested: bool = False
    regression_tests_run: List[str] = field(default_factory=list)
    regression_results: Dict[str, str] = field(default_factory=dict)  # test_name -> PASS/FAIL
    
    # Documentation (Step 7)
    documented: bool = False
    lessons_learned: List[str] = field(default_factory=list)
    prevention_measures: List[str] = field(default_factory=list)
    
    # Metadata
    created_time: str = ""
    updated_time: str = ""
    status: str = "OPEN"  # OPEN, IN_PROGRESS, FIXED, WONT_FIX, CANNOT_REPRODUCE
    assignee: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================================
# DEBUG TEMPLATES FOR COMMON ISSUES
# ============================================================================

def get_opcode_debug_template() -> DebugSession:
    """Template for opcode implementation bugs"""
    return DebugSession(
        session_id="OPCODE-XXX",
        title="Opcode [NAME] Incorrect Behavior",
        severity=Severity.HIGH,
        category=IssueCategory.OPCODE_ERROR,
        problem_description="Opcode [NAME] produces incorrect results or crashes",
        reproduction_steps=[
            "1. Create DEX file containing opcode [NAME]",
            "2. Execute through DalvikEngine",
            "3. Observe register state after execution",
            "4. Compare with expected AOSP behavior"
        ],
        expected_behavior="[Describe correct behavior per AOSP specification]",
        actual_behavior="[Describe what actually happens]",
        aosp_source_file="dalvik/vm/mterp/[arch]_[opcode].S or dalvik/vm/Interp.c",
        lessons_learned=[
            "Always check operand decoding order (vAA vs vA, vB)",
            "Verify signed/unsigned conversion for literals",
            "Check register index bounds before access"
        ]
    )


def get_parse_debug_template() -> DebugSession:
    """Template for DEX parsing bugs"""
    return DebugSession(
        session_id="PARSE-XXX",
        title="DEX Structure Parsing Error at Offset 0xOFFSET",
        severity=Severity.CRITICAL,
        category=IssueCategory.PARSE_ERROR,
        problem_description="DEX parser fails to correctly read structure at specified offset",
        reproduction_steps=[
            "1. Identify problematic DEX file",
            "2. Run parser with verbose output",
            "3. Examine bytes at reported offset",
            "4. Compare with DEX format specification"
        ],
        expected_behavior="Parser reads correct values per DEX format spec",
        actual_behavior="Parser reads incorrect values or crashes",
        aosp_source_file="dalvik/libdex/DexFile.cpp or art/libdexfile/dex_file_types.h",
        lessons_learned=[
            "DEX is little-endian - always use le32toh()/le16toh()",
            "String IDs are indices into string_ids[] table, not offsets",
            "MUTF-8 modified encoding for strings"
        ]
    )


def get_object_model_debug_template() -> DebugSession:
    """Template for object model issues"""
    return DebugSession(
        session_id="OBJMODEL-XXX",
        title="Object Model Field Access Incorrect",
        severity=Severity.HIGH,
        category=IssueCategory.OBJECT_MODEL,
        problem_description="Field operation (iget/iput/sget/sput) produces wrong result",
        reproduction_steps=[
            "1. Create class with instance/static fields",
            "2. Allocate object and set field value via iput/sput",
            "3. Read field value via iget/sget",
            "4. Verify round-trip correctness"
        ],
        expected_behavior="Field value matches what was written",
        actual_behavior="Field value differs or is wrong type",
        aosp_source_file="dalvik/vm/oo/Object.h (Field.byteOffset calculation)",
        lessons_learned=[
            "Field offsets must account for superclass fields",
            "Wide fields (long/double) require 8-byte alignment",
            "Static fields stored in ClassObject, not instance"
        ]
    )


def get_api_bridge_debug_template() -> DebugSession:
    """Template for API bridge issues"""
    return DebugSession(
        session_id="APIBRIDGE-XXX",
        title="Android API Stub Behavior Mismatch",
        severity=Severity.MEDIUM,
        category=IssueCategory.API_BRIDGE,
        problem_description="API call to [CLASS.METHOD] does not match Android behavior",
        reproduction_steps=[
            "1. Invoke method through DalvikEngine",
            "2. Capture API call trace",
            "3. Compare stub output with real Android device",
            "4. Identify behavioral difference"
        ],
        expected_behavior="[Describe correct Android behavior]",
        actual_behavior="[Describe MiniAndroid stub behavior]",
        aosp_source_file="frameworks/base/core/java/[full/class/path].java",
        lessons_learned=[
            "Stubs should return sensible defaults, not crash",
            "Log stub invocations for visibility",
            "Document what stubs DON'T do yet"
        ]
    )


# ============================================================================
# AOSP REFERENCE LOOKUP HELPERS
# ============================================================================

AOSP_SOURCE_MAP = {
    # Opcode implementations
    "opcode_interpreter": {
        "dalvik_path": "dalvik/vm/Interp.c",
        "art_path": "art/runtime/interpreter/interpreter.cc",
        "description": "Main interpreter switch statement",
        "key_functions": ["dvmInterpret", "ExecuteImpl"],
        "usage": "When implementing new opcodes or fixing existing ones"
    },
    "opcode_assembly": {
        "dalvik_path": "dalvik/vm/mterp/",
        "art_path": "art/runtime/interpreter/mterp/",
        "description": "Assembly-optimized opcode implementations",
        "key_functions": ["op_[opcode_name]"],
        "usage": "For performance-critical opcode verification"
    },
    
    # DEX Format
    "dex_format": {
        "dalvik_path": "dalvik/libdex/DexFile.cpp",
        "art_path": "art/libdexfile/dex_file.cc",
        "description": "DEX file format structures and parsing",
        "key_functions": ["dexFileParse", "OpenDexFile"],
        "usage": "When fixing DEX parsing issues"
    },
    "dex_structures": {
        "dalvik_path": "dalvik/libdex/DexProto.h",
        "art_path": "art/libdexfile/dex_file_structs.h",
        "description": "DEX structure definitions (header, class_def, etc.)",
        "key_functions": ["DexHeader", "ClassDef", "CodeItem"],
        "usage": "When understanding DEX layout"
    },
    
    # Object Model
    "object_model": {
        "dalvik_path": "dalvik/vm/oo/Object.h",
        "art_path": "art/runtime/mirror/object.h",
        "description": "Runtime object representations",
        "key_functions": ["Object", "ClassObject", "ArrayObject"],
        "usage": "When implementing object allocation or field access"
    },
    "field_access": {
        "dalvik_path": "dalvik/vm/oo/Object.h (Field struct)",
        "art_path": "art/runtime/art_field.h (ArtField)",
        "description": "Field offset resolution and access",
        "key_functions": ["dvmResolveInstField", "ArtField::GetInstanceFieldValue"],
        "usage": "When implementing iget/iput/sget/sput"
    },
    
    # Class Loading
    "class_loader": {
        "dalvik_path": "dalvik/vm/Reflect.h",
        "art_path": "runtime/class_linker.h",
        "description": "Class loading and resolution",
        "key_functions": ["dvmFindClass", "ClassLinker::DefineClass"],
        "usage": "When fixing class resolution issues"
    },
    
    # Method Dispatch
    "method_dispatch": {
        "dalvik_path": "dalvik/vm/oo/Object.h (vtable)",
        "art_path": "art/runtime/art_method.h",
        "description": "Virtual method dispatch mechanism",
        "key_functions": ["dvmInvokeVirtual", "ArtMethod::Invoke"],
        "usage": "When implementing invoke-virtual/interface/super"
    }
}


def generate_aosp_lookup_guide(issue_type: str) -> Dict[str, Any]:
    """Generate AOSP reference lookup guide for specific issue type"""
    
    base_info = {
        "issue_type": issue_type,
        "lookup_timestamp": datetime.now().isoformat(),
        "protocol": "GOLDEN_DEBUG_RULE_6",
        "steps": []
    }
    
    if issue_type == "opcode":
        sources = [AOSP_SOURCE_MAP["opcode_interpreter"], AOSP_SOURCE_MAP["opcode_assembly"]]
        base_info["steps"] = [
            {
                "step": 1,
                "action": "Identify opcode name and format (e.g., iget vA, vB, @CCCC)",
                "purpose": "Know exactly what to search for"
            },
            {
                "step": 2,
                "action": f"Search in {sources[0]['dalvik_path']} for opcode handler",
                "purpose": "Find reference implementation"
            },
            {
                "step": 3,
                "action": "Compare operand extraction logic (register indices, literal values)",
                "purpose": "Identify where MiniAndroid differs"
            },
            {
                "step": 4,
                "action": "Verify side effects (register writes, exceptions, etc.)",
                "purpose": "Ensure complete behavior match"
            }
        ]
        base_info["primary_sources"] = sources
        
    elif issue_type == "parse":
        sources = [AOSP_SOURCE_MAP["dex_format"], AOSP_SOURCE_MAP["dex_structures"]]
        base_info["steps"] = [
            {
                "step": 1,
                "action": "Identify which DEX structure is misparsed (header, string_ids, class_def, etc.)",
                "purpose": "Narrow search scope"
            },
            {
                "step": 2,
                "action": f"Check structure definition in {sources[1]['dalvik_path']}",
                "purpose": "Understand correct layout"
            },
            {
                "step": 3,
                "action": f"Compare parsing code with {sources[0]['dalvik_path']}",
                "purpose": "Find parsing logic errors"
            },
            {
                "step": 4,
                "action": "Verify endianness handling (DEX is always little-endian)",
                "purpose": "Common source of parse bugs"
            }
        ]
        base_info["primary_sources"] = sources
        
    elif issue_type == "object_model":
        sources = [AOSP_SOURCE_MAP["object_model"], AOSP_SOURCE_MAP["field_access"]]
        base_info["steps"] = [
            {
                "step": 1,
                "action": "Determine if issue is allocation, field access, or type-related",
                "purpose": "Choose correct investigation path"
            },
            {
                "step": 2,
                "action": f"For field issues, check {sources[1]['dalvik_path']}",
                "purpose": "Understand offset calculation"
            },
            {
                "step": 3,
                "action": "Trace field resolution from DEX field_id to byte offset",
                "purpose": "Find where resolution fails"
            },
            {
                "step": 4,
                "action": "Verify inheritance chain includes superclass fields",
                "purpose": "Common omission in object models"
            }
        ]
        base_info["primary_sources"] = sources
        
    else:
        base_info["steps"] = [
            {"step": 1, "action": "Categorize issue type specifically", "purpose": "Enable targeted search"},
            {"step": 2, "action": "Search AOSP source for relevant component", "purpose": "Find reference"},
            {"step": 3, "action": "Compare behaviors systematically", "purpose": "Identify differences"},
            {"step": 4, "action": "Document differences before fixing", "purpose": "Preserve knowledge"}
        ]
        base_info["primary_sources"] = list(AOSP_SOURCE_MAP.values())[:3]
    
    return base_info


# ============================================================================
# DEBUG CHECKLIST GENERATOR
# ============================================================================

def generate_debug_checklist(session_type: str) -> Dict[str, List[str]]:
    """Generate pre-debug checklist based on issue type"""
    
    checklists = {
        "opcode_issue": {
            "before_changing_code": [
                "☐ Captured full instruction trace showing failure",
                "☐ Identified exact opcode hex value causing issue",
                "☐ Recorded PC (program counter) at time of failure",
                "☐ Dumped register state before and after opcode",
                "☐ Verified bytecode is valid (not corrupted)",
                "☐ Checked opcode format matches documentation",
                "☐ Searched AOSP Interp.c for reference implementation",
                "☐ Compared operand decoding with AOSP",
                "☐ Documented hypothesis about root cause",
                "☐ Created minimal reproducer DEX if possible"
            ],
            "after_fix": [
                "☐ Fix solves original issue without breaking others",
                "☐ All existing tests still pass",
                "☐ Added specific test for this opcode case",
                "☐ Updated opcode coverage tracking",
                "☐ Documented fix in commit message",
                "☐ Updated CHANGELOG if user-visible"
            ]
        },
        "parse_issue": {
            "before_changing_code": [
                "☐ Captured raw DEX bytes around error location",
                "☐ Identified which DEX section has the problem",
                "☐ Verified DEX magic number is valid",
                "☐ Checked endianness of all multi-byte reads",
                "☐ Compared parsed values with `dexdump` output",
                "☐ Reviewed DEX format specification for structure",
                "☐ Searched AOSP DexFile.cpp for parsing logic",
                "☐ Validated string pool can be read correctly",
                "☐ Documented offset where parsing diverges",
                "☐ Tested with multiple DEX files (not just one)"
            ],
            "after_fix": [
                "☐ Parser handles edge cases (empty tables, max values)",
                "☐ No buffer overflows on malformed input",
                "☐ Error messages are informative",
                "☐ Existing DEX files still parse correctly",
                "☐ Added unit test for previously-failing case"
            ]
        },
        "object_model_issue": {
            "before_changing_code": [
                "☐ Identified exact field/method causing problem",
                "☐ Traced object allocation path",
                "☐ Verified class metadata loaded correctly",
                "☐ Checked field offset calculation",
                "☐ Confirmed object ID is valid (not freed/null)",
                "☐ Compared with AOSP Object.h field layout",
                "☐ Tested static vs instance field distinction",
                "☐ Verified wide field (long/double) handling",
                "☐ Checked inheritance chain completeness",
                "☐ Documented expected vs actual memory layout"
            ],
            "after_fix": [
                "☐ Field read/write round-trip works correctly",
                "☐ Multiple objects of same class independent",
                "☐ Static fields shared across instances",
                "☐ No memory leaks from object allocation",
                "☐ Added object model unit tests"
            ]
        },
        "general": {
            "always": [
                "☐ Issue reproducible (not one-time flake)",
                "☐ Evidence collected BEFORE code changes",
                "☐ Root cause identified (not just symptom fixed)",
                "☐ Fix is minimal (no unnecessary changes)",
                "☐ Changes don't break existing functionality",
                "☐ Tests added for the specific issue",
                "☐ Documentation updated",
                "☐ Commit message explains 'why' not just 'what'"
            ]
        }
    }
    
    return checklists.get(session_type, checklists["general"])


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_phase6_report(debug_templates: Dict, 
                          aosp_map: Dict,
                          checklists: Dict) -> Dict:
    """Generate comprehensive Phase 6 report"""
    
    report = {
        "phase": "PHASE_6_DEBUG_PROCESS_IMPROVEMENT",
        "timestamp": datetime.now().isoformat(),
        "status": "CREATED",  # Rule 3: Created ≠ Validated
        
        "golden_debug_protocol": {
            "name": "Golden Debug Protocol",
            "purpose": "Standardized debugging workflow ensuring evidence-based fixes",
            "phases": [
                {
                    "phase": DebugPhase.EVIDENCE_COLLECTION.value,
                    "name": "Evidence Collection",
                    "description": "Collect logs, traces, dumps, and reproduction cases BEFORE changing code",
                    "rule_reference": "RULE 4.1",
                    "mandatory_artifacts": ["instruction_trace.json", "register_dump.json", "error_log.txt"]
                },
                {
                    "phase": DebugPhase.HYPOTHESIS_FORMATION.value,
                    "name": "Hypothesis Formation",
                    "description": "Form clear hypothesis about root cause",
                    "rule_reference": "RULE 4.3",
                    "output": "DebugHypothesis record with status tracking"
                },
                {
                    "phase": DebugPhase.AOSP_REFERENCE_CHECK.value,
                    "name": "AOSP Reference Check",
                    "description": "Consult AOSP source code to understand correct behavior",
                    "rule_reference": "RULE 6",
                    "output": "Reference comparison document"
                },
                {
                    "phase": DebugPhase.ROOT_CAUSE_IDENTIFICATION.value,
                    "name": "Root Cause Identification",
                    "description": "Identify actual cause, not just symptom",
                    "rule_reference": "RULE 4.2",
                    "output": "Root cause description with evidence"
                },
                {
                    "phase": DebugPhase.FIX_IMPLEMENTATION.value,
                    "name": "Fix Implementation",
                    "description": "Implement minimal fix addressing root cause",
                    "rule_reference": "Best Practice",
                    "output": "Code changes with clear commit message"
                },
                {
                    "phase": DebugPhase.REGRESSION_TESTING.value,
                    "name": "Regression Testing",
                    "description": "Verify fix doesn't break existing functionality",
                    "rule_reference": "RULE 4.2",
                    "output": "Test results showing pass/fail"
                },
                {
                    "phase": DebugPhase.DOCUMENTATION.value,
                    "name": "Documentation",
                    "description": "Document findings, lessons learned, prevention measures",
                    "rule_reference": "RULE 5",
                    "output": "Updated experiment docs + worklog"
                }
            ]
        },
        
        "debug_templates": {
            "count": len(debug_templates),
            "types": list(debug_templates.keys()),
            "templates": {k: v.to_dict() for k, v in debug_templates.items()}
        },
        
        "aosp_reference_map": {
            "total_components": len(aosp_map),
            "components": {k: {"paths": [v.get("dalvik_path", ""), v.get("art_path", "")], 
                             "description": v.get("description", "")} 
                         for k, v in aosp_map.items()}
        },
        
        "debug_checklists": checklists,
        
        "implementation_status": {
            "protocol_documented": True,
            "templates_created": True,
            "checklists_available": True,
            "integration_needed": "Integrate into development workflow",
            "training_needed": "Team members must follow protocol"
        },
        
        "next_steps": [
            "Create new DebugSession for each bug using templates",
            "Follow phases sequentially (no skipping!)",
            "Store completed sessions in experiments/ directory",
            "Review sessions in team meetings for pattern detection",
            "Update templates based on lessons learned"
        ]
    }
    
    return report


def generate_markdown_report(report: Dict) -> str:
    """Generate human-readable markdown report"""
    
    md = f"""# EXP-032 Phase 6: Debug Process Improvement

**Generated**: {report['timestamp']}
**Status**: {report['status']}
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

"""

    for phase_data in report['golden_debug_protocol']['phases']:
        md += f"""### {phase_data['phase'].upper().replace('_', ' ')}: {phase_data['name']}

**Rule Reference**: {phase_data['rule_reference']}

{phase_data['description']}

**Required Output**: {phase_data.get('mandatory_artifacts', phase_data.get('output', 'N/A'))}

---

"""

    md += f"""## Debug Templates

Use these templates when creating new debug sessions:

| Template | For | Severity |
|----------|-----|----------|
"""

    template_descriptions = {
        "opcode": "Opcode implementation bugs",
        "parse": "DEX parsing errors", 
        "object_model": "Object model / field access issues",
        "api_bridge": "Android API stub behavior"
    }

    for tname, desc in template_descriptions.items():
        md += f"| `{tname.capitalize()} Template` | {desc} | HIGH |\n"

    md += f"""
## AOSP Reference Quick Guide

| Component | Dalvik Source | ART Source | Usage |
|-----------|---------------|------------|-------|
"""


    for comp_name, comp_data in report['aosp_reference_map']['components'].items():
        paths = comp_data.get('paths', [])
        dalvik_path = paths[0] if paths and len(paths) > 0 else "N/A"
        art_path = paths[1] if len(paths) > 1 else "N/A"
        desc = comp_data.get('description', 'N/A')
        display_name = comp_name.replace('_', ' ').title()
        row = "| " + display_name + " | `" + dalvik_path + "` | `" + art_path + "` | " + desc + " |"
        md += row + "\n"


    md += f"""
## Debug Checklists

### Before Changing Code (MANDATORY)

"""

    general_checklist = report['debug_checklists'].get('general', {}).get('always', [])
    for item in general_checklist:
        md += f"{item}\n"

    md += f"""
### Opcode-Specific Checklist

"""
    opcode_checklist = report['debug_checklists'].get('opcode_issue', {}).get('before_changing_code', [])
    for item in opcode_checklist[:5]:  # Show first 5
        md += f"{item}\n"
    md += "... (see full checklist in JSON)\n"

    md += f"""
## Implementation Status

| Item | Status |
|------|--------|
| Protocol Documented | {'✅' if report['implementation_status']['protocol_documented'] else '❌'} |
| Templates Created | {'✅' if report['implementation_status']['templates_created'] else '❌'} |
| Checklists Available | {'✅' if report['implementation_status']['checklists_available'] else '❌'} |

### Next Steps

"""

    for step in report['next_steps']:
        md += f"- [ ] {step}\n"

    md += f"""
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
"""
    
    return md


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 80)
    print("EXP-032 PHASE 6: DEBUG PROCESS IMPROVEMENT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Step 1: Create debug templates
    print("[1/4] Creating debug templates...")
    templates = {
        "opcode": get_opcode_debug_template(),
        "parse": get_parse_debug_template(),
        "object_model": get_object_model_debug_template(),
        "api_bridge": get_api_bridge_debug_template()
    }
    print(f"      Created {len(templates)} templates")
    
    # Step 2: Prepare AOSP reference map
    print("\n[2/4] Preparing AOSP reference map...")
    print(f"      Mapped {len(AOSP_SOURCE_MAP)} components")
    
    # Step 3: Generate checklists
    print("\n[3/4] Generating debug checklists...")
    checklists = {}
    for ctype in ["opcode_issue", "parse_issue", "object_model_issue", "general"]:
        checklists[ctype] = generate_debug_checklist(ctype)
    print(f"      Generated {len(checklists)} checklist types")
    
    # Step 4: Generate report
    print("\n[4/4] Generating report...")
    report = generate_phase6_report(templates, AOSP_SOURCE_MAP, checklists)
    
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
    print("PHASE 6 COMPLETE SUMMARY")
    print("=" * 80)
    print(f"Status: {report['status']}")
    print(f"Protocol Phases: {len(report['golden_debug_protocol']['phases'])}")
    print(f"Debug Templates: {report['debug_templates']['count']}")
    print(f"AOSP Components: {report['aosp_reference_map']['total_components']}")
    print()
    print("Key Output: Golden Debug Protocol now MANDATORY for all debugging")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    main()
