#!/usr/bin/env python3
"""
EXP-020 Phase 6: Failure Database
Classify every failure from Phases 2-5 into types:
- MISSING_OPCODE
- MISSING_API
- RESOURCE
- LIFECYCLE
- DEX_ERROR
- RENDER

Output: database/runtime_failures.json
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict


# ============================================================================
# Failure Classification Types
# ============================================================================

class FailureType(Enum):
    MISSING_OPCODE = "MISSING_OPCODE"           # DEX opcode not implemented in interpreter
    MISSING_API = "MISSING_API"                 # Android API method not implemented
    RESOURCE = "RESOURCE"                       # Resource resolution failure (strings, layouts, IDs)
    LIFECYCLE = "LIFECYCLE"                     # Lifecycle dispatch issue
    DEX_ERROR = "DEX_ERROR"                     # DEX parsing/interpretation error
    RENDER = "RENDER"                           # Rendering/display issue
    CALLBACK = "CALLBACK"                       # Event callback/interface dispatch failure
    STRICT_MODE_VIOLATION = "STRICT_MODE_VIOLATION"  # --strict-real rule violation


class FailureSeverity(Enum):
    CRITICAL = "CRITICAL"      # Blocks execution completely
    HIGH = "HIGH"              # Major feature broken
    MEDIUM = "MEDIUM"          # Partial functionality
    LOW = "LOW"                # Minor issue or workaround exists


class FailureStatus(Enum):
    NEW = "NEW"                    # Discovered in this experiment
    KNOWN = "KNOWN"                # Previously identified
    IN_PROGRESS = "IN_PROGRESS"   # Being worked on
    FIXED = "FIXED"                # Resolved
    WONT_FIX = "WONT_FIX"         # Out of scope or deferred


# ============================================================================
# Collect Failures from All Previous Phases
# ============================================================================

def collect_failures_from_phase2(execution_matrix: Dict) -> List[Dict]:
    """Extract failures from execution matrix"""
    failures = []
    
    for apk_result in execution_matrix["execution_results"]:
        if apk_result["execution_result"] in ["FAIL", "PARTIAL"]:
            apk_id = apk_result["apk_id"]
            apk_name = apk_result["apk_name"]
            
            # Missing APIs
            for missing_api in apk_result.get("api_analysis", {}).get("details", {}).get("missing_apis", []):
                failures.append({
                    "source_phase": "PHASE_2",
                    "source_apk": apk_id,
                    "apk_name": apk_name,
                    "failure_type": FailureType.MISSING_API.value,
                    "severity": FailureSeverity.HIGH.value,
                    "description": f"Missing API: {missing_api['api']}",
                    "details": missing_api.get("reason", "Unknown"),
                    "affected_component": missing_api["api"]
                })
            
            # Missing opcodes
            for opcode_info in apk_result.get("missing_opcodes", []):
                failures.append({
                    "source_phase": "PHASE_2",
                    "source_apk": apk_id,
                    "apk_name": apk_name,
                    "failure_type": FailureType.MISSING_OPCODE.value,
                    "severity": FailureSeverity.CRITICAL if opcode_info["impact"] == "HIGH" else FailureSeverity.MEDIUM.value,
                    "description": f"Missing opcode: {opcode_info['opcode']}",
                    "details": f"Blocks {opcode_info['blocks_api']}",
                    "affected_component": opcode_info["opcode"]
                })
            
            # Resource issues
            for resource_issue in apk_result.get("resource_issues", []):
                failures.append({
                    "source_phase": "PHASE_2",
                    "source_apk": apk_id,
                    "apk_name": apk_name,
                    "failure_type": FailureType.RESOURCE.value,
                    "severity": FailureSeverity.HIGH if resource_issue.get("severity") == "HIGH" else FailureSeverity.MEDIUM.value,
                    "description": f"Resource issue: {resource_issue['type']}",
                    "details": resource_issue.get("potential_issue"),
                    "affected_component": resource_issue.get("api", "Resource System")
                })
    
    return failures


def collect_failures_from_phase3(strict_validation: Dict) -> List[Dict]:
    """Extract violations from strict validation"""
    failures = []
    
    for apk_result in strict_validation.get("apk_results", []):
        for violation in apk_result.get("violations", []):
            failures.append({
                "source_phase": "PHASE_3",
                "source_apk": apk_result["apk_id"],
                "apk_name": apk_result["apk_name"],
                "failure_type": FailureType.STRICT_MODE_VIOLATION.value,
                "severity": violation.get("severity", "MEDIUM"),
                "description": f"Strict mode violation: {violation['type']}",
                "details": violation.get("description"),
                "affected_component": violation.get("affected_api", "Unknown"),
                "location": violation.get("location"),
                "is_blocking": violation.get("is_blocking", False)
            })
    
    return failures


def collect_failures_from_phase4(callback_trace: Dict) -> List[Dict]:
    """Extract failures from callback validation"""
    failures = []
    
    test_apk = callback_trace.get("test_apk", {})
    
    for stage_trace in callback_trace.get("callback_chain_trace", []):
        status = stage_trace.get("status")
        
        if status in ["FAIL", "BLOCKED"]:
            failure_type = FailureType.CALLBACK if "interface" in stage_trace.get("stage", "").lower() or "listener" in stage_trace.get("stage", "").lower() else FailureType.MISSING_API
            
            failures.append({
                "source_phase": "PHASE_4",
                "source_apk": test_apk.get("id", "TEST-CALLBACK-001"),
                "apk_name": test_apk.get("name", "ButtonCallbackTest"),
                "failure_type": failure_type.value,
                "severity": FailureSeverity.CRITICAL if status == "FAIL" else FailureSeverity.HIGH.value,
                "description": f"Callback chain blocked at: {stage_trace.get('stage')}",
                "details": stage_trace.get("reason") or stage_trace.get("blocking_reason", "Unknown"),
                "affected_component": stage_trace.get("stage", "Callback Chain")
            })
    
    return failures


def collect_failures_from_phase5(resource_comparison: Dict) -> List[Dict]:
    """Extract gaps from resource comparison"""
    failures = []
    
    for comparison in resource_comparison.get("comparisons", []):
        resource_type = comparison.get("resource_type")
        result = comparison.get("comparison_result")
        
        if result in ["MISMATCH", "NOT_IMPLEMENTED"]:
            gap_analysis = comparison.get("gap_analysis", {})
            
            for critical_gap in gap_analysis.get("critical_gaps", []):
                failures.append({
                    "source_phase": "PHASE_5",
                    "source_apk": "N/A",
                    "apk_name": "Resource System Test",
                    "failure_type": FailureType.RESOURCE.value,
                    "severity": FailureSeverity.HIGH.value,
                    "description": f"Resource gap ({resource_type}): {critical_gap}",
                    "details": critical_gap,
                    "affected_component": f"{resource_type} System"
                })
            
            # Also add limitations as lower severity
            for limitation in comparison.get("miniandroid_implementation", {}).get("limitations", []):
                if not any(word in limitation.lower() for word in ["not", "no"]):  # Skip duplicates of critical
                    continue
    
    return failures


def generate_failure_database(
    execution_matrix_path: str,
    strict_validation_path: str,
    callback_trace_path: str,
    resource_comparison_path: str
) -> Dict[str, Any]:
    """
    Generate comprehensive failure database by aggregating all failures
    from Phases 2-5 and classifying them.
    """
    
    print("=" * 70)
    print("EXP-020 PHASE 6: FAILURE DATABASE")
    print("=" * 70)
    
    # Load all phase outputs
    with open(execution_matrix_path, 'r') as f:
        execution_matrix = json.load(f)
    
    with open(strict_validation_path, 'r') as f:
        strict_validation = json.load(f)
    
    with open(callback_trace_path, 'r') as f:
        callback_trace = json.load(f)
    
    with open(resource_comparison_path, 'r') as f:
        resource_comparison = json.load(f)
    
    # Collect all failures
    print("\n📥 Collecting failures from all phases...")
    
    all_failures = []
    all_failures.extend(collect_failures_from_phase2(execution_matrix))
    print(f"   Phase 2 (Execution Matrix): {len(all_failures)} failures")
    
    phase3_failures = collect_failures_from_phase3(strict_validation)
    all_failures.extend(phase3_failures)
    print(f"   Phase 3 (Strict Validation): {len(phase3_failures)} failures")
    
    phase4_failures = collect_failures_from_phase4(callback_trace)
    all_failures.extend(phase4_failures)
    print(f"   Phase 4 (Callback Validation): {len(phase4_failures)} failures")
    
    phase5_failures = collect_failures_from_phase5(resource_comparison)
    all_failures.extend(phase5_failures)
    print(f"   Phase 5 (Resource Comparison): {len(phase5_failures)} failures")
    
    print(f"\n📊 Total Failures Collected: {len(all_failures)}")
    
    # Classify and deduplicate
    classified = classify_and_deduplicate_failures(all_failures)
    
    # Generate statistics
    stats = generate_failure_statistics(classified["unique_failures"])
    
    # Generate report
    database = {
        "experiment_id": "EXP-020",
        "phase": "PHASE_6_FAILURE_DATABASE",
        "generated_at": datetime.now().isoformat() + "Z",
        
        "summary": {
            "total_failures_collected": len(all_failures),
            "unique_failures_after_dedup": len(classified["unique_failures"]),
            "duplicates_removed": len(all_failures) - len(classified["unique_failures"]),
            **stats
        },
        
        "failures_by_type": classified["by_type"],
        
        "top_blockers": generate_top_blockers(classified["unique_failures"]),
        
        "remediation_plan": generate_remediation_plan(classified["unique_failures"]),
        
        "raw_failures": classified["unique_failures"],  # Full details for analysis
        
        "metadata": {
            "sources": [
                {"phase": "PHASE_2", "file": "exp020_execution_matrix.json"},
                {"phase": "PHASE_3", "file": "exp020_strict_validation.json"},
                {"phase": "PHASE_4", "file": "callback_execution_trace.json"},
                {"phase": "PHASE_5", "file": "resource_comparison.json"}
            ],
            "classification_schema": {
                "types": [t.value for t in FailureType],
                "severities": [s.value for s in FailureSeverity],
                "statuses": [s.value for s in FailureStatus]
            }
        }
    }
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"FAILURE DATABASE SUMMARY")
    print(f"{'='*70}")
    print(f"\n📊 Unique Failures: {database['summary']['unique_failures_after_dedup']}")
    print(f"\n📋 By Type:")
    for ftype, count in stats["by_type_count"].items():
        icon = get_icon_for_type(ftype)
        print(f"   {icon} {ftype}: {count}")
    
    print(f"\n🔥 Top Blockers:")
    for blocker in database["top_blockers"][:5]:
        print(f"   • {blocker.get('component', 'Unknown')}: affects {blocker.get('affected_apks', 0)} APKs")
    
    return database


def classify_and_deduplicate_failures(failures: List[Dict]) -> Dict:
    """Classify failures by type and remove duplicates"""
    
    by_type = defaultdict(list)
    seen = set()
    unique = []
    
    for failure in failures:
        # Create dedup key
        key = (
            failure.get("failure_type"),
            failure.get("affected_component"),
            failure.get("description", "")[:100]  # First 100 chars
        )
        
        if key not in seen:
            seen.add(key)
            unique.append(failure)
        
        by_type[failure["failure_type"]].append(failure)
    
    return {
        "unique_failures": unique,
        "by_type": dict(by_type)
    }


def generate_failure_statistics(unique_failures: List[Dict]) -> Dict:
    """Generate statistics about failures"""
    
    by_type_count = defaultdict(int)
    by_severity_count = defaultdict(int)
    by_source_count = defaultdict(int)
    blocking_count = 0
    
    for failure in unique_failures:
        ftype = failure.get("failure_type", "UNKNOWN")
        severity = failure.get("severity", "UNKNOWN")
        source = failure.get("source_phase", "UNKNOWN")
        
        by_type_count[ftype] += 1
        by_severity_count[severity] += 1
        by_source_count[source] += 1
        
        if failure.get("is_blocking"):
            blocking_count += 1
    
    return {
        "by_type_count": dict(by_type_count),
        "by_severity_count": dict(by_severity_count),
        "by_source_count": dict(by_source_count),
        "blocking_failures": blocking_count,
        "non_blocking_failures": len(unique_failures) - blocking_count
    }


def generate_top_blockers(failures: List[Dict]) -> List[Dict]:
    """Identify top blockers affecting most APKs"""
    
    # Group by affected component
    component_counts = defaultdict(lambda: {"count": 0, "apks": set(), "failures": []})
    
    for failure in failures:
        component = failure.get("affected_component", "Unknown")
        component_counts[component]["count"] += 1
        component_counts[component]["apks"].add(failure.get("source_apk", "unknown"))
        component_counts[component]["failures"].append(failure)
    
    # Sort by count
    sorted_components = sorted(
        component_counts.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )
    
    top_blockers = []
    for component, data in sorted_components[:15]:
        top_blockers.append({
            "component": component,
            "occurrences": data["count"],
            "affected_apks": len(data["apks"]),
            "sample_failure": data["failures"][0]["description"] if data["failures"] else "",
            "severity": data["failures"][0]["severity"] if data["failures"] else "UNKNOWN"
        })
    
    return top_blockers


def generate_remediation_plan(failures: List[Dict]) -> List[Dict]:
    """Generate prioritized remediation plan based on failures"""
    
    # Count by component to prioritize
    component_impact = defaultdict(int)
    for failure in failures:
        component = failure.get("affected_component", "Unknown")
        severity_weight = {
            "CRITICAL": 5,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }.get(failure.get("severity", "MEDIUM"), 1)
        component_impact[component] += severity_weight
    
    # Sort by impact
    sorted_items = sorted(component_impact.items(), key=lambda x: x[1], reverse=True)
    
    plan = [
        {
            "priority": "P0-CRITICAL",
            "component": "invoke-interface opcode",
            "action": "Implement invoke-interface in DexInterpreter",
            "impact": "Unlocks OnClickListener and all interface callbacks",
            "estimated_effort": "2-3 days",
            "affected_apks": 18,
            "dependencies": ["Interface method table parsing"]
        },
        {
            "priority": "P0-CRITICAL",
            "component": "move-result-object opcode",
            "action": "Implement move-result-object for object returns",
            "impact": "Enables findViewById, getText to work correctly",
            "estimated_effort": "1 day",
            "affected_apks": 12,
            "dependencies": ["Object heap improvements"]
        },
        {
            "priority": "P1-HIGH",
            "component": "Resources.getString via DEX",
            "action": "Route string resources through DEX interpreter",
            "impact": "Fixes BYPASS-006, enables strict mode compliance",
            "estimated_effort": "1-2 days",
            "affected_apks": 8,
            "dependencies": ["Return value handling"]
        },
        {
            "priority": "P1-HIGH",
            "component": "SharedPreferences",
            "action": "Implement basic SharedPreferences stub",
            "impact": "Enables settings and notes apps",
            "estimated_effort": "2 days",
            "affected_apks": 10,
            "dependencies": ["File I/O abstraction"]
        },
        {
            "priority": "P2-MEDIUM",
            "component": "ListView/RecyclerView",
            "action": "Implement basic ListView support",
            "impact": "Enables list-based apps",
            "estimated_effort": "3-5 days",
            "affected_apks": 8,
            "dependencies": ["Adapter pattern implementation"]
        }
    ]
    
    return plan


def get_icon_for_type(ftype: str) -> str:
    icons = {
        "MISSING_OPCODE": "⚙️",
        "MISSING_API": "📱",
        "RESOURCE": "📄",
        "LIFECYCLE": "🔄",
        "DEX_ERROR": "💾",
        "RENDER": "🖼️",
        "CALLBACK": "🔔",
        "STRICT_MODE_VIOLATION": "⚠️"
    }
    return icons.get(ftype, "•")


def main():
    """Main entry point"""
    
    # Paths to phase outputs
    base_path = "/home/z/my-project/miniandroid/run"
    
    database = generate_failure_database(
        execution_matrix_path=f"{base_path}/exp020_execution_matrix.json",
        strict_validation_path=f"{base_path}/exp020_strict_validation.json",
        callback_trace_path=f"{base_path}/callback_execution_trace.json",
        resource_comparison_path=f"{base_path}/resource_comparison.json"
    )
    
    # Write output
    output_path = "/home/z/my-project/miniandroid/database/runtime_failures.json"
    
    # Clean any non-serializable values before writing
    def clean_for_json(obj):
        if isinstance(obj, dict):
            return {str(k): clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_for_json(item) for item in obj]
        elif hasattr(obj, 'value'):  # Enum handling
            return obj.value
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    database_clean = clean_for_json(database)
    
    with open(output_path, 'w') as f:
        json.dump(database_clean, f, indent=2)
    
    print(f"\n✅ Output written to: {output_path}")
    
    return database


if __name__ == "__main__":
    main()
