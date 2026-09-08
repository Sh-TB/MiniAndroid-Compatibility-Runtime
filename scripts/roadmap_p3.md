
---

# 71. FAMILY BQ — ANDROIDX + R8 + REFLECTION CROSS TEST

Construct/collect real APKs combining:

```text
AndroidX
+
Kotlin
+
R8
+
reflection
+
lifecycle
+
generated classes
```

This is much more representative of modern APKs than isolated API fixtures.

---

# 72. FAMILY BR — MODERN APK STRESS CLUSTER

Maintain at least one APK in each category:

* [ ] Java
* [ ] Kotlin
* [ ] R8-heavy
* [ ] AndroidX
* [ ] AppCompat
* [ ] Room
* [ ] SQLite
* [ ] reflection
* [ ] timer/async
* [ ] custom View
* [ ] complex layout
* [ ] graphics
* [ ] multi-screen
* [ ] multi-dex
* [ ] native boundary
* [ ] Compose boundary
* [ ] WebView boundary
* [ ] libGDX boundary

---

# 73. FAMILY BS — AUTOMATIC GAP HUNTER

Build a permanent scanner that looks for:

```text
unimplemented API
silent default
missing class
missing method
missing field
missing constructor
missing resource
missing XML attribute
unsupported service
native method
reflection target
unhandled opcode
unexpected exception
future queue item
unknown drawable
unknown View subclass
```

Every finding enters the compatibility graph.

---

# 74. FAMILY BT — NO-DUPLICATE FINDING ENGINE

Before creating a finding:

```text
normalize
↓
search existing findings
↓
search worklog
↓
search issue
↓
search commits
↓
search compatibility graph
```

If same root cause exists:

```text
extend existing finding
```

instead of creating duplicate findings.

---

# 75. FAMILY BU — AUTOMATIC FAMILY COMPLETION CHECK

A family cannot become `[X]` unless:

```text
[ ] no known missing public API required by corpus
[ ] no known semantic gap
[ ] no silent stub
[ ] real APK proof
[ ] independent APK proof
[ ] guard APK
[ ] hostile test where applicable
[ ] deterministic 3-run
[ ] regression battery
[ ] documentation
```

---

# 76. FAMILY BV — BOUNDARY COMPLETION

Not everything needs to be implemented.

But every boundary must be explicit.

Example:

```text
Compose:
[D] outside current renderer architecture

WebView:
[D] native/web rendering boundary

OpenGL:
[D] native GPU boundary

IME:
[D] external input surface boundary
```

A boundary is complete only when:

* detected
* diagnosed
* documented
* reproducibly classified
* prevented from appearing as a mysterious blank screen

---

# 77. FAMILY BW — BLANK SCREEN PROTOCOL

Every blank APK follows:

```text
1. APK integrity
2. manifest
3. entry component
4. class loading
5. <clinit>
6. constructor
7. lifecycle
8. root View
9. child count
10. measured geometry
11. layout geometry
12. drawable
13. Canvas
14. text
15. input
16. async
17. native boundary
18. Compose/WebView/etc boundary
```

Stop only at the first causal failure.

---

# 78. FAMILY BX — PARTIAL SCREEN PROTOCOL

For partially rendered APK:

```text
missing region
→ responsible View
→ measurement
→ layout
→ drawable
→ text
→ callback
→ resource
```

Never fix pixels directly.

---

# 79. FAMILY BY — EXECUTION TRACE

Add a compact causal trace:

```text
APK
Activity
method
PC
API
receiver
result
state mutation
scheduled event
frame
```

This becomes the equivalent of a debugger for MiniAndroid.

---

# 80. FAMILY BZ — FRAME GRAPH

For visual/async APKs record:

```text
FRAME 0
FRAME 1
FRAME 2
...
```

Each frame has:

```text
virtual_time
callbacks
state changes
layout hash
render hash
screenshot hash
```

This turns visual debugging into causal debugging.

---

# 81. FAMILY CA — STATE MACHINE VALIDATION

Every stateful component must have:

```text
states
events
transitions
side effects
invalid transitions
```

