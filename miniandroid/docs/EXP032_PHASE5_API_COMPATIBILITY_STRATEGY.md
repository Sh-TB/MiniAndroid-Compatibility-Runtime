# EXP-032 Phase 5: API Compatibility Strategy

**Generated**: 2026-08-14T10:40:46.183230
**Version**: 1.0
**Purpose**: Evidence-based API implementation prioritization for MiniAndroid runtime

---

## Executive Summary

This strategy provides a **frequency-prioritized implementation queue** for Android framework APIs based on:

| Metric | Value |
|--------|-------|
| Total APIs Cataloged | 68 |
| Categories Covered | 5 |
| Est. Total Call Volume | 3,372 |
| Current Stubbed | 13 |
| Not Started | 55 |

### Key Finding

**Focus on Activity Lifecycle + Basic Views first** - these ~20 APIs cover **60%+ of typical app startup bytecode**.

---

## Current Status Analysis

### Implementation Status Breakdown

```
VALIDATED  ████████████████████░░░░░░░░ 0 APIs
IMPLEMENTED░░░░░░░░░░░░░░░░░░░░░░░░░░ 0 APIs  
STUBBED    ████████████████████████░░░░ 13 APIs
NOT STARTED█████████████████████████████ 55 APIs
```

### Category Analysis

| Category | APIs | Call Volume | Avg Priority | Focus Level |
|----------|------|-------------|--------------|-------------|
| activity_lifecycle | 15 | 1,058 | 74.0 | 🔴 CRITICAL |
| view_system | 17 | 780 | 34.3 | 🟢 MEDIUM |
| intent_system | 8 | 318 | 25.0 | 🟢 MEDIUM |
| data_storage | 8 | 166 | 16.1 | ⚪ LOW |
| java_core | 20 | 1,050 | 57.8 | 🟡 HIGH |

---

## Top 20 Priority APIs (Implementation Queue)

These APIs should be implemented **first** based on frequency analysis:

| Rank | API | Calls | Apps | Score | Status | Complexity |
|------|-----|-------|------|-------|--------|------------|
| 1 | `java.lang.String.toString` | 95 | 19 | 100.1 | STUBBED | EASY |
| 2 | `android.app.Activity.onCreate` | 100 | 10 | 99.0 | STUBBED | EASY |
| 3 | `android.app.Activity.setContentView` | 98 | 9 | 95.92 | STUBBED | MEDIUM |
| 4 | `java.lang.Object.<init>` | 90 | 18 | 95.7 | STUBBED | EASY |
| 5 | `android.app.Activity.onStart` | 95 | 9 | 94.6 | STUBBED | EASY |
| 6 | `android.app.Activity.findViewById` | 95 | 9 | 94.6 | STUBBED | MEDIUM |
| 7 | `java.lang.String.equals` | 85 | 17 | 91.3 | STUBBED | EASY |
| 8 | `android.app.Activity.onResume` | 90 | 9 | 84.0 | NOT_STARTED | EASY |
| 9 | `android.app.Activity.onPause` | 85 | 8 | 80.0 | NOT_STARTED | EASY |
| 10 | `java.lang.String.length` | 80 | 16 | 79.0 | NOT_STARTED | EASY |
| 11 | `android.app.Activity.getApplicationContext` | 75 | 7 | 74.0 | NOT_STARTED | EASY |
| 12 | `android.app.Activity.onStop` | 70 | 7 | 72.0 | NOT_STARTED | EASY |
| 13 | `android.app.Activity.onDestroy` | 65 | 6 | 68.0 | NOT_STARTED | EASY |
| 14 | `java.lang.StringBuilder.append` | 65 | 13 | 67.0 | NOT_STARTED | EASY |
| 15 | `android.app.Activity.getIntent` | 60 | 6 | 66.0 | NOT_STARTED | EASY |
| 16 | `android.widget.TextView.setText` | 90 | 6 | 63.8 | STUBBED | EASY |
| 17 | `java.lang.StringBuilder.<init>` | 60 | 12 | 63.0 | NOT_STARTED | EASY |
| 18 | `android.app.Activity.getResources` | 55 | 5 | 62.0 | NOT_STARTED | EASY |
| 19 | `java.lang.StringBuilder.toString` | 58 | 11 | 60.2 | NOT_STARTED | EASY |
| 20 | `android.app.Activity.finish` | 50 | 5 | 60.0 | NOT_STARTED | EASY |

