# EXP-022: Transparent APK Corpus Audit

## Goal
Honest, evidence-based assessment of what's REAL vs PROJECTED in our claims.

## Motivation
EXP-020/021 claimed 35-APK corpus testing, but this needed verification.
**Golden Debug Protocol**: No fake PASS results, no estimated APK names.

## Implemented
- Complete 8-phase audit script (~900 lines)
- Per-claim verification against actual evidence
- Execution status taxonomy:
  - **REAL_EXECUTED**: Actually ran through MiniAndroid
  - **STATIC_ONLY**: Analyzed but not executed
  - **LOADED_ONLY**: Parsed but not interpreted
  - **FAILED_TO_LOAD**: Could not parse
  - **PROJECTED**: Theoretical/estimated
  - **UNKNOWN**: Cannot determine

## Critical Finding
### 🚨 ONLY 1 REAL APK WAS EXECUTED

| Status | Count | Percentage |
|--------|-------|------------|
| REAL_EXECUTED | 1 | 2.8% |
| PROJECTED/SIMULATED | 90+ | 97.2% |

**Real Execution**: Only `HelloWorld.apk` (com.example.helloworld)

**NOT Actually Tested**:
- ❌ WhatsApp
- ❌ Telegram  
- ❌ TikTok
- ❌ All other "popular apps" in corpus

## Scripts
- `scripts/exp022_corpus_audit.py` - Main audit script

## Key Outputs
- `run/exp022_report.md` - **Honest transparency report**
- `database/exp022_corpus_inventory.json` - 36 tracked APKs
- `run/exp022_missing_category_report.json` - 17 missing popular apps
- `run/exp022_claim_validation.json` - EXP-021 claims flagged as PROJECTIONS
- `run/exp022_apk_list_report.md` - Full application listing
- `run/apk_execution_proofs/com_example_helloworld.json` - Only real proof
- `database/apk_storage_policy.json` - Storage rules

## False Assumptions Corrected (from EXP-020/021)
1. ~~35 APKs tested~~ → Only 1 actually executed
2. ~~38/100 score empirical~~ → Based largely on projections
3. ~~WhatsApp/Telegram analyzed~~ → NEVER in our corpus

## Rules Established
1. Never fabricate APK execution results
2. Never convert STATIC_ONLY to PASS
3. Separate static analysis from execution evidence
4. Preserve all historical evidence (don't overwrite)
5. Report discrepancies honestly

## Status
✅ **COMPLETE** - Full transparency achieved
## Impact: Sets stage for EXP-023 real validation
