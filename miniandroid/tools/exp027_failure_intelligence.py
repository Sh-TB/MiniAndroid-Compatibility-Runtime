#!/usr/bin/env python3
"""
EXP-027: Failure Intelligence System
=====================================
Analyzes real execution failures and classifies them.

Categories:
- DEX failures: unsupported opcode, bad verifier, invalid register
- API failures: missing methods, wrong signatures, stub not implemented
- Resource failures: layout inflation, drawable missing, style missing
- Runtime crashes: segfault, null object, exception

Produces actionable intelligence for engineering priorities.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Configuration
BASE_DIR = Path("/home/z/my-project/miniandroid")
RESULTS_DIR = BASE_DIR / "run" / "exp027" / "results"
TRACE_DIR = BASE_DIR / "run" / "exp027" / "traces"
DATABASE_DIR = BASE_DIR / "database"

FAILURE_DB_FILE = DATABASE_DIR / "exp027_failure_database.json"


class FailureClassifier:
    """
    Classifies execution failures into categories.
    
    Provides intelligence on:
    - What types of failures occur most frequently
    - Which APKs share similar failure patterns
    - What needs to be fixed to improve compatibility
    """

    def __init__(self):
        self.failures: List[Dict] = []
        self.categories = {
            'DEX_PARSE_ERROR': [],      # DEX header/format issues
            'DEX_OPCODE_UNSUPPORTED':[], # Unknown opcodes
            'DEX_VERIFIER_ERROR': [],   # Verification failures
            'API_NOT_IMPLEMENTED': [],  # Stub methods not implemented
            'API_WRONG_SIGNATURE': [],  # Method signature mismatches
            'RESOURCE_MISSING': [],     # Missing layouts/drawables
            'RESOURCE_INFLATION': [],   # Layout inflation errors
            'RUNTIME_EXCEPTION': [],    # Runtime exceptions (NPE, etc)
            'RUNTIME_CRASH': [],        # Segfaults, aborts
            'UNKNOWN': []               # Unclassified
        }
        
        self.failure_patterns = defaultdict(int)
        self.affected_packages = set()
        
    def analyze_crash_log(self, crash_log_path: Path) -> Dict:
        """Analyze a single crash log and classify the failure."""
        if not crash_log_path.exists():
            return {'category': 'UNKNOWN', 'type': 'no_crash_log', 'details': 'No crash log found'}
        
        content = crash_log_path.read_text()
        
        classification = {
            'category': 'UNKNOWN',
            'type': '',
            'details': '',
            'severity': 'medium',
            'fix_complexity': 'medium',
            'keywords_found': []
        }
        
        # Check for specific error patterns
        content_lower = content.lower()
        
        # DEX Parse Errors
        if 'parse_error' in content_lower or 'invalid header' in content_lower:
            classification['category'] = 'DEX_PARSE_ERROR'
            classification['type'] = 'dex_header_invalid'
            classification['details'] = 'DEX file has invalid or unsupported header format'
            classification['severity'] = 'high'
            classification['fix_complexity'] = 'high'
            classification['keywords_found'].append('parse_error')
            
        elif 'unsupported opcode' in content_lower or 'unknown opcode' in content_lower:
            classification['category'] = 'DEX_OPCODE_UNSUPPORTED'
            classification['type'] = 'opcode_not_implemented'
            classification['details'] = 'DEX contains opcodes not yet implemented in interpreter'
            classification['severity'] = 'high'
            classification['fix_complexity'] = 'medium'
            classification['keywords_found'].append('unsupported_opcode')
            
        elif 'verifier' in content_lower and ('error' in content_lower or 'fail' in content_lower):
            classification['category'] = 'DEX_VERIFIER_ERROR'
            classification['type'] = 'verification_failed'
            classification['details'] = 'DEX bytecode verification failed'
            classification['severity'] = 'medium'
            classification['fix_complexity'] = 'high'
            classification['keywords_found'].append('verifier_error')
            
        # API Failures
        elif 'not implemented' in content_lower or 'stub' in content_lower:
            classification['category'] = 'API_NOT_IMPLEMENTED'
            classification['type'] = 'stub_method'
            classification['details'] = 'Called method is a stub and not fully implemented'
            classification['severity'] = 'medium'
            classification['fix_complexity'] = 'medium'
            classification['keywords_found'].append('not_implemented')
            
        elif 'nosuchmethod' in content_lower or 'wrong signature' in content_lower:
            classification['category'] = 'API_WRONG_SIGNATURE'
            classification['type'] = 'method_signature_mismatch'
            classification['details'] = 'Method call signature does not match available methods'
            classification['severity'] = 'medium'
            classification['fix_complexity'] = 'low'
            classification['keywords_found'].append('signature_mismatch')
            
        # Resource Failures
        elif 'resource' in content_lower and 'not found' in content_lower:
            classification['category'] = 'RESOURCE_MISSING'
            classification['type'] = 'resource_file_missing'
            classification['details'] = 'Required resource file (drawable/layout) not found in APK'
            classification['severity'] = 'low'
            classification['fix_complexity'] = 'low'
            classification['keywords_found'].append('resource_missing')
            
        elif 'inflate' in content_lower and ('error' in content_lower or 'exception' in content_lower):
            classification['category'] = 'RESOURCE_INFLATION'
            classification['type'] = 'layout_inflation_failure'
            classification['details'] = 'Failed to inflate layout XML into view hierarchy'
            classification['severity'] = 'medium'
            classification['fix_complexity'] = 'medium'
            classification['keywords_found'].append('inflation_error')
            
        # Runtime Crashes
        elif 'nullpointer' in content_lower or 'npe' in content_lower:
            classification['category'] = 'RUNTIME_EXCEPTION'
            classification['type'] = 'null_pointer_exception'
            classification['details'] = 'Null pointer exception during execution'
            classification['severity'] = 'high'
            classification['fix_complexity'] = 'low'
            classification['keywords_found'].append('null_pointer')
            
        elif 'segmentation' in content_lower or 'segfault' in content_lower or 'abort' in content_lower:
            classification['category'] = 'RUNTIME_CRASH'
            classification['type'] = 'native_crash'
            classification['details'] = 'Native code crash (segfault/abort)'
            classification['severity'] = 'critical'
            classification['fix_complexity'] = 'high'
            classification['keywords_found'].append('crash')
            
        elif 'exception' in content_lower:
            classification['category'] = 'RUNTIME_EXCEPTION'
            classification['type'] = 'general_exception'
            classification['details'] = f'Runtime exception: {content[:200]}'
            classification['severity'] = 'medium'
            classification['fix_complexity'] = 'medium'
            classification['keywords_found'].append('exception')
        
        # If still unknown, use raw message
        if classification['category'] == 'UNKNOWN':
            classification['details'] = content[:500] if content else 'Empty crash log'
        
        return classification
    
    def analyze_all_traces(self) -> Dict:
        """
        Analyze all trace directories and build failure database.
        """
        print("=" * 70)
        print("EXP-027: FAILURE INTELLIGENCE ANALYSIS")
        print("=" * 70)
        
        if not TRACE_DIR.exists():
            print(f"Trace directory not found: {TRACE_DIR}")
            return {}
        
        # Find all trace sessions
        trace_sessions = [d for d in TRACE_DIR.iterdir() if d.is_dir()]
        print(f"Found {len(trace_sessions)} trace sessions\n")
        
        total_analyzed = 0
        
        for session_dir in sorted(trace_sessions):
            crash_log = session_dir / "crash.log"
            api_trace = session_dir / "api_trace.json"
            report_md = session_dir / "report.md"
            
            # Extract package name from session directory
            session_name = session_dir.name
            
            # Analyze crash log
            failure_info = self.analyze_crash_log(crash_log)
            failure_info['session'] = session_name
            failure_info['timestamp'] = datetime.fromtimestamp(
                session_dir.stat().st_mtime
            ).isoformat()
            
            # Check for additional context from api_trace
            if api_trace.exists():
                try:
                    with open(api_trace, 'r') as f:
                        trace_data = json.load(f)
                        if isinstance(trace_data, dict):
                            failure_info['api_calls_made'] = len(trace_data.get('calls', []))
                            failure_info['execution_stages'] = list(set(
                                call.get('method', '') for call in trace_data.get('calls', [])
                                if call.get('class') == 'ExecutionEngine'
                            ))
                except Exception as e:
                    failure_info['trace_parse_error'] = str(e)
            
            # Categorize
            category = failure_info['category']
            self.categories[category].append(failure_info)
            self.failure_patterns[failure_info.get('type', 'unknown')] += 1
            total_analyzed += 1
            
            print(f"[{total_analyzed:2d}] {session_name}: {category} | {failure_info.get('type', '?')}")
        
        # Build summary database
        failure_db = self._build_database(total_analyzed)
        
        # Save
        with open(FAILURE_DB_FILE, 'w') as f:
            json.dump(failure_db, f, indent=2, default=str)
        
        print(f"\n📄 Failure database saved to: {FAILURE_DB_FILE}")
        
        # Print summary
        self._print_summary(total_analyzed)
        
        return failure_db
    
    def _build_database(self, total_analyzed: int) -> Dict:
        """Build comprehensive failure database."""
        
        # Calculate statistics
        category_stats = {}
        for cat, failures in self.categories.items():
            if failures:
                category_stats[cat] = {
                    'count': len(failures),
                    'percentage': (len(failures) / max(total_analyzed, 1)) * 100,
                    'types': list(set(f.get('type', 'unknown') for f in failures)),
                    'affected_apps': [f.get('session', 'unknown') for f in failures[:5]]
                }
        
        # Identify top blockers
        blockers = []
        for pattern, count in sorted(self.failure_patterns.items(), key=lambda x: -x[1]):
            blockers.append({
                'pattern': pattern,
                'affected_count': count,
                'percentage': (count / max(total_analyzed, 1)) * 100,
                'priority': 'P0' if count > total_analyzed * 0.5 else 
                          'P1' if count > total_analyzed * 0.25 else
                          'P2' if count > total_analyzed * 0.1 else 'P3'
            })
        
        db = {
            'experiment': 'EXP-027',
            'title': 'Real Execution Failure Intelligence Database',
            'generated_at': datetime.now().isoformat(),
            'analysis_summary': {
                'total_failures_analyzed': total_analyzed,
                'unique_failure_types': len(self.failure_patterns),
                'categories_affected': len([c for c in self.categories.values() if c]),
                'top_blocker': blockers[0] if blockers else None
            },
            'categories': category_stats,
            'failure_patterns': dict(self.failure_patterns),
            'top_blockers': blockers[:10],
            'engineering_recommendations': self._generate_recommendations(blockers),
            'raw_categories': {k: v for k, v in self.categories.items() if v}
        }
        
        return db
    
    def _generate_recommendations(self, blockers: List[Dict]) -> List[Dict]:
        """Generate engineering recommendations based on failure analysis."""
        recommendations = []
        
        for blocker in blockers[:5]:
            pattern = blocker['pattern']
            count = blocker['affected_count']
            
            if pattern == 'dex_header_invalid':
                recommendations.append({
                    'problem': 'DEX Header Parsing',
                    'description': f'{count} apps failed due to invalid DEX headers',
                    'recommendation': 'Improve DEX parser to handle more header variations',
                    'expected_impact': '+50 compatibility points',
                    'effort': 'HIGH',
                    'files_to_modify': ['src/dex/dex_parser.cpp', 'src/dex/dex_parser.h']
                })
                
            elif pattern == 'opcode_not_implemented':
                recommendations.append({
                    'problem': 'Opcode Support Gap',
                    'description': f'{count} apps use unsupported Dalvik opcodes',
                    'recommendation': 'Implement missing opcodes in DexInterpreter',
                    'expected_impact': '+30 compatibility points',
                    'effort': 'MEDIUM',
                    'files_to_modify': [
                        'src/dex/dex_interpreter.cpp',
                        'src/dex/dex_interpreter.h'
                    ]
                })
                
            elif pattern == 'stub_method':
                recommendations.append({
                    'problem': 'Incomplete API Stubs',
                    'description': f'{count} apps call unimplemented Android APIs',
                    'recommendation': 'Expand android_stubs.h with real implementations',
                    'expected_impact': '+40 compatibility points',
                    'effort': 'MEDIUM',
                    'files_to_modify': ['src/api/android_stubs.h']
                })
                
            elif pattern == 'layout_inflation_failure':
                recommendations.append({
                    'problem': 'Layout Inflation',
                    'description': f'{count} apps fail during view inflation',
                    'recommendation': 'Improve resource parser and view creation',
                    'expected_impact': '+25 compatibility points',
                    'effort': 'MEDIUM',
                    'files_to_modify': [
                        'src/resources/resource_parser.cpp',
                        'src/runtime/application_runtime.cpp'
                    ]
                })
                
            elif pattern == 'null_pointer_exception':
                recommendations.append({
                    'problem': 'Null Safety',
                    'description': f'{count} apps encounter null pointer issues',
                    'recommendation': 'Add null checks throughout runtime',
                    'expected_impact': '+20 compatibility points',
                    'effort': 'LOW',
                    'files_to_modify': ['Multiple runtime files']
                })
                
            else:
                recommendations.append({
                    'problem': pattern.replace('_', ' ').title(),
                    'description': f'Affects {count} applications',
                    'recommendation': 'Investigate and implement fix',
                    'expected_impact': '+15 compatibility points',
                    'effort': 'TBD',
                    'files_to_modify': ['To be determined']
                })
        
        return recommendations
    
    def _print_summary(self, total: int):
        """Print failure analysis summary."""
        print("\n" + "=" * 70)
        print("FAILURE INTELLIGENCE SUMMARY")
        print("=" * 70)
        print(f"Total Failures Analyzed: {total}\n")
        
        print("By Category:")
        print("-" * 50)
        for cat, failures in sorted(self.categories.items(), key=lambda x: -len(x[1])):
            if failures:
                pct = (len(failures) / max(total, 1)) * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"  {cat:30s} {len(failures):3d} ({pct:5.1f}%) {bar}")
        
        print("\nTop Failure Patterns:")
        print("-" * 50)
        for i, (pattern, count) in enumerate(sorted(self.failure_patterns.items(), key=lambda x: -x[1])[:5], 1):
            pct = (count / max(total, 1)) * 100
            print(f"  {i}. {pattern:35s} {count:3d} ({pct:.1f}%)")


def main():
    """Main entry point."""
    classifier = FailureClassifier()
    db = classifier.analyze_all_traces()
    
    if db:
        print("\n✅ Failure intelligence database generated")
        return 0
    else:
        print("\n⚠️ No failures to analyze")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
