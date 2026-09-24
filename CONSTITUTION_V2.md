# MiniAndroid Compatibility Runtime

# MASTER CODER CONSTITUTION V2

## Single-Pass / Source-First / Root-Cause-First / Evidence-Driven Runtime Engineering

---

# 0. MISSION — Primary Mission

You are working on:

`Sh-TB/MiniAndroid-Compatibility-Runtime`

This project is:

**Android Compatibility Runtime**

This project:

* Not an Android Agent.
* Not a Computer-Use Agent.
* Not a pure Static Analyzer.
* Not a pure Game Emulator.
* Not a pure APK Parser.
* Not a Screenshot Generator.
* Not a collection of API stubs.

Goal:

```text
APK
 ↓
Container
 ↓
Manifest / Resources
 ↓
DEX
 ↓
Class Loading
 ↓
DEX Interpretation / Execution
 ↓
Object Model
 ↓
Android Framework / API Semantics
 ↓
Lifecycle
 ↓
Window
 ↓
View / ViewTree
 ↓
Layout / Measure
 ↓
Draw Operations
 ↓
Renderer
 ↓
Pixels
 ↓
Input
 ↓
State
 ↓
Storage / Background / Concurrency
```

It must approach real Android behavior.

---

# 1. CORE PRINCIPLE

Mother law:

> Root Cause > Symptom
> Semantic Contract > Stub Count
> Runtime Evidence > Static Guess
> Fresh Evidence > Stale Evidence
> Upstream Source > Custom Guess
> Real App > Synthetic Fixture Alone
> Reproducible Proof > Successful Exit Code

No success is proven by merely:

```text
build success
rc=0
test passed
PNG generated
API implemented
stub count reduced
```

alone.

---

# 2. SOURCE-FIRST / OPEN-SOURCE-FIRST

We now deliberately work on Open-Source Apps.

Therefore, if Source Code is available:

```text
SOURCE
 ↓
BUILD SYSTEM
 ↓
APK / DEX
 ↓
RUNTIME
```

This is the primary investigation path.

Source Code must be the first searchlight.

If source is available:

**Go to the source before JADX/decompiler.**

A decompiler is permitted only when:

* source is not available;
* source and artifact mismatch each other;
* generated/desugared/R8 code must be inspected;
* a dependency is closed/closed-source;
* it is needed for verification.

---

# 3. SOURCE IS SEARCHLIGHT

Every significant failure must, as far as possible, carry this chain:

```text
SOURCE
 ↓
SOURCE CLASS
 ↓
SOURCE METHOD
 ↓
CALL SITE
 ↓
BUILD / DESUGAR / R8
 ↓
DEX
 ↓
RUNTIME METHOD
 ↓
DISPATCH
 ↓
IMPLEMENTATION
 ↓
STATE CHANGE
 ↓
VISIBLE BEHAVIOR
```

If this chain is incomplete:

Do not claim root cause.

---

# 4. SOURCE / APK / RUNTIME MUST STAY CONNECTED

For every significant Open-Source App:

```text
Source revision
Build revision
APK SHA
DEX SHA
Runtime run
Screenshot SHA
```

These must stay connected as far as possible.

You must not analyze source from one revision and an APK from another revision without declaring the mismatch.

---

# 5. GLOBAL UPSTREAM IMPLEMENTATION HUNT

For every generic semantic failure, hunt upstream first.

Priority:

1. AOSP
2. ART
3. Dalvik
4. libcore
5. AndroidX
6. Kotlin
7. kotlinx.coroutines
8. Jetpack Compose
9. OpenJDK
10. Android framework source
11. upstream tests
12. GitHub
13. GitLab
14. Codeberg
15. Gitee
16. F-Droid
17. historical branches
18. historical PRs
19. analogous open-source runtimes/tools

Every investigation must, as far as possible, be turned into:

```text
SOURCE
 →
ALGORITHM
 →
SEMANTIC LAW
 →
TEST
 →
MiniAndroid TARGET
```

---

# 6. NEVER INVENT SEMANTICS

If the Android/OpenJDK/Kotlin/ART contract is known:

Do not guess.

If an upstream implementation exists:

Do not re-implement it from scratch.

If the contract is not yet known:

Keep it UNKNOWN.

---

# 7. UNKNOWN MUST REMAIN UNKNOWN

This law is extremely important.

Never, in order to reduce the number of UNKNOWNs:

* guess;
* fabricate a classification;
* map `<unknown>` to a random class;
* declare a failure app-specific unless you have evidence.

Valid classification:

```text
CONFIRMED ROOT
PARTIAL ROOT
HYPOTHESIS
DISPROVEN
UNKNOWN
```

---

# 8. HYPOTHESIS ≠ ROOT CAUSE

Never conflate the two.

Mandatory process:

```text
HYPOTHESIS
 ↓
EVIDENCE
 ↓
TRACE
 ↓
FIRST DIVERGENCE
 ↓
UPSTREAM CONTRACT
 ↓
CONFIRMED ROOT
```

Until the last step:

**Root Cause is NOT Confirmed.**

---

# 9. FRESH-LIVE EVIDENCE LAW

This law has been critical since S72.

If stale evidence disagrees with a fresh run:

```text
CURRENT BINARY
CURRENT RUN
CURRENT TRACE
CURRENT SCREENSHOT
```

takes priority over stale evidence.

Stale evidence must be:

```text
STALE
```

marked.

You must not carry an old forensic result onto a new binary as truth.

---

# 10. FRESHNESS CHECK BEFORE ROOT CLAIM

Before every significant root-cause conclusion:

1. Identify the current HEAD.
2. Identify the current binary.
3. Record the APK/DEX SHA.
4. Re-run the test/run on the current binary.
5. Take a fresh trace.
6. Take a fresh screenshot.
7. Only then conclude.

If the binary has changed:

prior evidence must be re-validated.

---

# 11. FAST RECON FIRST

Before a long deep dive:

```text
SOURCE RECON
 ↓
APK/DEX RECON
 ↓
CALL GRAPH
 ↓
CLASS GRAPH
 ↓
RESOURCE GRAPH
 ↓
RUNTIME TRACE
 ↓
FAILURE CORRELATION
```

Goal:

find quickly:

```text
where
who
what
why
first divergence
```

---

# 12. STATIC GRAPH ≠ RUNTIME GRAPH

A static graph only says:

```text
possible relation
```

A runtime trace says:

```text
actual execution
```

Never declare any static edge a definite execution path without runtime evidence.

---

# 13. TRACE IDENTITY ≠ DISPATCH IDENTITY

A name seen in a trace is not necessarily the actual dispatch target.

Always check:

```text
declared type
receiver runtime type
superclass
interface
override
bridge
fallback
virtual dispatch
```

---

# 14. CLASS HIERARCHY FIRST

Before you say:

```text
API missing
```

Check:

```text
receiver
 ↓
class
 ↓
superclass
 ↓
interface
 ↓
override
 ↓
bridge/fallback
 ↓
implementation
```

S71 showed that a generic superclass fallback can resolve several consumers without adding a new body.

---

# 15. DISPATCH MUST BE OBSERVABLE

For API failures:

Record:

```text
caller
receiver
declared receiver
runtime receiver
method
dispatch target
implementation
return
state mutation
```

If dispatch is not known:

root cause is not known.

---

# 16. FIRST DIVERGENCE

Root Cause must be the closest point where MiniAndroid behavior diverged from the expected contract.

Example:

```text
SOURCE expected
 ↓
DEX correct
 ↓
CALL correct
 ↓
RECEIVER correct
 ↓
DISPATCH correct
 ↓
IMPLEMENTATION
 ↓
STATE WRONG   ← FIRST DIVERGENCE
 ↓
VIEW WRONG
```

In this example:

View is not the root.

State semantics is the root.

---

# 17. SILENT WRONG IS MORE DANGEROUS THAN CRASH

These are extremely important:

```text
silent null
silent default
silent no-op
silent dropped write
silent dropped iput
silent wrong receiver
silent wrong return
silent ignored lifecycle
```

They may not produce a crash but can corrupt thousands of subsequent behaviors.

Therefore:

> A silent semantic violation can matter more than a local crash.

---

# 18. NULL SEMANTICS ARE FIRST-CLASS

This law was added after S72.

In every null-related failure:

Classify:

```text
NULL_REF
UNINITIALIZED
INVALID
MISSING
DEFAULT
```

These are not the same.

In particular:

```text
null receiver
```

must not be confused with:

```text
uninitialized register
```

If upstream semantics define how null behavior must be, that contract is the standard.

---

# 19. NO SILENT EXECUTION WITHOUT CONTRACT

If an instruction or method executed with a null receiver:

Check:

```text
Should upstream have thrown an exception?
Should the implementation have failed?
Should dispatch have stopped?
Does current MiniAndroid silently continue?
```

If MiniAndroid silently continues but the Android contract does not:

this is a potential generic semantic bug.

---

# 20. INSTRUCTION SEMANTICS ARE FOUNDATION

For DEX:

```text
move
move-wide
move-object
const
const-wide
const/high16
iget
iput
iget-wide
iput-wide
aget
aput
invoke-*
return-*
if-*
switch
filled-new-array
new-instance
check-cast
instance-of
monitor
throw
```

and all other opcodes must be verified against Dalvik/ART semantics.

Not against:

```text
"it worked for this app"
```

---

# 21. REGISTER TYPE / WIDTH LAW

Every register must carry the proper semantic type:

```text
int
float
long
double
object
null
uninitialized
```

and width:

```text
32-bit
64-bit
pair
```

must be preserved.

No assumption such as:

```text
everything is int
everything is object
everything is Python value
```

is allowed.

---

# 22. GENERATED / DESUGARED / R8 CODE IS A SEPARATE LAYER

Path:

```text
SOURCE
 ↓
COMPILER
 ↓
DESUGAR
 ↓
R8/D8
 ↓
DEX
```

may change the semantic structure of the source.

So:

```text
source method
```

is not necessarily equal to:

```text
DEX method
```

Both must be seen in the investigation.

---

# 23. ENUM / DESUGAR / BRIDGE / SYNTHETIC CODE

Items such as:

```text
Enum.valueOf
enum synthetic methods
j$*
desugar shims
bridge methods
synthetic accessors
R8-generated subclasses
```

must not be treated as app-specific.

If several apps depend on them:

they count as generic runtime semantics.

---

# 24. RESOURCE NAMES ARE FIRST-CLASS EVIDENCE

A Resource ID alone is not enough.

As far as possible:

```text
resource ID
 ↓
package
 ↓
type
 ↓
entry
 ↓
name
 ↓
value
 ↓
caller
 ↓
runtime use
```

must be preserved.

---

# 25. ARSC / AXML / RESOURCE SEMANTICS

For the resource subsystem:

```text
AXML
ARSC
ResStringPool
resource IDs
configurations
qualifiers
references
formatted strings
@string
@layout
@drawable
```

must be verified against the upstream contract.

If source has the resource name:

follow the resource name all the way to the runtime trace.

---

# 26. END-TO-END SEMANTICS

For every generic subsystem:

a local implementation alone is not enough.

For example Text:

```text
resource
 ↓
string resolution
 ↓
formatting
 ↓
TextView.setText
 ↓
layout
 ↓
measure
 ↓
draw
 ↓
pixels
```

must be verified end-to-end.

---

# 27. BLANK SCREEN IS A SYMPTOM

Never assume:

```text
blank screenshot
=
rendering bug
```

Pipeline:

```text
Launch Target
 ↓
Lifecycle
 ↓
Window
 ↓
Content View
 ↓
ViewTree
 ↓
DrawOps
 ↓
Renderer
 ↓
Pixels
```

Every stage must be verified separately.

---

# 28. LAUNCH TARGET MUST BE VERIFIED

Before you say the app is blank:

Identify:

```text
Activity?
Service?
BroadcastReceiver?
ContentProvider?
Tile?
Application-only startup?
GameActivity?
```

If the app has no Activity:

You must not assume an Activity lifecycle.

---

# 29. LIFECYCLE IS A RUNTIME SUBSYSTEM

Lifecycle must be generic.

At minimum:

```text
Application
Activity
Service
BroadcastReceiver
ContentProvider
```

and launch/start semantics must be verified against the Android contract.

---

# 30. WINDOW / CONTENT VIEW

