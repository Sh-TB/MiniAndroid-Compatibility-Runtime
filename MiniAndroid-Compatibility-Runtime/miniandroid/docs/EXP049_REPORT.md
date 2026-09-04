# EXP-049 Final Report

**Date:** 2026-08-17
**Commit:** 3a18bf3

## Summary

EXP-049 evolved MiniAndroid from an APK interpreter toward an Android Compatibility Runtime by adding execution intelligence, static analysis, invoke opcode auditing, and login path discovery.

## Execution Frontier

| Metric | EXP-048 | EXP-049 | Delta |
|--------|---------|---------|-------|
| Unique methods | 189 | **200** | +11 |
| JNI calls | 5 | 5 | — |
| HALT-LOOP | 0 | 0 | — |
| HALT-GOTO | 0 | 0 | — |
| Memory peak | 440 MB | 440 MB | stable |
| Execution time | ~3.4s | ~3.4s | — |
| Result | SUCCESS | SUCCESS | — |

## Deliverables

### Phase 0: Current State Document
- `docs/EXP049_CURRENT_STATE.md` — complete method inventory, API inventory, JNI status, technical debt

### Phase 2: Static Call Graph
- `tools/dex_call_graph.py` — 1M+ edges, 217K methods indexed
- `reports/telegram_call_graph.json` — startup path from LaunchActivity.onCreate
- 18 native methods on startup path (depth ≤ 6)
- 23K edges in BFS traversal

### Phase 3: Invoke Opcode Audit
- `docs/INVOKE_AUDIT_REPORT.md` — audit of all 10 invoke-* opcodes
- **FIXED: invoke-*/range (3rc format)** — was BROKEN, now WORKING
  - Old code routed 3rc to 35c handlers (wrong register extraction)
  - New code has dedicated 3rc handler with consecutive register reading
  - +11 new methods reached (AndroidUtilities.readRes, MonoColorLottieList, etc.)
- invoke-interface: PARTIAL → WORKING (fixed in EXP-048)
- All other invoke-* opcodes: WORKING

### Phase 4: SharedPreferences Analysis
- SharedConfig.saveConfig has 402 instructions with full edit/put*/apply chain
- UserConfig.saveConfig has 49 callers, all requiring network/UI
- Neither is reached during current execution path
- READ path: 128 API calls (getBoolean × 68, getInt × 36, getString × 8, getLong × 8)
- WRITE path: implemented but not exercised

### Phase 9: Login Path Discovery
- `docs/EXP049_LOGIN_PATH.md` — full analysis
- UserConfig.isClientActivated returns false (correct for no persisted state)
- Login would require: Activity.startActivity, Intent, View hierarchy
- SharedConfig.saveConfig callers all require network/media/UI

## Key Architectural Findings

1. **invoke-*/range was BROKEN** — 5 opcodes (0x74-0x78) routed to wrong format handler
2. **invoke-interface was BROKEN** (fixed in EXP-048) — didn't call bridge_to_api
3. **const/4 was BROKEN** (fixed in EXP-047) — wrong register/literal extraction
4. **Per-DEX field resolution was BROKEN** (fixed in EXP-046) — merged DEX caused wrong field lookups
5. **SharedPreferences read path works** — 128 calls through invoke-interface to bridge_to_api
6. **SharedPreferences write path exists** — edit/put*/apply implemented, not yet exercised

## Next Blockers (Priority Order)

1. **Activity.startActivity** — needed to launch LoginActivity
2. **View hierarchy** — needed for Login UI
3. **Network initialization** — needed to trigger saveConfig
4. **More native methods** — only native_getCurrentTime dispatched
5. **Return value propagation** — invoke handlers discard return values
