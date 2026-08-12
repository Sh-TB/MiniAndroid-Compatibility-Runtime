# EXP-020: Validation Corpus & Compatibility Analysis

## Goal
Create comprehensive APK compatibility testing corpus and scoring system.

## Implemented
- 35-APK test corpus (theoretical)
- 7-phase validation pipeline:
  1. Phase 1: Corpus collection
  2. Phase 2: Execution testing
  3. Phase 3: Strict validation
  4. Phase 4: Callback analysis
  5. Phase 5: Resource testing
  6. Phase 6: Failure tracking
  7. Phase 7: Score calculation
- Compatibility scoring algorithm

## Scripts
- `scripts/exp020_phase1_corpus.py`
- `scripts/exp020_phase2_execution.py`
- `scripts/exp020_phase3_strict.py`
- `scripts/exp020_phase4_callback.py`
- `scripts/exp020_phase5_resource.py`
- `scripts/exp020_phase6_failures.py`
- `scripts/exp020_phase7_score.py`

## Key Outputs
- `run/exp020_corpus_inventory.json` - Corpus metadata
- `run/exp020_execution_matrix.json` - Execution results
- `run/exp020_strict_validation.json` - Strict mode results
- `run/exp020_report.md` - Final report
- `run/compatibility_score.json` - Score data

## Baseline Results
- **Overall Compatibility: 38/100**
- APK Pass Rate: 20% (7/35 projected)
- API Coverage: 45%
- Opcode Coverage: 72%

## False Assumptions Corrected
1. ⚠️ **CRITICAL**: Most "corpus" entries were projections, NOT real executions
2. Only HelloWorld.apk was actually executed
3. Scores were theoretical, not empirical
4. This led to EXP-022 transparency audit

## Lessons Learned (for EXP-022)
- Must distinguish STATIC_ONLY from REAL_EXECUTED
- Never convert static analysis to PASS without execution proof
- Preserve all evidence chains

## Status
✅ **COMPLETE** - But see EXP-022 for honest assessment