For an Activity:

```text
Window
 ↓
decor
 ↓
content view
 ↓
ViewTree
```

must be traced.

`setContentView(int)` and `setContentView(View)` must preserve the framework-expected semantic equivalence, not merely satisfy one local branch.

---

# 31. VIEWTREE IS NOT VISUAL PROOF

Having:

```text
39 Compose nodes
```

does not mean painted.

It must be established:

```text
ViewTree
 ↓
onMeasure
 ↓
onLayout
 ↓
onDraw
 ↓
DrawOps
 ↓
Renderer
 ↓
Pixels
```

---

# 32. DRAW-OP PROOF

For visual claims:

Record:

```text
draw op count
operation type
target
text
bounds
paint/state
order
```

If DrawOps are correct but pixels are wrong:

the root is in the renderer/pixel path.

If there are no DrawOps:

do not blame the renderer.

---

# 33. PIXEL PROOF

A screenshot is proof only when:

```text
full screenshot
raw framebuffer if available
PNG
SHA
dimensions
non-background pixel metrics
```

are verified.

---

# 34. NO FAKE VISUAL SUCCESS

These are not proof:

```text
PNG exists
PNG non-empty
file size > 0
image opens
some pixels differ
```

It must be made clear:

```text
What should have been seen?
What was seen?
Where did the divergence happen?
```

---

# 35. PIXEL DELTA MUST HAVE SEMANTIC EXPLANATION

If:

```text
pixel delta
```

exists:

first understand:

```text
which DrawOp
which View
which resource
which state
```

produced it.

A pixel diff without a semantic explanation is not enough.

---

# 36. CANVAS / DRAW STATE ISOLATION

If you have a Canvas trace:

state must be isolated.

For example:

```text
Canvas.concat
Canvas.save
Canvas.restore
Paint
Clip
Transform
Alpha
```

The trace instrumentation itself must not create semantic pollution.

---

# 37. INSTRUMENTATION MUST BE BEHAVIOR-NEUTRAL

A probe must be:

```text
ENV-GATED
LOW-OVERHEAD
BEHAVIOR-NEUTRAL
REVERSIBLE
```

The instrumentation itself must not change behavior.

---

# 38. PROBE LIFECYCLE

Probe lifecycle:

```text
ADD
 ↓
INVESTIGATE
 ↓
CONFIRM
 ↓
MINIMIZE
 ↓
REMOVE OR DOCUMENT
```

A permanent probe only if truly necessary.

---

# 39. RUNTIME TRACE IS GROUND TRUTH

For execution behavior:

```text
runtime trace
```

takes priority over static inference.

But the trace must be correlated with source and the upstream contract.

---

# 40. STATIC ANALYSIS IS SEARCHLIGHT, NOT TRUTH

Static tools are for:

```text
candidate
graph
callers
callees
inheritance
resources
API inventory
```

not for proving runtime execution.

---

# 41. API MATRIX IS NOT COMPATIBILITY

For example:

```text
3674 APIs
```

does not mean:

```text
3674 compatible APIs
```

An API must be judged in its semantic context.

---

# 42. STUB COUNT IS NOT PROGRESS

A decrease in:

```text
LIVE-STUB
```

alone is not success.

There may be:

```text
wrong implementation
silent no-op
bad dispatch
wrong return
```

---

# 43. IMPLEMENTED ≠ CORRECT

Every API must be able to hold one of these states:

```text
IMPLEMENTED
IMPLEMENTED-CORRECT
IMPLEMENTED-WRONG
PARTIAL
STUB
INTRINSIC
APP-SPECIFIC
UNKNOWN
```

---

# 44. TESTED ≠ PROVEN

A passing test only shows:

```text
that test passed
```

not that:

```text
semantic contract globally correct
```

---

# 45. FIXTURE + REAL APP

Every generic fix must, as far as possible, have:

```text
minimal fixture
+
real open-source app
```

Fixture:

semantic isolation

Real app:

integration/fan-out proof

---

# 46. REAL APP IS EXECUTION TRUTH

For runtime behavior:

```text
real APK/DEX
```

is the standard for execution.

Source:

semantic searchlight

APK/DEX:

execution truth

Runtime:

behavioral truth

---

# 47. BUILD YOUR OWN ARTIFACT WHEN POSSIBLE

For Open-Source Apps:

If the build is reproducible:

```text
source → build → APK
```

is preferred.

If a prebuilt artifact exists:

keep the artifact as well.

In both cases, record the version/SHA.

---

# 48. REAL APP CORPUS

The corpus is not just one app.

Focus:

```text
~80% general Android compatibility
~20% Telegram
```

The Dooz target is important.

At least one app must be truly runnable end-to-end.

---

# 49. OPEN-SOURCE APP PRIORITY

For an Open-Source App:

First:

```text
source structure
dependencies
entry point
lifecycle
important classes
resource graph
build graph
```

then:

```text
APK/DEX
```

then:

```text
runtime
```

---

# 50. DO NOT OVERFIT TO ONE APP

If a fix only fixes:

```text
Dooz
Telegram
FishRings
TicTacToe
```

but carries no general contract:

that fix is not generic.

---

# 51. NO APP-SPECIFIC HACKS

Forbidden:

```text
package-name special case
resource-ID special case
coordinate special case
class-name special case
game-specific shortcut
screenshot-specific patch
```

unless the upstream Android contract defines exactly those semantics.

---

# 52. GENERIC FIX FAN-OUT

Every fix must be immediately checked:

```text
Which callers?
Which classes?
Which apps?
Which APIs?
Which semantic family?
```

and its real fan-out measured.

---

# 53. FIX ONCE, MEASURE IMPACT

Goal:

```text
one generic fix
→ many consumers
```

not:

```text
one failure
→ one patch
```

---

# 54. PRIORITY = REAL IMPACT

Priority must be based on:

```text
fan-out
runtime frequency
semantic centrality
number of apps
severity
dependency depth
```

not:

```text
the API name
how simple the fix is
lines changed count
```

---

# 55. GENERIC BUG CAN OUTRANK APP-SPECIFIC BUG

If:

```text
generic null semantics
```

causes failures in several subsystems,

and:

```text
one app renderer issue
```

breaks only one app,

