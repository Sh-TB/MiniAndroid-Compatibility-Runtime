#!/usr/bin/env python3
"""
EXP-028: Phase 4 — DEX Loader Validation
============================================
Tests fixed DEX generator output against MiniAndroid runtime.

Validates:
- DEX header parsing success
- Classes extracted
- Methods counted
- Strings counted
- Types counted

Tests minimum 10 APKs including:
- HelloWorld (regression baseline)
- Simple apps
- Medium apps
- Complex apps
"""

import json
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Configuration
BASE_DIR = Path("/home/z/my-project/miniandroid")
RUNTIME = BASE_DIR / "build_exp028" / "miniandroid"
APK_DIR = BASE_DIR / "download" / "exp027_real_apks"
OUTPUT_FILE = BASE_DIR / "run" / "exp028" / "exp028_dex_validation.json"


def validate_single_apk(apk_path: Path, runtime: Path) -> Dict:
    """Validate single APK through runtime."""
    result = {
        'apk_name': apk_path.stem,
        'apk_path': str(apk_path),
        'dex_loaded': False,
        'header_valid': False,
        'classes_count': 0,
        'methods_count': 0,
        'strings_count': 0,
        'types_count': 0,
        'runtime_exit_code': -1,
        'runtime_output': '',
        'error': '',
        'validation_time': ''
    }
    
    if not apk_path.exists():
        result['error'] = 'APK file not found'
        return result
    
    # Extract DEX info
    try:
        with zipfile.ZipFile(apk_path, 'r') as zf:
            if 'classes.dex' in zf.namelist():
                dex_info = zf.getinfo('classes.dex')
                result['dex_file_size'] = dex_info.file_size
            else:
                result['error'] = 'No classes.dex in APK'
                return result
    except Exception as e:
        result['error'] = f'ZIP error: {e}'
        return result
    
    # Run runtime
    try:
        cmd = [
            str(runtime),
            'analyze',  # Use analyze command for DEX parsing only
            str(apk_path)
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BASE_DIR)
        )
        
        result['runtime_exit_code'] = proc.returncode
        result['runtime_output'] = proc.stdout + "\n" + proc.stderr
        
        # Parse output for validation info
        output = result['runtime_output']
        
        # Check for DEX loading success
        if 'DEX version' in output or 'parsed' in output.lower():
            result['dex_loaded'] = True
            result['header_valid'] = True
        
        # Check for header validation errors
        if 'Invalid header size' in output or 'Invalid magic' in output:
            result['header_valid'] = False
            result['error'] = 'Header validation failed'
        
        # Try to extract counts from output
        import re
        
        classes_match = re.search(r'(\d+)\s*classes?', output, re.IGNORECASE)
        if classes_match:
            result['classes_count'] = int(classes_match.group(1))
        
        methods_match = re.search(r'(\d+)\s*methods?', output, re.IGNORECASE)
        if methods_match:
            result['methods_count'] = int(methods_match.group(1))
        
        strings_match = re.search(r'(\d+)\s*strings?', output, re.IGNORECASE)
        if strings_match:
            result['strings_count'] = int(strings_match.group(1))
        
        types_match = re.search(r'(\d+)\s*types?', output, re.IGNORECASE)
        if types_match:
            result['types_count'] = int(types_match.group(1))
        
        # Determine overall status
        if result['runtime_exit_code'] == 0 and result['header_valid']:
            result['status'] = 'DEX_LOAD_SUCCESS'
        elif result['header_valid'] and not result['error']:
            result['status'] = 'DEX_LOADED_WITH_WARNINGS'
        else:
            result['status'] = 'DEX_LOAD_FAIL'
            
    except subprocess.TimeoutExpired:
        result['error'] = 'Runtime timeout'
        result['status'] = 'TIMEOUT'
    except Exception as e:
        result['error'] = str(e)
        result['status'] = 'ERROR'
    
    result['validation_time'] = datetime.now().isoformat()
    return result


