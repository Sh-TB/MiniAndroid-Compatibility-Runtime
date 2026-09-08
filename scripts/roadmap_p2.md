
---

# 34. FAMILY AF — ANNOTATION / GENERIC / SYNTHETIC METADATA

Audit real APK use of:

* [ ] annotations
* [ ] annotation values
* [ ] parameter annotations
* [ ] generic signatures
* [ ] inner classes
* [ ] enclosing methods
* [ ] synthetic flags
* [ ] bridge flags
* [ ] debug metadata

---

# 35. FAMILY AG — MULTI-DEX

This deserves explicit closure.

* [ ] classes.dex
* [ ] classes2.dex
* [ ] classes3.dex
* [ ] cross-dex references
* [ ] class lookup
* [ ] method lookup
* [ ] resource references
* [ ] duplicate classes
* [ ] deterministic ordering

No "single DEX" assumption may remain hidden.

---

# 36. FAMILY AH — NATIVE / JNI BOUNDARY

Do not immediately implement native execution.

First inventory.

For every native call:

```text
library
symbol
caller
arguments
return type
frequency
APK
```

Classify:

```text
CAN SHADOW
CAN PURE-JAVA REIMPLEMENT
CAN STUB SAFELY
REQUIRES NATIVE
OUT OF SCOPE
```

Important candidates:

* [ ] libc-like utility calls
* [ ] graphics
* [ ] SQLite
* [ ] crypto
* [ ] compression
* [ ] WebView
* [ ] OpenGL
* [ ] audio

Never silently return fake success.

---

# 37. FAMILY AI — JNI / NATIVE METHOD SEMANTICS

Separate from native library implementation.

* [ ] native method detection
* [ ] registration
* [ ] signature lookup
* [ ] static native
* [ ] instance native
* [ ] argument conversion
* [ ] return conversion
* [ ] exception propagation

---

# 38. FAMILY AJ — ANIMATION / FRAME PROGRESSION

A screenshot at t=0 is not sufficient.

Audit:

* [ ] Animation
* [ ] Animator
* [ ] ValueAnimator
* [ ] ObjectAnimator
* [ ] interpolators
* [ ] frame timing
* [ ] invalidation
* [ ] cancellation
* [ ] end callbacks
* [ ] deterministic frame progression

---

# 39. FAMILY AK — ACCESSIBILITY / SEMANTIC EVENTS

Only implement when demanded, but inventory:

* [ ] content descriptions
* [ ] accessibility events
* [ ] accessibility click
* [ ] importantForAccessibility
* [ ] semantic tree

If unsupported, classify honestly.

---

# 40. FAMILY AL — FRAGMENT / NAVIGATION

Do not implement prematurely, but formally classify.

### AL1

* [ ] Fragment
* [ ] FragmentManager
* [ ] Fragment lifecycle
* [ ] child fragments
* [ ] back stack
* [ ] Fragment result
* [ ] saved state

### AL2

If current corpus does not demand it:

```text
[D] OUTSIDE CURRENT BASE
```

But keep the dependency map ready.

---

# 41. FAMILY AM — COMPOSE / WEBVIEW / GLSURFACE / NATIVE UI

Do not call these "bugs" when the architecture does not support them.

Classify separately:

```text
Compose
WebView
GLSurfaceView
OpenGL
libGDX
native rendering
IME surface
```

For each:

* [ ] detect
* [ ] explain
* [ ] collect demand
* [ ] estimate architecture cost
* [ ] define boundary

---

# 42. FAMILY AN — CORPUS MINING

The corpus itself becomes an instrument.

For every APK record:

```text
APK
SHA256
SDK
target SDK
DEX count
framework families
AndroidX families
Kotlin
R8
resources
views
native libraries
entry point
render status
interaction status
async status
persistence status
failure signature
```

---

# 43. FAMILY AO — AUTOMATIC API DEMAND MINING

EXP-017 must evolve into a permanent subsystem.

Mine:

* [ ] methods
* [ ] classes
* [ ] constructors
* [ ] fields
* [ ] interfaces
* [ ] reflection
* [ ] native calls
* [ ] resource IDs
* [ ] XML tags
* [ ] style attributes
* [ ] services
* [ ] permissions

Rank by:

```text
frequency
APK count
UI impact
dependency centrality
implementation difficulty
reusability
```

The next target must be chosen from this score, not intuition.

---

# 44. FAMILY AP — SILENT STUB ELIMINATION

Search the entire runtime for:

```text
return 0;
return false;
return null;
return "";
TODO
FIXME
unimplemented
not implemented
ignore
no-op
```

But do NOT mechanically replace them.

For each:

1. identify caller
2. identify API contract
3. identify AOSP law
4. identify actual APK consumer
5. classify safe/unsafe default
6. implement or explicitly boundary it

Every silent stub becomes either:

```text
REAL
EXPLICITLY UNSUPPORTED
SAFE SEMANTIC DEFAULT
```

Never silent.

---

# 45. FAMILY AQ — DIAGNOSTIC FORENSICS