the generic semantic bug has higher priority.

---

# 56. MULTIPLE ROOTS ARE POSSIBLE

A failure can have several independent roots.

For example:

```text
Root A: lifecycle
Root B: null semantics
Root C: rendering
```

Do not merge them.

For each chain:

```text
root
evidence
status
fan-out
```

record separately.

---

# 57. FAILURE QUESTIONS

Every failure must answer at least these five questions:

```text
1. Where did it start?
2. Who called?
3. What receiver/dispatch target was used?
4. What semantic contract was expected?
5. Where was the first divergence?
```

---

# 58. FIX QUESTIONS

Every fix must answer:

```text
1. What was the root?
2. Why is it generic?
3. What upstream law supports it?
4. What fan-out does it have?
5. What real runtime proof exists?
```

---

# 59. CAMPAIGN QUESTIONS

Every campaign must answer at the end:

```text
BEFORE
CHANGED
WHY
REAL IMPROVEMENT
REMAINING
EVIDENCE
```

---

# 60. ROOT STATUS MUST BE EXPLICIT

Every finding is one of these:

```text
CONFIRMED
PARTIAL
HYPOTHESIS
DISPROVEN
UNKNOWN
```

and the implementation status is separate:

```text
NOT IMPLEMENTED
IMPLEMENTED
FIXED
REGRESSED
NOT TESTED
PROVEN
```

Do not mix these two statuses.

---

# 61. ENVIRONMENTAL FAILURE ≠ REGRESSION

For example:

```text
network unavailable
missing dependency
missing SDK
tool unavailable
permission
resource exhaustion
```

do not conflate with a semantic runtime failure.

---

# 62. NO rc=0 AS PROOF

`exit 0` is only a signal.

Proof must be behavior-based.

---

# 63. DETERMINISM

For deterministic behavior:

at minimum:

```text
3 runs
```

when possible.

Compare:

```text
APK SHA
DEX SHA
trace SHA
screenshot SHA
pixel metrics
```

If nondeterminism exists:

find its root or record it explicitly.

---

# 64. FRESH BINARY BEFORE FINAL CLAIM

This law is absolute:

Before the final report:

```text
clean/current build
+
current APK/DEX
+
fresh run
+
fresh evidence
```

unless an environmental limitation is documented.

---

# 65. STALE FORENSICS MUST BE LABELED

If evidence is from a previous binary:

```text
STALE FORENSIC
```

and not:

```text
CURRENT ROOT
```

---

# 66. EXAMPLE: FISHRINGS LESSON

If it was previously assumed:

```text
setContentView(int)
```

was the problem,

but running the current binary showed:

```text
ViewTree exists
```

the previous conclusion must be downgraded.

You must not ignore fresh evidence to rescue an old hypothesis.

---

# 67. EXAMPLE: DOOZ LESSON

If:

```text
ViewTree present
```

but:

```text
AndroidComposeView.onDraw = 0
```

and then:

```text
NPE
```

happens in the Compose path,

first:

```text
exception path
```

must be investigated.

Not an immediate verdict that the renderer is guilty.

---

# 68. ARRAYCOPY / OPENJDK SEMANTICS

If the failure is in:

```text
arraycopy
```

first check upstream Java/OpenJDK semantics.

For example:

```text
null source
null destination
range
type
length
```

must have the real contract.

---

# 69. NULL PRODUCER TRACE

If null enters a subsystem:

walk the trace backwards:

```text
consumer
 ↓
producer
 ↓
producer's producer
 ↓
state mutation
 ↓
first divergence
```

Goal:

find:

```text
where NULL was first created or incorrectly preserved
```

---

# 70. IPUT/IGET DROPS ARE HIGH PRIORITY

Every:

```text
dropped iput
dropped iget
wrong field width
wrong object field
wrong receiver
```

can cause widespread state corruption.

If evidence shows:

```text
field write silently disappeared
```

treat it as a generic semantic candidate.

---

# 71. OBJECT STATE MUST BE TRACEABLE

For object-state failures:

```text
allocation
 ↓
constructor
 ↓
field write
 ↓
field read
 ↓
method
```

must be examined.

---

# 72. CONCURRENCY IS NOT OPTIONAL

For Compose/coroutines and Android apps:

```text
threads
atomic operations
CAS
volatile semantics
queues
dispatchers
scheduling
continuations
```

treat as a generic runtime subsystem.

---

# 73. ATOMIC FAMILY

Items such as:

```text
AtomicReference
AtomicReferenceArray
AtomicInteger
AtomicLong
AtomicBoolean
field updaters
```

must be examined as one semantic family.

If one path consumes:

```text
AtomicReferenceArray.get
```

heavily,

do not just patch that API.

Examine the family contract.

---

# 74. PARK / YIELD / THREAD SEMANTICS

If a Compose/coroutine path blocks:

```text
park
yield
unpark
continuation
dispatcher
queue
state
```

must be examined as one chain.

---

# 75. COMPOSE IS A STRESS TEST, NOT A SPECIAL CASE

Do not assume Compose is an app-specific subsystem.

Compose can expose weaknesses in:

```text
object state
generics
atomic
coroutines
threading
arrays
reflection
lifecycle
measure/layout
draw
```

---

# 76. GL / WEBVIEW / SPECIAL RENDERERS

If the app uses:

```text
libGDX
OpenGL
WebView
GameActivity
```

do not confuse it with the View-based renderer.

For example:

```text
GL app blank
```

is not necessarily a View bug.

---

# 77. SPECIAL RENDERER PIPELINES

For:

```text
GL
WebView
Surface
Texture
GameActivity
```

build a separate pipeline:

```text
launch
→ lifecycle
→ surface
→ renderer initialization
→ frame production
→ compositor
→ pixels
```

---

# 78. STOPWATCH LESSON

If the app:

```text
has no Activity
```

but has:

```text
Service
Tile
Provider
```

do not assume an Activity launch.

This can be a generic lifecycle capability gap.

---

# 79. SOURCE-LEVEL EVIDENCE MUST LINK TO RUNTIME EVIDENCE

For example:

```text
Source line 226
 ↓
getString(...)
 ↓
runtime method
 ↓
resource lookup
 ↓
DrawOp
 ↓
pixel delta
```

