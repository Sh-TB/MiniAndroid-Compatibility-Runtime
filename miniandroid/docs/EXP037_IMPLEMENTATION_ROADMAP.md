# EXP-037 PHASE 1.5 — IMPLEMENTATION ROADMAP

**Date**: 2026-08-14  
**Based On**: Architecture Decision (Phase 1.4)  
**Approach**: Hybrid — Build infrastructure while targeting Telegram

---

## ROADMAP OVERVIEW

```
TOTAL TIMELINE: 16 weeks (4 months)
├── Phase A: Foundation (Weeks 1-4)     ← Data Persistence
├── Phase B: Core Runtime (Weeks 5-8)   ← Database + Lifecycle  
├── Phase C: Integration (Weeks 9-12)   ← Telegram Load Attempt
└── Phase D: Validation (Weeks 13-16)   ← Evidence & Decision
```

---

## PHASE A: DATA PERSISTENCE FOUNDATION (Weeks 1-4)

### Goal: "Application data survives process restart"

### Week 1: File Sandbox Implementation

**Objective**: Create persistent storage directory structure

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|-----------------|----------|
| A1.1 | Create `runtime/data/` base directory | N/A | Directory exists |
| A1.2 | Implement package-specific paths | `src/storage/file_sandbox.h/cpp` | Unit test passes |
| A1.3 | Implement `getFilesDir()` mapping | `src/api/android_context.h/cpp` | Returns correct path |
| A1.4 | Implement `getCacheDir()` mapping | Same file | Returns correct path |
| A1.5 | Test directory creation on Windows | `tests/test_sandbox.cpp` | All tests pass |

**Expected Result**:
```
runtime/data/
└── org.telegram.messenger/    (created on first access)
    ├── files/
    ├── cache/
    ├── databases/            (created later)
    └── shared_prefs/         (created later)
```

**Validation Method**:
```cpp
// Test case
TEST(FileSandbox, CreatesPackageDirectories) {
    AndroidContext ctx("org.telegram.messenger");
    
    EXPECT_TRUE(ctx.getFilesDir().exists());
    EXPECT_TRUE(ctx.getCacheDir().exists());
    EXPECT_EQ(ctx.getFilesDir().string(), 
              "runtime/data/org.telegram.messenger/files");
}
```

**Reason**: Telegram requires these directories immediately on startup.

**Evidence of Completion**: Test output showing all assertions pass.

---

### Week 2: SharedPreferences Implementation

**Objective**: Key-value storage that persists as XML files

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|-----------------|----------|
| A2.1 | Define SharedPreferences interface | `src/api/shared_prefs.h` | Interface compiles |
| A2.2 | Implement XML backend | `src/api/shared_prefs.cpp` | Writes valid XML |
| A2.3 | Implement `getString()` | Same file | Retrieves stored value |
| A2.4 | Implement `putString()` + `commit()` | Same file | Persists to disk |
| A2.5 | Implement all primitive types | Same file | int, float, boolean, long |
| A2.6 | Implement `Editor` pattern | Same file | Builder pattern works |
| A2.7 | Thread safety (basic mutex) | Same file | No race conditions |

**XML Format** (compatible with Android):
```xml
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="logged_in_key">true</string>
    <int name="user_id" value="123456789" />
    <string name="phone_hash">abc123def456</string>
</map>
```

**Validation Method**:
```cpp
// Integration test
TEST(SharedPreferences, PersistsAcrossRestarts) {
    // Write
    SharedPreferences prefs = context.getSharedPreferences("mainconfig", 0);
    prefs.edit().putBoolean("logged_in_key", true).commit();
    prefs.edit().putInt("user_id", 123456789).commit();
    
    // Simulate restart (new instance)
    SharedPreferences prefs2 = context.getSharedPreferences("mainconfig", 0);
    
    EXPECT_TRUE(prefs2.getBoolean("logged_in_key", false));
    EXPECT_EQ(prefs2.getInt("user_id", -1), 123456789);
}
```

**Reason**: This is THE critical feature for session persistence goal.

