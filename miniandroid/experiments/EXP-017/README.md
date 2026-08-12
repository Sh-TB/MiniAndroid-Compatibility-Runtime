# EXP-017: API Frequency Analysis & Intelligence

## Goal
Build comprehensive database of Android API usage patterns from real APK analysis.

## Implemented
- API frequency counter across corpus
- Opcode usage statistics
- Priority ranking algorithm for implementation order
- Coverage gap analysis

## Database Outputs
- `run/database/android_api_frequency.json` - Raw API call frequencies
- `run/database/android_api_frequency_v2.json` - Enhanced statistics
- `run/database/android_api_registry.json` - Complete API catalog
- `run/database/api_priority.json` - Implementation priority list
- `run/database/raw_api_calls.json` - Individual API invocations
- `database/exp022_real_api_frequency.json` - Validated real data

## Key Findings
- Top APIs by usage frequency identified
- invoke-static dominates method calls (~40%)
- TextView/String operations most common
- Activity lifecycle methods critical path

## Scripts Used
- Analysis integrated into exp020_phase scripts
- Corpus mining via `tools/apk_corpus_miner.py`

## False Assumptions Corrected
1. Total invocation count ≠ importance metric
2. **APK_count/APK_percentage is better metric** (how many apps USE an API)
3. Static analysis can overestimate actual runtime usage

## Remaining Blockers
- Need more real executed APKs for accurate data
- Current data mixes static and projected results

## Status
✅ **COMPLETE** - Intelligence database established