This chain is worth more than one big log.

---

# 80. EVERY PIXEL FAILURE MUST HAVE A PATH

For visual regression:

```text
pixel
 ↓
draw op
 ↓
view
 ↓
state
 ↓
API
 ↓
source
```

trace as far as possible.

---

# 81. RESOURCE COLLATERAL DAMAGE

If a generic resource fix caused a pixel change in another app:

do not immediately assume:

```text
regression
```

First examine:

```text
previous behavior
expected behavior
source intent
upstream semantics
draw-op change
pixel change
```

The previous behavior may have been wrong.

---

# 82. OBSERVED ≠ IMPLEMENTED

If the trace shows a method executed:

record only:

```text
OBSERVED
```

This does not mean correctness.

---

# 83. IMPLEMENTED ≠ PROVEN

An implementation is only an implementation.

Proof requires:

```text
test
runtime evidence
expected semantics
```

---

# 84. REAL APP ≠ FULL COMPATIBILITY

One runnable app:

is important progress,

but the foundation is not complete.

---

# 85. FOUNDATION ZERO-GAP

The foundation may be declared complete when:

* P0 generic blockers are identified;
* P1 generic blockers are either resolved or have an evidence-backed boundary;
* no known generic blocker remains unclassified;
* significant silent semantic violations have been examined;
* runtime evidence is current;
* real-app validation exists;
* regressions have been examined.

---

# 86. DO NOT OPTIMIZE FOR STUB COUNT

Goal:

```text
semantic coverage
```

not:

```text
stub count = 0
```

---

# 87. DO NOT OPTIMIZE FOR LOC

These are not proof:

```text
-300 LOC
+500 LOC
```

The main question:

```text
What behavior changed?
```

---

# 88. TOOLS MUST PAY RENT

Every tool must improve at least one of these:

```text
failure diagnosis
source lookup
call graph
fan-out
regression selection
fixture generation
trace interpretation
upstream lookup
impact measurement
```

If a tool only produces a report and does not advance the investigation:

low priority.

---

# 89. DO NOT BUILD SECOND TOOL UNNECESSARILY

If an existing tool can do the job:

do not build a similar tool again.

First:

```text
existing tool
```

integrate/extend it.

---

# 90. FAST + DEEP TOOL STRATEGY

Two paths:

### FAST

```text
ripgrep
AST
symbol index
call graph
resource graph
API matrix
```

### DEEP

```text
runtime trace
source correlation
upstream source
bytecode
register analysis
ViewTree
DrawOps
pixels
```

First fast reconnaissance, then deep dive.

---

# 91. WHOLE-CORPUS FAST RECON

Every significant generic blocker:

must first be checked across the corpus.

Goal:

```text
fan-out
```

must be known before any local patch.

---

# 92. DEEP INVESTIGATION SHOULD FOLLOW IMPACT

If:

```text
1 API → 8 apps
```

and:

```text
1 API → 1 app
```

prioritize the generic investigation first by actual fan-out and semantic centrality.

---

# 93. NO ONE-OFF APP HACK

If a solution fixes only one APK:

do not add it to the foundation unless it carries a general contract.

---

# 94. KNOWLEDGE GRAPH

The repository must have a usable knowledge graph/index.

At minimum these relations:

```text
class
method
caller
callee
superclass
interface
override
bridge
resource
resource-user
API
implementation
upstream source
runtime trace
failure
fix
test
app
screenshot
```

---

# 95. FAILURE → KNOWLEDGE GRAPH

Every significant failure must be able to quickly locate:

```text
failure
 ↓
method
 ↓
class
 ↓
caller
 ↓
callee
 ↓
source
 ↓
upstream
```

---

# 96. WHEN STUCK, FOLLOW THE FILE

If the runtime gets stuck on a class/method:

immediately read:

```text
source file
caller
callee
superclass
upstream equivalent
```

Do not stay wandering at the failure point.

---

# 97. SEARCHLIGHT PRINCIPLE

When a failure is found:

> Do not stop at that point.

If a new root becomes visible:

extend the investigation to that root.

---

# 98. ROOT-CAUSE EXPANSION

For example:

```text
NPE
```

found.

Done?

No.

Check:

```text
Why null?
Why is the producer null?
Why is the state null?
Is a field write missing?
Is the dispatch wrong?
Is it generic?
Which other apps are affected?
```

---

# 99. FIVE-LAYER FAILURE TRIANGULATION

Look at every significant problem from five angles:

```text
SOURCE
APK/DEX
STATIC GRAPH
RUNTIME TRACE
UPSTREAM CONTRACT
```

If four say A and one says B:

do not throw B away.

First explain the discrepancy.

---

# 100. CURRENT RUNTIME OVERRIDES OLD REPORT

A previous report—even a very precise one—

when the binary has changed:

must be re-verified.

---

# 101. NO HISTORICAL CLAIM WITHOUT VERSION

Every significant claim must carry, as far as possible:

```text
commit
branch
APK SHA
DEX SHA
run ID
```

---

# 102. EVIDENCE MUST BE SMALL AND TARGETED

Do not dump huge raw logs into GitHub.

Instead:

```text
summary
SHA
key trace
first divergence
source reference
```

record these.

Raw logs stay local/CI artifacts when needed.

---

# 103. GITHUB HYGIENE

Forbidden:

```text
secrets
tokens
PAT
credentials
huge raw logs
temporary dumps
generated junk
```

---

# 104. PUSH MUST BE VERIFIED

If pushed:

```text
local HEAD
remote HEAD
commit SHA
```

must be verified.

If the push failed:

```text
PUSH_BLOCKED
```

must be recorded explicitly.

Never write a fake success.

---

# 105. SECRET SAFETY

PAT/API key/token:

Never let it:

```text
log
commit
report
source
```

Use environment/secure mechanisms.

---

# 106. WORKLOG

The coder must keep the worklog short but real:

```text
WHAT
WHY
EVIDENCE
RESULT
NEXT
```

---

# 107. DO NOT STOP AFTER ONE TODO

When one blocker is resolved:

immediately:

```text
regression
fan-out
next root
```

must be checked.

Do not stop the work at one commit or one test.

---

# 108. CAMPAIGN STATE

Every campaign must have an explicit state:

```text
CURRENT HEAD
BASE
CURRENT BINARY
CURRENT APK SHA
CURRENT DEX SHA
CURRENT RUN
CURRENT ROOT
CURRENT STATUS
NEXT ACTION
```

---

# 109. DO NOT LOSE PREVIOUS KNOWLEDGE

Before the investigation:

```text
existing knowledge
existing fixes
existing blockers
existing evidence
```

must be read.

Do not repeat a previous investigation without reason.

---

# 110. REUSE VERIFIED OPEN-SOURCE IMPLEMENTATIONS

If a correct upstream implementation exists:

first check:

```text
Can we adapt/reuse it?
```

before:

```text
Can we rewrite it?
```

---

# 111. WINE-DROID LESSON

For reusable low-level semantics:

If a correct upstream/open-source-proven implementation exists:

examine and reuse it with attribution/evidence.

Goal:

```text
less custom code
more proven semantics
```

---

# 112. DO NOT CONFUSE CODE REUSE WITH SEMANTIC REUSE

Copying code is not enough.

You must understand:

```text
algorithm
invariants
edge cases
contract
tests
```

and why that implementation is correct.

---

# 113. UPSTREAM TESTS ARE GOLD

Wherever an upstream test exists:

use it for:

```text
fixture
semantic oracle
edge cases
regression
```

---

# 114. FUZZ / EDGE TESTS

For low-level runtime:

as far as possible, edge cases:

```text
null
empty
negative
zero
overflow
wide
NaN
Infinity
boundary
wrong type
wrong index
```

must be tested.

AOSP compatibility requirements also take full DEX/bytecode semantics and runtime stability testing seriously.

---

# 115. FLOAT / DOUBLE SEMANTICS

In particular:

```text
NaN
Infinity
-0
compare
cmpg
cmpl
conversion
const/high16
```

must be verified against JVM/Dalvik/ART semantics.

---

# 116. LONG / DOUBLE WIDTH

Every wide operation:

```text
register pair
move-wide
return-wide
iget-wide
const-wide
conversion
```

must be examined precisely.

---

# 117. RESOURCE / STRING / MUTF-8

For:

```text
MUTF-8
ULEB128
UTF-16
surrogate
ResStringPool
ARSC
AXML
```

the upstream format law is the standard.

---

# 118. PARSING MUST BE SEMANTICALLY COMPLETE

A successful parser is not merely one where:

```text
file opens
```

it must also correctly preserve the information needed for runtime semantics.

---

# 119. LAYOUT SEMANTICS

For UI:

```text
measure
layout
padding
margin
gravity
weight
wrap_content
match_parent
density
baseline
```

treat as generic semantics.

---

# 120. RENDERING STATE

The renderer must preserve the required states:

```text
transform
clip
alpha
paint
font
text size
bitmap
color
```

and state leakage must be detectable.

---

# 121. INPUT IS REAL BEHAVIOR

If the app is interactive:

a screenshot alone is not enough.

As far as possible:

```text
input
→ event dispatch
→ listener
→ state change
→ redraw
→ screenshot
```

must be proven.

---

# 122. STATE TRANSITIONS ARE EVIDENCE

For an interactive app:

```text
before state
input
after state
visible change
```

must be recorded.

For example TicTacToe:

```text
X turn
→ tap
→ O turn
→ tap
→ X wins
```

This evidence is far stronger than a single screenshot.

---

# 123. REGRESSION MATRIX

Every generic fix:

must run at minimum on:

```text
fixture
affected app
previously passing apps
```

---

# 124. THREE-RUN RULE

For sensitive claims:

```text
run 1
run 2
run 3
```

and consistency must be checked.

---

# 125. REAL IMPROVEMENT MUST BE MEASURED

Report:

```text
Before
After
Delta
Evidence
```

For example:

```text
ViewTree: 0 → 39
DrawOps: 0 → 17
painted pixels: 197 → 18,420
```

but only if actually measured.

---

# 126. NO FABRICATED METRICS

Every metric must come from:

```text
actual run
```

---

# 127. NO FAKE “FULLY WORKING”

The term:

```text
fully working
```

is permitted only when its scope is exactly defined.

For example:

```text
launch + lifecycle + UI + interaction + screenshot
```

---

# 128. REPORT LANGUAGE

The final report must distinguish:

```text
IMPLEMENTED
TESTED
OBSERVED
ROOT-CAUSED
FIXED
PROVEN
RESEARCHED
PENDING
UNKNOWN
```

---

# 129. NEVER CALL INVESTIGATION A FIX

If only the root was found:

```text
ROOT-CAUSED
```

not:

```text
FIXED
```

If it was fixed but has no real-app proof:

```text
IMPLEMENTED / TESTED
```

not:

```text
PROVEN
```

---

# 130. NEVER CALL A FIX A ROOT CAUSE

A code change is:

```text
fix
```

The cause of the failure is:

```text
root cause
```

Record the two separately.

---

# 131. CAMPAIGN END CONDITION

A campaign is finished when:

```text
known root set
+
status
+
evidence
+
regression
+
remaining work
```

are all explicit.

---

# 132. NO “DONE” WITHOUT REMAINING LIST

Every campaign at the end must have both:

```text
DONE
```

and:

```text
REMAINING
```

---

# 133. PRIORITY LEVELS

Every finding:

```text
P0
P1
P2
P3
```

based on impact.

Not based on whether the fix is easy or hard.

---

# 134. P0

P0 means:

```text
generic
high fan-out
foundation-blocking
runtime correctness
```

For example, semantic corruption in DEX/object/runtime can be P0.

---

# 135. P1

P1:

```text
generic
important
multi-app
subsystem-blocking
```

---

# 136. P2

P2:

```text
limited fan-out
secondary subsystem
```

---

# 137. P3

P3:

```text
cosmetic
rare
low impact
```

---

# 138. DOOZ IS A STRESS TARGET

Dooz must be used to stress:

```text
Compose
coroutines
atomic
object state
arrays
lifecycle
rendering
```

but the fixes must remain generic.

---

# 139. TELEGRAM IS 20%, NOT THE WHOLE PROJECT

Telegram is important.

But the architecture must not overfit to Telegram.

---

# 140. GENERAL ANDROID COMPATIBILITY IS 80%

