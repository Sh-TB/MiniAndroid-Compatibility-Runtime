#!/usr/bin/env python3
"""
EXP-028: Baseline Freeze & DEX Forensic Analysis Tool
=====================================================
Collects comprehensive baseline data for DEX parser investigation.

Captures:
- Working APK: HelloWorld.apk
- Failing APKs: 5+ examples across complexity levels
- For each: SHA256, DEX size, header bytes, runtime error, parser state
"""

import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Configuration
BASE_DIR = Path("/home/z/my-project/miniandroid")
RUNTIME_BINARY = BASE_DIR / "build" / "miniandroid"
OUTPUT_DIR = BASE_DIR / "run" / "exp028" / "baseline"
DEX_ANALYSIS_DIR = BASE_DIR / "run" / "exp028" / "dex_analysis"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEX_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass 
class APKBaselineEntry:
    """Complete baseline data for one APK."""
    name: str
    path: str
    category: str  # working_simple, failing_simple, failing_medium, failing_complex, failing_production
    apk_sha256: str = ""
    apk_size: int = 0
    dex_size: int = 0
    dex_sha256: str = ""
    header_bytes_hex: str = ""  # First 112 bytes as hex
    header_parsed: Dict = field(default_factory=dict)
    runtime_error: str = ""
    runtime_exit_code: int = -1
    parser_state: str = ""
    timestamp: str = ""


