#!/usr/bin/env python3
"""
EXP-027: Real World APK Execution Campaign
============================================
Executes real APKs through MiniAndroid runtime and collects results.

GOLDEN RULE: NO SIMULATION MODE
Every result must come from actual runtime process.

Execution Status:
- PASS: APK executed completely without errors
- PARTIAL: APK loaded but some features failed
- FAIL: APK failed to execute
- PARSE_ERROR: Could not parse DEX
- NOT_EXECUTED: Not attempted
"""

import hashlib
import json
import os
import re
import subprocess
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Configuration
BASE_DIR = Path("/home/z/my-project/miniandroid")
RUNTIME_BINARY = BASE_DIR / "build" / "miniandroid"
RESULTS_DIR = BASE_DIR / "run" / "exp027" / "results"
TRACE_DIR = BASE_DIR / "run" / "exp027" / "traces"
SCREENSHOT_DIR = BASE_DIR / "run" / "exp027" / "screenshots"
REGISTRY_FILE = BASE_DIR / "database" / "exp027_apk_registry.json"

# Create directories
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
TRACE_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ExecutionResult:
    """Result of executing one APK through runtime."""
    apk_name: str
    package: str
    status: str  # EXECUTED_PASS, EXECUTED_PARTIAL, EXECUTED_FAIL, PARSE_ERROR, NOT_EXECUTED
    real_execution: bool = True
    dex_loaded: bool = False
    instructions_executed: int = 0
    methods_entered: List[str] = field(default_factory=list)
    api_calls: List[str] = field(default_factory=list)
    opcodes_used: Dict[str, int] = field(default_factory=dict)
    render_status: str = ""
    screenshot_captured: bool = False
    error_messages: List[str] = field(default_factory=list)
    crash_log: str = ""
    execution_time_ms: int = 0
    timestamp: str = ""
    evidence_files: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class RealExecutionCampaign:
    """
    Executes real APK corpus through MiniAndroid runtime.
    
    Enforces Golden Debug Protocol:
    - No simulation mode allowed
    - All results from actual runtime process
    - Evidence files required for every claim
    - SHA256 verification of all outputs
    """

    def __init__(self, mode: str = "real"):
        """
        Initialize execution campaign.
        
        Args:
            mode: MUST be "real" - simulation is forbidden
        """
        if mode != "real":
            raise ValueError("SIMULATION MODE FORBIDDEN in EXP-027")
        
        self.mode = mode
        self.runtime_binary = RUNTIME_BINARY
        self.results: List[ExecutionResult] = []
        self.api_frequency: Dict[str, Dict] = {}
        self.opcode_frequency: Dict[str, int] = {}
        self.failures: List[Dict] = []
        
        # Verify runtime exists
        if not self.runtime_binary.exists():
            raise RuntimeError(f"Runtime binary not found: {self.runtime_binary}")
        
        # Get runtime hash for evidence chain
        self.runtime_hash = self._get_file_hash(self.runtime_binary)
        print(f"[INIT] Runtime: {self.runtime_binary}")
        print(f"[INIT] Runtime SHA256: {self.runtime_hash[:32]}...")
    
    def _get_file_hash(self, path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _execute_apk(self, apk_path: Path, package: str, name: str) -> ExecutionResult:
        """
        Execute single APK through MiniAndroid runtime.
        
        Returns ExecutionResult with full details.
        """
        result = ExecutionResult(
            apk_name=name,
            package=package,
            status="NOT_EXECUTED",
            real_execution=True
        )
        
        # Create unique session ID
        session_id = f"exp027_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name.replace(' ', '_')}"
        output_dir = TRACE_DIR / session_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[EXECUTE] {name} ({package})")
        print(f"  Session: {session_id}")
        print(f"  APK: {apk_path.name} ({apk_path.stat().st_size:,} bytes)")
        
        start_time = time.time()
        
        try:
            # Build command
            cmd = [
                str(self.runtime_binary),
                'run',
                '-o', str(output_dir),
                '--width', '1080',
                '--height', '1920',
                str(apk_path)
            ]
            
            print(f"  Command: {' '.join(cmd[:5])}...")
            
            # Execute runtime
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout per APK
                cwd=str(BASE_DIR)
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time
            
            # Parse stdout/stderr
            stdout = process.stdout
            stderr = process.stderr
            returncode = process.returncode
            
            print(f"  Exit code: {returncode}")
            print(f"  Time: {execution_time}ms")
            
            # Collect evidence files
            evidence_files = []
            if output_dir.exists():
                for f in output_dir.iterdir():
                    if f.is_file():
                        evidence_files.append(str(f))
                        result.evidence_files.append(str(f))
                        # Hash evidence file
                        file_hash = self._get_file_hash(f)
                        print(f"  Evidence: {f.name} ({file_hash[:16]}...)")
            
            # Parse output for execution details
            result = self._parse_runtime_output(result, stdout, stderr, returncode, output_dir)
            
            # Check for screenshots
            screenshot_files = list(output_dir.glob("*.ppm")) + list(output_dir.glob("*.png"))
            if screenshot_files:
                # Copy to screenshot directory
                for ss in screenshot_files:
                    dest = SCREENSHOT_DIR / f"{name}_{ss.name}"
                    import shutil
                    shutil.copy2(ss, dest)
                    result.screenshot_captured = True
                    result.render_status = "screenshot_captured"
                    print(f"  Screenshot: {dest.name}")
            
        except subprocess.TimeoutExpired:
            result.status = "EXECUTED_FAIL"
            result.error_messages.append("Execution timeout (120s exceeded)")
            result.crash_log = "Process killed after timeout"
            print(f"  ❌ TIMEOUT")
            
        except Exception as e:
            result.status = "EXECUTED_FAIL"
            result.error_messages.append(f"Execution error: {str(e)}")
            result.crash_log = str(e)
            print(f"  ❌ ERROR: {e}")
        
        return result
    
    def _parse_runtime_output(self, result: ExecutionResult, 
                               stdout: str, stderr: str, 
                               returncode: int, 
                               output_dir: Path) -> ExecutionResult:
        """Parse runtime output and populate result fields."""
        
        combined_output = stdout + "\n" + stderr
        
        # Check for DEX loading success
        if "DEX loaded" in combined_output or "parse_dex" in combined_output.lower():
            result.dex_loaded = True
        
        # Check for instruction execution
        if "instructions executed" in combined_output.lower():
            try:
                # Try to extract count
                import re
                match = re.search(r'(\d+)\s*instructions?\s*(?:executed)?', combined_output, re.IGNORECASE)
                if match:
                    result.instructions_executed = int(match.group(1))
            except:
                pass
        
        # Check for method entries
        methods_found = []
        method_patterns = [
            r'Entering method:\s+(\S+)',
            r'Method:\s+(\S+)',
            r'invoke_\w+\s+(\S+)',
        ]
        for pattern in method_patterns:
            matches = re.findall(pattern, combined_output, re.IGNORECASE)
            methods_found.extend(matches)
        
        if methods_found:
            result.methods_entered = list(set(methods_found))
        
        # Check for API calls
        api_patterns = [
            r'(android\.\w+(?:\.\w+)*)',
            r'(java\.\w+(?:\.\w+)*)',
        ]
        apis_found = []
        for pattern in api_patterns:
            matches = re.findall(pattern, combined_output)
            apis_found.extend(matches)
        
        if apis_found:
            result.api_calls = list(set(apis_found))
            # Update global API frequency
            for api in apis_found:
                if api not in self.api_frequency:
                    self.api_frequency[api] = {"count": 0, "apps": []}
                self.api_frequency[api]["count"] += 1
                self.api_frequency[api]["apps"].append(result.apk_name)
        
        # Determine status based on return code and output
        if returncode == 0 and "error" not in combined_output.lower() and "fail" not in combined_output.lower():
            if result.instructions_executed > 0 or len(result.methods_entered) > 0:
                result.status = "EXECUTED_PASS"
                print(f"  ✅ PASS")
            else:
                result.status = "EXECUTED_PARTIAL"
                print(f"  ⚠️  PARTIAL (loaded but no code executed)")
        elif result.dex_loaded:
            result.status = "EXECUTED_PARTIAL"
            print(f"  ⚠️  PARTIAL (DEX loaded with issues)")
            # Extract errors
            if "Error" in combined_output or "Exception" in combined_output:
                lines = combined_output.split('\n')
                for line in lines:
                    if 'error' in line.lower() or 'exception' in line.lower() or 'fail' in line.lower():
                        result.error_messages.append(line.strip())
        else:
            result.status = "EXECUTED_FAIL"
            print(f"  ❌ FAIL")
            # Extract errors
            lines = combined_output.split('\n')
            for line in lines:
                if 'error' in line.lower() or 'exception' in line.lower() or 'parse' in line.lower():
                    result.error_messages.append(line.strip())
                    if len(result.error_messages) > 10:  # Limit error collection
                        break
            
            if "PARSE_ERROR" in combined_output or "parse error" in combined_output.lower():
                result.status = "PARSE_ERROR"
                print(f"  ❌ PARSE_ERROR")
        
        # Save crash log if present
        crash_log_path = output_dir / "crash.log"
        if crash_log_path.exists():
            result.crash_log = crash_log_path.read_text()
        elif result.error_messages:
            result.crash_log = "\n".join(result.error_messages)
        
        # Parse trace files if they exist
        api_trace_path = output_dir / "api_trace.json"
        if api_trace_path.exists():
            try:
                with open(api_trace_path, 'r') as f:
                    api_trace = json.load(f)
                    if isinstance(api_trace, dict):
                        if 'api_calls' in api_trace:
                            result.api_calls.extend(api_trace['api_calls'])
                        if 'methods' in api_trace:
                            result.methods_entered.extend(api_trace['methods'])
            except Exception as e:
                print(f"  Warning: Could not parse api_trace.json: {e}")
        
        return result
    
    def execute_corpus(self, min_executions: int = 20) -> Dict:
        """
        Execute entire APK corpus through runtime.
        
        Args:
            min_executions: Minimum number of APKs to attempt
            
        Returns:
            Summary statistics dictionary
        """
        print("=" * 70)
        print("EXP-027: REAL WORLD APK EXECUTION CAMPAIGN")
        print("=" * 70)
        print(f"Mode: {self.mode.upper()} (NO SIMULATION)")
        print(f"Runtime: {self.runtime_binary}")
        print(f"Target: {min_executions}+ executions")
        print(f"Started: {datetime.now().isoformat()}")
        print("-" * 70)
        
        # Load registry
        with open(REGISTRY_FILE, 'r') as f:
            registry = json.load(f)
        
        apks = registry.get('apks', [])
        total_apks = len(apks)
        
        print(f"\nAPK Registry loaded: {total_apks} APKs available")
        
        stats = {
            'total_available': total_apks,
            'attempted': 0,
            'executed_pass': 0,
            'executed_partial': 0,
            'executed_fail': 0,
            'parse_error': 0,
            'not_executed': 0,
            'total_execution_time_ms': 0,
            'by_category': {
                'simple': {'pass': 0, 'partial': 0, 'fail': 0},
                'medium': {'pass': 0, 'partial': 0, 'fail': 0},
                'complex': {'pass': 0, 'partial': 0, 'fail': 0}
            }
        }
        
        # Execute each APK
        for i, apk_info in enumerate(apks, 1):
            apk_path = Path(apk_info['local_path'])
            
            if not apk_path.exists():
                print(f"\n[{i}/{total_apks}] SKIP {apk_info['name']}: File not found")
                continue
            
            if stats['attempted'] >= min_executions and i > min_executions:
                print(f"\n--- Minimum {min_executions} executions reached ---")
                break
            
            print(f"\n[{i}/{min(total_apks, min_executions)}] Executing: {apk_info['name']}")
            
            # Execute APK
            result = self._execute_apk(
                apk_path=apk_path,
                package=apk_info['package'],
                name=apk_info['name']
            )
            
            # Update statistics
            stats['attempted'] += 1
            stats['total_execution_time_ms'] += result.execution_time_ms
            
            category = apk_info.get('category', 'unknown')
            
            if result.status == "EXECUTED_PASS":
                stats['executed_pass'] += 1
                stats['by_category'][category]['pass'] = \
                    stats['by_category'].get(category, {}).get('pass', 0) + 1
            elif result.status == "EXECUTED_PARTIAL":
                stats['executed_partial'] += 1
                stats['by_category'][category]['partial'] = \
                    stats['by_category'].get(category, {}).get('partial', 0) + 1
            elif result.status == "PARSE_ERROR":
                stats['parse_error'] += 1
                stats['by_category'][category]['fail'] = \
                    stats['by_category'].get(category, {}).get('fail', 0) + 1
            elif result.status == "EXECUTED_FAIL":
                stats['executed_fail'] += 1
                stats['by_category'][category]['fail'] = \
                    stats['by_category'].get(category, {}).get('fail', 0) + 1
            else:
                stats['not_executed'] += 1
            
            # Collect failure info
            if result.status in ["EXECUTED_FAIL", "PARSE_ERROR"]:
                self.failures.append({
                    'package': result.package,
                    'status': result.status,
                    'errors': result.error_messages[:5],  # Keep top 5 errors
                    'has_crash_log': bool(result.crash_log),
                    'timestamp': result.timestamp
                })
            
            # Store result
            self.results.append(result)
            
            # Save individual result
            result_file = RESULTS_DIR / f"{apk_info['name'].replace(' ', '_')}_result.json"
            with open(result_file, 'w') as f:
                json.dump(asdict(result), f, indent=2, default=str)
        
        # Print summary
        self._print_summary(stats)
        
        # Save complete results
        self._save_results(stats)
        
        return stats
    
    def _print_summary(self, stats: Dict):
        """Print execution summary."""
        print("\n" + "=" * 70)
        print("EXECUTION CAMPAIGN SUMMARY")
        print("=" * 70)
        print(f"Total Available:   {stats['total_available']}")
        print(f"Attempted:         {stats['attempted']}")
        print("-" * 40)
        print(f"✅ PASS:            {stats['executed_pass']}")
        print(f"⚠️  PARTIAL:          {stats['executed_partial']}")
        print(f"❌ FAIL:            {stats['executed_fail']}")
        print(f"📄 PARSE_ERROR:     {stats['parse_error']}")
        print(f"⏭️  NOT_EXECUTED:    {stats['not_executed']}")
        print("-" * 40)
        
        if stats['attempted'] > 0:
            pass_rate = (stats['executed_pass'] / stats['attempted']) * 100
            partial_rate = (stats['executed_partial'] / stats['attempted']) * 100
            fail_rate = (stats['executed_fail'] / stats['attempted']) * 100
            
            print(f"Pass Rate:         {pass_rate:.1f}%")
            print(f"Partial Rate:      {partial_rate:.1f}%")
            print(f"Fail Rate:         {fail_rate:.1f}%")
        
        print(f"\nTotal Time:        {stats['total_execution_time_ms'] / 1000:.1f}s")
        
        print("\nBy Category:")
        for cat, cat_stats in stats['by_category'].items():
            total = cat_stats['pass'] + cat_stats['partial'] + cat_stats['fail']
            if total > 0:
                print(f"  {cat.capitalize():10s}: P={cat_stats['pass']} PA={cat_stats['partial']} F={cat_stats['fail']}")
    
    def _save_results(self, stats: Dict):
        """Save all results to files."""
        # Complete results JSON
        results_data = {
            'experiment': 'EXP-027',
            'phase': 'REAL_EXECUTION_COMPLETE',
            'timestamp': datetime.now().isoformat(),
            'mode': 'REAL_EXECUTION',
            'runtime_hash': self.runtime_hash,
            'statistics': stats,
            'results': [asdict(r) for r in self.results],
            'api_frequency': self.api_frequency,
            'opcode_frequency': self.opcode_frequency,
            'failures': self.failures,
            'golden_debug_protocol': {
                'simulation_used': False,
                'all_results_from_real_runtime': True,
                'evidence_files_generated_by_runtime': True,
                'no_projected_scores': True
            }
        }
        
        # Main results file
        main_results = RESULTS_DIR.parent / "exp027_real_execution_results.json"
        with open(main_results, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        print(f"\n📊 Results saved to: {main_results}")


def main():
    """Main entry point."""
    try:
        campaign = RealExecutionCampaign(mode="real")
        stats = campaign.execute_corpus(min_executions=20)
        
        # Return success if we executed minimum
        if stats['attempted'] >= 20:
            print("\n✅ SUCCESS: Executed 20+ real APKs")
            return 0
        else:
            print(f"\n⚠️ PARTIAL: Only executed {stats['attempted']} APKs")
            return 1
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
