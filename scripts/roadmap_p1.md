# MASTER-ROADMAP v3

## MiniAndroid Compatibility Runtime — 100% Base Execution Closure System

> **Mission:** Do not merely find bugs. Close compatibility families.
>
> This roadmap replaces the previous "find the next bug" workflow with a **source-mined, dependency-aware, family-closure execution system**.
>
> The objective is not to maximize the number of findings.
>
> The objective is to reach the point where:
>
> **real APK → APK parsing → class loading → DEX execution → Android API semantics → lifecycle → scheduling → resources → layout → rendering → interaction → persistence → asynchronous work → second/third UI state**
>
> works through one coherent runtime model, with deterministic evidence and without package-specific hacks.

---

# 0. ABSOLUTE OPERATING RULES

## 0.1 Current HEAD is the only truth

Before every campaign:

* record exact HEAD
* record branch
* record working tree state
* record corpus SHA-256
* record toolchain versions
* rebuild from clean state
* run full regression battery
* establish baseline

Never trust:

* previous agent claims
* old reports
* old screenshots
* old issue comments
* old commit descriptions
* stale README text
* stale local artifacts

Agent reports are **leads**, not evidence.

---

## 0.2 No arbitrary finding quota

Do NOT stop because:

* 5 findings were found
* 10 findings were found
* one APK improved
* one screenshot changed
* one crash disappeared

Continue until the current compatibility family is closed.

If investigation discovers a new dependency family, create it and continue.

---

## 0.3 Every family follows the same closure pipeline

For every family:

```text
FAMILY DISCOVERY
      ↓
API / SYMBOL INVENTORY
      ↓
SOURCE LAW MINING
      ↓
IMPLEMENTATION REFERENCE MINING
      ↓
DEPENDENCY GRAPH
      ↓
CURRENT RUNTIME GAP MAP
      ↓
MINIMAL SEMANTIC IMPLEMENTATION
      ↓
UNIT / LAW TESTS
      ↓
REAL APK
      ↓
INDEPENDENT APK
      ↓
GUARD APK
      ↓
METAMORPHIC / DIFFERENTIAL TEST
      ↓
3-RUN DETERMINISM
      ↓
REGRESSION BATTERY
      ↓
DOCUMENTATION + EVIDENCE
      ↓
FAMILY CLOSED
```

No shortcut.

---

## 0.4 Source hierarchy

Use sources in this order:

### Tier 1 — Behavioral law

1. AOSP framework source
2. Android Developers API contracts
3. ART source
4. AndroidX source

### Tier 2 — Implementation references

5. Robolectric
6. R8/D8
7. Apktool
8. dexlib2/smali
9. Androguard
10. ARSCLib

### Tier 3 — reusable Android-runtime implementations

11. WineDroid
12. other Android compatibility runtimes
13. emulator/runtime projects
14. specialized parser/VM projects

### Rule

AOSP defines **what Android means**.

External projects help determine **how to implement it efficiently**.

Never blindly copy behavior from a third-party implementation when AOSP contradicts it.

---

## 0.5 Every completed item needs evidence

Required:

```text
CLAIM
COMMIT
DETAILED GITHUB EVIDENCE
REPOSITORY EVIDENCE
TEST EVIDENCE
REAL APK EVIDENCE
REGRESSION EVIDENCE
```

Final report MUST contain direct GitHub URLs.

Never report only:

```text
Issue #123
comment 456
commit abcdef
```

Report:

```text
https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/...
```

---

## 0.6 Status vocabulary

Use only:

```text
[ ] DISCOVERED / NOT STARTED
[~] IN PROGRESS
[R] RESEARCHED
[I] IMPLEMENTED
[T] TESTED
[A] OBSERVED
[V] VERIFIED
[RV] REGRESSION-VERIFIED
[X] CLOSED
[B] BLOCKED
[D] DOCUMENTED BOUNDARY
[!] NEW FINDING
```

`[X]` means family closure.

---

# 1. THE NEW CORE METHOD — COMPATIBILITY CLOSURE GRAPH

Do not maintain only a flat TODO list.

Create:

```text
compatibility_graph/
```

Every capability becomes a node.

Example:

```text
MicroTimer countdown
 ├── Handler.postDelayed
 ├── Handler token
 ├── MessageQueue ordering
 ├── MessageQueue future-time advancement
 ├── SystemClock.uptimeMillis
 ├── Runnable identity
 ├── cancellation
 ├── StringBuilder
 ├── Math.ceil
 ├── View invalidation
 ├── redraw
 └── deterministic virtual clock
```

The important rule:

> If a capability fails, trace the graph downward before patching the visible symptom.

This prevents another F-005/F-006/F-008 style chain from being treated as unrelated bugs.

---

# 2. FAMILY CLOSURE ENGINE

For every family create a machine-readable record:

```text
FAMILY_ID
SOURCE_LAW
IMPLEMENTATION_REFERENCES
PUBLIC_APIS
INTERNAL_RUNTIME_APIS
DEPENDENCIES
CURRENT_IMPLEMENTATION
MISSING_SEMANTICS
REAL_APK_CONSUMERS
INDEPENDENT_APK
GUARD_APKS
LAW_TESTS
HOSTILE_TESTS
DETERMINISM_TEST
REGRESSION_STATUS
EVIDENCE_URL
COMMIT
STATUS
BOUNDARY
```

This becomes the permanent compatibility map.

---

# 3. MASTER FAMILY A — DEX FORMAT AND EXECUTION

Do not treat "168/168 opcodes" as completion.

Perform semantic closure of:

### A1 — Instruction decoding

* [ ] all opcode values
* [ ] all instruction widths
* [ ] all format families
* [ ] payload alignment
* [ ] branch targets
* [ ] signed/unsigned operands
* [ ] register width
* [ ] literal width
* [ ] jumbo forms
* [ ] range forms
* [ ] invoke forms
* [ ] quickened/optimized forms where encountered

### A2 — Arithmetic

* [ ] int
* [ ] long
* [ ] float
* [ ] double
* [ ] unary
* [ ] binary
* [ ] remainder
* [ ] shifts
* [ ] overflow semantics
* [ ] narrowing
* [ ] widening

### A3 — Conversion

* [ ] int→long
* [ ] long→int
* [ ] int→float
* [ ] int→double
* [ ] long→float
* [ ] long→double
* [ ] float→int
* [ ] float→long
* [ ] double→int
* [ ] double→long
* [ ] float↔double
* [ ] signed narrowing
* [ ] NaN behavior
* [ ] infinity behavior

### A4 — Comparison

* [ ] cmp-long
* [ ] cmpl
* [ ] cmpg
* [ ] zero comparison
* [ ] NaN semantics
* [ ] correct union field
* [ ] result -1/0/1

### A5 — Control flow

* [ ] goto
* [ ] if-eq
* [ ] if-ne
* [ ] if-lt
* [ ] if-ge
* [ ] if-gt
* [ ] if-le
* [ ] zero variants
* [ ] packed-switch
* [ ] sparse-switch
* [ ] fallthrough
* [ ] payload decoding
* [ ] branch-width correctness

### A6 — Arrays

* [ ] new-array
* [ ] filled-new-array
* [ ] filled-new-array/range
* [ ] aget family
* [ ] aput family
* [ ] array length
* [ ] primitive arrays
* [ ] reference arrays
* [ ] multidimensional arrays
* [ ] bounds exceptions
* [ ] type compatibility

### A7 — Exceptions

* [ ] try regions
* [ ] catch
* [ ] catch-all
* [ ] move-exception
* [ ] nested try
* [ ] finally semantics
* [ ] exception propagation
* [ ] stack unwinding
* [ ] exception frame state

### A8 — Monitor

* [ ] monitor-enter
* [ ] monitor-exit
* [ ] exception-safe monitor release
* [ ] nested monitor behavior

### A9 — Invocation

Close each separately:

* [ ] invoke-virtual
* [ ] invoke-super
* [ ] invoke-direct
* [ ] invoke-static
* [ ] invoke-interface
* [ ] range variants
* [ ] exact signature matching
* [ ] receiver type
* [ ] declaring type
* [ ] return type
* [ ] argument marshaling
* [ ] nested invoke return preservation
* [ ] wide return values
* [ ] reference returns
* [ ] void returns

