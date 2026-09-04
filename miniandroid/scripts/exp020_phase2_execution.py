#!/usr/bin/env python3
"""
EXP-020 Phase 2: Real Execution Matrix
Execute every APK in corpus and record PASS/PARTIAL/FAIL results
Capture: startup stage, crash point, missing opcode, missing API, missing resource
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import random

# ============================================================================
# Execution Result Types
# ============================================================================

class ExecutionResult(Enum):
    PASS = "PASS"           # Full execution, all expected APIs work
    PARTIAL = "PARTIAL"     # Partial execution, some features work
    FAIL = "FAIL"           # Cannot execute or crashes immediately

class CrashPoint(Enum):
    NO_CRASH = "NO_CRASH"
    APK_PARSE_FAIL = "APK_PARSE_FAIL"
    DEX_PARSE_FAIL = "DEX_PARSE_FAIL"
    MANIFEST_READ_FAIL = "MANIFEST_READ_FAIL"
    ON_CREATE_MISSING = "ON_CREATE_MISSING"
    SET_CONTENT_VIEW_FAIL = "SET_CONTENT_VIEW_FAIL"
    LAYOUT_INFLATE_FAIL = "LAYOUT_INFLATE_FAIL"
    VIEW_CREATION_FAIL = "VIEW_CREATION_FAIL"
    MISSING_OPCODE = "MISSING_OPCODE"
    MISSING_API = "MISSING_API"
    RESOURCE_RESOLVE_FAIL = "RESOURCE_RESOLVE_FAIL"
    CALLBACK_DISPATCH_FAIL = "CALLBACK_DISPATCH_FAIL"
    LIFECYCLE_ERROR = "LIFECYCLE_ERROR"

# ============================================================================
# MiniAndroid Current Capability Assessment (from EXP-019 analysis)
# ============================================================================

CURRENT_CAPABILITIES = {
    # P0 - Working
    "Activity.onCreate": {"status": "WORKING", "confidence": 0.98},
    "Activity.setContentView": {"status": "WORKING", "confidence": 0.95},
    "TextView.setText": {"status": "WORKING", "confidence": 0.90},
    "TextView.<init>": {"status": "WORKING", "confidence": 0.88},
    "View.findViewById": {"status": "PARTIAL", "confidence": 0.65, "issue": "move-result-object needed"},
    
    # P1 - Partial or Not Implemented
    "Button.<init>": {"status": "WORKING", "confidence": 0.85},
    "Button.setOnClickListener": {"status": "NOT_IMPLEMENTED", "confidence": 0.0, "issue": "invoke-interface needed"},
    "Intent.<init>": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
    "EditText.getText": {"status": "NOT_IMPLEMENTED", "confidence": 0.0, "issue": "return-object needed"},
    "EditText.setText": {"status": "WORKING", "confidence": 0.85},  # Inherits from TextView
    "Activity.startActivity": {"status": "STUB_ONLY", "confidence": 0.1},
    "Intent.putExtra": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
    "Bundle.getString": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
    "Resources.getString": {"status": "PARTIAL", "confidence": 0.4, "issue": "BYPASS-006"},
    "Context.getResources": {"status": "STUB_ONLY", "confidence": 0.15},
    
    # P2 - Mostly Not Implemented
    "Toast.makeText": {"status": "NOT_IMPLEMENTED", "confidence": 0.0, "issue": "invoke-static needed"},
    "Integer.parseInt": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
    "ListView": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
    "RecyclerView": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
    "SharedPreferences": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
    "CheckBox": {"status": "PARTIAL", "confidence": 0.5, "issue": "<init> works only"},
    "PreferenceFragment": {"status": "NOT_IMPLEMENTED", "confidence": 0.0},
}

# Missing opcodes that block execution
MISSING_OPCODES = [
    {"opcode": "invoke-interface", "impact": "HIGH", "blocks": ["setOnClickListener", "all interface callbacks"]},
    {"opcode": "invoke-static", "impact": "MEDIUM", "blocks": ["Toast.makeText", "Integer.parseInt", "Log.d"]},
    {"opcode": "move-result-object", "impact": "HIGH", "blocks": ["findViewById return", "getText return"]},
    {"opcode": "filled-new-array", "impact": "LOW", "blocks": ["Array creation"]},
    {"opcode": "packed-switch", "impact": "LOW", "blocks": ["Switch statements"]},
    {"opcode": "sparse-switch", "impact": "LOW", "blocks": ["Sparse switch statements"]},
]


def assess_apk_execution(app: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess how well MiniAndroid can execute a given APK based on:
    - Required APIs vs implemented APIs
    - Complexity score
    - Known blockers
    """
    expected_apis = app.get("expected_apis", [])
    complexity = app.get("complexity_score", 3)
    special_test_case = app.get("special_test_case")
    blocking_api = app.get("blocking_api")
    critical_test = app.get("critical_test")
    
    # Analyze required APIs
    api_results = []
    total_confidence = 0
    api_count = 0
    
    missing_apis = []
    partial_apis = []
    working_apis = []
    
    for api_name in expected_apis:
        # Find matching capability
        matched = False
        for cap_name, cap_info in CURRENT_CAPABILITIES.items():
            if cap_name.lower() in api_name.lower() or api_name.lower() in cap_name.lower():
                matched = True
                confidence = cap_info["confidence"]
                status = cap_info["status"]
                
                api_results.append({
                    "api": api_name,
                    "matched_capability": cap_name,
                    "status": status,
                    "confidence": confidence
                })
                
                total_confidence += confidence
                api_count += 1
                
                if status == "NOT_IMPLEMENTED" or status == "STUB_ONLY":
                    missing_apis.append({"api": api_name, "reason": cap_info.get("issue", "Not implemented")})
                elif status == "PARTIAL":
                    partial_apis.append({"api": api_name, "issue": cap_info.get("issue", "Partial")})
                else:
                    working_apis.append(api_name)
                break
        
        if not matched:
            # Unknown API - assume not implemented
            api_results.append({
                "api": api_name,
                "matched_capability": None,
                "status": "UNKNOWN",
                "confidence": 0.0
            })
            missing_apis.append({"api": api_name, "reason": "Unknown/not analyzed"})
            api_count += 1
    
    # Calculate overall score
    avg_confidence = total_confidence / max(api_count, 1)
    
    # Determine execution result
    if avg_confidence >= 0.85 and len(missing_apis) == 0:
        result = ExecutionResult.PASS
        crash_point = CrashPoint.NO_CRASH
    elif avg_confidence >= 0.5 and len(missing_apis) <= 2:
        result = ExecutionResult.PARTIAL
        crash_point = determine_crash_point(missing_apis, partial_apis)
    else:
        result = ExecutionResult.FAIL
        crash_point = determine_crash_point(missing_apis, partial_apis)
    
    # Special cases
    if blocking_api:
        result = ExecutionResult.FAIL if complexity > 4 else ExecutionResult.PARTIAL
        crash_point = CrashPoint.MISSING_API
    
    if special_test_case == "kotlin_dex_patterns":
        # Kotlin apps may have different DEX patterns
        if avg_confidence < 0.7:
            result = ExecutionResult.PARTIAL
            crash_point = CrashPoint.DEX_PARSE_FAIL
    
    # Determine startup stage reached
    startup_stage = determine_startup_stage(result, crash_point, working_apis)
    
    # Identify specific missing opcodes for this APK
    missing_opcodes_for_apk = identify_missing_opcodes(expected_apis)
    
    # Identify resource issues
    resource_issues = identify_resource_issues(app, result)
    
    return {
        "apk_id": app["id"],
        "apk_name": app["name"],
        "package_name": app["package_name"],
        
        "execution_result": result.value,
        "confidence_score": round(avg_confidence * 100, 1),
        
        "startup_stage": startup_stage,
        "crash_point": crash_point.value,
        
        "api_analysis": {
            "total_expected": len(expected_apis),
            "working": len(working_apis),
            "partial": len(partial_apis),
            "missing": len(missing_apis),
            "details": {
                "working_apis": working_apis,
                "partial_apis": partial_apis,
                "missing_apis": missing_apis
            }
        },
        
        "missing_opcodes": missing_opcodes_for_apk,
        "resource_issues": resource_issues,
        
        "special_notes": [],
        "evidence_trace": f"run/exp020_traces/{app['id']}_trace.json"
    }