Examples:

```text
Activity
View
Pressed state
Lifecycle
Timer
Room
SavedState
Intent
```

---

# 82. FAMILY CB — API CONTRACT MINING

When a method is missing:

Do not implement from its name.

Collect:

```text
signature
documentation
AOSP source
call sites
return semantics
exception semantics
side effects
thread semantics
lifecycle requirements
```

Then implement.

---

# 83. FAMILY CC — CALL-SITE MINING

For every missing API determine:

```text
how many APKs
how many call sites
argument distributions
receiver types
return consumers
common patterns
rare patterns
```

Implementation should be driven by actual demand.

---

# 84. FAMILY CD — RETURN-VALUE CONSUMER ANALYSIS

For every API returning a value:

determine whether caller:

```text
ignores
stores
branches
casts
invokes
renders
passes onward
```

This catches APIs where returning a syntactically valid but semantically wrong value creates delayed failures.

---

# 85. FAMILY CE — TYPE-FLOW ANALYSIS

Track:

```text
value
declared type
runtime type
union field
conversion
cast
consumer
```

This is mandatory after the historical CONV/CMP/LONG cascade.

---

# 86. FAMILY CF — OBJECT IDENTITY

Audit APIs where identity matters:

* [ ] Intent
* [ ] Runnable
* [ ] Handler
* [ ] View
* [ ] Context
* [ ] Drawable
* [ ] Bundle
* [ ] Class
* [ ] Thread
* [ ] Cursor
* [ ] Database
* [ ] listener

Never replace identity-sensitive objects with value-only approximations.

---

# 87. FAMILY CG — CACHE / LIFETIME SEMANTICS

For every cache:

```text
creation
lookup
invalidation
configuration change
lifecycle
identity
```

This is especially important for:

```text
Resources
Drawable
ViewModel
SavedState
Class
Reflection
```

---

# 88. FAMILY CH — MEMORY / OWNERSHIP

Audit:

* [ ] parent ownership
* [ ] View ownership
* [ ] Drawable ownership
* [ ] Cursor lifetime
* [ ] SQLite lifetime
* [ ] Message ownership
* [ ] Runnable identity
* [ ] Handler ownership

Look specifically for double registration and stale objects.

---

# 89. FAMILY CI — INITIALIZATION ORDER

Explicitly test:

```text
static initialization
application initialization
activity initialization
view constructor
resource initialization
AndroidX initialization
Room initialization
```

Many "random" failures are initialization-order failures.

---

# 90. FAMILY CJ — MODERNIZATION / VERSION QUALIFIERS

Do not assume one Android version.

Record:

```text
compile SDK
target SDK
min SDK
framework API used
behavioral version differences
```

Implement only the semantics required by actual corpus first, but keep version gates explicit.

---

# 91. FAMILY CK — PERFORMANCE WITHOUT SEMANTIC DAMAGE

After correctness:

* [ ] identify hot paths
* [ ] cache safe metadata
* [ ] avoid repeated class-chain resolution
* [ ] avoid repeated resource scans
* [ ] optimize parser allocations
* [ ] preserve deterministic ordering

Never optimize by weakening semantics.

---

# 92. FAMILY CL — FINAL EXECUTION GATE

MiniAndroid Base Execution is NOT considered complete merely because:

```text
59/59
```

passes.

The real gate is:

```text
DEX closure
+
class linker closure
+
Java core closure
+
Android API closure
+
resource closure
+
inflation closure
+
layout closure
+
render closure
+
input closure
+
lifecycle closure
+
async closure
+
persistence closure
+
reflection closure
+
R8 closure
+
AndroidX closure
+
corpus closure
+
determinism closure
+
diagnostic closure
+
reproducibility closure
```

---

# 93. FINAL MASTER ACCEPTANCE MATRIX

Before declaring the Base Runtime complete, produce:

| Domain          | Law | Implementation | Real APK | Independent APK | Guard | Deterministic | Regression | Status |
| --------------- | --- | -------------- | -------- | --------------- | ----- | ------------- | ---------- | ------ |
| DEX             |     |                |          |                 |       |               |            |        |
| ART/ClassLinker |     |                |          |                 |       |               |            |        |
| R8/D8           |     |                |          |                 |       |               |            |        |
| Java Core       |     |                |          |                 |       |               |            |        |
| Exceptions      |     |                |          |                 |       |               |            |        |
| Reflection      |     |                |          |                 |       |               |            |        |
| Context         |     |                |          |                 |       |               |            |        |
| Activity        |     |                |          |                 |       |               |            |        |
| Intent          |     |                |          |                 |       |               |            |        |
| Bundle          |     |                |          |                 |       |               |            |        |
| Handler         |     |                |          |                 |       |               |            |        |
| MessageQueue    |     |                |          |                 |       |               |            |        |
| Thread          |     |                |          |                 |       |               |            |        |
| AndroidX        |     |                |          |                 |       |               |            |        |
| View            |     |                |          |                 |       |               |            |        |
| ViewGroup       |     |                |          |                 |       |               |            |        |
| Measurement     |     |                |          |                 |       |               |            |        |
| Layout          |     |                |          |                 |       |               |            |        |
| Resources       |     |                |          |                 |       |               |            |        |
| AXML            |     |                |          |                 |       |               |            |        |
| Drawable        |     |                |          |                 |       |               |            |        |
| Canvas          |     |                |          |                 |       |               |            |        |
| Text            |     |                |          |                 |       |               |            |        |
| Input           |     |                |          |                 |       |               |            |        |
| Lifecycle       |     |                |          |                 |       |               |            |        |
| SQLite          |     |                |          |                 |       |               |            |        |
| Room            |     |                |          |                 |       |               |            |        |
| Persistence     |     |                |          |                 |       |               |            |        |
| Native boundary |     |                |          |                 |       |               |            |        |
| Multi-Dex       |     |                |          |                 |       |               |            |        |
| Toolchain       |     |                |          |                 |       |               |            |        |
| Corpus          |     |                |          |                 |       |               |            |        |

---

# 94. THE NEW CODER DECISION LOOP

For every cycle, Coder MUST execute:

```text
1. RUN CURRENT BATTERY
2. BUILD FAILURE GRAPH
3. FIND HIGHEST-CENTRALITY UNRESOLVED FAMILY
4. MINE AOSP LAW
5. MINE IMPLEMENTATION REFERENCES
6. TRACE CURRENT MINIANDROID PATH
7. IDENTIFY ROOT GAP
8. IMPLEMENT SMALLEST GENERIC SEMANTIC FIX
9. ADD LAW TEST
10. TEST REAL APK
11. TEST INDEPENDENT APK
12. TEST GUARD APK
13. RUN 3 DETERMINISTIC RUNS
14. RUN FULL REGRESSION
15. UPDATE COMPATIBILITY GRAPH
16. UPDATE ISSUE #9
17. SEARCH AGAIN FOR SECOND-ORDER GAPS
18. CONTINUE
```

Do NOT stop after step 8.

---

# 95. THE "LIGHT IN THE DARK" RULE

When blocked, Coder MUST NOT simply say:

```text
I found blocker X.
```

Instead report:

```text
BLOCKER
↓
LIKELY ROOT FAMILY
↓
AOSP SOURCE TO STUDY
↓
EXTERNAL IMPLEMENTATION TO STUDY
↓
EXACT MINIANDROID FILES TO TRACE
↓
EXPECTED SEMANTIC LAW
↓
MINIMAL FIX STRATEGY
↓
TEST STRATEGY
↓
REAL APK CONSUMER
↓
INDEPENDENT APK
```

The Coder should always have a next research direction.

---

# 96. WHEN A NEW FINDING APPEARS

Do not ask whether it fits the old roadmap.

Create:

```text
NEW FAMILY
or
SUB-FAMILY
```

and connect it to the graph.

Required:

```text
FINDING-ID
ROOT FAMILY
DEPENDENCIES
SOURCE LAW
SOURCE REFERENCES
IMPLEMENTATION PLAN
APK
TEST
STATUS
```