### A10 — Return-value integrity

Create explicit tests for:

```text
invoke A
  invoke B
    invoke C
  return C
return B
return A
```

Verify that nested calls cannot overwrite the caller's pending result.

---

# 4. FAMILY B — ART / CLASS LINKER SEMANTICS

Study ART ClassLinker, verifier and invocation resolution before modifying runtime dispatch.

AOSP explicitly models class resolution, verification and interpreter decisions.

### B1

* [ ] class definition lookup
* [ ] descriptor normalization
* [ ] superclass resolution
* [ ] interface resolution
* [ ] method lookup
* [ ] field lookup
* [ ] direct method lookup
* [ ] virtual method lookup
* [ ] interface method lookup
* [ ] static method lookup

### B2

* [ ] class initialization
* [ ] `<clinit>`
* [ ] initialization-on-first-use
* [ ] initialization ordering
* [ ] failure state
* [ ] recursive initialization

### B3

* [ ] Object root semantics
* [ ] Object.<init>
* [ ] Object methods
* [ ] equals
* [ ] hashCode
* [ ] toString
* [ ] getClass

### B4

* [ ] assignability
* [ ] instanceof
* [ ] check-cast
* [ ] array covariance
* [ ] interface assignability
* [ ] superclass traversal

### B5

* [ ] class loader identity
* [ ] boot classes
* [ ] application classes
* [ ] parent delegation
* [ ] duplicate class definitions
* [ ] class identity

---

# 5. FAMILY C — R8 / D8 / OPTIMIZED DEX REALITY

This family is now mandatory.

R8 horizontal class merging does not simply rename classes; it creates merge groups, synthetic class IDs, graph-lens rewrites, constructor handling and type-reference fixes.

### C1

* [ ] vertical class merging
* [ ] horizontal class merging
* [ ] synthetic class IDs
* [ ] merged constructors
* [ ] merged methods
* [ ] graph lens effects
* [ ] rewritten type references
* [ ] rewritten field references
* [ ] rewritten method references
* [ ] bridge methods
* [ ] interface dispatch
* [ ] R8-generated synthetic methods
* [ ] R8-generated fields

### C2

Generate or collect APKs containing:

* [ ] horizontal merging
* [ ] vertical merging
* [ ] enum optimization
* [ ] lambda desugaring
* [ ] Kotlin-generated classes
* [ ] synthetic accessors
* [ ] bridge methods
* [ ] companion objects
* [ ] default interface methods

### C3

Explicitly detect:

```text
declared receiver ≠ runtime receiver
```

and test:

```text
invoke-interface
invoke-virtual
invoke-super
invoke-direct
```

against all four combinations.

---

# 6. FAMILY D — DEX / APK FORENSIC PIPELINE

Use Apktool, Androguard, dexlib2/smali and independent parsers as forensic instruments, not as runtime replacements.

Apktool can decode resources and smali, while Androguard's current APK parser exposes archive, manifest, DEX and resource structure.

### D1

* [ ] ZIP/APK structure
* [ ] multiple DEX
* [ ] classes.dex
* [ ] classes2.dex
* [ ] classesN.dex
* [ ] manifest
* [ ] resources.arsc
* [ ] res/
* [ ] assets/
* [ ] META-INF
* [ ] native libraries

### D2

Cross-check every DEX structural issue with at least two independent parsers.

### D3

Create hostile APK tests for:

* [ ] oversized tables
* [ ] truncated sections
* [ ] invalid offsets
* [ ] invalid string indices
* [ ] invalid type indices
* [ ] invalid method indices
* [ ] malformed debug info
* [ ] malformed annotations
* [ ] malformed class data

---

# 7. FAMILY E — JAVA CORE SEMANTICS

Do not implement Android APIs while Java semantics underneath are incomplete.

### E1 Objects

* [ ] Object
* [ ] equals
* [ ] hashCode
* [ ] toString
* [ ] getClass
* [ ] clone boundary
* [ ] wait/notify boundary

### E2 String

* [ ] length
* [ ] charAt
* [ ] substring
* [ ] subSequence
* [ ] concat
* [ ] equals
* [ ] compareTo
* [ ] startsWith
* [ ] endsWith
* [ ] contains
* [ ] indexOf
* [ ] lastIndexOf
* [ ] replace
* [ ] split
* [ ] trim
* [ ] formatting
* [ ] Unicode
* [ ] surrogate pairs