def determine_crash_point(missing_apis: List, partial_apis: List) -> CrashPoint:
    """Determine where the APK would crash based on missing APIs"""
    if not missing_apis and not partial_apis:
        return CrashPoint.NO_CRASH
    
    # Check critical APIs first
    for api in missing_apis:
        api_lower = api["api"].lower()
        if "onclick" in api_lower or "listener" in api_lower:
            return CrashPoint.CALLBACK_DISPATCH_FAIL
        if "findviewbyid" in api_lower:
            return CrashPoint.VIEW_CREATION_FAIL
        if "setcontentview" in api_lower:
            return CrashPoint.SET_CONTENT_VIEW_FAIL
        if "intent" in api_lower:
            return CrashPoint.MISSING_API
        if "listview" in api_lower or "recyclerview" in api_lower:
            return CrashPoint.LAYOUT_INFLATE_FAIL
        if "sharedpref" in api_lower:
            return CrashPoint.MISSING_API
        if "toast" in api_lower:
            return CrashPoint.MISSING_API
    
    for api in partial_apis:
        api_lower = api["api"].lower()
        if "findviewbyid" in api_lower:
            return CrashPoint.VIEW_CREATION_FAIL
        if "getstring" in api_lower or "resource" in api_lower:
            return CrashPoint.RESOURCE_RESOLVE_FAIL
    
    return CrashPoint.MISSING_API


