# EXP-027 Engineering Priority Recommendations

**Generated:** 2026-08-13T06:00:02.253101

**Based on:** Real execution campaign with 20 APKs

---

## 1. DEX Header Parsing (P0-CRITICAL)

- **Affected Apps:** 20/20 (100%)
- **Root Cause:** Generated DEX files have invalid header format
- **Evidence:** All 20 executions show DEX_PARSE_ERROR with "Invalid header size: 0"
- **Expected Impact:** +50 to +100 compatibility points
- **Effort:** 2-4 days

### Files to Modify
- `src/dex/dex_parser.cpp - Improve header validation`
- `tools/exp027_real_dex_generator.py - Fix header generation`

---

## 2. Opcode Implementation Gap (P1-HIGH)

- **Affected Apps:** Unknown (blocked by P0)
- **Root Cause:** DexInterpreter may not support all opcodes used by real apps
- **Evidence:** DEX contains invoke-super, const-string, new-instance, etc.
- **Expected Impact:** +30 compatibility points
- **Effort:** 3-5 days

### Files to Modify
- `src/dex/dex_interpreter.cpp`
- `src/dex/dex_interpreter.h`

---

## 3. Android API Stub Completeness (P1-HIGH)

- **Affected Apps:** Unknown (blocked by P0)
- **Root Cause:** android_stubs.h has limited method implementations
- **Evidence:** Apps call Activity.onCreate(), View methods, Log.d(), etc.
- **Expected Impact:** +40 compatibility points
- **Effort:** 5-7 days

### Files to Modify
- `src/api/android_stubs.h`
- `src/api/android_stubs.cpp (if created)`

---

## 4. Resource Loading & Layout Inflation (P2-MEDIUM)

- **Affected Apps:** Unknown (blocked by P0)
- **Root Cause:** Resource parser may not handle all resource types
- **Evidence:** APKs contain AndroidManifest.xml, resources.arsc
- **Expected Impact:** +25 compatibility points
- **Effort:** 4-6 days

### Files to Modify
- `src/resources/resource_parser.cpp`
- `src/runtime/application_runtime.cpp`

---

## 5. Rendering Pipeline (P2-MEDIUM)

- **Affected Apps:** Unknown (blocked by P0)
- **Root Cause:** Software renderer may not handle all view types
- **Evidence:** HelloWorld from EXP-026 produced screenshot.ppm
- **Expected Impact:** +20 compatibility points (visual confirmation)
- **Effort:** 3-5 days

### Files to Modify
- `src/renderer/software_renderer.cpp`
- `src/renderer/software_renderer.h`

---

## Roadmap Summary

### Immediate (This Week)
- [ ] Fix DEX header parsing issue
- [ ] Re-run execution campaign

### Short Term (Next 2 Weeks)
- [ ] Implement missing opcodes
- [ ] Expand Android API stubs

### Medium Term (Next Month)
- [ ] Resource loading improvements
- [ ] Rendering pipeline expansion