### E3 StringBuilder/StringBuffer

* [ ] constructors
* [ ] capacity
* [ ] append primitives
* [ ] append objects
* [ ] insert
* [ ] delete
* [ ] setLength
* [ ] charAt
* [ ] substring
* [ ] toString

### E4 Math

Create complete semantic surface:

* [ ] abs
* [ ] min
* [ ] max
* [ ] ceil
* [ ] floor
* [ ] round
* [ ] sqrt
* [ ] pow
* [ ] exp
* [ ] log
* [ ] log10
* [ ] log1p
* [ ] cbrt
* [ ] sin
* [ ] cos
* [ ] tan
* [ ] asin
* [ ] acos
* [ ] atan
* [ ] atan2
* [ ] sinh
* [ ] cosh
* [ ] tanh
* [ ] signum
* [ ] hypot
* [ ] IEEEremainder
* [ ] toRadians
* [ ] toDegrees
* [ ] floorDiv
* [ ] floorMod

### E5 Collections

Close the family, not individual methods:

* [ ] List
* [ ] Set
* [ ] Map
* [ ] Queue
* [ ] Iterator
* [ ] Collections factories
* [ ] synchronized collections
* [ ] singleton collections
* [ ] empty collections
* [ ] unmodifiable collections
* [ ] equality/hash behavior
* [ ] iteration ordering

---

# 8. FAMILY F — KOTLIN/JVM INTEROP

Real APKs increasingly depend on generated Kotlin/JVM semantics.

### F1

* [ ] Intrinsics
* [ ] Unit
* [ ] Pair
* [ ] Triple
* [ ] Function interfaces
* [ ] lambdas
* [ ] FunctionN
* [ ] Default arguments
* [ ] synthetic `$default`
* [ ] object singletons
* [ ] companion objects
* [ ] data classes
* [ ] generated component methods
* [ ] `copy`
* [ ] null checks
* [ ] Kotlin collections bridges
* [ ] sequence basics

### F2

Detect Kotlin-generated synthetic methods automatically during APK mining.

---

# 9. FAMILY G — EXCEPTION / STACK / CONTROL SEMANTICS

This must be treated as a first-class runtime subsystem.

### G1

* [ ] throw
* [ ] catch
* [ ] finally
* [ ] nested exceptions
* [ ] rethrow
* [ ] exception cause
* [ ] stack frame creation
* [ ] stack frame restoration
* [ ] constructor failure
* [ ] `<clinit>` failure
* [ ] reflective exception wrapping

### G2

Create a standard exception torture APK.

It must contain:

```text
method A
 → method B
   → method C
     → throw
   → catch
 → finally
 → rethrow
```

and validate exact control-flow restoration.

---

# 10. FAMILY H — REFLECTION

Reflection must be closed as a subsystem.

### H1

* [ ] Class.forName
* [ ] getClass
* [ ] getName
* [ ] getPackage
* [ ] getCanonicalName
* [ ] getSuperclass
* [ ] getInterfaces
* [ ] getDeclaredMethods
* [ ] getDeclaredFields
* [ ] getDeclaredConstructors
* [ ] getMethod
* [ ] getDeclaredMethod
* [ ] getField
* [ ] getDeclaredField
* [ ] Constructor.newInstance
* [ ] Method.invoke
* [ ] Field.get
* [ ] Field.set

### H2

Validate:

* [ ] private members
* [ ] inherited members
* [ ] overloaded methods
* [ ] primitive parameters
* [ ] reference parameters
* [ ] arrays
* [ ] null
* [ ] wide values
* [ ] return values
* [ ] exceptions

---

# 11. FAMILY I — ANDROID CONTEXT / COMPONENT MODEL

### I1 Context

* [ ] getResources
* [ ] getAssets
* [ ] getPackageName
* [ ] getPackageManager
* [ ] getString
* [ ] getText
* [ ] getDrawable
* [ ] getColor
* [ ] getTheme
* [ ] getSystemService
* [ ] getApplicationContext

### I2 Components