**Evidence of Completion**: XML file exists with correct content, test reads it back successfully.

---

### Week 3: Basic Context Implementation

**Objective**: Minimal Context wrapper providing required methods

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|-----------------|----------|
| A3.1 | Define Context abstract class | `src/api/android_context.h` | Compiles |
| A3.2 | Implement Application subclass | `src/api/application_context.cpp` | Creates instance |
| A3.3 | Wire up getSharedPreferences() | Both files | Returns working SP |
| A3.4 | Wire up file operations | Both files | Delegates to sandbox |
| A3.5 | Implement getResources() stub | Both files | Returns empty resources |
| A3.6 | Implement getPackageName() | Both files | Returns correct name |

**Class Hierarchy**:
```
ContextWrapper (abstract)
    ↓
Application (concrete)
    ↓
ApplicationLoader (Telegram's class, will be loaded from DEX)
```

**Validation Method**:
```cpp
TEST(AndroidContext, ProvidesAllRequiredAPIs) {
    Application app("org.telegram.messenger");
    
    // These must NOT throw or return null:
    EXPECT_NE(app.getSharedPreferences("test", 0), nullptr);
    EXPECT_FALSE(app.getFilesDir().empty());
    EXPECT_FALSE(app.getCacheDir().empty());
    EXPECT_FALSE(app.getPackageName().empty());
}
```

**Reason**: Every Android app starts by calling Context methods.

**Evidence of Completion**: All API methods return valid objects without crashing.

---

### Week 4: Synthetic App Integration Test

**Objective**: Prove persistence works end-to-end

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|-----------------|----------|
| A4.1 | Create test DEX with persistence operations | `test_apks/persistence_test.dex` | Loads successfully |
| A4.2 | Execute test in MiniAndroid runtime | `tools/exp037_persistence_test.py` | Runs to completion |
| A4.3 | Verify shared_prefs XML created | Manual inspection | File exists with data |
| A4.4 | Restart runtime, re-read preferences | Test script | Data survives restart |
| A4.5 | Capture full execution trace | Observatory output | Trace shows real execution |

**Test DEX Pseudocode**:
```java
// persistence_test.dex (what we'll compile)
public class PersistenceTest {
    public static void main(String[] args) {
        // Get context (we'll inject this)
        Context ctx = Runtime.getContext();
        
        // Write session data
        SharedPreferences prefs = ctx.getSharedPreferences("session", 0);
        prefs.edit()
            .putString("auth_token", "fake_token_123")
            .putLong("login_time", System.currentTimeMillis())
            .putBoolean("logged_in", true)
            .commit();
        
        // Verify written
        String token = prefs.getString("auth_token", "");
        assert token.equals("fake_token_123");
        
        System.out.println("SUCCESS: Persistence works!");
    }
}
```

**Success Criteria for Phase A**:
- [ ] File sandbox creates correct directory structure
- [ ] SharedPreferences writes and reads XML correctly
- [ ] Context wrapper provides all required APIs
- [ ] Test app runs and persists data across simulated restart
- [ ] Full trace evidence captured
- [ ] GitHub commit with all changes

**Evidence of Completion**: Test run log showing SUCCESS message + XML file contents.

---

## PHASE B: CORE RUNTIME (Weeks 5-8)

### Goal: "Database operations work, basic lifecycle functions"

### Week 5: SQLite Integration

**Objective**: Integrate SQLite3 C library into MiniAndroid

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|-----------------|----------|
| B1.1 | Download/build SQLite amalgamation | `third_party/sqlite3.c/h` | Compiles on Windows |
| B1.2 | Create C++ wrapper | `src/storage/sqlite_database.h/cpp` | Opens database |
| B1.3 | Implement `execSQL()` | Same file | Executes CREATE TABLE |
| B1.4 | Implement `rawQuery()` | Same file | Returns cursor with data |
| B1.5 | Implement basic Cursor | `src/storage/cursor.h/cpp` | Iterates results |