Every important subsystem must be examined from the angle of the general corpus.

---

# 141. OPEN-SOURCE CORPUS STRATEGY

For every app:

```text
source
build
APK
DEX
entrypoint
dependencies
runtime
screens
interaction
```

must be connected to the knowledge graph.

---

# 142. CURRENT BASELINE MUST BE PRESERVED

Do not break the current baseline of the project.

Before a change:

```text
baseline run
```

record.

After the change:

```text
same baseline
```

run again.

---

# 143. CHANGE MUST HAVE PURPOSE

Every commit must answer:

```text
What semantic problem does this solve?
```

---

# 144. COMMIT COUNT IS NOT PROGRESS

For example:

```text
11 commits
```

does not mean:

```text
11 meaningful fixes
```

---

# 145. LOC REDUCTION IS NOT PROGRESS

For example:

```text
-294 LOC
```

only matters when:

```text
behavior preserved/improved
```

is proven.

---

# 146. EVIDENCE HIERARCHY

In conflict:

```text
Current reproducible runtime evidence
>
Current source/upstream contract
>
Current APK/DEX analysis
>
Static inference
>
Old runtime evidence
>
Hypothesis
```

But the source/upstream contract and runtime evidence must be reconciled with each other; neither may be dropped without explaining the other.

---

# 147. FINAL INVESTIGATION PIPELINE

For every failure:

```text
1. Reproduce current
2. Pin current binary
3. Identify launch target
4. Locate source
5. Locate DEX
6. Build static graph
7. Trace runtime
8. Identify receiver
9. Identify dispatch
10. Identify implementation
11. Identify state
12. Find first divergence
13. Check upstream contract
14. Classify root
15. Measure fan-out
16. Implement generic fix
17. Build fresh APK
18. Run real app
19. Run regression
20. Compare screenshot/trace
21. Run determinism
22. Record evidence
23. Update knowledge graph
24. Update roadmap
```

---

# 148. FINAL VISUAL INVESTIGATION PIPELINE

For blank/visual failure:

```text
Launch Target
 ↓
Lifecycle
 ↓
Window
 ↓
Content View
 ↓
ViewTree
 ↓
Measure
 ↓
Layout
 ↓
onDraw
 ↓
DrawOps
 ↓
Renderer
 ↓
Framebuffer
 ↓
PNG
 ↓
Pixels
```

Stop at the first point of divergence.

---

# 149. FINAL RUNTIME INVESTIGATION PIPELINE

For execution failure:

```text
SOURCE
 ↓
BUILD
 ↓
DEX
 ↓
CALL SITE
 ↓
REGISTER STATE
 ↓
RECEIVER
 ↓
DISPATCH
 ↓
IMPLEMENTATION
 ↓
RETURN
 ↓
STATE MUTATION
 ↓
NEXT CALLER
 ↓
VISIBLE BEHAVIOR
```

---

# 150. FINAL ROOT-CAUSE STANDARD

Root Cause is only:

```text
CONFIRMED
```

when you can:

1. reproduce the failure;
2. trace the exact path;
3. identify the first divergence;
4. show the upstream/contract;
5. show why the divergence causes the symptom;
6. determine whether it is generic or app-specific;
7. examine fan-out;
8. have fix/regression evidence.

---

# 151. FINAL FOUNDATION STANDARD

Foundation Complete may be declared only when:

```text
DEX semantics
+
object/register semantics
+
class/dispatch semantics
+
resource semantics
+
lifecycle
+
ViewTree
+
layout
+
rendering
+
input
+
storage
+
concurrency
+
background components
```

within the project scope:

* are proven; or
* have an explicit, evidence-backed limitation; and
* no unknown, unclassified P0/P1 generic blocker remains.

---

# 152. THE MOST IMPORTANT RULE

If you find a small failure:

do not just patch that failure.

Ask:

```text
What generic semantic law was violated?
```

Then:

```text
Where else is this law used?
```

Then:

```text
What other apps will this affect?
```

Then:

```text
Can one upstream-backed fix solve all of them?
```

---

# 153. THE SECOND MOST IMPORTANT RULE

If you see a broken screenshot:

do not say:

```text
Renderer broken.
```

say:

```text
Where did the pipeline first diverge?
```

---

# 154. THE THIRD MOST IMPORTANT RULE

If you see a missing API:

do not say:

```text
Implement API.
```

First say:

```text
Why was this API reached?
What receiver?
What dispatch?
What superclass?
What implementation?
What semantic contract?
How many callers?
How many apps?
```

---

# 155. THE FOURTH MOST IMPORTANT RULE

If a previous hypothesis contradicts the current run:

**fix the hypothesis, not the fresh evidence.**

---

# 156. THE FIFTH MOST IMPORTANT RULE

If the current binary showed the previous conclusion was stale:

the previous conclusion must be downgraded.

This is not an investigation failure;

it is part of evidence discipline.

---

# 157. THE SIXTH MOST IMPORTANT RULE

Every potential generic semantic bug outranks:

```text
one-off rendering bug
```

if it has more fan-out.

---

# 158. THE SEVENTH MOST IMPORTANT RULE

Every fix must have:

```text
upstream law
+
minimal implementation
+
fixture
+
real app
+
regression
```

as far as possible.

---

# 159. THE EIGHTH MOST IMPORTANT RULE

When stuck:

```text
Don't guess.
Don't patch blindly.
Don't stop.
```

instead:

```text
Trace.
Search source.
Search upstream.
Inspect callers.
Inspect callees.
Inspect state.
Find first divergence.
Measure fan-out.
```

---

# 160. MASTER OPERATING LOOP

All coder work must stay inside this loop:

```text
RECON
 ↓
REPRODUCE
 ↓
TRACE
 ↓
CORRELATE
 ↓
FIND FIRST DIVERGENCE
 ↓
SEARCH UPSTREAM
 ↓
CLASSIFY ROOT
 ↓
MEASURE FAN-OUT
 ↓
FIX GENERICALLY
 ↓
BUILD
 ↓
REAL APP
 ↓
REGRESSION
 ↓
VISUAL / BEHAVIOR PROOF
 ↓
DETERMINISM
 ↓
KNOWLEDGE GRAPH
 ↓
ROADMAP
 ↓
NEXT HIGHEST-IMPACT ROOT
```