Every missing behavior must generate structured evidence.

Required diagnostic channels:

```text
[CLASS-MISS]
[METHOD-MISS]
[FIELD-MISS]
[API-MISS]
[RESOURCE-MISS]
[XML-MISS]
[DRAWABLE-MISS]
[MEASURE-MISS]
[LAYOUT-MISS]
[INPUT-MISS]
[QUEUE-MISS]
[THREAD-MISS]
[REFLECTION-MISS]
[NATIVE-MISS]
[UNSUPPORTED-SERVICE]
[RETURN-MISMATCH]
[TYPE-MISMATCH]
[RECEIVER-MISMATCH]
[CONFIG-MISMATCH]
```

Each diagnostic must include:

```text
APK
class
method
descriptor
receiver
arguments
PC if applicable
call depth
source
```

---

# 46. FAMILY AR — DIFFERENTIAL TESTING

For each important API family create a reference oracle.

Possible oracle:

* AOSP source-derived expected behavior
* Robolectric
* Java/JVM reference
* Android emulator where available
* independent parser
* manually constructed semantic golden

Do not require pixel equality for dynamic OS-dependent fields.

---

# 47. FAMILY AS — METAMORPHIC TESTING

This is a major new addition.

Instead of only testing:

```text
input → expected output
```

test transformations that must preserve semantics.

Examples:

```text
same APK + different resource order
same APK + different class ordering
same APK + R8 optimization
same APK + equivalent XML attribute order
same APK + equivalent constructor path
same APK + same event with different frame partitioning
```

Expected semantic result should remain invariant.

This catches hidden state bugs.

---

# 48. FAMILY AT — DETERMINISM

Every important APK:

```text
RUN 1
RUN 2
RUN 3
```

must compare:

* screenshot
* frame sequence
* event sequence
* callback sequence
* state transitions
* logs
* resource decisions
* virtual time

Use exact binary hashes where appropriate.

---

# 49. FAMILY AU — HOSTILE INPUT

Every parser/runtime family receives hostile tests.

### DEX

* [ ] oversized
* [ ] truncated
* [ ] malformed

### ARSC

* [ ] bad offsets
* [ ] huge counts
* [ ] cycles
* [ ] invalid references

### AXML

* [ ] malformed chunks
* [ ] invalid strings
* [ ] invalid attributes

### PNG

* [ ] invalid IHDR
* [ ] unsupported color type
* [ ] truncated IDAT
* [ ] bad dimensions
* [ ] palette mismatch

### Runtime

* [ ] null
* [ ] wrong type
* [ ] invalid receiver
* [ ] missing method
* [ ] missing class
* [ ] cyclic inheritance
* [ ] duplicate registration

---

# 50. FAMILY AV — RESOURCE / PARSER CROSS-VALIDATION

For critical resource cases:

```text
MiniAndroid
vs
AOSP expectation
vs
independent parser
```

Use Apktool/ARSCLib/Androguard as forensic comparison tools where useful. ARSCLib is explicitly based on AOSP androidfw resource structures.

Never accept:

```text
our parser says X
```

as proof of Android correctness.

---

# 51. FAMILY AW — REAL APK EXECUTION LEVELS

Every APK gets a capability level.

### L0

APK opens.

### L1

Manifest/class loading.

### L2

Real DEX execution.

### L3

First Activity.

### L4

First visible UI.

### L5

Resource-correct UI.

### L6

Input works.

### L7

Real DEX callback works.

### L8

State transition works.

### L9

Second visual state works.

### L10

Async/persistence works.

### L11

Multi-screen lifecycle works.

### L12

3-run deterministic.

### L13

Independent APK cross-verified.

Do not report "supported" below the actual level.

---

# 52. FAMILY AX — APK CLUSTER CLOSURE

Group APKs by architecture:

```text
plain Android Views
custom Views
LinearLayout
RelativeLayout
TableLayout
AppCompat
AndroidX
Kotlin
Room
SQLite
R8-heavy
reflection-heavy
async-heavy
graphics-heavy
Compose
WebView
libGDX
native
```

Close clusters rather than chasing APK names.

---

# 53. FAMILY AY — REGRESSION PROTECTION

Every discovered semantic law must become:

```text
unit test
integration test
real APK test
guard APK
```

A bug fix without a permanent regression test is incomplete.

---

# 54. FAMILY AZ — GOLDEN INTEGRITY

Never weaken:

* existing golden screenshots
* interaction goldens
* deterministic sequences
* external APK hashes

If a law-correct change modifies a golden:

```text
OLD
WHY
AOSP LAW
NEW
PIXEL DELTA
REGRESSION ANALYSIS
```

must be documented.

---

# 55. FAMILY BA — REPRODUCIBLE TOOLCHAIN

The environment itself must be versioned.

* [ ] aapt2
* [ ] Java
* [ ] Python
* [ ] APK corpus
* [ ] parser tools
* [ ] compiler
* [ ] scripts
* [ ] hashes
* [ ] bootstrap script

A reset must reproduce the same environment.