* [ ] Application
* [ ] Activity
* [ ] Service
* [ ] BroadcastReceiver
* [ ] ContentProvider boundary

### I3 lifecycle

Close:

```text
Application
Activity
onCreate
onStart
onResume
onPause
onStop
onDestroy
finish
finishActivity
result delivery
```

with real DEX callbacks.

---

# 12. FAMILY J — INTENT / URI / BUNDLE / PARCEL

This should be its own complete family.

### J1 Intent

* [ ] explicit component
* [ ] implicit action
* [ ] categories
* [ ] data URI
* [ ] MIME type
* [ ] flags
* [ ] extras
* [ ] ClipData
* [ ] package/component identity

### J2 Bundle

* [ ] primitives
* [ ] String
* [ ] Parcelable boundary
* [ ] Serializable boundary
* [ ] arrays
* [ ] nested Bundle
* [ ] null
* [ ] key identity

### J3 Uri

* [ ] parse
* [ ] scheme
* [ ] host
* [ ] path
* [ ] query
* [ ] fragment
* [ ] encoding

---

# 13. FAMILY K — MESSAGEQUEUE / HANDLER / LOOPER

This family must remain one coherent subsystem.

AOSP Handler explicitly binds work to a Looper/MessageQueue and supports delayed and absolute-time scheduling.

### K1 Queue

* [ ] ordering by time
* [ ] insertion order for equal time
* [ ] future-head handling
* [ ] virtual clock advancement
* [ ] due-time dispatch
* [ ] idle
* [ ] cancellation
* [ ] token cancellation
* [ ] Runnable identity
* [ ] Message identity

### K2 Handler

* [ ] post
* [ ] postDelayed
* [ ] postAtTime
* [ ] sendMessage
* [ ] sendMessageDelayed
* [ ] sendEmptyMessage
* [ ] removeCallbacks
* [ ] removeCallbacksAndMessages
* [ ] token overloads
* [ ] callback
* [ ] Handler subclass

### K3 Looper

* [ ] prepare
* [ ] myLooper
* [ ] myQueue
* [ ] loop
* [ ] quit boundary
* [ ] deterministic drain

### K4 Differential scheduler tests

Compare MiniAndroid behavior against:

* [ ] AOSP law
* [ ] Robolectric scheduler semantics

Robolectric's scheduler model is particularly useful for virtual-time and task-draining semantics.

---

# 14. FAMILY L — THREAD / EXECUTOR / CONCURRENCY

Do not silently execute everything synchronously without modeling semantics.

### L1

* [ ] Thread constructor
* [ ] Thread.start
* [ ] Thread.run
* [ ] Runnable
* [ ] Executor
* [ ] ExecutorService
* [ ] Future boundary
* [ ] synchronization
* [ ] deterministic virtual thread identity

### L2

Define explicitly which concurrency semantics are:

```text
REAL
DETERMINISTICALLY SERIALIZED
SIMULATED
OUT OF SCOPE
```

Never leave this implicit.

---

# 15. FAMILY M — ANDROIDX CORE

AndroidX must be treated as a dependency ecosystem.

### M1 lifecycle

* [ ] LifecycleOwner
* [ ] Lifecycle
* [ ] observer registration
* [ ] state transitions
* [ ] observer removal

### M2 SavedState

* [ ] SavedStateRegistry
* [ ] provider registration
* [ ] keyed provider identity
* [ ] duplicate registration behavior
* [ ] state consume
* [ ] recreation semantics

The AndroidX API contract confirms that `enableSavedStateHandles()` is tied to component lifecycle state and SavedState/ViewModel ownership.

### M3 ViewModel

* [ ] ViewModelStore
* [ ] ViewModel retrieval
* [ ] key identity
* [ ] creation
* [ ] clearing

### M4 AndroidX startup

* [ ] initializer discovery
* [ ] dependency ordering
* [ ] duplicate initialization
* [ ] startup exceptions

---

# 16. FAMILY N — APPCOMPAT / MATERIAL / ANDROIDX VIEW STACK

Do not treat AppCompat as "one blocker".

Break it into:

* [ ] ContextThemeWrapper
* [ ] AppCompatActivity
* [ ] AppCompatDelegate
* [ ] Toolbar
* [ ] TextView subclasses
* [ ] Button subclasses
* [ ] AppCompat resources
* [ ] ColorStateList
* [ ] Drawable compatibility
* [ ] theme overlays
* [ ] tinting
* [ ] typed attributes

Each must be measured by real APK demand.

---

# 17. FAMILY O — VIEW / VIEWGROUP OBJECT MODEL

### O1 View

* [ ] identity
* [ ] ID
* [ ] tag
* [ ] keyed tag
* [ ] parent
* [ ] context
* [ ] visibility
* [ ] enabled
* [ ] selected
* [ ] pressed
* [ ] focused
* [ ] alpha
* [ ] background
* [ ] foreground
* [ ] padding
* [ ] minimum size

### O2 ViewGroup

* [ ] addView
* [ ] removeView
* [ ] removeAllViews
* [ ] index
* [ ] parent assignment
* [ ] duplicate parent protection
* [ ] cycle protection
* [ ] measure children
* [ ] layout children
* [ ] dispatchDraw

### O3 semantic ancestry

Replace broad class-name catches with:

```text
actual declared class
actual runtime class
resolved superclass chain
resolved interfaces
method declaration ownership
```

No catch-all ViewShadow behavior.

---

# 18. FAMILY P — MEASUREMENT / LAYOUT

Close each container independently.

### P1 MeasureSpec

* [ ] EXACTLY
* [ ] AT_MOST
* [ ] UNSPECIFIED
* [ ] mode extraction
* [ ] size extraction
* [ ] makeMeasureSpec

### P2 LayoutParams

* [ ] MATCH_PARENT
* [ ] WRAP_CONTENT
* [ ] fixed
* [ ] margins
* [ ] weights
* [ ] gravity

### P3 Containers

* [ ] FrameLayout
* [ ] LinearLayout
* [ ] RelativeLayout
* [ ] TableLayout
* [ ] TableRow
* [ ] ScrollView
* [ ] ViewAnimator
* [ ] GridLayout
* [ ] common Android containers

### P4 Generic rules

For every container:

```text
onMeasure
measure child
resolve size
onLayout
position child
gravity
margins
padding
visibility
weight/dependency
```

---

# 19. FAMILY Q — RESOURCE SYSTEM

This family must be treated as a subsystem.

AOSP exposes a much larger resource architecture than `resources.arsc → string`; `Resources`, `ResourcesImpl`, `AssetManager`, `TypedArray`, `ColorStateList`, configuration and caches all participate.

### Q1 Resource IDs

* [ ] package/type/entry decomposition
* [ ] framework IDs
* [ ] app IDs
* [ ] dynamic references
* [ ] references
* [ ] cycles
* [ ] invalid IDs

### Q2 Configuration

* [ ] density
* [ ] locale
* [ ] orientation
* [ ] screen size
* [ ] smallest width
* [ ] night mode
* [ ] API qualifiers
* [ ] precedence
* [ ] fallback

### Q3 Value types

* [ ] string
* [ ] string reference
* [ ] integer
* [ ] boolean
* [ ] color
* [ ] dimension
* [ ] fraction
* [ ] reference
* [ ] attribute
* [ ] null

### Q4 Style

* [ ] parent
* [ ] inheritance
* [ ] overlay
* [ ] explicit attribute
* [ ] framework style
* [ ] default style
* [ ] theme resolution

### Q5 TypedArray

* [ ] obtainStyledAttributes
* [ ] getString
* [ ] getText
* [ ] getInt
* [ ] getBoolean
* [ ] getDimension
* [ ] getColor
* [ ] getResourceId
* [ ] recycle semantics

### Q6 cache correctness

* [ ] cache key
* [ ] configuration invalidation
* [ ] theme invalidation
* [ ] drawable cache
* [ ] resource cache

---

# 20. FAMILY R — AXML / XML INFLATION

### R1

* [ ] namespace
* [ ] namespace aliases
* [ ] attribute names
* [ ] attribute resource IDs
* [ ] string values
* [ ] references
* [ ] styles
* [ ] booleans
* [ ] dimensions
* [ ] fractions
* [ ] enums
* [ ] flags

### R2 Inflation

