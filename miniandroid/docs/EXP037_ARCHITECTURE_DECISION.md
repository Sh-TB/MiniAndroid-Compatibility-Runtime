# EXP-037 PHASE 1.4 — ARCHITECTURE DECISION REPORT

**Date**: 2026-08-14  
**Decision Maker**: Based on evidence from Phases 1.1, 1.2, 1.3  
**Evidence Level**: CRITICAL DECISION — Based on hard data

---

## QUESTION 1: CAN TELEGRAM RUN WITH CURRENT MINIANDROID ARCHITECTURE?

### Possible Answers:

**A) YES: Only Android API layer missing**  
**B) PARTIAL: Android API + JNI layer required**  
**C) NO: Native runtime is too large for current scope**

---

### EVIDENCE ANALYSIS

#### Evidence Point 1: Current MiniAndroid Capabilities

From `EXP037_BASELINE.md`:

| Component | Status | Telegram Requirement |
|-----------|--------|---------------------|
| DEX Parser | ✅ Complete | Required |
| Dalvik Interpreter | ⚠️ 32/216 opcodes | **Insufficient** |
| Object Model | ✅ Complete | Required |
| VTable Dispatch | ✅ Complete | Required |
| Execution Observatory | ✅ Complete | Useful for debugging |
| Android Context | ❌ Missing | **CRITICAL** |
| SharedPreferences | ❌ Missing | **CRITICAL** |
| SQLiteDatabase | ❌ Missing | **CRITICAL** |
| File Sandbox | ❌ Missing | **CRITICAL** |
| JNI Bridge | ❌ Missing | **BLOCKER** |
| Native Loader | ❌ Missing | **BLOCKER** |

**Gap Analysis**: 4 CRITICAL components missing + 2 BLOCKERS.

---

#### Evidence Point 2: Native Code Dependency (from Phase 1.2)

```
Application.onCreate()
    ↓
System.loadLibrary("tgnet")     ← BLOCKS HERE
    ↓
[UnsatisfiedLinkError]
```

**Hard Evidence**: 
- StackOverflow #33765946 confirms crash
- Source code shows loadLibrary in first 150 lines
- No way to skip native initialization

**Conclusion**: Current architecture **cannot progress past startup** without JNI support.

---

#### Evidence Point 3: Opcode Coverage Gap

Current: **32 opcodes implemented** (14.8% coverage)  
Estimated needed for Telegram: **150+ opcodes** (based on usage patterns)

Missing critical categories:
- Arrays (new-array, aget, aput) — Used everywhere
- Arithmetic (add-int, mul-int, etc.) — Calculations
- Type conversions — Data handling
- Switch statements — State machines

**Conclusion**: Even if we solve JNI, interpreter is insufficient.

---

#### Evidence Point 4: Existing Solutions Research (from Phase 1.3)

All successful projects use:
- Full AOSP framework (not reimplemented)
- Container/virtualization approach
- Real ART runtime (not custom interpreter)
- Native code execution support

**No project** has successfully run real Android apps with:
- Custom DEX interpreter from scratch
- Reimplemented Android APIs
- No native code support

**Conclusion**: We're attempting something unprecedented in difficulty.

---

### DECISION ON QUESTION 1:

## **ANSWER: C) NO — WITH CAVEATS**

**Honest Assessment**:

> **Telegram cannot run with current architecture.**
> 
> The gaps are not superficial — they are foundational:
> 
> 1. **JNI Bridge** — Must exist before any native method can execute
> 2. **Native Library Loading** — libtgnet.so is non-negotiable
> 3. **Opcode Coverage** — Need ~5x more opcodes
> 4. **Android Framework Layer** — Need Context, SharedPreferences, SQLite at minimum
> 
> **Estimated effort to reach "Telegram launches"**: 6-12 months of full-time work.
> 
> **Estimated effort to reach "Telegram fully functional"**: 18-36 months.

---

## QUESTION 2: WHAT IS THE MINIMUM NEXT IMPLEMENTATION?

### Options Considered:

#### Option A: Implement Pure Java/Dalvik Components Only