The roadmap is intentionally extensible.

---

# 97. WHEN A FIX SOLVES MULTIPLE APKs

Do not create one finding per APK.

Create:

```text
ONE SEMANTIC ROOT FIX
+
MULTIPLE APK OBSERVATIONS
```

This is preferred.

---

# 98. WHEN A FIX CHANGES NOTHING VISUALLY

Do not assume it failed.

It may close:

```text
latent correctness
future APK compatibility
exception safety
resource correctness
reflection
R8 compatibility
```

Prove it with a targeted test.

---

# 99. WHEN A FIX CHANGES MANY PIXELS

Do not assume it is good.

Require:

```text
AOSP law
+
causal explanation
+
affected region
+
guard APK analysis
```

---

# 100. FINAL OBJECTIVE

The end state is NOT:

> "We fixed the current APKs."

The end state is:

> **MiniAndroid has a coherent, source-mined compatibility core whose behavior is defined by Android laws, whose implementation is generic, whose gaps are observable, whose real APK demand drives prioritization, and whose supported compatibility families can be independently reproduced and verified.**

The final evidence package must contain:

```text
CURRENT_HEAD_BASELINE
COMPATIBILITY_GRAPH
FAMILY_CLOSURE_MATRIX
REAL_APK_REGISTRY
SHA256 REGISTRY
SOURCE_REUSE_LEDGER
LAW_TEST INDEX
HOSTILE TEST INDEX
DETERMINISM INDEX
REGRESSION BATTERY
VISUAL GOLDEN INDEX
FINDING INDEX
BOUNDARY INDEX
GITHUB EVIDENCE INDEX
FINAL COMPATIBILITY MATRIX
```

---

# 101. ABSOLUTE STOP CONDITION

Coder may declare:

```text
BASE COMPATIBILITY CLOSED
```

only when:

1. all high-centrality families are closed or explicitly bounded;
2. no silent runtime stubs remain in exercised paths;
3. no known unsupported API is silently misrepresented;
4. DEX execution semantics are verified;
5. class/receiver/type semantics are verified;
6. resource/inflation/layout/render pipeline is verified;
7. lifecycle/async semantics are verified;
8. reflection/R8/AndroidX interactions are verified where demanded;
9. real APK coverage spans all currently supported architecture clusters;
10. independent APK validation exists;
11. guard APKs remain stable;
12. 3-run deterministic proof exists for major scenarios;
13. full regression passes;
14. toolchain/corpus restoration is reproducible;
15. all boundaries are explicitly documented;
16. all claims have direct GitHub evidence.

---

# 102. ISSUE #9 IS A LIVING DOCUMENT

Do NOT replace the roadmap when new work appears.

Append/merge new discoveries into the appropriate family.

Every future campaign must update:

```text
checkbox
status
finding
root cause
source
commit
test
APK
evidence URL
```

Preserve historical evidence.

Never erase solved work.

---

# 103. FINAL INSTRUCTION TO CODER

You are not being asked to "find bugs".

You are being asked to **close the compatibility system**.

Do not wait for another prompt after discovering the next missing family.

Do not stop after the first green test.

Do not trust previous agent claims without independent verification.

Do not implement package-specific hacks.

Do not weaken existing goldens.

Do not hide unsupported behavior behind null/zero/false.

Do not use static inspection as runtime proof.

Use:

```text
AOSP → source law
ART → runtime law
AndroidX → modern framework law
R8 → optimized APK reality
Robolectric → deterministic behavioral reference
Apktool / ARSCLib / Androguard → independent APK/resource/Dex forensics
WineDroid / compatible runtimes → reusable implementation patterns
REAL APKs → compatibility demand
INDEPENDENT APKs → generality proof
GUARD APKs → regression proof
METAMORPHIC TESTS → hidden-state proof
3-RUN REPLAY → determinism proof
```

Then continue automatically until the current family is genuinely closed.

**The goal is not "more findings".**

**The goal is fewer and fewer unresolved compatibility families until the runtime has no unexplained gap inside its declared base boundary.**