**SQLite Integration Approach**:
```cpp
// Use SQLite amalgamation (single-file implementation)
#include "third_party/sqlite3.h"

class SQLiteDatabase {
    sqlite3* db_;
public:
    bool open(const std::string& path);
    void execSQL(const std::string& sql);
    std::unique_ptr<Cursor> rawQuery(const std::string& sql, ...);
};
```

**Validation Method**:
```cpp
TEST(SQLiteDatabase, CreatesAndQueries) {
    SQLiteDatabase db;
    db.open("runtime/data/test.db");
    
    db.execSQL("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)");
    db.execSQL("INSERT INTO test (name) VALUES ('hello')");
    
    auto cursor = db.rawQuery("SELECT * FROM test");
    EXPECT_EQ(cursor->getCount(), 1);
    EXPECT_EQ(cursor->getString(1), "hello");
}
```

**Reason**: Telegram stores ALL messages in SQLite. This is non-negotiable.

---

### Week 6: Android Database Abstractions

**Objective**: Implement SQLiteDatabase and SQLiteOpenHelper

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|-----------------|----------|
| B2.1 | Implement SQLiteDatabase (Android API) | `src/api/sqlite_database.h/cpp` | Matches Android signature |
| B2.2 | Implement insert/update/delete/query | Same file | CRUD operations work |
| B2.3 | Implement transactions | Same file | begin/commit/rollback |
| B2.4 | Implement SQLiteOpenHelper | `src/api/sqlite_helper.h/cpp` | onCreate/onUpgrade called |
| B2.5 | Implement ContentValues | `src/api/content_values.h/cpp` | Key-value pairs for inserts |

**API Compatibility**:
```java
// Android API we're implementing:
SQLiteDatabase db = helper.getWritableDatabase();
ContentValues values = new ContentValues();
values.put("name", "Alice");
long rowId = db.insert("users", null, values);

Cursor cursor = db.query("users", null, null, null, null, null, null);
while (cursor.moveToNext()) {
    String name = cursor.getString(cursor.getColumnIndexOrThrow("name"));
}
cursor.close();
```

**Validation Method**:
```cpp
TEST(SQLiteOpenHelper, ManagesLifecycle) {
    class TestHelper : public SQLiteOpenHelper {
        void onCreate(SQLiteDatabase& db) override {
            db.execSQL("CREATE TABLE users (...)");
        }
    };
    
    TestHelper helper("runtime/data/test.db", 1);
    SQLiteDatabase db = helper.getWritableDatabase();
    // onCreate should have been called
    
    // Test CRUD cycle
    long id = db.insert("users", ContentValues().put("name", "Bob"));
    auto cursor = db.query("users");
    EXPECT_TRUE(cursor->moveToNext());
    EXPECT_EQ(cursor->getString(1), "Bob");
}
```

**Reason**: Telegram uses these exact APIs extensively.

---

### Week 7: Activity Lifecycle Implementation

**Objective**: Basic state machine for Activity lifecycle

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|-----------------|----------|
| B3.1 | Define Activity states enum | `src/api/activity_lifecycle.h` | Compiles |
| B3.2 | Implement state machine | `src/api/activity.h/cpp` | Transitions correctly |
| B3.3 | Implement onCreate() hook | Same file | Calls super.onCreate() |
| B3.4 | Implement onResume/onPause | Same file | State updates |
| B3.5 | Implement saved state bundle | Same file | Bundle persists |

**State Machine**:
```
          ┌─────────────┐
    ──────→│  CREATED    │
          └──────┬──────┘
                 │ onCreate()
                 ↓
          ┌─────────────┐
          │   STARTED   │←──────────────┐
          └──────┬──────┘               │
                 │ onStart()            │ onRestart()
                 ↓                      │
          ┌─────────────┐               │
          │   RESUMED   │───────────────┘
          └──────┬──────┘
                 │ onPause()
                 ↓
          ┌─────────────┐
          │   PAUSED    │
          └──────┬──────┘
                 │ onStop()
                 ↓
          ┌─────────────┐
          │   STOPPED   │──────────┐
          └──────┬──────┘           │
                 │ onDestroy()      │ getActivity()
                 ↓                  │ (if finished)
          ┌─────────────┐           │
          │ DESTROYED   │───────────┘
          └─────────────┘
```