**Components**:
- Context abstraction
- SharedPreferences with XML backend
- SQLiteDatabase with SQLite wrapper
- File sandbox (`runtime/data/`)
- Activity lifecycle state machine

**Pros**:
- ✅ Achievable in 2-3 months
- ✅ Proves persistence concept works
- ✅ Builds valuable infrastructure
- ✅ Can test with simpler apps

**Cons**:
- ❌ Still cannot run Telegram (JNI blocker remains)
- ❌ May feel like "not making progress" toward goal
- ❌ Requires pivot to simpler target app for demo

**Effort Estimate**: 8-12 weeks for solid implementation

---

#### Option B: Implement JNI Bridge + Native Support

**Components**:
- JNI call bridge (type conversion, method dispatch)
- .so file loader (dlopen/dlsym simulation)
- Native memory management
- Basic libtgnet.so stubs (50+ methods minimum)

**Pros**:
- ✅ Directly addresses the #1 blocker
- ✅ Enables loading real APKs further
- ✅ Most technically impressive if achieved

**Cons**:
- ❌ Extremely complex (JNI spec is dense)
- ❌ Error-prone (type mismatches, memory issues)
- ❌ Still need Android API layer anyway
- ❌ High risk of spending months with nothing to show

**Effort Estimate**: 16-24 weeks for basic bridge, 40+ weeks for usable

---

#### Option C: Change Target Application

**Approach**: Target a simpler app first, return to Telegram later.

**Candidate Apps** (ordered by complexity):

| App | Native Deps | Difficulty | Learning Value |
|-----|-------------|------------|----------------|
| Simple Notes | Minimal | Easy | Low |
| Todo List | Low | Medium | Medium |
| Calculator | None | Easy | Low |
| Weather Widget | Low | Medium | High |
| **Telegram** | **Extensive** | **Very Hard** | **Very High** |

**Pros**:
- ✅ Fast to working demo (2-4 weeks)
- ✅ Builds confidence and momentum
- ✅ Validates runtime architecture
- ✅ Provides evidence of capability

**Cons**:
- ❌ Abandons stated goal (temporarily)
- ❌ Less impressive demonstration
- ❌ Doesn't solve hard problems now
- ❌ May never return to Telegram

**Effort Estimate**: 2-6 weeks for simple app compatibility

---

### RECOMMENDATION: HYBRID APPROACH (Option A + Modified Option B)

**Proposed Path**:

```
PHASE 1 (Weeks 1-4): Core Infrastructure
├── Implement SharedPreferences (XML backend)
├── Implement File Sandbox (runtime/data/)
├── Implement basic Context wrapper
└── Test with synthetic app

PHASE 2 (Weeks 5-8): Database Layer  
├── Integrate SQLite3 library
├── Implement SQLiteDatabase wrapper
├── Implement SQLiteOpenHelper
└── Test CRUD operations

PHASE 3 (Weeks 9-12): Lifecycle & Integration
├── Implement Application.onCreate() lifecycle
├── Implement basic Activity lifecycle
├── Create stub native library loader
└── Attempt Telegram APK load (see where it fails)

PHASE 4 (Weeks 13-16): Evidence Collection
├── Document exact failure point
├── Measure what percentage of code executes
├── Capture full trace evidence
├── Decide: continue or pivot?
```

**This approach**:
- ✅ Makes tangible progress every week
- ✅ Produces working demos along the way
- ✅ Gathers real data about Telegram requirements
- ✅ Keeps door open for full implementation
- ✅ Provides clear checkpoint to reassess

---

## QUESTION 3: SHOULD WE CHANGE THE TARGET APPLICATION?

### Decision Framework:

**Keep Telegram If**:
- Goal is research/publication (novel contribution)
- Have 12+ months timeline
- Want to solve hardest problem first
- Accept risk of partial/failed result

**Change Target If**:
- Goal is working demo quickly
- Have 1-3 month timeline
- Want to validate approach first
- Need regular wins for motivation/funding

### My Recommendation:

**For this experiment (EXP-037)**: Keep Telegram as the **ultimate goal**, but set **intermediate milestones** with simpler apps.

**Revised Success Definition**:

```
ORIGINAL GOAL (May be 12+ months away):
"Telegram running with persistent session"

REVISED INTERMEDIATE GOAL (Achievable in 3 months):
"MiniAndroid can persist application data across restarts,
 and can load real APKs to the point of first native call"

MILESTONE 1 (4 weeks): Run simple notes app with persistence
MILESTONE 2 (8 weeks): Load Telegram APK, get past DEX parsing
MILESTONE 3 (12 weeks): Write data to shared_prefs, survive restart
MILESTONE 4 (16 weeks): Document exact path to full Telegram support
```

---

## FINAL ARCHITECTURE DECISION

### Decision Summary Table:

| Question | Answer | Confidence | Rationale |
|----------|--------|------------|-----------|
| Can Telegram run now? | **NO** | **100%** | Hard evidence from crashes, source analysis |
| What's missing most? | **JNI + APIs** | **95%** | Multiple sources confirm |
| Should we pivot? | **Not yet** | **80%** | Too early, gather more data first |
| Best next step? | **Hybrid approach** | **85%** | Balances progress with learning |
| Timeline to launch? | **6-12 months** | **70%** | Based on complexity analysis |

### Approved Architecture Direction:

```
IMMEDIATE (Next 4 weeks):
┌─────────────────────────────────────┐
│  Phase A: Data Persistence Layer    │
│  • SharedPreferences               │
│  • File Sandbox                     │
│  • Basic Context                    │
│  Target: Simple app compatibility   │
└─────────────────────────────────────┘
                ↓
SHORT-TERM (Weeks 5-12):
┌─────────────────────────────────────┐
│  Phase B: Database & Lifecycle      │
│  • SQLite integration               │
│  • Activity lifecycle               │
│  • Stub native loader               │
│  Target: Load Telegram APK          │
└─────────────────────────────────────┘
                ↓
MEDIUM-TERM (Months 4-12):
┌─────────────────────────────────────┐
│  Phase C: Full Compatibility        │
│  • JNI bridge implementation        │
│  • Native method stubs              │
│  • Network abstraction              │
│  Target: Telegram functional        │
└─────────────────────────────────────┘
```

---

## RISK ASSESSMENT

### High Risks (May Block Progress):

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| JNI complexity underestimated | 70% | High | Set strict timebox (4 weeks max) |
| Opcode coverage insufficient | 60% | Medium | Prioritize based on actual usage |
| Scope creep | 80% | High | Define MVP strictly |
| Motivation loss (slow progress) | 50% | High | Celebrate small wins |

### Medium Risks (Manageable):

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SQLite integration issues | 40% | Medium | Use well-tested library |
| Performance problems | 30% | Low | Optimize after working |
| Testing complexity | 50% | Medium | Automate where possible |

---

## SUCCESS METRICS (Measurable)

### For Phase A (4 weeks):

- [ ] SharedPreferences stores and retrieves values
- [ ] Files persist across process restarts
- [ ] Synthetic app runs completely
- [ ] Evidence captured and documented

### For Phase B (8 weeks):

- [ ] SQLite database operations work
- [ ] Telegram APK loads successfully
- [ ] DEX parsing completes without errors
- [ ] First screen renders (even if broken)
- [ ] Exact failure point documented

### For Phase C (12+ weeks):

- [ ] Login screen displays
- [ ] Session data persists
- [ ] Restart restores session
- [ ] Full trace evidence available

---

## CONCLUSION

### The Honest Truth:

> **MiniAndroid cannot run Telegram today. It will require significant investment to do so.**
>
> **However**, the research shows a **clear path forward**:
> 1. Build data persistence infrastructure (achievable)
> 2. Integrate database layer (well-understood problem)
> 3. Attempt Telegram load (gather real data)
> 4. Make informed decision about JNI investment
>
> **The goal is not wrong — it's just ambitious.**
> **With phased approach, we can make steady progress while keeping the ultimate goal in sight.**

### Next Action Required:

**Proceed to Phase 1.5** — Create detailed implementation roadmap based on these decisions.

---

*"Choose based on evidence, not opinion."* — ✅ This decision is based on:
- 3 comprehensive research documents
- 10+ web searches with results
- Source code analysis of Telegram
- Study of 6 existing projects
- Hard data on current capabilities vs requirements
