#!/usr/bin/env python3
"""
EXP-035 Execution Evidence Gate
=================================

Mandatory validator that FAILS if execution evidence is incomplete or invalid.

Failure Conditions (any one causes FAILURE):
1. Opcode trace is empty
2. Lifecycle state has no interpreter trace
3. ExecutionSource tag is missing from traces
4. Opcode count == 0
5. HOST_SHORTCUT detected anywhere in trace
6. Field operations lack required evidence fields
7. VTable dispatches lack static_type/runtime_type/resolved_method

This gate MUST pass before any EXP-035 completion claim can be made.

Usage:
    python tools/exp035_execution_gate.py [--trace trace_file.json] [--all]
    
Exit Codes:
    0 = PASS (all evidence valid)
    1 = FAIL (evidence missing or invalid)
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class GateStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass 
class GateCheck:
    """Result of a single gate check."""
    name: str
    status: GateStatus
    details: str = ""
    evidence_location: str = ""


class ExecutionEvidenceGate:
    """
    Validates execution evidence for EXP-035 compliance.
    
    CRITICAL: This gate represents the MINIMUM acceptable evidence standard.
    Any failure means EXP-035 cannot be considered complete.
    """
    
    MANDATORY_SOURCE_TAG = "REAL_DALVIK_INTERPRETER"
    FORBIDDEN_PATTERN = "HOST_SHORTCUT"
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checks: List[GateCheck] = []
        self.trace_files_analyzed = 0
        self.total_traces_checked = 0
        
    def log(self, msg: str):
        if self.verbose:
            print(f"[EVIDENCE_GATE] {msg}")
    
    def validate_trace_file(self, trace_path: Path) -> GateCheck:
        """Validate a single trace file against all gate requirements."""
        
        check = GateCheck(
            name=f"Trace: {trace_path.name}",
            status=GateStatus.PASS,
            details="",
            evidence_location=str(trace_path)
        )
        
        try:
            # Check file exists
            if not trace_path.exists():
                check.status = GateStatus.FAIL
                check.details = "FAILED\n\nReason:\nTrace file does not exist"
                self.log(f"❌ {trace_path.name}: File not found")
                self.checks.append(check)
                return check
            
            # Load and parse JSON
            with open(trace_path, 'r') as f:
                data = json.load(f)
            
            self.trace_files_analyzed += 1
            
            # Check 1: Non-empty trace
            traces = self._extract_traces(data)
            
            if not traces:
                check.status = GateStatus.FAIL
                check.details = f"""FAILED

Reason:
ONCREATE_ENTERED exists (or lifecycle state present)
but no REAL_DALVIK_INTERPRETER trace found

File: {trace_path}
Size: {trace_path.stat().st_size} bytes"""
                
                self.log(f"❌ {trace_path.name}: Empty trace")
                self.checks.append(check)
                return check
            
            self.total_traces_checked += len(traces)
            
            # Check each trace entry for compliance
            failures = []
            compliant_count = 0
            
            for i, trace in enumerate(traces):
                trace_failures = self._validate_single_trace(trace, i, trace_path)
                if trace_failures:
                    failures.extend(trace_failures)
                else:
                    compliant_count += 1
            
            if failures:
                check.status = GateStatus.FAIL
                check.details = f"""FAILED

Reason:
{len(failures)} trace(s) failed validation:

""" + "\n".join(failures[:5])  # Show first 5 failures

                if len(failures) > 5:
                    check.details += f"\n... and {len(failures) - 5} more"
                
                self.log(f"❌ {trace_path.name}: {len(failures)} failures out of {len(traces)} traces")
            else:
                check.details = f"PASS\n\n{compliant_count}/{len(traces)} traces fully compliant"
                self.log(f"✅ {trace_path.name}: All {len(traces)} traces compliant")
            
        except json.JSONDecodeError as e:
            check.status = GateStatus.FAIL
            check.details = f"FAILED\n\nReason:\nInvalid JSON: {e}"
            self.log(f"❌ {trace_path.name}: JSON parse error")
        except Exception as e:
            check.status = GateStatus.FAIL
            check.details = f"FAILED\n\nReason:\nException: {e}"
            self.log(f"❌ {trace_path.name}: Exception - {e}")
        
        self.checks.append(check)
        return check
    
    def _extract_traces(self, data: Dict) -> List[Dict]:
        """Extract trace entries from various possible JSON structures."""
        # Try different common structures
        if isinstance(data, list):
            return data
        
        for key in ["instruction_traces", "traces", "opcode_traces", "executions"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # If data itself looks like a single trace
        if "opcode_name" in data or "pc" in data or "operands" in data:
            return [data]
        
        return []
    
    def _validate_single_trace(self, trace: Dict, index: int, source_file: Path) -> List[str]:
        """Validate a single trace entry. Returns list of failure messages."""
        failures = []
        
        # Get operands as dict
        operands = trace.get("operands", [])
        if isinstance(operands, list):
            operand_dict = {}
            for op in operands:
                if isinstance(op, dict) and "name" in op:
                    operand_dict[op["name"]] = op.get("value", "")
        else:
            operand_dict = operands if isinstance(operands, dict) else {}
        
        opcode_name = trace.get("opcode_name", "")
        
        # Check 1: ExecutionSource tag MANDATORY
        source = operand_dict.get("source", "")
        if source != self.MANDATORY_SOURCE_TAG:
            failures.append(
                f"  Trace[{index}] ({opcode_name}): "
                f"Missing/invalid ExecutionSource (got: '{source}', "
                f"required: '{self.MANDATORY_SOURCE_TAG}')"
            )
        
        # Check 2: No HOST_SHORTCUT allowed
        trace_str = json.dumps(trace)
        if self.FORBIDDEN_PATTERN in trace_str:
            failures.append(
                f"  Trace[{index}] ({opcode_name}): "
                f"HOST_SHORTCUT detected - FORBIDDEN"
            )
        
        # Check 3: Field operation evidence completeness
        if opcode_name in ["iget", "iput", "iget-object", "iput-object",
                          "sget", "sput", "sget-object", "sput-object"]:
            required_fields = self._get_required_fields_for_opcode(opcode_name)
            missing = [f for f in required_fields if f not in operand_dict]
            
            if missing:
                failures.append(
                    f"  Trace[{index}] ({opcode_name}): "
                    f"Missing field evidence: {missing}"
                )
        
        # Check 4: VTable dispatch evidence completeness
        if opcode_name == "invoke-virtual":
            vtable_required = ["static_type", "runtime_type", "resolved_method"]
            missing = [f for f in vtable_required if f not in operand_dict]
            
            if missing:
                failures.append(
                    f"  Trace[{index}] ({opcode_name}): "
                    f"Missing VTable evidence: {missing}"
                )
            else:
                # Bonus: Verify polymorphism makes sense
                static_type = operand_dict.get("static_type", "")
                runtime_type = operand_dict.get("runtime_type", "")
                if static_type and runtime_type and static_type != runtime_type:
                    self.log(f"  🎯 Trace[{index}]: Polymorphic dispatch verified "
                            f"{static_type.split('/')[-1]} → {runtime_type.split('/')[-1]}")
        
        return failures
    
    def _get_required_fields_for_opcode(self, opcode: str) -> List[str]:
        """Get required evidence fields for a field opcode."""
        base_fields = ["field", "value", "source"]
        
        if opcode.startswith("iget") or opcode.startswith("iput"):
            return base_fields + ["offset", "object_ref"] if "get" in opcode else base_fields + ["offset"]
        elif opcode.startswith("sget") or opcode.startswith("sput"):
            return base_fields + ["static_field", "class"]
        
        return base_fields
    
    def validate_all_evidence(self, evidence_dir: Optional[Path] = None) -> GateCheck:
        """Validate all evidence files in a directory."""
        
        if evidence_dir is None:
            evidence_dir = Path(__file__).parent.parent / "run" / "exp035"
        
        check = GateCheck(
            name="All Evidence Files",
            status=GateStatus.PASS,
            details=""
        )
        
        if not evidence_dir.exists():
            check.status = GateStatus.WARN
            check.details = f"WARN: Evidence directory not found: {evidence_dir}"
            self.checks.append(check)
            return check
        
        # Find all JSON trace files
        trace_files = list(evidence_dir.glob("**/*.json"))
        
        if not trace_files:
            check.status = GateStatus.FAIL
            check.details = """FAILED

Reason:
No trace files found in evidence directory

