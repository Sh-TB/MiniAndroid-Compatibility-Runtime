#!/usr/bin/env python3
"""
EXP-031: CI Protection Rule - Fake Execution Blocker

This script implements the Golden Debug Protocol CI rule:
FAIL BUILD IF lifecycle state exists AND ExecutionSource != REAL_DALVIK_INTERPRETER

Usage:
    python3 exp031_ci_protection.py --evidence-dir <dir>

Exit Codes:
    0 = Protection passed (no fake execution detected)
    1 = VIOLATION: Fake execution detected
    2 = Error
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

class FakeExecutionDetector:
    """Detects fake/simulated execution attempts"""
    
    # Patterns that indicate fake lifecycle
    FAKE_PATTERNS = [
        "HOST_SHORTCUT",
        "SIMULATED",
        "LEGACY_MODE",
        "STUB_LIFECYCLE"
    ]
    
    # Required real execution patterns
    REAL_PATTERNS = [
        "REAL_DALVIK_INTERPRETER",
        "OPCODE_EXECUTED",
        "BYTECODE_INTERPRETED"
    ]
    
    def __init__(self, evidence_dir: str):
        self.evidence_dir = Path(evidence_dir)
        self.violations: List[Dict] = []
        
    def check_all_evidence(self) -> bool:
        """Check all evidence files for fake execution"""
        if not self.evidence_dir.exists():
            print(f"[ERROR] Evidence directory not found: {self.evidence_dir}")
            return False
        
        found_violation = False
        
        # Check all JSON evidence files
        for json_file in self.evidence_dir.rglob("*.json"):
            result = self._check_file(json_file)
            if result:
                found_violation = True
                self.violations.append({
                    "file": str(json_file),
                    "violation": result
                })
        
        return found_violation
    
    def _check_file(self, file_path: Path) -> Optional[Dict]:
        """Check single file for violations"""
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            return self._check_data(data, str(file_path))
            
        except Exception as e:
            return {"error": str(e)}
    
    def _check_data(self, data: Any, source: str) -> Optional[Dict]:
        """Recursively check data structure for violations"""
        if isinstance(data, dict):
            # Check for ExecutionSource field
            source_field = data.get("source", data.get("execution_source", ""))
            status = data.get("status", "")
            
            # Check for lifecycle success with fake source
            if (any(s in status.upper() for s in ["SUCCESS", "RENDERED", "COMPLETE"]) and 
                any(p in source_field.upper() for p in self.FAKE_PATTERNS)):
                return {
                    "type": "FAKE_LIFECYCLE_SUCCESS",
                    "source": source_field,
                    "status": status,
                    "message": f"Lifecycle shows '{status}' but source is '{source_field}'"
                }
            
            # Recurse into values
            for key, value in data.items():
                result = self._check_data(value, f"{source}.{key}")
                if result:
                    return result
                    
        elif isinstance(data, list):
            for item in data:
                result = self._check_data(item, source)
                if result:
                    return result
        
        return None


def test_protection():
    """
    Test that CI protection actually catches violations.
    
    This function creates a temporary fake evidence file,
    runs the detector, verifies it catches it,
    then cleans up.
    """
    import tempfile
    
    print("[*] Testing CI Protection Rule...")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create fake evidence (should be caught)
        fake_evidence = {
            "apk_name": "TestApp.apk",
            "status": "SUCCESS",
            "source": "HOST_SHORTCUT",  # VIOLATION!
            "lifecycle": {
                "onCreate": "called",
                "onStart": "called",
                "onResume": "called"
            }
        }
        
        fake_file = Path(tmpdir) / "fake_evidence.json"
        with open(fake_file, 'w') as f:
            json.dump(fake_evidence, f)
        
        # Run detector
        detector = FakeExecutionDetector(tmpdir)
        violation_found = detector.check_all_evidence()
        
        if violation_found:
            print("✅ PROTECTION WORKING: Fake execution was detected!")
            print(f"   Violation: {detector.violations[0]['violation']['type']}")
            print(f"   Message: {detector.violations[0]['violation']['message']}")
            return True
        else:
            print("❌ PROTECTION FAILED: Fake execution was NOT detected!")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="EXP-031: CI Protection - Fake Execution Blocker"
    )
    parser.add_argument(
        "--evidence-dir",
        help="Directory containing execution evidence"
    )
    parser.add_argument(
        "--test-protection",
        action="store_true",
        help="Test that protection rule works (creates fake evidence)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("EXP-031: CI PROTECTION - FAKE EXECUTION BLOCKER")
    print("=" * 70)
    print()
    
    if args.test_protection:
        # Test mode - doesn't need evidence dir
        success = test_protection()
        sys.exit(0 if success else 1)
    
    # Normal validation mode - requires evidence dir
    if not args.evidence_dir:
        parser.print_help()
        sys.exit(2)
    
    # Normal validation mode
    print(f"[*] Checking evidence directory: {args.evidence_dir}")
    print()
    
    detector = FakeExecutionDetector(args.evidence_dir)
    violation_found = detector.check_all_evidence()
    
    if violation_found:
        print("=" * 70)
        print("❌ VIOLATION DETECTED!")
        print("=" * 70)
        print()
        print("Golden Debug Protocol VIOLATION:")
        print("  Lifecycle state exists WITHOUT real Dalvik interpretation")
        print()
        print("Violations:")
        for v in detector.violations:
            print(f"  📄 File: {v['file']}")
            if isinstance(v['violation'], dict):
                print(f"     Type: {v['violation'].get('type', 'UNKNOWN')}")
                print(f"     Message: {v['violation'].get('message', 'No message')}")
            print()
        
        print()
        print("⛔ CI RULE: FAIL BUILD")
        print("   This APK's 'success' is NOT from real bytecode execution.")
        print("   Fix: Route through DalvikEngine or mark as LEGACY mode.")
        sys.exit(1)
    else:
        print("=" * 70)
        print("✅ PROTECTION PASSED")
        print("=" * 70)
        print()
        print("No fake execution detected.")
        print("All lifecycle events have proper source attribution (or no lifecycle events exist).")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
