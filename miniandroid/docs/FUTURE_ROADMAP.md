# Future Roadmap: EXP-023 Onward

**Generated**: 2026-08-12  
**Status**: 📋 PLANNING  
**Phase**: 9 of 9 (Preservation & Migration - Final Phase)

---

## Current Status Summary

### What We Have

| Component | Status | Quality |
|-----------|--------|---------|
| DEX Parser | ✅ Working | Production-ready |
| APK Parser | ✅ Working | Production-ready |
| DEX Interpreter | ✅ Working | 70+ opcodes |
| Class Resolver | ✅ Working | Good coverage |
| Application Runtime | ⚠️ Partial | Basic lifecycle |
| Resource Parser | ⚠️ Partial | Basic support |
| Software Renderer | ⚠️ Partial | Simple views |
| Trace Engine | ✅ Working | Comprehensive |
| API Stubs | ❌ Limited | ~40% coverage |

### Compatibility Score

```
Real Executed APKs:    1 (HelloWorld.apk)
Real Pass Rate:       100% (1/1)
Projected Score:      55.2/100 (from EXP-021)
Real Score Basis:     Insufficient data (need more real APKs)
Honest Assessment:    See EXP-022 transparency report
```

---

## Priority Roadmap

### P0: Critical Path (Next 30 Days)

#### 1. invoke-static Completeness
**Current Issue**: Many Android framework methods use `invoke-static` for utility calls  
**Impact**: High - blocks most framework interaction  

**Tasks**:
- [ ] Audit all invoke-static paths in HelloWorld.apk execution
- [ ] Identify missing static method implementations
- [ ] Implement top 20 most-used static methods:
  - `Ljava/lang/System;->loadLibrary()`
  - `Ljava/lang/Class;->forName()`
  - `Landroid/util/Log;->d/i/w/e()`
  - `Landroid/os/Build;->*` (all fields)
  - `Landroid/content/res/Resources;->getSystem()`
  - `Landroid/view/ViewConfiguration;->get()`
  - `Ljava/lang/Math;->min/max/abs()`
- [ ] Add unit tests for each implementation
- [ ] Update opcode frequency database with real data

**Expected Impact**: +10-15 compatibility points

---

#### 2. Real APK Execution Infrastructure
**Current Issue**: Only 1 APK actually executed; need more for valid scoring  
**Impact**: Critical - all scores are statistically invalid  

**Tasks**:
- [ ] Set up F-Droid download infrastructure
- [ ] Create APK download → hash → analyze → run → delete pipeline
- [ ] Download and execute 20+ open-source APKs:
  - **Simple Apps** (start here):
    - org.dfebnk.leon
    - com.example.android.hello
    - fm.libre
    - org.totschnig.myexpenses
  - **Medium Complexity**:
    - com.google.android.apps.maps (if available open-source)
    - org.mozilla.firefox (F-Droid version)
    - com.squareup.picasso (library, testable)
  - **Complex Apps** (stretch goals):
    - org.telegram.messenger
    - com.whatsapp (if FOSS version exists)
- [ ] Store only metadata/traces/reports (delete APKs per storage policy)
- [ ] Calculate REAL compatibility score from actual executions

**Expected Impact**: Valid statistical basis for all metrics

---

#### 3. Android Resource Compatibility
**Current Issue**: Resource loading incomplete; blocks layout inflation  
**Impact**: High - prevents UI rendering for most apps  

**Tasks**:
- [ ] Complete resources.arsc parsing
- [ ] Implement resource type resolution:
  - String resources (string, string-array)
  - Dimension resources (dimen, dp/sp handling)
  - Color resources (color, color-state-list)
  - Drawable resources (bitmap, 9-patch, selector)
  - Layout resources (XML inflation)
  - Style/Theme resources
- [ ] Implement resource ID resolution from R.java
- [ ] Add resource lookup caching
- [ ] Test with apps using complex layouts

**Expected Impact**: +15-20 compatibility points

---

### P1: Important (Next 60 Days)

#### 4. Object Initialization Completeness
**Current Issue**: Complex object init sequences fail silently  
**Impact**: Medium - affects apps with custom objects  

**Tasks**:
- [ ] Implement `<init>` chaining correctly
- [ ] Handle constructor overloading
- [ ] Support interface default methods
- [ ] Add object lifecycle tracking
- [ ] Improve garbage collection simulation

---

#### 5. Exception Handling
**Current Issue**: Exceptions cause crashes instead of graceful handling  
**Impact**: Medium - many apps use try/catch extensively  

**Tasks**:
- [ ] Implement exception table parsing
- [ ] Add try/catch block support in interpreter
- [ ] Handle common exceptions:
  - NullPointerException
  - IndexOutOfBoundsException
  - ClassCastException
  - IllegalArgumentException
- [ ] Add exception tracing to diagnostics

---

#### 6. Multi-dex Support
**Current Issue**: Only classes.dex processed; modern apps have multiple  
**Impact**: Medium - blocks most recent apps  

**Tasks**:
- [ ] Parse MultiDex application pattern
- [ ] Load classes2.dex, classes3.dex, etc.
- [ ] Resolve cross-dex references
- [ ] Handle multidex-list configuration

---

### P2: Enhancement (Next 90 Days)

#### 7. Expanded API Stubs
**Target**: Increase API coverage from 40% to 70%

**Priority APIs to implement**:

**android.content:**
- Intent (all constructors, extras, actions)
- Context (getSystemService, getResources, getContentResolver)
- SharedPreferences (editor, apply, commit)

**android.view:**
- View (onClick, onTouch, measurement)
- ViewGroup (addView, removeView, layout)
- TextView (setText, getText, movement)
- ImageView (setImageResource, setBitmap)