def main():
    """Run Phase 4 validation."""
    print("=" * 70)
    print("EXP-028: PHASE 4 — DEX LOADER VALIDATION")
    print("=" * 70)
    print(f"Runtime: {RUNTIME}")
    print(f"APK Directory: {APK_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    if not RUNTIME.exists():
        print(f"❌ ERROR: Runtime not found at {RUNTIME}")
        return 1
    
    # Define test APKs (minimum 10)
    test_apks = [
        # Regression: HelloWorld must still work
        ("HelloWorld", BASE_DIR / "test_apks" / "HelloWorld.apk", "regression_baseline"),
        
        # Simple apps (from EXP-027 corpus)
        ("OpenCalculator", APK_DIR / "OpenCalculator.apk", "simple"),
        ("QuickNotes", APK_DIR / "QuickNotes.apk", "simple"),
        ("TodoMaster", APK_DIR / "TodoMaster.apk", "simple"),
        ("PrecisionClock", APK_DIR / "PrecisionClock.apk", "simple"),
        ("TorchLite", APK_DIR / "TorchLite.apk", "simple"),
        
        # Medium apps
        ("FileManagerPro", APK_DIR / "FileManagerPro.apk", "medium"),
        ("MusicBoxPlayer", APK_DIR / "MusicBoxPlayer.apk", "medium"),
        ("WeatherNow", APK_DIR / "WeatherNow.apk", "medium"),
        
        # Complex app
        ("EmailClientPro", APK_DIR / "EmailClientPro.apk", "complex"),
    ]
    
    results = []
    stats = {
        'total_tested': 0,
        'dex_load_success': 0,
        'dex_load_fail': 0,
        'timeout': 0,
        'by_category': {}
    }
    
    print(f"\nTesting {len(test_apks)} APKs...\n")
    
    for name, path, category in test_apks:
        print(f"[{len(results)+1}/{len(test_apks)}] {name} ({category})")
        
        result = validate_single_apk(path, RUNTIME)
        result['category'] = category
        results.append(result)
        
        stats['total_tested'] += 1
        
        # Update stats
        status = result.get('status', 'UNKNOWN')
        if status == 'DEX_LOAD_SUCCESS':
            stats['dex_load_success'] += 1
            print(f"  ✅ SUCCESS: {result.get('classes_count', '?')} classes, {result.get('methods_count', '?')} methods")
        elif status == 'DEX_LOADED_WITH_WARNINGS':
            stats['dex_load_success'] += 1
            print(f"  ⚠️  PARTIAL: Loaded with warnings")
        elif status == 'TIMEOUT':
            stats['timeout'] += 1
            print(f"  ⏰ TIMEOUT")
        else:
            stats['dex_load_fail'] += 1
            print(f"  ❌ FAIL: {result.get('error', 'Unknown error')[:60]}")
        
        # Category stats
        cat_stats = stats['by_category'].setdefault(category, {'success': 0, 'fail': 0})
        if 'SUCCESS' in status:
            cat_stats['success'] += 1
        else:
            cat_stats['fail'] += 1
    
    # Generate report
    validation_data = {
        'experiment': 'EXP-028',
        'phase': 'DEX_LOADER_VALIDATION',
        'timestamp': datetime.now().isoformat(),
        'runtime_binary': str(RUNTIME),
        'runtime_sha256': '',  # Would calculate if needed
        'statistics': stats,
        'results': results,
        'success_criteria': {
            'min_apks_tested': 10,
            'actual_tested': stats['total_tested'],
            'min_pass_rate': 0.8,  # 80% should pass
            'actual_pass_rate': round(stats['dex_load_success'] / max(stats['total_tested'], 1) * 100, 1),
            'helloworld_passed': next((r for r in results if r['apk_name'] == 'HelloWorld'), {}).get('status', '') == 'DEX_LOAD_SUCCESS'
        }
    }
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(validation_data, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total Tested: {stats['total_tested']}")
    print(f"✅ Success:   {stats['dex_load_success']}")
    print(f"❌ Failed:    {stats['dex_load_fail']}")
    print(f"⏰ Timeout:   {stats['timeout']}")
    
    if stats['total_tested'] > 0:
        pass_rate = (stats['dex_load_success'] / stats['total_tested']) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")
    
    print("\nBy Category:")
    for cat, cat_stats in stats['by_category'].items():
        total = cat_stats['success'] + cat_stats['fail']
        rate = (cat_stats['success'] / max(total, 1)) * 100
        print(f"  {cat:15s}: {cat_stats['success']}/{total} ({rate:.0f}%)")
    
    print(f"\n📄 Results saved to: {OUTPUT_FILE}")
    
    # Return success if we tested enough and pass rate is good
    if stats['total_tested'] >= 10 and stats['dex_load_success'] >= 8:
        print("\n✅ PHASE 4 COMPLETE: DEX loading working!")
        return 0
    else:
        print("\n⚠️ PHASE 4 COMPLETE with issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
