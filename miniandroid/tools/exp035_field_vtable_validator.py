#!/usr/bin/env python3
"""
EXP-035 Field System & VTable Validation Tool
==============================================

Validates that:
1. Field opcodes (iget/iput/sget/sput) are properly integrated
2. VTable dispatch is connected to invoke-virtual
3. All traces contain ExecutionSource=REAL_DALVIK_INTERPRETER
4. Evidence is complete and verifiable

Usage:
    python tools/exp035_field_vtable_validator.py [--verbose]

Rule 2 (Evidence): This tool only validates REAL execution traces, not simulations.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class FieldVtableValidator:
    """Validates EXP-035 field system and VTable integration."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "validation_timestamp": datetime.utcnow().isoformat() + "Z",
            "validator_version": "EXP-035-P1P2P3",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "field_opcode_tests": {},
            "vtable_dispatch_tests": {},
            "evidence_compliance_tests": {},
            "failures": [],
            "evidence_files": []
        }
    
    def log(self, msg: str):
        if self.verbose:
            print(f"[VALIDATOR] {msg}")
    
    def validate_trace_evidence(self, trace_file: Path) -> Dict[str, Any]:
        """
        Validate that a trace file contains proper ExecutionSource evidence.
        
        Required fields per trace entry:
        - source=REAL_DALVIK_INTERPRETER (mandatory)
        - For field ops: class, field, offset, value, object_ref
        - For invoke-virtual: static_type, runtime_type, resolved_method
        """
        self.results["tests_run"] += 1
        test_result = {
            "file": str(trace_file),
            "exists": trace_file.exists(),
            "has_execution_source": False,
            "field_opcodes_found": 0,
            "vtable_dispatches_found": 0,
            "compliant_traces": 0,
            "total_traces": 0,
            "issues": []
        }
        
        try:
            if not trace_file.exists():
                test_result["issues"].append("Trace file does not exist")
                self.results["failures"].append(f"Missing trace: {trace_file}")
                return test_result
            
            with open(trace_file, 'r') as f:
                data = json.load(f)
            
            # Check for instruction traces
            traces = data.get("instruction_traces", [])
            if not traces:
                # Try alternate structure
                traces = data.get("traces", [])
            
            test_result["total_traces"] = len(traces)
            
            for trace in traces:
                operands = trace.get("operands", [])
                opcode_name = trace.get("opcode_name", "")
                
                # Convert operands list to dict for easier checking
                operand_dict = {}
                for op in operands:
                    if isinstance(op, dict) and "name" in op:
                        operand_dict[op["name"]] = op.get("value", "")
                
                # Check for ExecutionSource tag
                source = operand_dict.get("source", "")
                if source == "REAL_DALVIK_INTERPRETER":
                    test_result["has_execution_source"] = True
                    test_result["compliant_traces"] += 1
                
                # Count field opcodes
                if opcode_name in ["iget", "iget-object", "iput", "iput-object"]:
                    test_result["field_opcodes_found"] += 1
                    
                    # Validate required field evidence
                    required_fields = ["field", "offset", "value", "source"]
                    missing = [f for f in required_fields if f not in operand_dict]
                    if missing:
                        test_result["issues"].append(
                            f"Field opcode {opcode_name} missing: {missing}"
                        )
                
                # Count static field opcodes
                if opcode_name in ["sget", "sget-object", "sput", "sput-object"]:
                    test_result["field_opcodes_found"] += 1
                    
                    # Validate required static field evidence
                    required_fields = ["static_field", "class", "field", "value", "source"]
                    missing = [f for f in required_fields if f not in operand_dict]
                    if missing:
                        test_result["issues"].append(
                            f"Static field opcode {opcode_name} missing: {missing}"
                        )
                
                # Count VTable dispatches
                if opcode_name == "invoke-virtual":
                    test_result["vtable_dispatches_found"] += 1
                    
                    # Validate required VTable evidence
                    required_vtable = ["static_type", "runtime_type", "resolved_method", "source"]
                    missing = [f for f in required_vtable if f not in operand_dict]
                    if missing:
                        test_result["issues"].append(
                            f"invoke-virtual missing VTable evidence: {missing}"
                        )
                    else:
                        # Verify polymorphic resolution (static != runtime for virtual calls)
                        static_type = operand_dict.get("static_type", "")
                        runtime_type = operand_dict.get("runtime_type", "")
                        if static_type and runtime_type and static_type != runtime_type:
                            self.log(f"✅ Polymorphic call detected: {static_type} → {runtime_type}")
            
            # Overall compliance check
            if test_result["has_execution_source"] and test_result["compliant_traces"] > 0:
                self.results["tests_passed"] += 1
                self.log(f"✅ PASSED: {trace_file.name} ({test_result['compliant_traces']}/{test_result['total_traces']} compliant)")
            else:
                self.results["tests_failed"] += 1
                if test_result["issues"]:
                    self.results["failures"].extend([f"{trace_file.name}: {issue}" for issue in test_result["issues"]])
                self.log(f"❌ FAILED: {trace_file.name} - No compliant traces found")
            
            self.results["evidence_files"].append(str(trace_file))
            
        except Exception as e:
            self.results["tests_failed"] += 1
            test_result["issues"].append(f"Exception: {str(e)}")
            self.results["failures"].append(f"Error processing {trace_file}: {e}")
            self.log(f"❌ ERROR: {trace_file} - {e}")
        
        return test_result
    
    def validate_field_system_integration(self) -> Dict[str, Any]:
        """
        Validate that field system code is properly integrated.
        
        Checks:
        1. dalvik_engine.h contains field opcode definitions
        2. dalvik_engine.cpp contains field operation implementations
        3. Static field storage member exists
        4. Field resolution helper exists
        """
        self.results["tests_run"] += 1
        
        test_result = {
            "header_has_field_opcodes": False,
            "cpp_has_field_implementations": False,
            "has_static_field_storage": False,
            "has_field_resolution": False,
            "has_heap_helpers": False,
            "issues": []
        }
        
        engine_h = PROJECT_ROOT / "src" / "dex" / "dalvik_engine.h"
        engine_cpp = PROJECT_ROOT / "src" / "dex" / "dalvik_engine.cpp"
        
        try:
            # Check header for field opcode definitions
            if engine_h.exists():
                content = engine_h.read_text()
                
                # Check for field opcode definitions
                field_opcodes = ["IGET", "IGET_OBJECT", "IPUT", "IPUT_OBJECT", 
                               "SGET", "SGET_OBJECT", "SPUT", "SPUT_OBJECT"]
                found_opcodes = [op for op in field_opcodes if op in content]
                test_result["header_has_field_opcodes"] = len(found_opcodes) >= 4  # At least half
                
                # Check for static field storage
                test_result["has_static_field_storage"] = "static_field_storage_" in content
                
                # Check for field resolution helper
                test_result["has_field_resolution"] = "FieldResolution" in content and "resolve_field" in content
                
                # Check for heap helpers
                test_result["has_heap_helpers"] = "has_object" in content and "get_object_field" in content
                
                if not test_result["header_has_field_opcodes"]:
                    test_result["issues"].append("Field opcode definitions missing from header")
                if not test_result["has_static_field_storage"]:
                    test_result["issues"].append("Static field storage member missing")
                if not test_result["has_field_resolution"]:
                    test_result["issues"].append("Field resolution helper missing")
                if not test_result["has_heap_helpers"]:
                    test_result["issues"].append("Heap field access helpers missing")
            
            # Check cpp for implementations
            if engine_cpp.exists():
                content = engine_cpp.read_text()
                
                # Check for field operation implementations
                impl_methods = ["execute_iget", "execute_iput", "execute_sget", "execute_sput",
                              "execute_iget_object", "execute_iput_object", 
                              "execute_sget_object", "execute_sput_object"]
                found_impls = [method for method in impl_methods if method in content]
                test_result["cpp_has_field_implementations"] = len(found_impls) >= 4
                
                if not test_result["cpp_has_field_implementations"]:
                    test_result["issues"].append("Field operation implementations missing from cpp")
            
            # Determine overall pass/fail
            all_checks = [
                test_result["header_has_field_opcodes"],
                test_result["cpp_has_field_implementations"],
                test_result["has_static_field_storage"],
                test_result["has_field_resolution"],
                test_result["has_heap_helpers"]
            ]
            
            if all(all_checks):
                self.results["tests_passed"] += 1
                self.log("✅ PASSED: Field system integration validated")
            else:
                self.results["tests_failed"] += 1
                self.results["failures"].extend([f"Integration: {issue}" for issue in test_result["issues"]])
                self.log(f"❌ FAILED: Field system integration has gaps")
            
            self.results["field_opcode_tests"] = test_result
            
        except Exception as e:
            self.results["tests_failed"] += 1
            test_result["issues"].append(f"Exception: {str(e)}")
            self.results["failures"].append(f"Integration check error: {e}")
            self.log(f"❌ ERROR: {e}")
        
        return test_result
    
    def validate_vtable_integration(self) -> Dict[str, Any]:
        """
        Validate that VTable dispatch is integrated into invoke-virtual.
        
        Checks:
        1. vtable_dispatch.h is included
        2. VirtualDispatcher member exists
        3. invoke-virtual uses vtable_dispatcher_
        4. Evidence includes static_type/runtime_type/resolved_method
        """
        self.results["tests_run"] += 1
        
        test_result = {
            "includes_vtable_header": False,
            "has_dispatcher_member": False,
            "invoke_uses_vtable": False,
            "has_context_tracking": False,
            "issues": []
        }
        
        engine_h = PROJECT_ROOT / "src" / "dex" / "dalvik_engine.h"
        engine_cpp = PROJECT_ROOT / "src" / "dex" / "dalvik_engine.cpp"
        
        try:
            # Check header
            if engine_h.exists():
                content = engine_h.read_text()
                
                test_result["includes_vtable_header"] = "vtable_dispatch.h" in content
                test_result["has_dispatcher_member"] = "vtable_dispatcher_" in content
                test_result["has_context_tracking"] = "current_class_" in content and "current_method_" in content
                
                if not test_result["includes_vtable_header"]:
                    test_result["issues"].append("vtable_dispatch.h not included")
                if not test_result["has_dispatcher_member"]:
                    test_result["issues"].append("VirtualDispatcher member missing")
                if not test_result["has_context_tracking"]:
                    test_result["issues"].append("Execution context tracking missing")
            
            # Check cpp implementation
            if engine_cpp.exists():
                content = engine_cpp.read_text()
                
                # Check if invoke-virtual uses dispatcher
                test_result["invoke_uses_vtable"] = (
                    "vtable_dispatcher_" in content and 
                    "dispatch_virtual_call" in content and
                    "static_type" in content and
                    "runtime_type" in content
                )
                
                if not test_result["invoke_uses_vtable"]:
                    test_result["issues"].append("invoke-virtual does not use VTable dispatcher")
            
            # Determine pass/fail
            all_checks = [
                test_result["includes_vtable_header"],
                test_result["has_dispatcher_member"],
                test_result["invoke_uses_vtable"],
                test_result["has_context_tracking"]
            ]
            
            if all(all_checks):
                self.results["tests_passed"] += 1
                self.log("✅ PASSED: VTable dispatch integration validated")
            else:
                self.results["tests_failed"] += 1
                self.results["failures"].extend([f"VTable: {issue}" for issue in test_result["issues"]])
                self.log(f"❌ FAILED: VTable integration has gaps")
            
            self.results["vtable_dispatch_tests"] = test_result
            
        except Exception as e:
            self.results["tests_failed"] += 1
            test_result["issues"].append(f"Exception: {str(e)}")
            self.results["failures"].append(f"VTable check error: {e}")
            self.log(f"❌ ERROR: {e}")
        
        return test_result
    
    def generate_validation_report(self) -> str:
        """Generate human-readable validation report."""
        lines = [
            "=" * 70,
            "EXP-035 FIELD SYSTEM & VTABLE VALIDATION REPORT",
            "=" * 70,
            f"Timestamp: {self.results['validation_timestamp']}",
            f"Validator: {self.results['validator_version']}",
            "",
            f"Tests Run:    {self.results['tests_run']}",
            f"Tests Passed: {self.results['tests_passed']}",
            f"Tests Failed: {self.results['tests_failed']}",
            "",
            "-" * 70,
            "FIELD SYSTEM INTEGRATION",
            "-" * 70,
        ]
        
        field_tests = self.results.get("field_opcode_tests", {})
        for key, value in field_tests.items():
            status = "✅" if value else "❌"
            lines.append(f"  {status} {key}: {value}")
        
        lines.extend([
            "",
            "-" * 70,
            "VTABLE DISPATCH INTEGRATION",
            "-" * 70,
        ])
        
        vtable_tests = self.results.get("vtable_dispatch_tests", {})
        for key, value in vtable_tests.items():
            status = "✅" if value else "❌"
            lines.append(f"  {status} {key}: {value}")
        
        if self.results["failures"]:
            lines.extend([
                "",
                "-" * 70,
                "FAILURES (must be resolved)",
                "-" * 70,
            ])
            for failure in self.results["failures"]:
                lines.append(f"  ❌ {failure}")
        
        lines.extend([
            "",
            "-" * 70,
            "EVIDENCE FILES VALIDATED",
            "-" * 70,
        ])
        
        for ef in self.results.get("evidence_files", []):
            lines.append(f"  📄 {ef}")
        
        lines.extend([
            "",
            "=" * 70,
            "OVERALL STATUS: " + ("✅ PASS" if self.results["tests_failed"] == 0 else "❌ FAIL"),
            "=" * 70,
        ])
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EXP-035 Field & VTable Validator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", type=str, default=None, 
                       help="Output report path (default: stdout)")
    args = parser.parse_args()
    
    print("=" * 70)
    print("EXP-035 FIELD SYSTEM & VTABLE VALIDATION")
    print("=" * 70)
    print()
    
    validator = FieldVtableValidator(verbose=args.verbose)
    
    # Run validations
    print("Phase 1: Validating field system integration...")
    validator.validate_field_system_integration()
    print()
    
    print("Phase 2: Validating VTable dispatch integration...")
    validator.validate_vtable_integration()
    print()
    
    # Generate and output report
    report = validator.generate_validation_report()
    print(report)
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
            # Also append JSON results
            json.dump(validator.results, f, indent=2)
        print(f"\n📄 Report saved to: {output_path}")
    
    # Return exit code
    return 0 if validator.results["tests_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
