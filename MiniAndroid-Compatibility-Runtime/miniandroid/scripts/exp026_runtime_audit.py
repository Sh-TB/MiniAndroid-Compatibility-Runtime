#!/usr/bin/env python3
"""
EXP-026 PHASE 0: Runtime Availability Audit
============================================
Comprehensive check of MiniAndroid runtime components.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("  EXP-026 RUNTIME AVAILABILITY AUDIT")
print("  Checking if real execution is possible")
print("=" * 70)
print(f"  Time: {datetime.now().isoformat()}")
print("=" * 70)

audit_result = {
    "experiment": "EXP-026",
    "phase": "RUNTIME_AUDIT",
    "timestamp": datetime.now().isoformat(),
    "overall_status": "UNKNOWN",
    "components": {},
    "build_status": {},
    "recommendations": []
}

base_dir = Path(".")
src_dir = base_dir / "src"

# === CHECK 1: Source Code Existence ===
print("\n[CHECK 1] Source code structure...")

source_files = {
    "runtime_engine": src_dir / "runtime" / "execution_engine.h",
    "apk_parser": src_dir / "apk" / "apk_parser.h", 
    "dex_parser": src_dir / "dex" / "dex_parser.h",
    "dex_interpreter": src_dir / "dex" / "dex_interpreter.h",
    "api_dispatcher": src_dir / "api" / "api_dispatcher.h",
    "renderer": src_dir / "renderer" / "renderer.h",
    "main_cpp": src_dir / "main.cpp",
    "cmake": base_dir / "CMakeLists.txt",
    "makefile": base_dir / "Makefile"
}

for name, path in source_files.items():
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    audit_result["components"][name] = {
        "path": str(path),
        "exists": exists,
        "size": size
    }
    status = "✓" if exists else "✗"
    print(f"  [{status}] {name}: {path.name}")

source_exists_count = sum(1 for v in audit_result["components"].values() if v["exists"])
print(f"\n  Source files: {source_exists_count}/{len(source_files)} present")

# === CHECK 2: Build System ===
print("\n[CHECK 2] Build system...")

has_cmake = (base_dir / "CMakeLists.txt").exists()
has_makefile = (base_dir / "Makefile").exists()

audit_result["build_system"] = {
    "cmake_available": has_cmake,
    "makefile_available": has_makefile
}

print(f"  CMakeLists.txt: {'✓' if has_cmake else '✗'}")
print(f"  Makefile: {'✓' if has_makefile else '✗'}")

# === CHECK 3: Compiler Availability ===
print("\n[CHECK 3] Compiler availability...")

compilers = {
    "g++": ["g++", "--version"],
    "clang++": ["clang++", "--version"],
    "cmake": ["cmake", "--version"],
    "make": ["make", "--version"]
}

compiler_status = {}
for name, cmd_list in compilers.items():
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=10)
        version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
        compiler_status[name] = {"available": True, "version": version_line[:80]}
        print(f"  ✓ {name}: {version_line[:60]}...")
    except FileNotFoundError:
        compiler_status[name] = {"available": False, "version": "N/A"}
        print(f"  ✗ {name}: NOT FOUND")
    except Exception as e:
        compiler_status[name] = {"available": False, "error": str(e)[:50]}
        print(f"  ✗ {name}: ERROR - {str(e)[:40]}")

audit_result["compilers"] = compiler_status

# === CHECK 4: Existing Binary ===
print("\n[CHECK 4] Existing runtime binary...")

binary_locations = [
    base_dir / "build" / "miniandroid",
    base_dir / "bin" / "miniandroid",
    base_dir / "miniandroid",
]

binary_found = False
for binary_path in binary_locations:
    if binary_path.exists():
        size = binary_path.stat().st_size
        is_exec = os.access(binary_path, os.X_OK)
        audit_result["existing_binary"] = {
            "path": str(binary_path),
            "exists": True,
            "size": size,
            "executable": is_exec
        }
        print(f"  ✓ Found: {binary_path} ({size} bytes, executable={is_exec})")
        binary_found = True
        break

if not binary_found:
    audit_result["existing_binary"] = {"exists": False}
    print(f"  ✗ No existing binary found - BUILD REQUIRED")

# === CHECK 5: Key Header Analysis ===
print("\n[CHECK 5] Runtime capability analysis...")

capabilities = {}

# Check DexInterpreter
dex_interp_path = src_dir / "dex" / "dex_interpreter.h"
if dex_interp_path.exists():
    try:
        content = dex_interp_path.read_text()
        has_execute_method = "execute" in content.lower() or "interpret" in content.lower()
        has_opcode_handling = "opcode" in content.lower() or "instruction" in content.lower()
        
        # Count key methods
        method_lines = [line.strip() for line in content.split('\n') 
                       if ('void ' in line or 'int ' in line or 'bool ' in line) 
                       and '(' in line]
        
        capabilities["dex_interpreter"] = {
            "can_execute": has_execute_method,
            "handles_opcodes": has_opcode_handling,
            "method_count": len(method_lines)
        }
        print(f"  DEX Interpreter:")
        print(f"    - Can execute: {has_execute_method}")
        print(f"    - Handles opcodes: {has_opcode_handling}")
        print(f"    - Methods: {len(method_lines)}")
    except Exception as e:
        capabilities["dex_interpreter"] = {"error": str(e)}
        print(f"  DEX Interpreter: ERROR reading - {e}")

# Check API Dispatcher  
api_dispatch_path = src_dir / "api" / "api_dispatcher.h"
if api_dispatch_path.exists():
    try:
        content = api_dispatch_path.read_text()
        has_dispatch = "dispatch" in content.lower()
        has_api_registry = "register" in content.lower() or "api" in content.lower()
        
        capabilities["api_dispatcher"] = {
            "can_dispatch": has_dispatch,
            "has_registry": has_api_registry
        }
        print(f"  API Dispatcher:")
        print(f"    - Can dispatch: {has_dispatch}")
        print(f"    - Has registry: {has_api_registry}")
    except Exception as e:
        capabilities["api_dispatcher"] = {"error": str(e)}

# Check APK Parser
apk_parser_path = src_dir / "apk" / "apk_parser.h"
if apk_parser_path.exists():
    try:
        content = apk_parser_path.read_text()
        can_parse_apk = "parse" in content.lower() or "zip" in content.lower()
        can_extract_dex = "dex" in content.lower()
        
        capabilities["apk_parser"] = {
            "can_parse_apk": can_parse_apk,
            "can_extract_dex": can_extract_dex
        }
        print(f"  APK Parser:")
        print(f"    - Can parse APK: {can_parse_apk}")
        print(f"    - Can extract DEX: {can_extract_dex}")
    except Exception as e:
        capabilities["apk_parser"] = {"error": str(e)}

audit_result["capabilities"] = capabilities

# === DETERMINE OVERALL STATUS ===
print("\n" + "=" * 70)
print("  AUDIT SUMMARY")
print("=" * 70)

issues = []
recommendations = []

# Check critical requirements
if source_exists_count < 6:
    issues.append("Insufficient source files")
    recommendations.append("Restore missing source files from git")

cpp_available = compiler_status.get("g++", {}).get("available") or compiler_status.get("clang++", {}).get("available")
if not cpp_available:
    issues.append("No C++ compiler available")
    recommendations.append("Install g++ (apt install g++)")

if not binary_found:
    issues.append("No pre-built binary - compilation required")
    
    if cpp_available:
        recommendations.append("Build from source using: make or cmake")
        audit_result["build_required"] = True
        audit_result["build_possible"] = True
    else:
        recommendations.append("CRITICAL: Install C++ compiler first")
        audit_result["build_blocked"] = True
        audit_result["build_possible"] = False

if issues:
    audit_result["overall_status"] = "NEEDS_WORK"
    audit_result["issues"] = issues
else:
    audit_result["overall_status"] = "READY"

audit_result["recommendations"] = recommendations

print(f"\n  Overall Status: {audit_result['overall_status']}")
print(f"\n  Issues Found ({len(issues)}):")
for issue in issues:
    print(f"    ⚠  {issue}")

print(f"\n  Recommendations ({len(recommendations)}):")
for i, rec in enumerate(recommendations, 1):
    print(f"    {i}. {rec}")

# Component status summary
print(f"\n  COMPONENT STATUS:")
component_statuses = {}
for comp_name, comp_info in audit_result.get("components", {}).items():
    status = "PASS" if comp_info.get("exists") else "FAIL"
    component_statuses[comp_name] = status
    print(f"    {comp_name:20s}: {status}")

audit_result["component_statuses"] = component_statuses

# Save audit result
output_path = Path("run/exp026_runtime_audit.json")
with open(output_path, 'w') as f:
    json.dump(audit_result, f, indent=2, default=str)

print(f"\n[SAVED] Audit result: {output_path}")

# Exit with appropriate code
if audit_result["overall_status"] == "READY":
    print("\n[RESULT] ✅ Runtime appears ready for build/execution")
    sys.exit(0)
elif audit_result.get("build_blocked"):
    print("\n[RESULT] ❌ BLOCKED - Compiler installation required")
    sys.exit(2)
else:
    print("\n[RESULT] ⚠️  NEEDS_WORK - Build required but possible")
    sys.exit(1)