**Validation Method**:
```cpp
TEST(ActivityLifecycle, FollowsCorrectOrder) {
    MockActivity activity;
    LifecycleTracker tracker;
    activity.setLifecycleObserver(&tracker);
    
    // Simulate startup
    activity.performCreate(null);
    activity.performStart();
    activity.performResume();
    
    EXPECT_EQ(tracker.getSequence(), "CREATED->STARTED->RESUMED");
    
    // Simulate backgrounding
    activity.performPause();
    activity.performStop();
    
    EXPECT_EQ(activity.getState(), STOPPED);
}
```

**Reason**: Telegram's LaunchActivity expects lifecycle callbacks.

---

### Week 8: Application Class Integration

**Objective**: Wire up Application.onCreate() to initialize our systems

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|----------------|----------| 
| B4.1 | Implement Application base class | `src/api/application.h/cpp` | Instantiates |
| B4.2 | Call attachBaseContext() | Same file | Context available |
| B4.3 | Call onCreate() trigger | Same file | Systems initialized |
| B4.4 | Register Activity lifecycle callbacks | Same file | Callbacks fire |
| B4.5 | Integrate with existing DalvikEngine | `src/runtime/integration.cpp` | Full pipeline works |

**Integration Point**:
```cpp
// When DEX interpreter encounters:
// invoke-direct {v0}, Landroid/app/Application;->onCreate()V

// Our dispatcher should route to:
void Application::onCreate() {
    // Initialize our systems:
    this->initSharedPreferences();  // Ready to use
    this->initFileSandbox();        // Directories created
    this->initDatabase();            // SQLite ready
    this->registerReceivers();       // If any
    
    // Log for evidence
    LOG_INFO("Application.onCreate() completed");
}
```

**Validation Method**:
```cpp
TEST(FullPipeline, ApplicationStartsSuccessfully) {
    // Load a simple APK
    APKLoader loader;
    auto apk = loader.load("test_apks/SimpleApp.apk");
    
    // Execute in runtime
    DalvikEngine engine;
    ExecutionResult result = engine.execute(apk);
    
    // Verify our systems initialized
    EXPECT_TRUE(result.applicationCreated);
    EXPECT_TRUE(result.sharedPrefsReady);
    EXPECT_TRUE(result.fileSandboxReady);
    
    // Check trace evidence
    EXPECT_TRUE(result.trace.contains("REAL_DALVIK_INTERPRETER"));
    EXPECT_TRUE(result.trace.contains("Application.onCreate"));
}
```

**Success Criteria for Phase B**:
- [ ] SQLite database opens, queries, closes correctly
- [ ] Android database API matches expected signatures
- [ ] Activity lifecycle transitions follow correct order
- [ ] Application.onCreate() initializes all subsystems
- [ ] End-to-end test runs without crashes
- [ ] Full trace evidence captured
- [ ] GitHub commit with all changes

---

## PHASE C: TELEGRAM INTEGRATION ATTEMPT (Weeks 9-12)

### Goal: "Load real Telegram APK, measure how far execution gets"

### Week 9: Real APK Loading

**Objective**: Successfully parse and load Telegram's classes.dex

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|----------------|----------|
| C1.1 | Obtain real Telegram APK | `download/apks/Telegram.apk` | File exists (~60MB) |
| C1.2 | Parse APK structure | Existing parser | Manifest extracted |
| C1.3 | Extract classes.dex | Existing parser | DEX file obtained |
| C1.4 | Parse DEX header | Existing parser | Header valid |
| C1.5 | Enumerate all classes | New tool | List of 50,000+ classes |
| C1.6 | Find entry point (LaunchActivity) | Analysis script | Class identified |

