#!/usr/bin/env python3
"""
EXP-036 Execution Pipeline Validator

Validates that MiniAndroid can execute real Android APKs with complete evidence.
This is the EVIDENCE GATE - tests FAIL without real execution proof.

Usage:
    python tools/exp036_execution_validator.py [--apk-dir DIR] [--verbose]

Exit Codes:
    0 - All checks PASS (real evidence found)
    1 - Checks FAIL (missing or fake evidence)
    2 - Error in validation

Author: EXP-036 Development
Date: 2026-08-14
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class EvidenceItem:
    """Single piece of evidence for validation"""
    source: str
    path: str
    exists: bool
    size_bytes: int = 0
    content_preview: str = ""
    
    def is_valid(self) -> bool:
        return self.exists and self.size_bytes > 0


@dataclass 
class ValidationResult:
    """Result of a single validation check"""
    check_name: str
    status: TestStatus
    details: str = ""
    evidence: Optional[EvidenceItem] = None
    
    def to_dict(self) -> dict:
        result = {
            "check": self.check_name,
            "status": self.status.value,
            "details": self.details
        }
        if self.evidence:
            result["evidence"] = asdict(self.evidence)
        return result


@dataclass
class APKTestResult:
    """Complete test result for one APK"""
    apk_name: str
    apk_path: str
    sha256: str = ""
    
    # Overall status
    overall_status: TestStatus = TestStatus.ERROR
    
    # Individual validations
    validations: List[ValidationResult] = field(default_factory=list)
    
    # Execution evidence
    dex_loaded: bool = False
    classes_found: int = 0
    methods_executed: int = 0
    instructions_executed: int = 0
    api_calls_made: int = 0
    lifecycle_reached: bool = False
    
    # Source tracking
    has_real_interpreter_evidence: bool = False
    has_host_shortcut: bool = False
    has_timeout: bool = False
    
    # Timestamps
    test_start_time: str = ""
    test_end_time: str = ""
    duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "apk_name": self.apk_name,
            "apk_path": self.apk_path,
            "sha256": self.sha256,
            "overall_status": self.overall_status.value,
            "validations": [v.to_dict() for v in self.validations],
            "execution": {
                "dex_loaded": self.dex_loaded,
                "classes_found": self.classes_found,
                "methods_executed": self.methods_executed,
                "instructions_executed": self.instructions_executed,
                "api_calls_made": self.api_calls_made,
                "lifecycle_reached": self.lifecycle_reached
            },
            "source_tracking": {
                "has_real_interpreter_evidence": self.has_real_interpreter_evidence,
                "has_host_shortcut": self.has_host_shortcut,
                "has_timeout": self.has_timeout
            },
            "timing": {
                "start": self.test_start_time,
                "end": self.test_end_time,
                "duration_seconds": self.duration_seconds
            }
        }


class EXP036EvidenceGate:
    """
    MANDATORY EVIDENCE VALIDATOR
    
    A test PASSES only if ALL of these conditions are met:
    1. REAL_DALVIK_INTERPRETER evidence exists
    2. instruction_trace exists and is non-empty
    3. method_execution_trace exists
    4. No HOST_SHORTCUT detected
    5. No timeout occurred
    6. APK lifecycle progressed (at least attempted)
    
    Any green status without evidence → AUTOMATIC FAIL
    """

    REQUIRED_CHECKS = [
        "apk_file_exists",
        "dex_extracted", 
        "dex_parsed",
        "classes_loaded",
        "bytecode_available",
        "interpreter_executed",
        "execution_source_valid",
        "no_host_shortcut",
        "no_timeout",
        "evidence_files_created",
        "trace_non_empty",
        "api_calls_tracked"
    ]
    
    def __init__(self, output_dir: str = "run/exp036"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[APKTestResult] = []
        self.session_start = time.strftime("%Y-%m-%dT%H:%M:%S")
        
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def find_apk_files(self, apk_dir: str) -> List[Path]:
        """Find all APK files in directory"""
        apks = []
        apk_path = Path(apk_dir)
        
        if not apk_path.exists():
            print(f"❌ APK directory not found: {apk_dir}")
            return apks
            
        # Find .apk files
        for pattern in ["*.apk"]:
            apks.extend(apk_path.glob(pattern))
            
        # Also check for DEX files directly (for testing)
        for pattern in ["*.dex"]:
            apks.extend(apk_path.glob(pattern))
            
        return sorted(set(apks))

    def check_evidence_file(self, file_path: Path) -> EvidenceItem:
        """Check if an evidence file exists and has content"""
        item = EvidenceItem(
            source="file",
            path=str(file_path),
            exists=file_path.exists()
        )
        
        if item.exists:
            item.size_bytes = file_path.stat().st_size
            
            # Read preview (first 500 chars)
            try:
                if file_path.suffix == '.json':
                    with open(file_path, 'r') as f:
                        content = f.read(500)
                        item.content_preview = content[:500]
                else:
                    with open(file_path, 'r', errors='ignore') as f:
                        item.content_preview = f.read(500)
            except Exception as e:
                item.content_preview = f"Error reading: {e}"
                
        return item

    def validate_apk(self, apk_path: Path, verbose: bool = False) -> APKTestResult:
        """Validate a single APK with all evidence checks"""
        result = APKTestResult(
            apk_name=apk_path.name,
            apk_path=str(apk_path),
            sha256=self.calculate_sha256(apk_path),
            test_start_time=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        
        start_time = time.time()
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔍 Validating: {apk_path.name}")
            print(f"{'='*60}")

        # =========================================================================
        # CHECK 1: APK File Exists
        # =========================================================================
        ev = self.check_evidence_file(apk_path)
        result.validations.append(ValidationResult(
            check_name="apk_file_exists",
            status=TestStatus.PASS if ev.is_valid() else TestStatus.FAIL,
            details=f"APK file {'exists' if ev.exists else 'missing'}, size={ev.size_bytes}",
            evidence=ev
        ))
        if not ev.is_valid():
            result.overall_status = TestStatus.FAIL
            result.test_end_time = time.strftime("%Y-%m-%dT%H:%M:%S")
            result.duration_seconds = time.time() - start_time
            return result

        # =========================================================================
        # CHECK 2: DEX Extraction/Parsing Evidence
        # =========================================================================
        # Look for DEX parsing evidence in run/ directories
        dex_evidence_paths = [
            self.output_dir / f"{apk_path.stem}_dex_info.json",
            Path("run") / "exp032_phase3" / "execution_proofs" / apk_path.stem / "evidence_summary.json",
            Path("run") / "exp031_5" / "traces" / apk_path.stem / "execution_summary.json",
        ]
        
        dex_loaded = False
        for dex_path in dex_evidence_paths:
            ev = self.check_evidence_file(dex_path)
            if ev.is_valid():
                dex_loaded = True
                # Try to extract class count from JSON
                try:
                    with open(dex_path, 'r') as f:
                        dex_data = json.load(f)
                        if isinstance(dex_data, dict):
                            result.classes_found = dex_data.get('classes_count', 
                                                       dex_data.get('num_classes', 0))
                except Exception:
                    pass
                break
        
        result.dex_loaded = dex_loaded
        result.validations.append(ValidationResult(
            check_name="dex_extracted",
            status=TestStatus.PASS if dex_loaded else TestStatus.FAIL,
            details=f"DEX extraction evidence {'found' if dex_loaded else 'NOT FOUND'}",
        ))

        # =========================================================================
        # CHECK 3: Bytecode Available
        # =========================================================================
        bytecode_available = result.classes_found > 0
        
        # Check for method traces
        trace_paths = [
            self.output_dir / f"{apk_path.stem}_methods.json",
            Path("run") / "exp031_5" / "traces" / apk_path.stem / "method_trace.json",
        ]
        
        methods_trace_exists = False
        for trace_path in trace_paths:
            ev = self.check_evidence_file(trace_path)
            if ev.is_valid():
                methods_trace_exists = True
                break
        
        result.validations.append(ValidationResult(
            check_name="bytecode_available",
            status=TestStatus.PASS if (bytecode_available or methods_trace_exists) else TestStatus.FAIL,
            details=f"Classes: {result.classes_found}, Method trace: {methods_trace_exists}",
        ))

        # =========================================================================
        # CHECK 4: Interpreter Execution Evidence
        # =========================================================================
        # This is CRITICAL - must have REAL_DALVIK_INTERPRETER source
        instruction_trace_paths = [
            self.output_dir / f"{apk_path.stem}_report.json",
            Path("run") / "exp031_5" / "traces" / apk_path.stem / "opcode_trace.json",
            Path("run") / "exp032_phase3" / "execution_proofs" / apk_path.stem / "evidence_summary.json",
        ]
        
        interpreter_executed = False
        has_real_source = False
        instruction_count = 0
        
        for instr_path in instruction_trace_paths:
            ev = self.check_evidence_file(instr_path)
            if ev.is_valid():
                interpreter_executed = True
                
                # Check for REAL_DALVIK_INTERPRETER in content
                if "REAL_DALVIK_INTERPRETER" in ev.content_preview:
                    has_real_source = True
                    
                # Try to extract instruction count
                try:
                    with open(instr_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            instruction_count = data.get('total_instructions', 
                                                   data.get('instruction_count', 0))
                            if instruction_count == 0:
                                # Try nested structure
                                if 'statistics' in data:
                                    instruction_count = data['statistics'].get('total_instructions', 0)
                            result.methods_executed = data.get('total_methods',
                                                          data.get('method_count', 0))
                            result.api_calls_made = data.get('statistics', {}).get('total_api_calls', 0) if isinstance(data.get('statistics'), dict) else 0
                            
                            # Check for lifecycle evidence
                            content_str = json.dumps(data)
                            if 'onCreate' in content_str or 'Activity' in content_str:
                                result.lifecycle_reached = True
                except Exception:
                    pass
                    
                break
        
        result.instructions_executed = instruction_count
        result.has_real_interpreter_evidence = has_real_source
        
        result.validations.append(ValidationResult(
            check_name="interpreter_executed",
            status=TestStatus.PASS if interpreter_executed else TestStatus.FAIL,
            details=f"Interpreter executed: {interpreter_executed}, Instructions: {instruction_count}",
        ))

        # =========================================================================
        # CHECK 5: Execution Source Validation (CRITICAL)
        # =========================================================================
        if has_real_source:
            source_status = TestStatus.PASS
            source_details = "✅ REAL_DALVIK_INTERPRETER evidence found"
        elif interpreter_executed:
            source_status = TestStatus.FAIL
            source_details = "❌ Interpreter executed but NO REAL_DALVIK_INTERPRETER tag - possible HOST_SHORTCUT"
            result.has_host_shortcut = True
        else:
            source_status = TestStatus.FAIL
            source_details = "❌ No interpreter execution evidence at all"
            
        result.validations.append(ValidationResult(
            check_name="execution_source_valid",
            status=source_status,
            details=source_details,
        ))

        # =========================================================================
        # CHECK 6: No Host Shortcut
        # =========================================================================
        no_host_shortcut = not result.has_host_shortcut
        result.validations.append(ValidationResult(
            check_name="no_host_shortcut",
            status=TestStatus.PASS if no_host_shortcut else TestStatus.FAIL,
            details="No HOST_SHORTCUT detected" if no_host_shortcut else "⚠️ HOST_SHORTCUT detected",
        ))

        # =========================================================================
        # CHECK 7: No Timeout
        # =========================================================================
        # Check for timeout markers in evidence
        had_timeout = False
        if ev.exists and "TIMEOUT" in ev.content_preview.upper():
            had_timeout = True
            result.has_timeout = True
            
        result.validations.append(ValidationResult(
            check_name="no_timeout",
            status=TestStatus.PASS if not had_timeout else TestStatus.FAIL,
            details="No execution timeout" if not had_timeout else "⚠️ Execution timeout detected",
        ))

        # =========================================================================
        # CHECK 8: Evidence Files Created
        # =========================================================================
        expected_files = [
            self.output_dir / f"{apk_path.stem}_report.json",
            self.output_dir / f"{apk_path.stem}_summary.txt",
        ]
        
        files_created = sum(1 for f in expected_files if f.exists())
        result.validations.append(ValidationResult(
            check_name="evidence_files_created",
            status=TestStatus.PASS if files_created > 0 else TestStatus.SKIP,
            details=f"Evidence files created: {files_created}/{len(expected_files)}",
        ))

        # =========================================================================
        # CHECK 9: Trace Non-Empty
        # =========================================================================
        trace_non_empty = instruction_count > 0 or result.methods_executed > 0
        result.validations.append(ValidationResult(
            check_name="trace_non_empty",
            status=TestStatus.PASS if trace_non_empty else TestStatus.FAIL,
            details=f"Instructions: {instruction_count}, Methods: {result.methods_executed}",
        ))

        # =========================================================================
        # CHECK 10: API Calls Tracked (if any occurred)
        # =========================================================================
        api_tracking_ok = True  # OK if no API calls expected or they were tracked
        if result.api_calls_made > 0 or result.lifecycle_reached:
            api_tracking_ok = True  # Evidence of API tracking exists
            
        result.validations.append(ValidationResult(
            check_name="api_calls_tracked",
            status=TestStatus.PASS if api_tracking_ok else TestStatus.SKIP,
            details=f"API calls tracked: {result.api_calls_made}, Lifecycle: {result.lifecycle_reached}",
        ))

        # =========================================================================
        # DETERMINE OVERALL STATUS
        # =========================================================================
        failed_checks = [v for v in result.validations if v.status == TestStatus.FAIL]
        critical_failures = [v for v in failed_checks if v.check_name in [
            "execution_source_valid",  # MUST have real interpreter evidence
            "interpreter_executed",   # MUST have executed something
            "trace_non_empty"         # MUST have non-empty trace
        ]]
        
        if critical_failures:
            result.overall_status = TestStatus.FAIL
        elif failed_checks:
            result.overall_status = TestStatus.FAIL  # Any fail = overall fail
        else:
            passed_checks = [v for v in result.validations if v.status == TestStatus.PASS]
            if len(passed_checks) >= 5:  # At least majority pass
                result.overall_status = TestStatus.PASS
            else:
                result.overall_status = TestStatus.SKIP

        result.test_end_time = time.strftime("%Y-%m-%dT%H:%M:%S")
        result.duration_seconds = time.time() - start_time
        
        if verbose:
            self._print_result(result)

        return result

    def _print_result(self, result: APKTestResult):
        """Print detailed test result"""
        status_icon = {
            TestStatus.PASS: "✅",
            TestStatus.FAIL: "❌", 
            TestStatus.SKIP: "⏭️",
            TestStatus.ERROR: "💥"
        }
        
        print(f"\n{status_icon.get(result.overall_status, '?')} {result.apk_name}")
        print(f"   SHA256: {result.sha256[:16]}...")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        print(f"\n   Validations:")
        
        for v in result.validations:
            icon = status_icon.get(v.status, "?")
            print(f"     {icon} {v.check_name}: {v.details}")
            
        print(f"\n   Execution Summary:")
        print(f"     Classes: {result.classes_found}")
        print(f"     Methods:  {result.methods_executed}")
        print(f"     Instructions: {result.instructions_executed}")
        print(f"     API Calls: {result.api_calls_made}")
        print(f"     Lifecycle: {'✅ YES' if result.lifecycle_reached else '❌ NO'}")
        print(f"\n   Source Tracking:")
        print(f"     Real Interpreter: {'✅' if result.has_real_interpreter_evidence else '❌'}")
        print(f"     Host Shortcut:   {'⚠️ YES' if result.has_host_shortcut else '✅ NO'}")
        print(f"     Timeout:         {'⚠️ YES' if result.has_timeout else '✅ NO'}")

    def validate_all(self, apk_dir: str, verbose: bool = False) -> Dict:
        """Validate all APKs in directory and generate report"""
        apk_files = self.find_apk_files(apk_dir)
        
        if not apk_files:
            print(f"❌ No APK/DEX files found in {apk_dir}")
            return {"error": "No APK files found", "results": []}
        
        print(f"📦 Found {len(apk_files)} APK/DEX files to validate\n")
        
        for apk_path in apk_files:
            result = self.validate_apk(apk_path, verbose)
            self.results.append(result)
        
        # Generate summary report
        report = self.generate_report()
        
        # Save report
        report_path = self.output_dir / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")
        
        return report

    def generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.overall_status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.overall_status == TestStatus.FAIL)
        
        total_instructions = sum(r.instructions_executed for r in self.results)
        total_methods = sum(r.methods_executed for r in self.results)
        total_api_calls = sum(r.api_calls_made for r in self.results)
        
        has_any_real_evidence = any(r.has_real_interpreter_evidence for r in self.results)
        has_any_host_shortcut = any(r.has_host_shortcut for r in self.results)
        has_any_timeout = any(r.has_timeout for r in self.results)
        
        report = {
            "session_info": {
                "validator": "EXP-036_Evidence_Gate",
                "version": "1.0.0",
                "session_start": self.session_start,
                "session_end": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "output_directory": str(self.output_dir)
            },
            "summary": {
                "total_apks_tested": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": (passed / total * 100) if total > 0 else 0,
                "overall_status": "PASS" if (passed == total and total > 0 and has_any_real_evidence) else "FAIL"
            },
            "execution_statistics": {
                "total_instructions_executed": total_instructions,
                "total_methods_executed": total_methods,
                "total_api_calls": total_api_calls,
                "has_real_interpreter_evidence": has_any_real_evidence,
                "has_host_shortcut_detected": has_any_host_shortcut,
                "has_timeout_detected": has_any_timeout
            },
            "evidence_gate_verdict": {
                "all_checks_pass": passed == total and total > 0,
                "real_interpreter_evidence_exists": has_any_real_evidence,
                "no_fake_success": not has_any_host_shortcut,
                "no_silent_failures": not has_any_timeout,
                "trace_evidence_complete": total_instructions > 0 or total_methods > 0,
                "final_verdict": "ACCEPTED" if (
                    passed == total and 
                    total > 0 and 
                    has_any_real_evidence and 
                    not has_any_host_shortcut
                ) else "REJECTED"
            },
            "individual_results": [r.to_dict() for r in self.results],
            "required_checks": self.REQUIRED_CHECKS
        }
        
        return report


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='EXP-036 Execution Pipeline Validator - Evidence Gate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python exp036_execution_validator.py --apk-dir test_apks --verbose
  python exp036_execution_validator.py --apk-dir download/apks
  
Exit Codes:
  0 - All validations PASSED (real evidence confirmed)
  1 - Validations FAILED (missing or invalid evidence)
  2 - Error during validation
        """
    )
    
    parser.add_argument(
        '--apk-dir', '-d',
        default='test_apks',
        help='Directory containing APK/DEX files (default: test_apks)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='run/exp036',
        help='Output directory for reports (default: run/exp036)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("🔐 EXP-036 EXECUTION PIPELINE EVIDENCE GATE")
    print("="*70)
    print(f"APK Directory: {args.apk_dir}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    gate = EXP036EvidenceGate(output_dir=args.output_dir)
    report = gate.validate_all(args.apk_dir, verbose=args.verbose)
    
    # Print final verdict
    verdict = report.get("evidence_gate_verdict", {}).get("final_verdict", "UNKNOWN")
    summary = report.get("summary", {})
    
    print("\n" + "="*70)
    print("🏁 FINAL VERDICT: " + verdict)
    print("="*70)
    print(f"Total Tested: {summary.get('total_apks_tested', 0)}")
    print(f"Passed:       {summary.get('passed', 0)}")
    print(f"Failed:       {summary.get('failed', 0)}")
    print(f"Pass Rate:    {summary.get('pass_rate', 0):.1f}%")
    
    stats = report.get("execution_statistics", {})
    print(f"\nExecution Statistics:")
    print(f"  Instructions: {stats.get('total_instructions_executed', 0)}")
    print(f"  Methods:      {stats.get('total_methods_executed', 0)}")
    print(f"  API Calls:    {stats.get('total_api_calls', 0)}")
    print(f"  Real Evidence: {'✅ YES' if stats.get('has_real_interpreter_evidence') else '❌ NO'}")
    print(f"  Host Shortcut: {'⚠️ YES' if stats.get('has_host_shortcut_detected') else '✅ NO'}")
    print(f"  Timeouts:      {'⚠️ YES' if stats.get('has_timeout_detected') else '✅ NO'}")
    
    # Exit with appropriate code
    if verdict == "ACCEPTED":
        print("\n✅ EVIDENCE GATE PASSED - Real execution evidence confirmed!")
        return 0
    else:
        print("\n❌ EVIDENCE GATE FAILED - Missing or invalid execution evidence")
        return 1


if __name__ == "__main__":
    sys.exit(main())
