# EXP-088 Phase I — Multi-DEX Audit Report

**Generated:** 2026-08-23T06:50:00Z

## Audit Summary

### Per-DEX Resolution Functions (VERIFIED)

| Function | File | Line | Status |
|---|---|---:|---|
| `build_class_dex_index` | dalvik_engine.cpp | 130 | ✅ Iterates all per_dex_raw_data_ |
| `resolve_method_name_for_dex` | dalvik_engine.cpp | 380 | ✅ Uses per_dex_raw_data_[dex_index] |
| `resolve_method_proto_for_dex` | dalvik_engine.cpp | 412 | ✅ Uses per_dex_raw_data_[dex_index] |
| `resolve_type_for_dex` | dalvik_engine.cpp | 451 | ✅ Uses per_dex_raw_data_[dex_index] |
| `read_dex_string_from_raw` | dalvik_engine.cpp | 270 | ✅ Reads from correct DEX raw data |

### Per-DEX Index Access Pattern

All per-DEX resolution functions follow this pattern:
1. Check `dex_index < per_dex_raw_data_.size()`
2. Get `const auto& raw = per_dex_raw_data_[dex_index]`
3. Read from `raw` (the correct DEX's data)
4. Return the resolved value

### current_dex_index_ Propagation

- Set by `execute_invoke_virtual`, `execute_invoke_direct`, `execute_invoke_static`
- Used by `resolve_method_name_for_dex`, `resolve_method_proto_for_dex`
- Correctly set before `execute_method_internal` calls

### Multi-DEX Test Results

**EXP-085 Phase 1 (independent verifier):**
- Telegram (5 DEX files): ✅ PASS — 0 mismatches
  - DEX 0: 56,182 strings, 65,452 methods, 31,552 fields
  - DEX 1: 2,225 strings, 5,506 methods, 1,116 fields
  - DEX 2: 85,759 strings, 62,162 methods, 52,664 fields
  - DEX 3: 62,169 strings, 65,122 methods, 44,061 fields
  - DEX 4: 53,217 strings, 55,656 methods, 38,140 fields
  - All per-DEX counts match independent Python parser

**EXP-086 Phase 2 (entry-point regression):**
- Telegram: ✅ PASS — LaunchActivity.onCreate entered (757 instructions)
- All 7 APKs correctly resolve and enter onCreate

### EXP-086 Phase 1 (B5 manifest resolver):
- Telegram: ✅ PASS — LaunchActivity found in DEX 3
- Multi-DEX fallback correctly injects class from DEX 3 into dex_report

### Cross-DEX Method Dispatch (EXP-085 Phase 2):
- Telegram: ✅ PASS — 63,166 cross-DEX method references, 21,450 polymorphic overrides
- All verified at index level

## Audit Conclusion

The multi-DEX resolution infrastructure is **PROVEN**:
1. ✅ Per-DEX string/type/method/field resolution uses correct DEX data
2. ✅ current_dex_index_ is correctly propagated
3. ✅ Multi-DEX entry-point resolution works (LaunchActivity in DEX 3)
4. ✅ Independent parser confirms per-DEX counts match
5. ✅ Cross-DEX method dispatch verified (63k references)

No per-DEX index bugs found. The EXP-082 fix (sorted DEX file ordering)
and EXP-086 fix (multi-DEX class injection) are working correctly.

**Phase I status: PROVEN**
