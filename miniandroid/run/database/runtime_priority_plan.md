# MiniAndroid Runtime Priority Plan

**Generated:** EXP-017 Android API Intelligence Mining System  
**Data Source:** 100 APK corpus analysis  
**Date:** 2026-08-12  

---

## Executive Summary

This document provides a data-driven implementation roadmap for MiniAndroid runtime development. All priorities are based on real API usage statistics extracted from 100 Android applications.

**Key Finding:** Implementing just 20 APIs would cover **80%+ of common Android app patterns**.

---

## Implementation Priority Order

### Phase A: Complete Core Execution (Immediate - Week 1)

These items unblock the maximum number of applications with minimal effort.

#### A1. Control Flow Opcodes (P0 CRITICAL)

| Opcode | Hex | Impact | Apps Unblocked | Effort |
|--------|-----|--------|----------------|--------|
| `invoke-static` | 0x67 | Enables static methods | +75% | Medium |
| `if-eqz` | 0x39 | Enables null checks | +67% | Low |
| `goto` | 0x28 | Enables loops | +92% | Low |
| `if-nez` | 0x3A | Enables non-null checks | +58% | Low |

**Expected Result:** Corpus pass rate increases from ~50% to ~70%

#### A2. Return Value Handling (P1 HIGH)

| Component | Impact | Effort |
|-----------|--------|--------|
| `return-object` opcode | Methods can return values | Low |
| `move-result-object` opcode | Return values can be captured | Low |
| `iput-object` opcode | Instance fields can be set | Low-Medium |

**Expected Result:** Method chaining works, state management possible**

### Phase B: Interactive App Support (Week 2)

#### B1. Interface Dispatch

| API | Usage % | Implementation Notes |
|-----|---------|---------------------|
| `View.setOnClickListener` | 50% | Requires invoke-interface opcode |
| `View.OnClickListener.onClick` | 25% | Interface method dispatch |
| `TextWatcher` | 15% | Input validation apps |

**Blocker:** Must implement `invoke-interface` (0x72) opcode first

#### B2. Navigation Support

| API | Usage % | Implementation Notes |
|-----|---------|---------------------|
| `Intent.<init>(Context, Class)` | 38% | Intent construction |
| `Intent.putExtra(String, *)` | 26% | Data passing |
| `Activity.startActivity(Intent)` | 30% | Activity launch |
| `Activity.finish()` | 14% | Activity close |

**Note:** Full navigation requires Activity stack management

### Phase C: Resource & State (Week 3)

#### C1. Fix BYPASS-006: Resource Loading

| API | Usage % | Current Status | Fix Required |
|-----|---------|---------------|--------------|
| `Context.getResources()` | 20% | Returns null stub | Initialize Resources in Context |
| `Resources.getString(int)` | 20% | C++ parser used | Bridge to existing parser via DEX |
| `sget-object` opcode | 25% | Not implemented | For R.field access |

**Impact:** +10 strict mode points, proper resource path

#### C2. State Persistence

| API | Usage % | Implementation Notes |
|-----|---------|---------------------|
| `Bundle.getString/putString` | 24% | Simple key-value store |
| `SharedPreferences.edit()` | 8% | Editor pattern |
| `Editor.putString/putBoolean/apply()` | 8% | Async commit |

### Phase D: UI Feedback (Week 4)

| API | Usage % | Category |
|-----|---------|----------|
| `Toast.makeText(Context, int, int)` | 22% | Notifications |
| `Toast.show()` | 22% | Display |
| `Log.d/i/w/e(String, String)` | 9% | Debugging |
| `AlertDialog.Builder` | 5% | User confirmation |

---

## Top APIs to Implement (Ranked by Impact)

### Top 10 Next APIs

| Rank | API | Apps Using | Calls | Status | Priority Score |
|------|-----|------------|-------|--------|----------------|
| 1 | `Button.setOnClickListener` | 50 | 52 | NOT IMPLEMENTED | **94** |
| 2 | `Intent.<init>` | 38 | 45 | NOT IMPLEMENTED | **88** |
| 3 | `EditText.getText` | 34 | 38 | NOT IMPLEMENTED | **83** |
| 4 | `Activity.startActivity` | 30 | 32 | STUB ONLY | **78** |
| 5 | `Intent.putExtra` | 26 | 28 | NOT IMPLEMENTED | **75** |
| 6 | `Bundle.getString` | 24 | 26 | NOT IMPLEMENTED | **72** |
| 7 | `Resources.getString` | 20 | 21 | PARTIAL | **70** |
| 8 | `Context.getResources` | 20 | 20 | STUB | **70** |
| 9 | `View.onClick (interface)` | 25 | 27 | NOT IMPLEMENTED | **68** |
| 10 | `Toast.makeText` | 22 | 24 | NOT IMPLEMENTED | **58** |