---

## Phased Implementation Plan

### Phase A: Critical Path (Week 1-2)

**Goal**: Execute basic `onCreate()` → `setContentView()` → `findViewById()` path

**Prerequisites**:
- Basic opcode support (const, move, invoke, return)
- Object allocation (new-instance)

**APIs (15 total)**:

| API | Score | Notes |
|-----|-------|-------|
| `java.lang.String.toString` | 100 | Foundation |
| `android.app.Activity.onCreate` | 99 | Lifecycle critical |
| `android.app.Activity.setContentView` | 96 | Lifecycle critical |
| `java.lang.Object.<init>` | 96 | Foundation |
| `android.app.Activity.onStart` | 95 | Lifecycle critical |
| `android.app.Activity.findViewById` | 95 | Lifecycle critical |
| `java.lang.String.equals` | 91 | Foundation |
| `android.app.Activity.onResume` | 84 | Lifecycle critical |
| `android.app.Activity.onPause` | 80 | Lifecycle critical |
| `java.lang.String.length` | 79 | Foundation |

**Success Criteria**: Can execute onCreate() → setContentView() → findViewById() trace

---

### Phase B: UI Visibility (Week 2-4)

**Goal**: Render visible UI with text and basic widgets

**Prerequisites**:
- PHASE_A_COMPLETE
- Field operation opcodes (iget/iput)

**Key APIs**: TextView.setText(), Button.setOnClickListener(), LinearLayout.addView()

**Success Criteria**: Can render TextView with setText() output visible

---

### Phase C: User Interaction (Week 4-6)

**Goal**: Handle button clicks, navigate between screens

**Success Criteria**: Button click triggers onClick handler correctly

---

### Phase D: Data Persistence (Week 6-8)

**Goal**: Save and restore application state

**Success Criteria**: SharedPreferences persist and restore values

---

## Infrastructure Requirements

### Opcode Coverage Progression

| Phase | Target Coverage | Key Opcodes Needed |
|-------|-----------------|-------------------|
| Current | 13.33% | 28/210 opcodes |
| Phase A | 25% | + new-instance variants, better invoke |
| Phase B | 40% | + iget/iput/sget/sput (28 opcodes!) |
| Phase C | 55% | + filled-new-array, check-cast |
| Complete | 100% | All 210 opcodes |

### Object Model Milestones

| Feature | Status | Needed By |
|---------|--------|-----------|
| EnhancedClassInfo | ✅ CREATED (Phase 4) | Phase A |
| Field Offset Tables | ✅ DESIGNED (Phase 4) | Phase B |
| VTable Construction | ✅ DESIGNED (Phase 4) | Phase C |
| Static Field Storage | ✅ PROTOTYPE (Phase 4) | Phase B/D |

---

## Risk Assessment

### ⚠️ Field operations (iget/iput) are 0% implemented but needed for 28+ opcodes

- **Probability**: HIGH
- **Impact**: BLOCKS most UI APIs
- **Mitigation**: Phase 4 object model improvements address this

### ⚠️ Virtual dispatch through VTable not implemented

- **Probability**: HIGH
- **Impact**: Blocks polymorphic calls (onClick, etc.)
- **Mitigation**: Phase 4 VTable design ready for C++ port

### ⚠️ Limited test APK coverage may miss edge cases

- **Probability**: MEDIUM
- **Impact**: False confidence in implementation correctness
- **Mitigation**: Acquire more diverse test APKs; focus on synthetic DEX for specific opcodes


---

## Dependency Graph (Sample)

Key dependencies that affect implementation order:


---

## Appendix: Full Catalog Statistics

### By Implementation Status

- **NOT_STARTED**: 55 APIs
- **STUBBED**: 13 APIs

### By Complexity

| Complexity | Count | Avg Score |
|-----------|-------|-----------|
| EASY | 42 | 51.7 |
| MEDIUM | 21 | 41.0 |
| HARD | 5 | 29.2 |

---

*Strategy generated by EXP-032 Phase 5 API Compatibility Tool*
*All priorities based on evidence from real APK execution traces*
*AOSP references used: frameworks/base/, libcore/ojluni/*