* [ ] constructor selection
* [ ] Context
* [ ] AttributeSet
* [ ] style
* [ ] default style
* [ ] `<include>`
* [ ] `<merge>`
* [ ] `<requestFocus>`
* [ ] unknown view handling
* [ ] custom views

### R3 constructor correctness

For every custom view:

```text
Class.<init>
super.<init>
field initialization
attribute parsing
constructor side effects
```

---

# 21. FAMILY S — DRAWABLE / IMAGE PIPELINE

### S1

* [ ] ColorDrawable
* [ ] BitmapDrawable
* [ ] StateListDrawable
* [ ] GradientDrawable
* [ ] LayerDrawable
* [ ] InsetDrawable
* [ ] ShapeDrawable
* [ ] VectorDrawable boundary
* [ ] NinePatch
* [ ] animated drawable boundary

### S2

* [ ] intrinsic width
* [ ] intrinsic height
* [ ] bounds
* [ ] state
* [ ] alpha
* [ ] tint
* [ ] padding
* [ ] density scaling

### S3 Bitmap

* [ ] PNG
* [ ] JPEG
* [ ] palette PNG
* [ ] alpha
* [ ] color type
* [ ] row stride
* [ ] density
* [ ] scaling
* [ ] FIT_CENTER
* [ ] CENTER_CROP
* [ ] nodpi
* [ ] drawable density

ARSCLib and Apktool should be used as independent resource/AXML forensic references, not as substitutes for MiniAndroid's runtime semantics.

---

# 22. FAMILY T — CANVAS / PAINT / RENDERING

This is a major family that must not be hidden under "visual".

### T1 Canvas

* [ ] drawColor
* [ ] drawRect
* [ ] drawRoundRect
* [ ] drawCircle
* [ ] drawLine
* [ ] drawBitmap
* [ ] drawText
* [ ] save
* [ ] restore
* [ ] translate
* [ ] scale
* [ ] rotate
* [ ] clip

### T2 Paint

* [ ] color
* [ ] alpha
* [ ] style
* [ ] strokeWidth
* [ ] textSize
* [ ] typeface
* [ ] antiAlias
* [ ] flags
* [ ] shader boundary

### T3 Rendering state

Verify that Canvas state is isolated per frame.

---

# 23. FAMILY U — TEXT / TYPOGRAPHY

### U1

* [ ] font family
* [ ] typeface
* [ ] size
* [ ] density
* [ ] scaledDensity
* [ ] baseline
* [ ] ascent
* [ ] descent
* [ ] leading
* [ ] line spacing
* [ ] fallback
* [ ] bidi
* [ ] Unicode
* [ ] surrogate pairs

### U2

* [ ] TextView measurement
* [ ] wrapping
* [ ] gravity
* [ ] ellipsize
* [ ] maxLines
* [ ] padding
* [ ] compound drawables
* [ ] spans boundary

---

# 24. FAMILY V — INPUT / TOUCH / FOCUS

### V1 Touch

* [ ] ACTION_DOWN
* [ ] ACTION_MOVE
* [ ] ACTION_UP
* [ ] ACTION_CANCEL
* [ ] coordinates
* [ ] parent dispatch
* [ ] child dispatch
* [ ] interception
* [ ] pressed state

### V2 Click

* [ ] OnClickListener
* [ ] XML onClick
* [ ] accessibility click boundary

### V3 Long press

* [ ] timeout
* [ ] Runnable scheduling
* [ ] listener
* [ ] cancellation
* [ ] return value
* [ ] Toast/Clipboard side effects

### V4 Focus

* [ ] focusable
* [ ] requestFocus
* [ ] clearFocus
* [ ] focus traversal

---

# 25. FAMILY W — WINDOW / DECOR / ACTIVITY ROOT

Do not assume Activity root == content View.

Investigate:

* [ ] Window
* [ ] DecorView
* [ ] content root
* [ ] setContentView
* [ ] window background
* [ ] foreground
* [ ] status-bar boundary
* [ ] navigation-bar boundary
* [ ] display metrics
* [ ] window flags
* [ ] fullscreen
* [ ] theme/window attributes

Explicitly document what MiniAndroid emulates and what it intentionally does not.