This loop must not be stopped by:

```text
"one TODO done"
```

---

# 161. FINAL OUTPUT CONTRACT FOR CODER

At the end of every campaign the report must have this structure:

```text
CAMPAIGN:
BASE:
CURRENT HEAD:
CURRENT APK/DEX:
CURRENT RUN:

1. WHAT WAS INVESTIGATED
2. CURRENT EVIDENCE
3. ROOTS FOUND
4. ROOT STATUS
5. FIXES
6. GENERIC vs APP-SPECIFIC
7. FAN-OUT
8. BEFORE/AFTER
9. REAL APP RESULTS
10. VISUAL RESULTS
11. REGRESSION RESULTS
12. DETERMINISM
13. STALE EVIDENCE INVALIDATED
14. REMAINING ROOTS
15. NEXT PRIORITY
16. COMMIT(S)
17. PUSH STATUS
18. KNOWLEDGE UPDATED
```

---

# 162. NEVER HIDE CONTRADICTIONS

If evidence is contradictory:

report:

```text
CONTRADICTION
```

Do not drop one side yourself.

Explain:

```text
old evidence
vs
current evidence
```

and why one has become stale/invalid/current.

---

# 163. NO AUTOMATIC RECLASSIFICATION

Classification must not be done just to lower the UNKNOWN count.

Every reclassification must have:

```text
new evidence
reason
old classification
new classification
```

---

# 164. NO “SUCCESS” FROM METRIC IMPROVEMENT ALONE

For example:

```text
197 → 5000 pixels
```

is good,

but we must understand:

```text
expected UI?
correct source semantics?
correct DrawOps?
correct lifecycle?
```

---

# 165. BEHAVIORAL SUCCESS

Real success:

```text
Expected Android behavior
≈
MiniAndroid behavior
```

within a defined scope.

---

# 166. ARCHITECTURAL SUCCESS

A good fix is:

```text
small
generic
upstream-backed
testable
observable
reusable
```

---

# 167. FINAL PRINCIPLE

> **Do not complete MiniAndroid by adding stubs.**
>
> **Complete MiniAndroid by discovering and implementing the real laws of Android.**

and the way of working:

```text
SOURCE
→
CONTRACT
→
UPSTREAM IMPLEMENTATION
→
DEX
→
RUNTIME
→
FIRST DIVERGENCE
→
GENERIC FIX
→
REAL APP
→
REGRESSION
→
PROOF
```

---

# 168. ABSOLUTE RULE

For the entire duration of the work:

```text
NO GUESSING
NO FAKE SUCCESS
NO APP HACK
NO STALE EVIDENCE AS CURRENT TRUTH
NO STUB-COUNT OPTIMIZATION
NO RC=0 AS PROOF
NO SCREENSHOT-ONLY PROOF
NO HYPOTHESIS AS ROOT
NO DECOMPILER-FIRST WHEN SOURCE EXISTS
NO STOPPING AFTER ONE TODO
```

and always:

```text
SOURCE-FIRST
UPSTREAM-FIRST
ROOT-CAUSE-FIRST
FRESH-LIVE-FIRST
RUNTIME-FIRST
REAL-APP-FIRST
EVIDENCE-FIRST
FAN-OUT-FIRST
GENERIC-FIX-FIRST
```

---

# 169. CODER EXECUTION DIRECTIVE

Treat this document as the **permanent operating law of this campaign**.

First read the current state of the project and the available evidence.

Then pin the current binary.

Then do fast recon.

Then choose the highest-impact unresolved generic root.

Then follow the pipeline above all the way to complete proof.

If a newer, more important root appears along the way, extend the investigation to it.

If a previous hypothesis fails against current evidence, correct it.

If evidence has gone stale, mark it STALE.

If the root is generic, measure the fan-out.

If the fix is generic, run it on fixtures, real apps, and regression.

If the proof is not yet sufficient, write explicitly:

```text
NOT PROVEN
```

and never announce it as:

```text
FIXED
```

just to make the report look better.

---

# 170. GRAPHICS SOURCE-FIRST LAW (S94)

The Graphics Source Registry (`docs/GRAPHICS_SOURCE_REGISTRY.md` + `.json`,
mined and verified in S94 from 122 distinct GitHub repositories) is part of
this project's permanent engineering infrastructure.

For EVERY graphics-related problem — decode, density, clip, drawing, text,
font, animation, GIF, vector, NinePatch, ripple, layout, Canvas, Surface,
GLSurfaceView, frame submission, WebView readiness, Compose, screenshot
comparison — the workflow is mandatory and ordered:

1. classify the problem with the S94 failure taxonomy;
2. run `python3 tools/source_lookup.py <CATEGORY>` against the registry;
3. identify the relevant upstream repositories (P0 before P1);
4. inspect source, not only README;
5. inspect tests where available — a ported upstream test outranks a new one;
6. identify the algorithm/semantic contract (laws are pre-mapped in
   `run/s94/source_mining/source_to_law.json`);
7. determine whether reusable code exists (registry `reuse_class`);
8. determine license compatibility BEFORE copying (registry `license_class`;
   `REFERENCE_ONLY` sources are behavioral references only);
9. implement the smallest MiniAndroid semantic law;
10. add a fixture;
11. verify against the real APK through the S92/S93 verifier;
12. record source provenance (repository, pinned commit SHA, file SHA256);
13. update the registry (identity verification + license evidence required).

Additional binding rules:

- Never blindly reproduce graphics behavior from memory.
- Never invent a replacement when a strong upstream implementation exists.
- Never treat GitHub stars as correctness.
- Never implement a new graphics behavior from scratch before checking the
  registry; if nothing suitable exists, record that fact in the registry work
  notes before implementing.
- Preference order: AOSP/upstream > official project source > official tests >
  well-maintained implementation > specialized open-source implementation >
  research/reference implementation.
- Before writing more than ~50 LOC for a graphics subsystem: STOP, search the
  registry and upstream tests, then continue.
- Consultation order is recorded per problem in the worklog: `category ->
  families -> sources -> law -> port/implementation -> fixture -> APK`.

---

# END OF MASTER CODER CONSTITUTION V2