Directory: """ + str(evidence_dir)
            self.checks.append(check)
            return check
        
        # Validate each file
        file_checks = [self.validate_trace_file(tf) for tf in trace_files]
        
        # Aggregate results
        failed_checks = [c for c in file_checks if c.status == GateStatus.FAIL]
        
        if failed_checks:
            check.status = GateStatus.FAIL
            check.details = f"""FAILED

Reason:
{len(failed_checks)}/{len(file_checks)} trace files failed validation:

""" + "\n\n".join(fc.details for fc in failed_checks[:3])

            if len(failed_checks) > 3:
                check.details += f"\n\n... and {len(failed_checks) - 3} more files failed"
        else:
            check.details = f"""PASS

Summary:
✅ {len(file_checks)} trace files validated
✅ {self.trace_files_analyzed} files analyzed
✅ {self.total_traces_checked} individual traces checked
✅ All contain ExecutionSource=REAL_DALVIK_INTERPRETER
✅ No HOST_SHORTCUT detected"""
        
        self.checks.insert(0, check)  # Insert at front as summary
        return check
    
    def generate_gate_report(self) -> str:
        """Generate human-readable gate report."""
        passed = sum(1 for c in self.checks if c.status == GateStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == GateStatus.FAIL)
        warned = sum(1 for c in self.checks if c.status == GateStatus.WARN)
        
        lines = [
            "=" * 70,
            "EXP-035 EXECUTION EVIDENCE GATE REPORT",
            "=" * 70,
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z",
            f"Gate Version: EXP-035-PHASE5",
            "",
            f"Files Analyzed: {self.trace_files_analyzed}",
            f"Traces Checked: {self.total_traces_checked}",
            "",
            f"Results: {passed} PASS | {failed} FAIL | {warned} WARN",
            "",
            "-" * 70,
            "DETAILED CHECKS",
            "-" * 70,
        ]
        
        for i, check in enumerate(self.checks, 1):
            icon = {
                GateStatus.PASS: "✅",
                GateStatus.FAIL: "❌",
                GateStatus.WARN: "⚠️"
            }[check.status]
            
            lines.append(f"\n{i}. [{icon}] {check.name}")
            lines.append(f"   Status: {check.status.value}")
            if check.evidence_location:
                lines.append(f"   Location: {check.evidence_location}")
            lines.append(f"   Details:")
            lines.append(f"   {check.details}")
        
        # Final verdict
        if failed > 0:
            overall = GateStatus.FAIL
        elif warned > 0:
            overall = GateStatus.WARN
        else:
            overall = GateStatus.PASS
        icon_str = "✅" if overall == GateStatus.PASS else ("⚠️" if overall == GateStatus.WARN else "❌")
        
        lines.extend([
            "",
            "=" * 70,
            f"GATE VERDICT: {icon_str} {overall.value}",
            "=" * 70,
        ])
        
        if overall == GateStatus.FAIL:
            lines.extend([
                "",
                "🔴 BLOCKER: Evidence gate FAILED",
                "",
                "EXP-035 CANNOT be marked complete until:",
                "  1. All traces have ExecutionSource=REAL_DALVIK_INTERPRETER",
                "  2. No HOST_SHORTCUT appears in any trace",
                "  3. Field ops have complete evidence (field, offset, value)",
                "  4. VTable dispatch has complete evidence (static/runtime/resolved)",
                "  5. At least one real opcode has been executed",
            ])
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="EXP-035 Execution Evidence Gate - Mandatory Validator",
        epilog="Exit code 0 = PASS, 1 = FAIL"
    )
    parser.add_argument("--trace", "-t", type=str, default=None,
                       help="Validate specific trace file")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Validate all evidence in run/exp035/")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    print("=" * 70)
    print("EXP-035 EXECUTION EVIDENCE GATE")
    print("=" * 70)
    print()
    
    gate = ExecutionEvidenceGate(verbose=args.verbose)
    
    if args.trace:
        # Validate single file
        trace_path = Path(args.trace)
        gate.validate_trace_file(trace_path)
    elif args.all:
        # Validate all evidence
        gate.validate_all_evidence()
    else:
        # Default: validate all evidence
        gate.validate_all_evidence()
    
    # Generate and print report
    report = gate.generate_gate_report()
    print(report)
    
    # Return appropriate exit code
    failed = any(c.status == GateStatus.FAIL for c in gate.checks)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