---

## Opcodes to Implement (Ranked by Frequency)

### Critical Missing Opcodes (Top 10)

| Rank | Opcode | Count | % of Total | Implemented | Priority |
|------|--------|-------|------------|-------------|----------|
| 1 | `invoke-static` | 485 | 3.78% | ❌ | **P0** |
| 2 | `if-eqz` | 450 | 3.50% | ❌ | **P0** |
| 3 | `goto` | 420 | 3.27% | ❌ | **P0** |
| 4 | `if-nez` | 340 | 2.65% | ❌ | **P0** |
| 5 | `iput-object` | 520 | 4.05% | ❌ | P1 |
| 6 | `move-result-object` | 380 | 2.96% | ❌ | P1 |
| 7 | `sget-object` | 280 | 2.18% | ❌ | P1 |
| 8 | `return-object` | 250 | 1.95% | ❌ | P1 |
| 9 | `if-eq` | 180 | 1.40% | ❌ | P1 |
| 10 | `invoke-interface` | 150 | 1.17% | ❌ | P1 |

---

## Milestone Targets

### M1: Basic App Execution (Current → Week 1)
- [x] Activity.onCreate
- [x] Activity.setContentView
- [x] TextView.setText / <init>
- [ ] invoke-static, if-eqz, goto, if-nez
- [ ] return-object, move-result-object

**Target:** 70% corpus onCreate pass rate

### M2: Interactive Apps (Week 2)
- [ ] Button.setOnClickListener (invoke-interface)
- [ ] EditText.getText/setText
- [ ] Intent + navigation basics
- [ ] onClick handler execution

**Target:** 60% corpus full execution pass rate

### M3: Resource Correctness (Week 3)
- [ ] Fix BYPASS-006 (resource loading)
- [ ] Bundle state save/restore
- [ ] SharedPreferences basic support

**Target:** Strict mode score >85%

### M4: UI Completeness (Week 4)
- [ ] Toast notifications
- [ ] Log support
- [ ] AlertDialog basic
- [ ] CheckBox/ToggleButton full support

**Target:** 80% of P1/P2 APIs implemented

---

## Effort Estimates

| Phase | Opcodes | APIs | Estimated Days | Cumulative Days |
|-------|---------|------|----------------|-----------------|
| A (Control Flow) | 4 | 2 | 3-4 | 3-4 |
| B (Interactive) | 2 | 6 | 4-5 | 7-9 |
| C (Resources) | 2 | 5 | 3-4 | 10-13 |
| D (UI Feedback) | 1 | 6 | 3-4 | 13-17 |

**Total Estimated: 2-3 weeks for significant coverage improvement**

---

## Risk Assessment

### High Confidence Items
- ✅ invoke-static (well-defined semantics)
- ✅ if-eqz/if-nez/goto (standard branch opcodes)
- ✅ return-object/move-result-object (simple register ops)

### Medium Complexity Items
- ⚠️ invoke-interface (vtable lookup differs from virtual)
- ⚠️ Intent/Activity navigation (requires stack management)
- ⚠️ Resources bridge (existing code integration)

### Lower Priority / Higher Complexity
- ❌ ListView/RecyclerView (adapter pattern complex)
- ❌ SharedPreferences (async operations)
- ❌ Canvas/graphics (large surface area)

---

## Success Metrics

After implementing Phase A-D:

| Metric | Current | Target |
|--------|---------|--------|
| Opcodes implemented | 7 (7.37%) | 16 (16.8%) |
| APIs implemented | 19 (7.76%) | 45 (18.4%) |
| Corpus onCreate pass | ~50% | ~80% |
| Strict mode score | 70/100 | 88/100 |
| HelloWorld still passes | ✅ | ✅ (regression test required) |

---

*Document Version: 1.0*  
*Generated by: EXP-017 API Intelligence Mining System*  
*Data Source: 100 APK corpus analysis*
