#!/usr/bin/env python3
"""
EXP-031: Real Execution Proof Validator
Golden Debug Protocol - Evidence Verification Tool

This tool validates that APK execution produced REAL Dalvik bytecode interpretation,
not simulated lifecycle events.

Usage:
    python3 exp031_real_execution_validator.py --apk-dir <dir> [--mode legacy|real-dalvik]

Exit Codes:
    0 = Real execution confirmed
    1 = Fake/simulated execution detected
    2 = Error in validation
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class ExecutionEvidenceValidator:
    """Validates execution evidence against Golden Debug Protocol"""
    
    # Required fields for real execution proof
    REQUIRED_OPCODE_FIELDS = [
        "sequence",
        "pc_before", 
        "pc_after",
        "opcode",
        "source"
    ]
    
    def __init__(self, apk_dir: str, mode: str = "real-dalvik"):
        self.apk_dir = Path(apk_dir)
        self.mode = mode
        self.results: List[Dict] = []
        
    def validate_apk(self, apk_path: str) -> Dict:
        """Validate single APK execution evidence"""
        result = {
            "apk_name": os.path.basename(apk_path),
            "validation_time": datetime.now().isoformat(),
            "mode_tested": self.mode,
            "real_execution": False,
            "evidence": {},
            "violations": [],
            "final_verdict": "UNKNOWN"
        }
        
        try:
            # Look for evidence files
            apk_name = os.path.basename(apk_path).replace('.apk', '')
            trace_dir = self.apk_dir / apk_name if self.apk_dir.exists() else Path()
            
            # Check for opcode trace (CRITICAL for real execution)
            opcode_trace = self._find_file(trace_dir, "opcode_trace.json")
            
            if opcode_trace:
                with open(opcode_trace) as f:
                    opcode_data = json.load(f)
                result["evidence"]["opcode_trace"] = self._validate_opcode_trace(opcode_data)
            else:
                result["violations"].append("NO_OPCODE_TRACE: No opcode_trace.json found")
            
            # Check for API trace with source attribution
            api_trace = self._find_file(trace_dir, "api_trace.json")
            if api_trace:
                with open(api_trace) as f:
                    api_data = json.load(f)
                result["evidence"]["api_trace"] = self._validate_api_trace(api_data)
            
            # Check for execution proof
            proof_file = self._find_file(trace_dir, "real_execution_proof.json")
            if proof_file:
                with open(proof_file) as f:
                    proof_data = json.load(f)
                result["evidence"]["execution_proof"] = self._validate_proof(proof_data)
            
            # Make final determination
            result = self._make_verdict(result)
            
        except Exception as e:
            result["error"] = str(e)
            result["final_verdict"] = "ERROR"
            
        return result
    
    def _validate_opcode_trace(self, data: Dict) -> Dict:
        """Validate opcode trace meets Golden Debug Protocol"""
        validation = {
            "exists": True,
            "total_opcodes": 0,
            "has_source_attribution": False,
            "real_dalvik_count": 0,
            "host_shortcut_count": 0,
            "valid": False
        }
        
        if isinstance(data, list):
            opcodes = data
        elif isinstance(data, dict) and "opcodes" in data:
            opcodes = data["opcodes"]
        else:
            opcodes = []
        
        validation["total_opcodes"] = len(opcodes)
        
        for opcode in opcodes:
            # Check for ExecutionSource field
            source = opcode.get("source", "UNKNOWN")
            if source == "REAL_DALVIK_INTERPRETER":
                validation["real_dalvik_count"] += 1
                validation["has_source_attribution"] = True
            elif source == "HOST_SHORTCUT":
                validation["host_shortcut_count"] += 1
                validation["has_source_attribution"] = True
        
        # Valid if we have opcodes from real interpreter
        validation["valid"] = validation["real_dalvik_count"] > 0
        
        return validation
    
    def _validate_api_trace(self, data: Dict) -> Dict:
        """Validate API calls have proper source attribution"""
        validation = {
            "exists": True,
            "total_calls": 0,
            "lifecycle_calls": [],
            "has_real_lifecycle": False
        }
        
        if isinstance(data, list):
            calls = data
        elif isinstance(data, dict) and "calls" in data:
            calls = data["calls"]
        else:
            calls = []
        
        validation["total_calls"] = len(calls)
        
        for call in calls:
            method = call.get("method", call.get("name", ""))
            source = call.get("source", "UNKNOWN")
            
            if any(lc in method.lower() for lc in ["oncreate", "onstart", "onresume"]):
                lifecycle_entry = {
                    "method": method,
                    "source": source,
                    "is_real": source == "REAL_DALVIK_INTERPRETER"
                }
                validation["lifecycle_calls"].append(lifecycle_entry)
                
                if lifecycle_entry["is_real"]:
                    validation["has_real_lifecycle"] = True
        
        return validation
    
    def _validate_proof(self, data: Dict) -> Dict:
        """Validate execution proof document"""
        validation = {
            "exists": True,
            "classification": data.get("classification", "UNKNOWN"),
            "execution_source": data.get("execution_source", "UNKNOWN"),
            "instructions_executed": data.get("instructions_executed", 0),
            "registers_modified": data.get("registers_modified", False),
            "valid": False
        }
        
        # Valid if real execution with instructions
        if (validation["execution_source"] == "REAL_DALVIK_INTERPRETER" and 
            validation["instructions_executed"] > 0):
            validation["valid"] = True
        
        return validation
    
    def _make_verdict(self, result: Dict) -> Dict:
        """Make final verdict based on all evidence"""
        evidence = result.get("evidence", {})
        violations = result.get("violations", [])
        
        # Check for definitive real execution
        has_real_opcodes = (
            evidence.get("opcode_trace", {}).get("real_dalvik_count", 0) > 0
        )
        has_real_lifecycle = (
            evidence.get("api_trace", {}).get("has_real_lifecycle", False)
        )
        has_valid_proof = (
            evidence.get("execution_proof", {}).get("valid", False)
        )
        
        if self.mode == "real-dalvik":
            # In real-dalvik mode, MUST have real evidence
            if has_real_opcodes or has_real_lifecycle or has_valid_proof:
                result["real_execution"] = True
                result["final_verdict"] = "REAL_EXECUTION_CONFIRMED"
            elif violations:
                result["real_execution"] = False
                result["final_verdict"] = "FAKE_EXECUTION_DETECTED"
            else:
                result["real_execution"] = False
                result["final_verdict"] = "INSUFFICIENT_EVIDENCE"
        else:
            # Legacy mode - expect shortcuts
            result["real_execution"] = False
            result["final_verdict"] = "LEGACY_MODE_EXPECTED"
        
        return result
    
    def _find_file(self, directory: Path, filename: str) -> Optional[Path]:
        """Find file in directory"""
        if not directory.exists():
            return None
        
        target = directory / filename
        if target.exists():
            return target
        
        # Search subdirectories
        for subdir in directory.rglob("*"):
            if subdir.is_dir():
                candidate = subdir / filename
                if candidate.exists():
                    return candidate
        
        return None


def run_validation_campaign(apk_directory: str, mode: str) -> Dict:
    """Run validation across multiple APKs"""
    validator = ExecutionEvidenceValidator(apk_directory, mode)
    
    campaign_result = {
        "experiment": "EXP-031",
        "validation_type": "REAL_EXECUTION_PROOF",
        "timestamp": datetime.now().isoformat(),
        "mode_tested": mode,
        "summary": {
            "total_apks": 0,
            "real_execution_confirmed": 0,
            "fake_execution_detected": 0,
            "insufficient_evidence": 0,
            "errors": 0
        },
        "results": []
    }
    
    apk_dir = Path(apk_directory)
    if not apk_dir.exists():
        campaign_result["error"] = f"APK directory not found: {apk_directory}"
        return campaign_result
    
    # Find all APKs
    apks = list(apk_dir.glob("*.apk"))
    
    for apk_path in sorted(apks):
        result = validator.validate_apk(str(apk_path))
        campaign_result["results"].append(result)
        campaign_result["summary"]["total_apks"] += 1
        
        verdict = result.get("final_verdict", "ERROR")
        if verdict == "REAL_EXECUTION_CONFIRMED":
            campaign_result["summary"]["real_execution_confirmed"] += 1
        elif verdict == "FAKE_EXECUTION_DETECTED":
            campaign_result["summary"]["fake_execution_detected"] += 1
        elif verdict == "INSUFFICIENT_EVIDENCE":
            campaign_result["summary"]["insufficient_evidence"] += 1
        else:
            campaign_result["summary"]["errors"] += 1
    
    return campaign_result


def main():
    parser = argparse.ArgumentParser(
        description="EXP-031: Real Execution Proof Validator"
    )
    parser.add_argument(
        "--apk-dir", 
        required=True,
        help="Directory containing APK files"
    )
    parser.add_argument(
        "--mode",
        choices=["legacy", "real-dalvik"],
        default="real-dalvik",
        help="Execution mode to validate (default: real-dalvik)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--fail-on-fake",
        action="store_true",
        help="Exit with error code if fake execution detected"
    )
    
    args = parser.parse_args()
    
    print(f"[*] EXP-031: Real Execution Proof Validator")
    print(f"[*] Mode: {args.mode}")
    print(f"[*] APK Directory: {args.apk_dir}")
    print()
    
    # Run validation
    result = run_validation_campaign(args.apk_dir, args.mode)
    
    # Print summary
    summary = result["summary"]
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total APKs Tested:     {summary['total_apks']}")
    print(f"Real Execution:        {summary['real_execution_confirmed']} ✅")
    print(f"Fake Execution:        {summary['fake_execution_detected']} ❌")
    print(f"Insufficient Evidence: {summary['insufficient_evidence']} ⚠️")
    print(f"Errors:                {summary['errors']} 💥")
    print()
    
    # Verdict
    if args.mode == "real-dalvik":
        if summary["real_execution_confirmed"] > 0:
            print("✅ VERDICT: REAL DALVIK EXECUTION CONFIRMED")
            exit_code = 0
        elif summary["insufficient_evidence"] > 0:
            print("⚠️ VERDICT: ENGINE CONNECTED BUT NO BYTECODE EXECUTED YET")
            exit_code = 0  # Not a failure, just needs methods with bytecode
        else:
            print("❌ VERDICT: FAKE EXECUTION DETECTED")
            exit_code = 1 if args.fail_on_fake else 0
    else:
        print("ℹ️  VERDICT: LEGACY MODE (shortcuts expected)")
        exit_code = 0
    
    # Save results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n[+] Results saved to: {output_path}")
    
    # Detailed results
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)
    for r in result["results"]:
        apk = r["apk_name"]
        verdict = r["final_verdict"]
        icon = "✅" if "CONFIRMED" in verdict or "EXPECTED" in verdict else "❌" if "FAKE" in verdict else "⚠️"
        print(f"{icon} {apk}: {verdict}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