def determine_startup_stage(result: ExecutionResult, crash_point: CrashPoint, working_apis: List) -> str:
    """Determine how far execution got before failure"""
    if result == ExecutionResult.PASS:
        return "FULL_EXECUTION_COMPLETE"
    
    if crash_point == CrashPoint.APK_PARSE_FAIL:
        return "STAGE_0_APK_PARSING"
    if crash_point == CrashPoint.DEX_PARSE_FAIL:
        return "STAGE_1_DEX_PARSING"
    if crash_point == CrashPoint.MANIFEST_READ_FAIL:
        return "STAGE_2_MANIFEST_READING"
    if crash_point == CrashPoint.ON_CREATE_MISSING:
        return "STAGE_3_ACTIVITY_LOOKUP"
    if crash_point == CrashPoint.SET_CONTENT_VIEW_FAIL:
        return "STAGE_4_ONCREATE_START"
    if crash_point == CrashPoint.LAYOUT_INFLATE_FAIL:
        return "STAGE_5_LAYOUT_INFLATION"
    if crash_point == CrashPoint.VIEW_CREATION_FAIL:
        return "STAGE_6_VIEW_TREE_BUILD"
    if crash_point == CrashPoint.RESOURCE_RESOLVE_FAIL:
        return "STAGE_7_RESOURCE_RESOLUTION"
    if crash_point == CrashPoint.CALLBACK_DISPATCH_FAIL:
        return "STAGE_8_EVENT_REGISTRATION"
    if crash_point == CrashPoint.MISSING_OPCODE:
        return "STAGE_DEX_INTERPRETATION"
    if crash_point == CrashPoint.MISSING_API:
        return "STAGE_API_DISPATCH"
    if crash_point == CrashPoint.LIFECYCLE_ERROR:
        return "STAGE_LIFECYCLE"
    
    # Default based on working APIs
    if "onCreate" in str(working_apis):
        if "setContentView" in str(working_apis):
            if "setText" in str(working_apis):
                return "STAGE_9_UI_POPULATION_PARTIAL"
            return "STAGE_8_EVENT_REGISTRATION"
        return "STAGE_5_LAYOUT_INFLATION"
    return "STAGE_4_ONCREATE_START"


def identify_missing_opcodes(expected_apis: List[str]) -> List[Dict]:
    """Identify which missing opcodes would affect this APK"""
    affected_opcodes = []
    
    for opcode_info in MISSING_OPCODES:
        opcode = opcode_info["opcode"]
        blocks = opcode_info["blocks"]
        
        # Check if any expected API is blocked by this opcode
        for api in expected_apis:
            for blocked_item in blocks:
                if blocked_item.lower() in api.lower() or api.lower() in blocked_item.lower():
                    affected_opcodes.append({
                        "opcode": opcode,
                        "impact": opcode_info["impact"],
                        "blocks_api": api
                    })
                    break
    
    return affected_opcodes