**Expected Output**:
```
Telegram APK Analysis Report:
============================
APK Size: 62.4 MB
DEX Files: 1 (classes.dex)
Classes: 52,847
Methods: 342,156
Entry Point: org.telegram.ui.LaunchActivity

Top Classes by Method Count:
1. org.telegram.messenger.MessagesController (2,341 methods)
2. org.telegram.ui.ChatActivity (1,892 methods)
3. org.telegram.tgnet.ConnectionsManager (987 methods)
...
```

**Validation**: Script produces report without errors.

---

### Week 10: Static Analysis

**Objective**: Catalog every Android API call Telegram makes

**Tasks**:

| Task | Description | Files to Create | Evidence |
|------|-------------|----------------|----------|
| C2.1 | Scan all method references | Analysis script | CSV of all calls |
| C2.2 | Identify Android framework calls | Filter script | Framework API list |
| C2.3 | Categorize by package | Analysis script | Grouped by android.* |
| C2.4 | Count frequency | Statistics script | Usage histogram |
| C2.5 | Cross-reference with our impl | Comparison matrix | Gap analysis |

**Output Format**:
```csv
Class,Method,Signature,Frequency,Implemented?
android.app.Activity,onCreate,(Landroid/os/Bundle;)V,15,YES
android.content.SharedPreferences,getString,(Ljava/lang/String;)Ljava/lang/String;,87,YES
android.database.sqlite.SQLiteDatabase,execSQL,(Ljava/lang/String;)V,234,YES
org.telegram.tgnet.ConnectionsManager,native_init,(J)V,45,NO_NATIVE
...
```

**Validation**: Complete inventory with no gaps.

---

### Week 11: Execution Attempt

**Objective**: Actually try to run Telegram in MiniAndroid

**Tasks**:

| Task | Description | Evidence |
|------|-------------|----------|
| C3.1 | Load Telegram into DalvikEngine | Engine accepts DEX |
| C3.2 | Begin execution at ApplicationLoader | Trace shows start |
| C3.3 | Capture exact failure point | Error logged |
| C3.4 | Document what executed successfully | Success log |
| C3.5 | Measure percentage complete | Metric calculated |

**Expected Outcome** (based on research):
```
Execution Trace:
===============
[00:00.000] APK Loaded: Telegram.apk (62.4 MB)
[00:00.001] DEX Parsed: 52,847 classes found
[00:00.002] Entry Point: ApplicationLoader.onCreate()
[00:00.003] Executing: invoke-super {p0}, Landroid/app/Application;->onCreate()V
[00:00.004] ✅ SUCCESS: Our Application.onCreate() called
[00:00.005] Executing: sget-object v0, Lorg/telegram/messenger/ApplicationLoader;->instance:L...;
[00:00.006] ✅ SUCCESS: Static field accessed
[00:00.007] Executing: const-string v1, "tgnet"
[00:00.008] ✅ SUCCESS: String constant loaded
[00:00.009] Executing: invoke-static {v1}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V
[00:00.010] ❌ FAILURE: UnsatisfiedLinkError - libtgnet.so not found
[00:00.010] === EXECUTION HALTED ===
[00:00.010] Instructions executed: 247
[00:00.010] Methods completed: 3
[00:00.010] Success rate: 0.001% (247 of ~millions needed)
```

**This is EXTREMELY VALUABLE EVIDENCE** — even though it "failed".

---

### Week 12: Stub Native Library Experiment

**Objective**: What if we provide an empty libtgnet.so?

**Tasks**:

| Task | Description | Evidence |
|------|-------------|----------|
| C4.1 | Create minimal .so file with JNI_OnLoad | C source compiled | Library loads |
| C4.2 | Register empty native methods | jni.c | Methods registered |
| C4.3 | Re-run Telegram execution | Trace output | Gets further? |
| C4.4 | Document new failure point | Analysis | Next barrier identified |
| C4.5 | Measure progress made | Metrics | Compare to Week 11 |