class BaselineCollector:
    """
    Collects baseline data for DEX parser investigation.
    
    Evidence-first approach: capture everything before making changes.
    """

    def __init__(self):
        self.entries: List[APKBaselineEntry] = []
        self.runtime_binary = RUNTIME_BINARY
        
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def extract_dex_from_apk(self, apk_path: Path) -> Tuple[Optional[bytes], Optional[Path]]:
        """Extract classes.dex from APK file."""
        try:
            with zipfile.ZipFile(apk_path, 'r') as zf:
                # Look for classes.dex
                if 'classes.dex' in zf.namelist():
                    dex_data = zf.read('classes.dex')
                    # Save to analysis directory
                    output_dex = DEX_ANALYSIS_DIR / f"{apk_path.stem}_classes.dex"
                    with open(output_dex, 'wb') as f:
                        f.write(dex_data)
                    return dex_data, output_dex
                
                # List available files for debugging
                print(f"  Available in ZIP: {zf.namelist()[:10]}")
                return None, None
                
        except Exception as e:
            print(f"  Error extracting DEX: {e}")
            return None, None
    
    def parse_dex_header_raw(self, dex_data: bytes) -> Dict:
        """
        Parse DEX header fields manually for forensic analysis.
        
        Returns raw values of all header fields.
        """
        if len(dex_data) < 112:
            return {'error': f'Data too short: {len(dex_data)} bytes'}
        
        import struct
        
        header = {}
        
        try:
            # Magic number (8 bytes)
            header['magic'] = dex_data[0:8].hex()
            header['magic_ascii'] = dex_data[0:8].decode('ascii', errors='replace')
            
            # Checksum (4 bytes) - offset 8
            header['checksum'] = struct.unpack('<I', dex_data[8:12])[0]
            
            # Signature (20 bytes) - offset 12  
            header['signature'] = dex_data[12:32].hex()
            
            # File size (4 bytes) - offset 32
            header['file_size'] = struct.unpack('<I', dex_data[32:36])[0]
            
            # Header size (4 bytes) - offset 36
            header['header_size'] = struct.unpack('<I', dex_data[36:40])[0]
            
            # Endian tag (4 bytes) - offset 40
            header['endian_tag'] = struct.unpack('<I', dex_data[40:44])[0]
            
            # String IDs (size + offset) - offset 44
            header['string_ids_size'] = struct.unpack('<I', dex_data[44:48])[0]
            header['string_ids_off'] = struct.unpack('<I', dex_data[48:52])[0]
            
            # Type IDs (size + offset) - offset 52
            header['type_ids_size'] = struct.unpack('<I', dex_data[52:56])[0]
            header['type_ids_off'] = struct.unpack('<I', dex_data[56:60])[0]
            
            # Proto IDs (size + offset) - offset 60
            header['proto_ids_size'] = struct.unpack('<I', dex_data[60:64])[0]
            header['proto_ids_off'] = struct.unpack('<I', dex_data[64:68])[0]
            
            # Field IDs (size + offset) - offset 68
            header['field_ids_size'] = struct.unpack('<I', dex_data[68:72])[0]
            header['field_ids_off'] = struct.unpack('<I', dex_data[72:76])[0]
            
            # Method IDs (size + offset) - offset 76
            header['method_ids_size'] = struct.unpack('<I', dex_data[76:80])[0]
            header['method_ids_off'] = struct.unpack('<I', dex_data[80:84])[0]
            
            # Class defs (size + offset) - offset 84
            header['class_defs_size'] = struct.unpack('<I', dex_data[84:88])[0]
            header['class_defs_off'] = struct.unpack('<I', dex_data[88:92])[0]
            
            # Data size & offset - offset 92
            header['data_size'] = struct.unpack('<I', dex_data[92:96])[0]
            header['data_off'] = struct.unpack('<I', dex_data[96:100])[0]
            
            # Actual data size
            header['actual_size'] = len(dex_data)
            
            # Validation flags
            header['magic_valid'] = dex_data[0:8] in [b'dex\n035\x00', b'dex\n036\x00', b'dex\n037\x00', b'dex\n038\x00', b'dex\n039\x00']
            header['header_size_valid'] = header['header_size'] == 0x70
            header['file_size_matches'] = header['file_size'] == len(dex_data)
            header['endian_valid'] = header['endian_tag'] == 0x12345678
            
        except Exception as e:
            header['parse_error'] = str(e)
        
        return header
    
    def run_runtime_on_apk(self, apk_path: Path) -> Tuple[int, str, str]:
        """
        Run MiniAndroid runtime on APK and capture error.
        
        Returns: (exit_code, stdout, stderr)
        """
        if not self.runtime_binary.exists():
            return -1, "", "Runtime binary not found"
        
        # Create temp output dir
        temp_output = OUTPUT_DIR / f"runtime_test_{apk_path.stem}"
        temp_output.mkdir(exist_ok=True)
        
        try:
            cmd = [
                str(self.runtime_binary),
                'run',
                '-o', str(temp_output),
                str(apk_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(BASE_DIR)
            )
            
            # Read crash log if exists
            crash_log_content = ""
            crash_log = temp_output / "crash.log"
            if crash_log.exists():
                crash_log_content = crash_log.read_text()
            
            return result.returncode, result.stdout + "\n" + result.stderr, crash_log_content
            
        except subprocess.TimeoutExpired:
            return -1, "", "Execution timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def collect_baseline_for_apk(self, apk_path: Path, category: str) -> APKBaselineEntry:
        """Collect complete baseline data for one APK."""
        entry = APKBaselineEntry(
            name=apk_path.stem,
            path=str(apk_path),
            category=category,
            timestamp=datetime.now().isoformat()
        )
        
        print(f"\n{'='*60}")
        print(f"ANALYZING: {entry.name} ({category})")
        print(f"{'='*60}")
        
        # APK basic info
        entry.apk_size = apk_path.stat().st_size
        entry.apk_sha256 = self.calculate_sha256(apk_path)
        print(f"APK Size: {entry.apk_size:,} bytes")
        print(f"APK SHA256: {entry.apk_sha256[:32]}...")
        
        # Extract DEX
        dex_data, dex_path = self.extract_dex_from_apk(apk_path)
        
        if dex_data is None:
            entry.parser_state = "NO_DEX_FOUND"
            entry.runtime_error = "Could not extract classes.dex from APK"
            print(f"❌ No classes.dex found in APK")
            return entry
        
        entry.dex_size = len(dex_data)
        entry.dex_sha256 = self.calculate_sha256(dex_path) if dex_path else ""
        print(f"DEX Size: {entry.dex_size:,} bytes")
        print(f"DEX SHA256: {entry.dex_sha256[:32]}...")
        
        # Capture header bytes (first 112 bytes = standard DEX header)
        header_bytes = dex_data[:112]
        entry.header_bytes_hex = header_bytes.hex()
        print(f"Header (112 bytes): {entry.header_bytes_hex[:64]}...")
        
        # Parse header fields
        entry.header_parsed = self.parse_dex_header_raw(dex_data)
        print(f"\nHeader Parsed:")
        for key, value in entry.header_parsed.items():
            if not key.startswith('_'):
                print(f"  {key}: {value}")
        
        # Run runtime
        print(f"\nRunning runtime...")
        exit_code, stdout, crash_log = self.run_runtime_on_apk(apk_path)
        entry.runtime_exit_code = exit_code
        entry.runtime_error = crash_log if crash_log else stdout[-500:]  # Last 500 chars
        
        # Determine parser state
        if "PARSE_ERROR" in entry.runtime_error or "Invalid header" in entry.runtime_error:
            entry.parser_state = "PARSE_ERROR"
        elif "DEX loaded" in entry.runtime_error or "parse_dex" in entry.runtime_error.lower():
            entry.parser_state = "DEX_LOADED"
        elif exit_code == 0:
            entry.parser_state = "EXECUTION_COMPLETE"
        else:
            entry.parser_state = "UNKNOWN_STATE"
        
        print(f"\nRuntime Result:")
        print(f"  Exit Code: {exit_code}")
        print(f"  Parser State: {entry.parser_state}")
        print(f"  Error Preview: {entry.runtime_error[:200]}...")
        
        return entry
    
    def collect_all_baselines(self) -> Dict:
        """Collect baselines for all target APKs."""
        print("=" * 70)
        print("EXP-028: BASELINE FREEZE")
        print("Collecting working vs failing APK data for DEX investigation")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Runtime: {self.runtime_binary}")
        
        # Define targets
        targets = []
        
        # 1. WORKING: HelloWorld
        hello_world = BASE_DIR / "test_apks" / "HelloWorld.apk"
        if hello_world.exists():
            targets.append((hello_world, "working_simple"))
        
        # 2. FAILING: Simple app from EXP-027
        simple_apps = [
            ("OpenCalculator", "failing_simple"),
            ("QuickNotes", "failing_simple"),
            ("TodoMaster", "failing_simple"),
        ]
        
        for name, cat in simple_apps:
            apk_path = BASE_DIR / "download" / "exp027_real_apks" / f"{name}.apk"
            if apk_path.exists():
                targets.append((apk_path, cat))
        
        # 3. FAILING: Medium complexity apps
        medium_apps = [
            ("FileManagerPro", "failing_medium"),
            ("MusicBoxPlayer", "failing_medium"),
        ]
        
        for name, cat in medium_apps:
            apk_path = BASE_DIR / "download" / "exp027_real_apks" / f"{name}.apk"
            if apk_path.exists():
                targets.append((apk_path, cat))
        
        # 4. FAILING: Complex app
        complex_app = BASE_DIR / "download" / "exp027_real_apks" / "EmailClientPro.apk"
        if complex_app.exists():
            targets.append((complex_app, "failing_complex"))
        
        # 5. FAILING: Original HelloWorld from EXP-025 (if different)
        original_hw = BASE_DIR / "download" / "apks" / "HelloWorld_original.apk"
        if original_hw.exists():
            targets.append((original_hw, "failing_original"))
        
        print(f"\nTargets identified: {len(targets)}")
        
        # Collect each
        for apk_path, category in targets:
            entry = self.collect_baseline_for_apk(apk_path, category)
            self.entries.append(entry)
        
        # Generate summary
        summary = self._generate_summary()
        
        # Save baseline
        baseline_data = {
            'experiment': 'EXP-028',
            'phase': 'BASELINE_FREEZE',
            'timestamp': datetime.now().isoformat(),
            'runtime_binary': str(self.runtime_binary),
            'runtime_exists': self.runtime_binary.exists(),
            'total_analyzed': len(self.entries),
            'entries': [asdict(e) for e in self.entries],
            'summary': summary
        }
        
        baseline_file = OUTPUT_DIR / "exp028_baseline.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2, default=str)
        
        print(f"\n{'='*70}")
        print("BASELINE COLLECTION COMPLETE")
        print(f"{'='*70}")
        print(f"Total APKs analyzed: {len(self.entries)}")
        print(f"Baseline saved to: {baseline_file}")
        
        # Print comparison table
        self._print_comparison_table()
        
        return baseline_data
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics."""
        working = [e for e in self.entries if 'working' in e.category]
        failing = [e for e in self.entries if 'failing' in e.category]
        
        return {
            'working_count': len(working),
            'failing_count': len(failing),
            'working_states': list(set(e.parser_state for e in working)),
            'failing_states': list(set(e.parser_state for e in failing)),
            'common_errors': self._find_common_errors(failing)
        }
    
    def _find_common_errors(self, entries: List[APKBaselineEntry]) -> List[str]:
        """Find common error patterns in failing entries."""
        error_patterns = []
        for entry in entries:
            if entry.runtime_error:
                # Extract first meaningful line
                for line in entry.runtime_error.split('\n'):
                    if 'Error' in line or 'error' in line or 'Invalid' in line:
                        error_patterns.append(line.strip()[:100])
                        break
        return error_patterns
    
    def _print_comparison_table(self):
        """Print side-by-side comparison of working vs failing."""
        print(f"\n{'='*70}")
        print("COMPARISON TABLE: Working vs Failing")
        print(f"{'='*70}")
        
        print(f"\n{'Name':<25} {'Category':<20} {'State':<18} {'DEX Size':>10}")
        print("-" * 75)
        
        for entry in sorted(self.entries, key=lambda x: x.category):
            print(f"{entry.name:<25} {entry.category:<20} {entry.parser_state:<18} {entry.dex_size:>10,}")


def main():
    """Main entry point."""
    collector = BaselineCollector()
    baseline = collector.collect_all_baselines()
    
    if len(collector.entries) >= 5:
        print("\n✅ Baseline collected successfully (5+ APKs)")
        return 0
    else:
        print(f"\n⚠️ Only collected {len(collector.entries)} APKs (target: 5+)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