---

# 26. FAMILY X — PERSISTENCE

### X1 SharedPreferences

* [ ] get
* [ ] put
* [ ] remove
* [ ] clear
* [ ] contains
* [ ] listener
* [ ] persistence
* [ ] deterministic storage

### X2 Files

* [ ] application files
* [ ] cache
* [ ] open/read/write
* [ ] directory
* [ ] existence
* [ ] deterministic paths

### X3 SQLite

Continue the F-ROOM-CHAIN architecture:

* [ ] database open
* [ ] create
* [ ] upgrade
* [ ] query
* [ ] insert
* [ ] update
* [ ] delete
* [ ] Cursor
* [ ] SQLiteStatement
* [ ] bind arguments
* [ ] transaction
* [ ] close

### X4 Room

* [ ] Database_Impl
* [ ] generated DAO
* [ ] generated callbacks
* [ ] entity mapping
* [ ] query execution
* [ ] cursor mapping

---

# 27. FAMILY Y — NETWORK / ASYNC BOUNDARY

Do not fake arbitrary network behavior.

First classify:

```text
LOCAL deterministic
MOCKABLE
REQUIRES external network
OUT OF SCOPE
```

Then support deterministic mockable semantics.

* [ ] URL
* [ ] URI
* [ ] request object
* [ ] callback
* [ ] async completion
* [ ] cancellation
* [ ] error path
* [ ] timeout
* [ ] deterministic injected response

---

# 28. FAMILY Z — SYSTEM SERVICES

Build a demand-driven registry.

Possible services:

* [ ] ClipboardManager
* [ ] InputMethodManager boundary
* [ ] WindowManager
* [ ] LayoutInflater
* [ ] ConnectivityManager boundary
* [ ] NotificationManager boundary
* [ ] AlarmManager boundary
* [ ] Vibrator boundary
* [ ] PackageManager
* [ ] ActivityManager boundary

Never create empty stubs silently.

Every unsupported service must emit:

```text
[UNSUPPORTED-SERVICE]
caller
requested service
method
APK
stack
```

---

# 29. FAMILY AA — PACKAGE MANAGER / APPLICATION METADATA

### AA1

* [ ] package name
* [ ] version
* [ ] application info
* [ ] activity info
* [ ] service info
* [ ] receiver info
* [ ] provider info
* [ ] permissions
* [ ] exported
* [ ] process
* [ ] target SDK
* [ ] min SDK

### AA2

Use manifest truth rather than guessing from APK code.

---

# 30. FAMILY AB — PERMISSIONS / SECURITY BOUNDARY

Do not pretend the runtime is a real Android security sandbox.

Define:

* [ ] permission lookup
* [ ] permission grant model
* [ ] permission denial
* [ ] security exception
* [ ] boundary documentation

The model must be deterministic.

---

# 31. FAMILY AC — DATE / TIME / LOCALE / FORMAT

This family is easy to underestimate.

### AC1

* [ ] SystemClock
* [ ] uptimeMillis
* [ ] elapsedRealtime
* [ ] Calendar
* [ ] Date
* [ ] Locale
* [ ] NumberFormat
* [ ] DateFormat
* [ ] String formatting
* [ ] timezone
* [ ] deterministic clock

### AC2

Any time-based API must be routed through the virtual deterministic clock where appropriate.

---

# 32. FAMILY AD — RANDOMNESS

Identify all sources:

* [ ] Math.random
* [ ] java.util.Random
* [ ] SecureRandom boundary
* [ ] UUID
* [ ] app-specific PRNG

For deterministic test mode:

```text
seed
source
sequence
reset
replay
```

must be controlled.

---

# 33. FAMILY AE — FILE / STREAM / BUFFER APIs

Real APKs can fail because Java infrastructure is missing.

Audit:

* [ ] InputStream
* [ ] OutputStream
* [ ] Reader
* [ ] Writer
* [ ] ByteArrayInputStream
* [ ] ByteArrayOutputStream
* [ ] Buffered streams
* [ ] StringReader
* [ ] StringWriter
* [ ] ByteBuffer
* [ ] Charset
* [ ] UTF-8
* [ ] UTF-16
* [ ] MUTF-8 boundary