**Possible Outcome**:
```
With Stub Library:
===================
[... previous trace ...]
[00:00.010] ✅ SUCCESS: libtgnet.so loaded (stub)
[00:00.011] Executing: invoke-native {v0}, native_init
[00:00.012] ⚠️ STUB: native_init() returned void (no-op)
[00:00.013] Executing: invoke-virtual {v1}, MessagesController.getInstance()
[00:00.014] ✅ SUCCESS: Object created (but fields uninitialized)
[00:00.015] Executing: invoke-virtual {v2}, ConnectionsManager.getInstance()
[00:00.016] ⚠️ STUB: Returns object with null fields
[... continues further ...]
[00:01.234] ❌ CRASH: NullPointerException in MessagesController.init()
[00:01.234] === EXECUTION HALTED ===
[00:01.234] Instructions executed: 15,847
[00:01.234] Methods completed: 127
[00:01.234] Success rate: 0.05% (much better!)
```

**Success Criteria for Phase C**:
- [ ] Real Telegram APK loads without parser errors
- [ ] Complete API usage inventory created
- [ ] Execution attempt produces detailed trace
- [ ] Exact failure points documented with line numbers
- [ ] Stub library experiment completed
- [ ] Progress metrics show measurable advancement
- [ ] GitHub commit with all findings

---

## PHASE D: VALIDATION & DECISION (Weeks 13-16)

### Goal: "Make go/no-go decision based on hard evidence"

### Week 13: Comprehensive Testing

**Objective**: Validate everything built so far

**Tasks**:

| Task | Description | Evidence |
|------|-------------|----------|
| D1.1 | Run full test suite | Test output | All tests pass |
| D1.2 | Test persistence across actual restarts | Demo script | Data survives |
| D1.3 | Performance profiling | Profiler output | Acceptable speed |
| D1.4 | Memory leak detection | Valgrind/ASAN | No leaks |
| D1.5 | Edge case testing | Test cases | Robust behavior |

---

### Week 14: Documentation & Evidence Compilation

**Objective**: Prepare comprehensive proof of progress

**Deliverables**:

| Document | Content | Location |
|----------|---------|----------|
| **EXP037_FINAL_REPORT.md** | Complete experiment findings | docs/ |
| **EVIDENCE_PACKAGE.zip** | All traces, logs, screenshots | download/ |
| **TELEGRAM_ANALYSIS.csv** | Complete API inventory | database/ |
| **GAP_ANALYSIS.md** | What's left to implement | docs/ |
| **TIMELINE_REPORT.md** | Actual vs estimated time | docs/ |

---

### Week 15: Architecture Review

**Objective**: Honest assessment of path forward

**Questions to Answer**:

1. **Did Phase C reveal unexpected blockers?**
2. **Is the remaining effort still feasible?**
3. **Should we continue with Telegram or pivot?**
4. **What did we learn that changes the plan?**
5. **What's the revised timeline estimate?**

**Possible Outcomes**:

| Outcome | Criteria | Action |
|---------|----------|--------|
| **GO** | Got past 50% of initialization, clear path visible | Continue to next 16-week cycle |
| **PIVOT** | Blocked early, alternative target looks promising | Switch to simpler app |
| **HOLD** | Made progress but major unknowns remain | Research more before committing |
| **STOP** | Fundamental incompatibility discovered | Document lessons learned, move on |

---

### Week 16: Final Presentation & GitHub Preservation

**Objective**: Preserve all work and present findings

**Tasks**:

| Task | Description | Evidence |
|------|-------------|----------|
| D6.1 | Final GitHub commit | Git log | Commit hash recorded |
| D6.2 | Push to origin/main | Remote status | Push successful |
| D6.3 | Update README.md with EXP-037 section | README change | Updated |
| D6.4 | Update CHANGELOG.md | Changelog entry | Recorded |
| D6.5 | Update worklog.md | Worklog entry | Complete |
| D6.6 | Create summary presentation | Slides/doc | Ready to share |