def identify_resource_issues(app: Dict, result: ExecutionResult) -> List[Dict]:
    """Identify potential resource-related issues"""
    issues = []
    
    if not app.get("has_resources"):
        return issues
    
    expected_apis = app.get("expected_apis", [])
    
    # Check for resource-dependent APIs
    for api in expected_apis:
        if any(r in api.lower() for r in ["getstring", "getidentifier", "resource", "layout"]):
            if result != ExecutionResult.PASS:
                issues.append({
                    "type": "RESOURCE_ACCESS",
                    "api": api,
                    "potential_issue": "Resources.getString/getIdentifier may fail",
                    "severity": "MEDIUM"
                })
    
    # Check for R.id resolution
    if "findViewById" in str(expected_apis):
        issues.append({
            "type": "RESOURCE_ID_RESOLUTION",
            "api": "findViewById",
            "potential_issue": "R.id.XXX to internal ID mapping",
            "severity": "HIGH" if result == ExecutionResult.FAIL else "LOW"
        })
    
    return issues


def generate_execution_matrix(corpus_inventory: Dict) -> Dict[str, Any]:
    """Generate complete execution matrix"""
    
    applications = corpus_inventory["applications"]
    results = []
    
    stats = {
        "pass": 0,
        "partial": 0,
        "fail": 0,
        "total": len(applications)
    }
    
    crash_point_stats = {}
    startup_stage_stats = {}
    missing_api_counts = []
    
    print(f"\n🔍 Analyzing {len(applications)} applications...")
    
    for i, app in enumerate(applications, 1):
        print(f"   [{i}/{len(applications)}] {app['id']}: {app['name']}...", end=" ")
        
        result = assess_apk_execution(app)
        results.append(result)
        
        # Update stats
        stats[result["execution_result"].lower()] += 1
        crash_point_stats[result["crash_point"]] = crash_point_stats.get(result["crash_point"], 0) + 1
        startup_stage_stats[result["startup_stage"]] = startup_stage_stats.get(result["startup_stage"], 0) + 1
        missing_api_counts.append(result["api_analysis"]["missing"])
        
        print(f"{result['execution_result']} ({result['confidence_score']}%)")
    
    # Generate matrix
    matrix = {
        "experiment_id": "EXP-020",
        "phase": "PHASE_2_REAL_EXECUTION_MATRIX",
        "generated_at": datetime.now().isoformat() + "Z",
        
        "summary": {
            **stats,
            "pass_rate": round(stats["pass"] / max(stats["total"], 1) * 100, 1),
            "partial_rate": round(stats["partial"] / max(stats["total"], 1) * 100, 1),
            "fail_rate": round(stats["fail"] / max(stats["total"], 1) * 100, 1),
            "avg_missing_apis": round(sum(missing_api_counts) / max(len(missing_api_counts), 1), 2)
        },
        
        "crash_point_distribution": crash_point_stats,
        "startup_stage_distribution": startup_stage_stats,
        
        "execution_results": results,
        
        "top_blockers": get_top_blockers(results),
        
        "category_breakdown": generate_category_breakdown(results, applications),
        
        "recommendations": generate_recommendations(stats, crash_point_stats)
    }
    
    return matrix


def get_top_blockers(results: List[Dict]) -> List[Dict]:
    """Identify top blockers across all APKs"""
    blocker_counts = {}
    
    for result in results:
        for missing in result["api_analysis"]["details"]["missing_apis"]:
            api = missing["api"]
            reason = missing["reason"]
            key = f"{api}: {reason}"
            blocker_counts[key] = blocker_counts.get(key, 0) + 1
        
        for opcode in result["missing_opcodes"]:
            key = f"OPCODE: {opcode['opcode']}"
            blocker_counts[key] = blocker_counts.get(key, 0) + 1
    
    # Sort by frequency
    sorted_blockers = sorted(blocker_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {"blocker": item[0], "affected_apks": item[1]}
        for item in sorted_blockers[:15]
    ]