**android.widget:**
- Button, EditText, ListView, RecyclerView basics
- LinearLayout, RelativeLayout, ConstraintLayout

**android.graphics:**
- Canvas (drawRect, drawText, drawBitmap)
- Paint (color, textSize, style)
- Bitmap (creation, manipulation)

---

#### 8. Service & BroadcastReceiver Simulation
**Current Issue**: Only Activity lifecycle supported  
**Impact**: Low-Medium - needed for background apps  

**Tasks**:
- [ ] Implement Service lifecycle
- [ ] Add BroadcastReceiver simulation
- [ ] ContentProvider basic support
- [ ] Intent dispatch between components

---

#### 9. Diagnostics Integration
**Goal**: Make trace analysis easier and more visual

**Tasks**:
- [ ] Web-based trace viewer (HTML/JS)
- [ ] Execution flow visualization
- [ ] API call graph generation
- [ ] Performance profiling output
- [ ] Comparison tool (before/after traces)

---

## Experiment Plan: EXP-024 through EXP-030

### EXP-024: F-Droid Integration Batch
**Goal**: Download and execute 20 real F-Droid APKs  
**Duration**: 2 weeks  
**Deliverables**:
- Real corpus of 20+ executed APKs
- Real compatibility score (statistically valid)
- Per-APK execution traces
- Failure patterns analysis

### EXP-025: invoke-static Implementation Sprint
**Goal**: Complete top 50 static methods  
**Duration**: 1 week  
**Deliverables**:
- 50 new static method implementations
- Unit tests for each
- Updated API priority database
- Score improvement validation

### EXP-026: Resource System Completion
**Goal**: Full resource loading and layout inflation  
**Duration**: 2 weeks  
**Deliverables**:
- Complete resources.arsc parser
- All resource type handlers
- Layout XML inflater
- Theme/style resolution

### EXP-027: Exception Handling Framework
**Goal**: Robust exception handling throughout runtime  
**Duration**: 1 week  
**Deliverables**:
- Exception table interpreter
- Common exception types
- Graceful degradation mode
- Exception trace output

### EXP-028: UI Rendering Validation
**Goal**: Verify rendered output matches expected  
**Duration**: 1 week  
**Deliverables**:
- Screenshot comparison system
- Golden screenshot library
- Pixel-level diff detection
- Visual regression tests

### EXP-029: Performance Optimization
**Goal**: Improve execution speed by 10x  
**Duration**: 2 weeks  
**Deliverables**:
- Profiled bottlenecks
- Optimized hot paths
- Caching layer for resolved methods
- Benchmark suite

### EXP-030: Release Candidate Preparation
**Goal**: Prepare for public release/v1.0  
**Duration**: 1 week  
**Deliverables**:
- Complete documentation
- User guide
- API reference
- Release notes
- Packaging/distribution

---

## Technical Debt Tracking

### Known Issues Requiring Attention

| Issue | Severity | Effort | Priority |
|-------|----------|--------|----------|
| Memory leaks in interpreter | Medium | 2 days | P1 |
| Thread safety (single-threaded only) | Low | 5 days | P2 |
| No JNI support | High | 2 weeks | P1 |
| Limited reflection support | Medium | 3 days | P1 |
| Unicode handling incomplete | Low | 2 days | P2 |
| Error messages cryptic | Low | 1 day | P3 |

### Code Quality Goals

- [ ] Achieve 80%+ code coverage on interpreter
- [ ] Add static analysis (clang-tidy/cppcheck)
- [ ] Establish coding standards document
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Add memory sanitizer testing

---

## Success Metrics

### Target Metrics (6 months)

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Real APKs executed | 1 | 100+ | Count unique packages |
| Compatibility score | 55.2 | 75+ | Weighted average |
| API stub coverage | 40% | 70% | Methods implemented / total referenced |
| Opcode coverage | 72% | 95% | Opcodes implemented / 216 total |
| Build time | ~2min | <30s | CMake profile |
| Memory usage | Unknown | <512MB per APK | Valgrind/massif |

### Quality Gates

- [ ] All golden tests pass before merge
- [ ] No regression on HelloWorld.apk
- [ ] New features include evidence traces
- [ ] All claims backed by execution proof

---

## Collaboration Opportunities

### Potential Contributors Welcome For:
- Android framework experts (API stubs)
- Security researchers (APK analysis)
- Compiler engineers (interpreter optimization)
- UI developers (trace visualization)

### Integration Points:
- **Androguard**: Compare our parser with established tool
- **APKAnalyzer**: Cross-validate results
- **Frida**: Runtime instrumentation comparison
- **Android Emulator**: Ground truth for rendering

---

## Immediate Next Steps (This Week)

1. **Complete GitHub push** (manual step from Phase 8)
2. **Set up F-Droid download pipeline**
3. **Start EXP-024 planning** (real APK batch)
4. **Implement top 10 invoke-static methods**
5. **Add CI configuration** (.github/workflows)

---

## Conclusion

The MiniAndroid project has achieved a solid foundation through 23 experiments. The preservation work in this session ensures:

✅ All history documented and preserved  
✅ Clean repository ready for collaboration  
✅ Honest assessment of current capabilities  
✅ Clear roadmap for improvement  

**Key Insight from EXP-022/023**: Our biggest weakness is lack of **real execution data**. The #1 priority must be executing more actual APKs to establish genuine compatibility metrics.

**Path Forward**: Focus on quantity of real executions first, then quality improvements based on observed failure patterns.

---

**Roadmap Created By**: Super Z AI Agent  
**Timestamp**: 2026-08-12T15:05:00Z  
**Review Date**: 2026-08-19 (1 week)  
**Version**: 1.0 - Initial planning