---

# 56. FAMILY BB — CORPUS RECOVERY

No dependency on mutable URLs.

For every APK:

```text
URL
SHA256
version
source
license
local cache
restore method
```

If URL disappears:

```text
RECOVERY BLOCKED
```

not "download latest".

---

# 57. FAMILY BC — SOURCE REUSE LEDGER

For every transferred idea:

```text
SOURCE PROJECT
SOURCE FILE
SOURCE COMMIT
LICENSE
BEHAVIORAL LAW
TRANSFERRED SEMANTIC UNIT
MINIANDROID FILE
TEST
```

The existing WineDroid work proves this workflow is productive.

Continue it.

---

# 58. FAMILY BD — RESEARCH-TO-CODE LOOP

Every research item must answer:

```text
What does Android require?
Where is it implemented?
Why is our behavior different?
What is the smallest reusable semantic unit?
What tests prove it?
Which real APK needs it?
```

If these cannot be answered, the item remains `[R]`, not `[X]`.

---

# 59. FAMILY BE — FAILURE TAXONOMY

Every failure must receive one root category:

```text
PARSER
DEX
TYPE
CLASSLINKER
REFLECTION
JAVA
ANDROID API
RESOURCE
XML
CONSTRUCTOR
VIEW
MEASURE
LAYOUT
RENDER
INPUT
LIFECYCLE
QUEUE
THREAD
PERSISTENCE
NATIVE
TOOLCHAIN
CORPUS
DETERMINISM
```

Do not create five findings for one root cause.

---

# 60. FAMILY BF — ROOT-CAUSE COMPRESSION

When multiple APKs fail:

```text
failure A
failure B
failure C
```

ask:

> Can all three be explained by one missing semantic law?

If yes:

```text
ONE ROOT FINDING
MULTIPLE OBSERVATIONS
MULTIPLE APK PROOFS
```

This is the preferred optimization.

---

# 61. FAMILY BG — SECOND-ORDER EFFECT ANALYSIS

After every major fix:

Do not only rerun the failing APK.

Run:

```text
direct consumer
related family
unrelated guard
previous goldens
R8-heavy APK
reflection-heavy APK
async APK
resource-heavy APK
```

Look for cascades.

This is specifically designed to prevent:

```text
CONV → CMP → LONG
```

and:

```text
shadow registry → constructor → lifecycle → AndroidX
```

style hidden chains from escaping validation.

---

# 62. FAMILY BH — CAPABILITY CENTRALITY

When choosing the next implementation, calculate:

```text
number of APKs affected
number of APIs unlocked
number of families unlocked
number of current blockers removed
reusability
implementation risk
```

Prefer high-centrality capabilities.

Examples:

```text
class dispatch
reflection
MessageQueue
TypedArray
resource resolution
constructor semantics
ViewGroup ancestry
```

often unlock many APKs at once.

---

# 63. FAMILY BI — BLOCKER DEPENDENCY GRAPH

For every blank/partial APK:

```text
APK
 ↓
first failure
 ↓
root semantic family
 ↓
blocking dependency
 ↓
next closure family
```

Never attack a blocked APK at the screenshot layer if its constructor/classloader/API dependency is still missing.

---

# 64. FAMILY BJ — REAL-APK-FIRST DEVELOPMENT

For each new semantic capability:

```text
REAL APK
→ isolate behavior
→ create minimal law test
→ implement
→ return to REAL APK
```

Never:

```text
100 fixture tests
→ assume Android support
```

---

# 65. FAMILY BK — INDEPENDENT APK VALIDATION

Every major family requires:

```text
APK-A = discovery consumer
APK-B = independent consumer
APK-C = regression guard
```

`APK-A` proving success is insufficient.

---

# 66. FAMILY BL — VISUAL PROOF

A visual feature is closed only when:

```text
resource correctness
+
geometry correctness
+
render correctness
+
text correctness
+
state correctness
```

are independently established.

---

# 67. FAMILY BM — INTERACTION PROOF

Every interaction family must prove:

```text
input
→ dispatch
→ listener
→ real DEX
→ state mutation
→ scheduled work if applicable
→ next frame
→ visible result
```

No screenshot-only proof.

---

# 68. FAMILY BN — ASYNC VISUAL PROOF

For timers/async:

```text
initial
→ schedule
→ time advances
→ callback
→ state mutation
→ redraw
→ next callback
→ expiry/cancel
```

Use virtual time, not wall-clock sleeps.

---

# 69. FAMILY BO — PERSISTENCE VISUAL PROOF

For Room/SQLite/Preferences:

```text
write
→ commit
→ read
→ render
```

and:

```text
new Activity/process-equivalent state
→ read persisted data
→ render
```

where architecture permits.

---

# 70. FAMILY BP — REFLECTION + R8 CROSS TEST

This must become a permanent stress category.

Construct APKs where:

```text
R8 merges classes
+
reflection looks them up
+
interface dispatch occurs
+
constructor is invoked
+
returned object is used
```

This is one of the highest-value compatibility tests.