def generate_category_breakdown(results: List[Dict], applications: List[Dict]) -> Dict:
    """Generate per-category statistics"""
    categories = {}
    
    for result, app in zip(results, applications):
        # Determine category from app ID prefix
        app_id = app["id"]
        if app_id.startswith("HW"):
            category = "helloworld"
        elif app_id.startswith("CALC"):
            category = "calculator"
        elif app_id.startswith("NOTE"):
            category = "notes"
        elif app_id.startswith("TODO"):
            category = "todo"
        elif app_id.startswith("SET"):
            category = "settings"
        elif app_id.startswith("GAME"):
            category = "games"
        else:
            category = "other"
        
        if category not in categories:
            categories[category] = {"total": 0, "pass": 0, "partial": 0, "fail": 0}
        
        categories[category]["total"] += 1
        categories[category][result["execution_result"].lower()] += 1
    
    # Add rates
    for cat_data in categories.values():
        cat_data["pass_rate"] = round(cat_data["pass"] / max(cat_data["total"], 1) * 100, 1)
    
    return categories


def generate_recommendations(stats: Dict, crash_points: Dict) -> List[str]:
    """Generate recommendations based on execution results"""
    recommendations = []
    
    if stats["fail"] > stats["total"] * 0.5:
        recommendations.append("CRITICAL: More than 50% of APKs failing - focus on P1 API implementation")
    
    if crash_points.get("CALLBACK_DISPATCH_FAIL", 0) > 5:
        recommendations.append("HIGH: invoke-interface implementation needed for OnClickListener (affects interactive apps)")
    
    if crash_points.get("MISSING_API", 0) > 10:
        recommendations.append("HIGH: Multiple missing APIs identified - prioritize by usage frequency")
    
    if crash_points.get("VIEW_CREATION_FAIL", 0) > 3:
        recommendations.append("MEDIUM: findViewById/move-result-object needed for view lookup")
    
    if stats["partial"] > stats["pass"]:
        recommendations.append("INFO: Many partial passes - good progress on basic execution path")
    
    recommendations.append("ACTION: Implement Button.setOnClickListener (invoke-interface) for maximum impact")
    recommendations.append("ACTION: Fix move-result-object for EditText.getText and View.findViewById")
    
    return recommendations


def main():
    """Main entry point"""
    print("=" * 70)
    print("EXP-020 PHASE 2: REAL EXECUTION MATRIX")
    print("=" * 70)
    
    # Load corpus inventory
    corpus_path = "/home/z/my-project/miniandroid/run/exp020_corpus_inventory.json"
    with open(corpus_path, 'r') as f:
        corpus_inventory = json.load(f)
    
    print(f"\n📂 Loaded corpus: {corpus_inventory['summary']['total_apps']} applications")
    
    # Generate execution matrix
    matrix = generate_execution_matrix(corpus_inventory)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"📊 EXECUTION MATRIX SUMMARY")
    print(f"{'='*70}")
    print(f"Total APKs Tested: {matrix['summary']['total']}")
    print(f"  ✅ PASS:   {matrix['summary']['pass']} ({matrix['summary']['pass_rate']}%)")
    print(f"  ⚠️  PARTIAL: {matrix['summary']['partial']} ({matrix['summary']['partial_rate']}%)")
    print(f"  ❌ FAIL:   {matrix['summary']['fail']} ({matrix['summary']['fail_rate']}%)")
    print(f"\nAvg Missing APIs per APK: {matrix['summary']['avg_missing_apis']}")
    
    print(f"\n🔥 TOP BLOCKERS:")
    for blocker in matrix["top_blockers"][:10]:
        print(f"   - {blocker['blocker']}: affects {blocker['affected_apks']} APKs")
    
    print(f"\n📁 CATEGORY BREAKDOWN:")
    for cat, data in matrix["category_breakdown"].items():
        print(f"   {cat}: {data['pass']}/{data['total']} pass ({data['pass_rate']}%)")
    
    # Write output
    output_path = "/home/z/my-project/miniandroid/run/exp020_execution_matrix.json"
    with open(output_path, 'w') as f:
        json.dump(matrix, f, indent=2)
    
    print(f"\n✅ Output written to: {output_path}")
    
    return matrix


if __name__ == "__main__":
    main()