**Final Commit Message Example**:
```
EXP-037: Telegram Compatibility Research & Infrastructure Phase

Research:
- Comprehensive Telegram API usage analysis (docs/EXP037_TELEGRAM_API_USAGE.md)
- Native dependency investigation (docs/EXP037_NATIVE_DEPENDENCY_ANALYSIS.md)
- External solutions study (docs/EXP037_EXTERNAL_RESEARCH.md)
- Architecture decision report (docs/EXP037_ARCHITECTURE_DECISION.md)

Implementation:
- File sandbox (runtime/data/ directory structure)
- SharedPreferences (XML-based key-value storage)
- SQLite integration (via sqlite3 amalgamation)
- Android Context wrapper (basic implementation)
- Activity lifecycle state machine
- Application class integration

Testing:
- Real Telegram APK loading (successful parsing)
- Execution attempt (documented failure at JNI call)
- Stub native library experiment (measurable progress)
- Persistence validation (data survives restart)

Evidence:
- 15+ trace files in run/exp037/
- Complete API usage inventory
- Gap analysis with priorities
- Timeline actual vs estimated

Conclusion: Telegram cannot fully run yet, but path is clear.
Recommendation: Continue with hybrid approach (Option A+B).

Files changed: 42
Tests added: 28
Lines of code: +18,000
```

---

## RISK REGISTER

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| SQLite integration fails | Low | High | Use well-tested amalgamation | Week 5 |
| Telegram APK too large to parse | Medium | Medium | Stream processing | Week 9 |
| Stub library approach doesn't work | High | Medium | Have fallback plan ready | Week 11 |
| Scope creep extends timeline | High | High | Strict MVP definition | Ongoing |
| Motivation loss due to slow progress | Medium | High | Weekly demos, small wins | Ongoing |
| Unexpected technical blockers | Medium | High | Research buffer time | Ongoing |

---

## SUCCESS DEFINITION (FINAL)

### Minimum Viable Success (Must Achieve):

> "MiniAndroid can load a real Android APK, execute Dalvik bytecode through our interpreter,
> persist application data to disk using SharedPreferences and SQLite,
> restore that data after a simulated restart,
> and provide detailed evidence of exactly where Telegram's execution fails."

### Stretch Goal (Nice to Have):

> "Using stub native libraries, Telegram's ApplicationLoader completes onCreate(),
> the LaunchActivity begins rendering, and we can see the login screen
> (even if non-functional)."

### Dream Goal (Unlikely but Possible):

> "With partial native method implementations, Telegram reaches the main chat list,
> and we can prove session persistence by logging in once and seeing the session survive restart."

---

## RESOURCE REQUIREMENTS

### Development Environment:

- [x] C++ compiler (MSVC/GCC/Clang)
- [x] CMake build system
- [x] SQLite3 amalgamation source
- [x] Real Telegram APK (from official sources)
- [x] Python for test scripts
- [ ] Time: 16 weeks (4 months) part-time

### External Dependencies:

| Dependency | Version | Purpose | License |
|------------|---------|---------|---------|
| SQLite3 | 3.44.0+ | Database engine | Public Domain |
| nlohmann/json | 3.11+ | JSON handling | MIT |
| GoogleTest | 1.14+ | Unit testing | BSD-3-Clause |
| (Optional) OpenSSL | 3.x | Future crypto | Apache 2.0 |

---

## CONCLUSION

### This Roadmap Provides:

✅ **Clear weekly milestones** — Always know what to do next  
✅ **Measurable success criteria** — Know when you've achieved goals  
✅ **Evidence-based decisions** — Every choice backed by data  
✅ **Risk mitigation** — Anticipated problems with solutions  
✅ **Flexible exit points** — Can stop at any phase with useful results  

### The Path Forward:

```
TODAY → Start Week 1 (File Sandbox)
    ↓
4 WEEKS → Phase A complete (Persistence works!)
    ↓
8 WEEKS → Phase B complete (Database + Lifecycle ready)
    ↓
12 WEEKS → Phase C complete (Telegram loaded, analyzed, attempted)
    ↓
16 WEEKS → Decision point (Go/Pivot/Hold/Stop based on evidence)
```

**The goal is ambitious but achievable with disciplined execution.**

**Every week produces tangible evidence of progress.**

**At the end, we'll have a definitive answer about Telegram compatibility.**

---

*"Every step must have reason, evidence, and expected result."* — ✅ This roadmap provides all three.
