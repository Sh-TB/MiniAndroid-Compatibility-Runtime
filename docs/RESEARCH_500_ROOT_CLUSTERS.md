# R500 ROOT CLUSTERS

Every ROOT links the findings that share one underlying missing semantic law.
`fan-out` is measured (probe/corpus evidence), never estimated.

---

## ROOT-001 — REFLECTION-FIELD-IDENTITY (20 findings, FIXED this wave)

**Law**: one canonical field key — (declaring-class, name) — across
interpreter sget/sput, heap iget/iput, sun.misc.Unsafe offsets and
java.lang.reflect.Field. Upstream: libcore `java.lang.reflect.Field`,
OpenJDK `Class.getField`/`getDeclaredField` contracts.

**Findings**: R500-005, 006, 056–072 (§9 reflection family), 077, 082, 084,
090; N-002 family slice (R500-010).

**Divergences reproduced** (S103 maxext_probe, 3/3 deterministic; R500 rerun on
the fixed engine, 3/3 byte-identical screenshots `f6ead59b…` pre-frame-law,
`cd4e4af0…` post):
R1–R4 null/boxed static reads; R5 missing NPE on null receiver; R6 missing
NSFE from getDeclaredField; R7 getField stub-null → NPE (5 census titles);
R8 set silent no-op; R9 modifiers hardcoded 9; R11 boxed static pre-init
defaults.

**MiniAndroid divergence (was)**: reflection Field objects carried only
(declaring_class, field_name, field_type); kind/modifiers/accessible absent;
static reads bypassed `static_field_storage_` when a receiver was present;
getDeclaredField always succeeded; getField unimplemented; no boxing.

**Fix (L5)**: dex-derived Field identity (`field_kind`, `field_mods`,
`accessible` on every Field object); static get/set routed through the SAME
`static_field_storage_` keys as sget/sput (+ `ensure_class_initialized`);
NSFE/NPE/IAE laws; getField superclass walk (public-only, first declaring
class); boxing on get / unboxing on set; real access flags; final-write
IAE unless setAccessible. Companion display laws: StringBuilder.append /
Object.toString on boxed primitives render the boxed VALUE; the static
`Integer.toString(int)` arm no longer swallows the virtual 0-arg form.

**Probe result (R500)**: R1=42, R2=nonnull, R3=const-value, R4=IAE (correct
law — receiver is not a Host instance), R5=NPE(correct), R6=NSFE(correct),
R7=inherited=99, R8=after-set=43 (identity with sget proven), R9=mods=1,
R10=NSFE(correct), R11=boxed=1234, R12 direct=1234/prim=43. 3/3 runs,
identical screenshots.

**Corpus**: 30/61 titles carry null-producer crash evidence (S103 log sweep);
the getField-NULL slice alone killed 5 census titles.

**Battery**: 105/105 ALL PASS.

## ROOT-002 — VIEW-FRAME (7 findings, FIXED this wave)

**Law**: `View.layout(l,t,r,b)` → `setFrame` materializes
mLeft/mTop/mRight/mBottom; `getWidth() = mRight - mLeft` (0 before the first
layout is CORRECT); `measure` → default `onMeasure` →
`getDefaultSize` (EXACTLY/AT_MOST → specSize); `MeasureSpec` mode constants
are in-place values (`EXACTLY = 0x40000000`) and `makeMeasureSpec` ORs the
already-shifted mode (API 17+ law, matches F-096b getMode).

**Findings**: R500-004, 013, 018, 092–095.

**Divergence reproduced**: W2 `measure(EXACTLY 200)` → mw=0; W3
`layout(10,20,210,120)` → getWidth()=0; W4 GONE direct-layout → w=0. Root
chain: layout/measure were silent no-ops; `makeMeasureSpec` re-shifted the
mode constant (`(mode<<30)` on the already-shifted 0x40000000 → 0), so every
programmatic spec was mode-less; EXACTLY/AT_MOST statics seeded as 0.

**Fix (L5)**: layout/setFrame write the frame through the SAME ViewNode
geometry store the engine layout stage uses (measured_left/top/right/bottom,
x/y/width/height, laid_out); measure answers the default-onMeasure law when
no DEX onMeasure exists; MeasureSpec constants seeded in the int-sget path;
makeMeasureSpec ORs the in-place mode; getWidth/getHeight answer the frame
(measured_right-left / bottom-top), getMeasuredWidth/Height answer the
measure store. Engine-laid-out trees and programmatic layouts now observe
ONE geometry identity (the F-NEW-170 Dodge draw-geometry law is preserved —
the engine layout stage writes the same fields).

**Probe result (R500)**: W1 w=0 mw=0 (correct), W2 w=0 mw=200 (correct:
measure alone must not answer getWidth), W3 w=200 h=100, W4 w=50 vis=8,
W5 w=0 (correct). 3/3 runs identical.

**Battery**: 105/105 ALL PASS.

## ROOT-003 — PFQ-ORDER (7 findings, FIXED this wave)

**Law**: `Handler.postAtFrontOfQueue` → AOSP
`sendMessageAtFrontOfQueue` → `enqueueMessage(queue, msg, 0)` — the message
rides when=0, is always due, and drains BEFORE every normally-posted
message. (FL-004's "missing implementation = root cause" was already
DISPROVEN in S103: the callbacks execute; only the order diverged.)

**Findings**: R500-003, 017, 119–124 (Looper/Handler/post/postDelayed are
verified-correct members of the cluster; 122/124 carry the order law).

**Divergence reproduced**: H6 order-final="-PF" (front-post drained after
already-posted work; ties at virtual-now broke FIFO).

**Fix (L5)**: `enqueue_front` inserts with ready_at=0 + from_front rank;
drain comparator orders front-posts before normal posts at equal ready time.
Documented subset: multiple front-posts within one pump drain FIFO among
themselves (corpus pattern — a single front-post jumping queued work — is
exact).

**Probe result (R500)**: H3 posted=RAN, H4 front=RAN, H6 order-final="-FP".
3/3 runs identical.

**Battery**: 105/105 ALL PASS.

## ROOT-004 — DECOR-LINKAGE (3 findings, REPRODUCED — not fixed this wave)

**Law**: the AppCompat sub-decor (created by createSubDecor, holding the
action_bar / decor_content_parent subtrees) must be reachable from the
window DecorView root that WindowDecorActionBar uses for findViewById.

**Findings**: R500-001 (new first divergence), 096, 097, 099.

**Evidence (S103, 3/3)**: WindowDecorActionBar.init findViewById
(decor_content_parent 0x7f080054, search_root=70) NOT FOUND while the same
run's receiver=cf subtree HAS the Toolbar (view 232) → ISE "Can't make a
decor toolbar out of null". Ticketed frontier (#348 stage: sub-decor attach
model + menu XmlPullParser + WindowInsets nulls).

**Status**: REPRODUCED (L3). Not fixed this wave — the attach model is a
structural change to the inflater/decor interplay; it needs its own wave
(next queue, measured fan-out: decor-toolbar family + all
decor.findViewById consumers).

## ROOT-005 — CLASS-IDENTITY (5 findings, REPRODUCED — dual-identity law pending)

**Law**: inflation substitution (AppCompatViewInflater) means a real Android
object IS the AppCompat class; type tests against mapped-away descriptors
must answer accordingly.

**Findings**: R500-001, 009 (N-001), 086–088.

**Evidence**: 22/59 corpus APKs execute instanceof/check-cast on exactly the
classes the inflater maps away (run/s103/u001_typescan.json). Engine
instanceof answers FALSE where real Android answers TRUE; check-cast is
deliberately optimistic (dalvik_engine.cpp) so the two disagree. S101's
Toolbar real-class-identity law (L5) is the template: inflate under the REAL
descriptor / record dual identity and consult it in is_subclass_of.

**Status**: REPRODUCED + corpus-cross-checked. Not fixed this wave: the
dual-identity instanceof law touches the shared type-test path for 22+
titles; it must land with a full census rerun and check-cast strictness
measured (blind flipping risks regressions the optimistic cast currently
absorbs).

## ROOT-006 — ARSC-ENCODING (5 findings, REPRODUCED, CORPUS-UNCONFIRMED)

**Findings**: R500-007, 011 (N-003), 115–118.

**Evidence**: FLAG_SPARSE supported; FLAG_OFFSET16/COMPACT unhandled (u16
offset tables misread as u32 — AOSP ResourceTypes.h pinned). Corpus scan:
0/54 APKs use any of the flags.

**Status**: SOURCE_SUPPORTED + REPO_SUPPORTED + CORPUS_UNCONFIRMED.
Deliberately NOT implemented (zero measured corpus demand; §21 evidence-based
priority).

## ROOT-007 — GL-BRIDGE / GLSL / TEX-COMPRESSION / EGL-SHADOW (16 findings, classified)

**Findings**: R500-019/022/023/025/029/031/033/035/038–040/046/047/051/052/055.

**Classification** (rule 7/8: does MiniAndroid own the layer?):
- Bridge-absent (PGL implements at C level, bridge never dispatches):
  glTexImage2D/glTexSubImage2D family, glReadPixels, glFramebufferTexture2D,
  texture arrays → ROOT-GL-BRIDGE. Implement on measured corpus demand.
- GLSL execution: PGL executes C-function shaders; GLSL stored verbatim
  (GLES_BACKEND_COMPARISON_010.md) → ROOT-GLSL frontier (geometry/
  tessellation/compute shaders behind it).
- Compressed textures (ETC1/S3TC/ATC/PVRTC): absent engine-wide; corpus
  asset scan = the gate (ROOT-TEX-COMPRESSION).
- EGL shadow statics (BAD_ALLOC/CONTEXT_LOST/surfaceless/pbuffer/config
  matching/swap interval): shadow surface, no allocator/loss model;
  host-only semantics in the software model (ROOT-EGL-SHADOW).

## ROOT-008 — THEME-PRODUCER (2 findings, FIXED S101/S100 — verified held)

**Findings**: R500-002 (U-002), 106 (TypedArray), 107/110/111/112 (style
resolution/density/dimensions/colors — all L5 from S95–S101 waves).

**Evidence**: F-NEW-175 theme-backed producer consumed in fresh ballbreak;
S103 held the law two stages deeper.

## ROOT-NULL-PRODUCER / OUT-OF-SCOPE families

- ROOT-NULL-PRODUCER (R500-010): umbrella over the 30/61-title null-receiver
  family; the biggest slice (Field identity) is ROOT-001 — fixed.
- Host-only layers (no SurfaceFlinger/BufferQueue/GraphicBuffer/Vulkan/
  real JNI/AudioTrack producer): R500-014–016, 020/021/025/027/028/030/032/
  034/036/037/041–044/053 + 132/135 → OUT_OF_SCOPE per rule 7.

## ROOT-009 — SWITCH-KEY-WIDENING (2 findings, FIXED S104 — commit 4feaaeda)

**Law**: packed-switch/sparse-switch consume an INT register; a
BYTE/CHAR/SHORT/BOOLEAN register value must widen to int (AOSP semantics —
dalvik_int_value). The engine's switch key extraction collapsed every
non-INT32/INT64 value to 0.

**Findings**: R500-082 (packed-switch), R500-084 (R8 merged lambdas — the
"wrong branch" observation), R500-083/081 (sparse-switch/payload family —
shared site, research-level).

**Divergence reproduced (S104, solitaire)**: R8 horizontal class merging
gives every merged class a `$r8$classId:B` field + packed-switch constructor
dispatch. The merged SavedStateRegistryController (classId=5) ran the
classId=0 fall-through branch (key collapsed to 0), leaving field `input`
unset → NPE `MatcherMatchResult.getSavedStateProvider on a null object
reference` at `ComponentActivity.<init>` → process death, 12 census errors.

**Fix (L5)**: `dalvik_engine.cpp` switch key extraction now uses the shared
`dalvik_int_value` widening (one shared law — not per-class patches).
Probe `[S104-SW]`: pre-fix key=0 → dest=5 (wrong branch); post-fix
key=5 → dest=11 + key=4 → dest=5 (both branches correct).

**Corpus**: com.vayunmathur.games.solitaire errors 12 → 0 (3/3 runs,
byte-identical screenshots SHA `59fdbfcd60b86a23`); compose chain advanced
past saved-state wiring to the AndroidComposeView layout path. Second
merged-class APK (sgtpuzzles): unchanged, 0 errors. Battery 105/105.
Fan-out: 2/54 census APKs carry `$r8$classId`; the widening law covers
every packed/sparse-switch on a narrow-typed register corpus-wide.

**Ticket crosswalk**: P082 [x] SOLVED, P084 PARTIAL (lambda-specific rerun
pending) — see `docs/RESEARCH_500_PROBLEM_REGISTRY.md` + FIX-005 in
`docs/RESEARCH_FIX_CROSSWALK.md`.

## Counts

```text
clustered findings            = 64 (13 named clusters incl. ROOT-009)
single-item dispositions      = 72
verified-fixed this wave      = 4 roots (REFLECTION-FIELD-IDENTITY,
                                VIEW-FRAME, PFQ-ORDER, SWITCH-KEY-WIDENING)
                                — 34 findings L5 (S103) + packed-switch L5 (S104)
reproduced-not-fixed (next)   = 2 roots (DECOR-LINKAGE, CLASS-IDENTITY)
latent / corpus-unconfirmed   = 1 root (ARSC-ENCODING)
classified host-only/absent   = 1 root family (GL/EGL/TEX)
```

## ROOT-010 — WORKER-PARK-DEPTH (9 findings, FIXED S105)

**Law**: kotlinx.coroutines `CoroutineScheduler.Worker.runLoop` — when
`findNextTaskAndExecute` returns null the worker transitions PARKING and
calls `LockSupport.parkNanos` (upstream: kotlinx-coroutines
`CoroutineScheduler.kt` + AOSP libcore `LockSupport.park` contract: the
thread stays suspended until unparked or the timeout elapses; a parked
worker consumes no CPU). The serialized engine's counterpart (R-NEW-345
extension): park inside a drained worker body (drain depth >= 1) with zero
work drained = deterministic suspension of the body at the drain boundary;
the body re-registers in the F-150 yielded-thread registry and re-drains at
the NEXT scheduler boundary (one bounded rescan per clock tick).

**Root cause (dooz v23 ground truth, S105 BEFORE run)**: the
`LockSupport.park` bridge drained the queues synchronously and THEN checked
`park_drain_last_depth_ >= 1` — but `drain_park_queues_bounded` restores
its own depth (0 at outermost) on exit, destroying the enclosing drained
body's depth before the check read it. Every top-level worker park saw
depth 0, never yielded, and spun park→scan→park until the F084 loop-visit
cap destroyed the frame chain: `[HALT-LOOP] Infinite loop at PC=0xb2 in
Lsr;.run` (engine PC 178 cu = bytecode 0x164, `iget-object
nextParkedWorker`, op 0x54), 50001 visits, 24x `[PARK-DRAIN] depth=0
work_units=0`, 0x `[PARK-YIELD]` → `VirtualMachineError` → 9 unwind rows →
onCreate APP BOUNDARY. The Job double-completion ISE (`Loj0;.T`) and the
navigation null-route NPE (`Lox0;.a`) recorded by S104-r3 as separate
sub-frontiers were downstream casualties of the same frame destruction and
died with the fix.

**Fix (L5)**: the park bridge now saves the enclosing drained-body depth
and restores it after the drain (the same save/restore discipline
`run_thread_start_body` applies to the identical variable), and registers
the parked body due at `now + 1ms` (exactly ONE park/rescan per scheduler
boundary — a 0 wake re-pops the worker up to the 8-slice cap within the
same boundary, observed as `resumed=8`/`parks=9` before the refinement).

**Probe**: `fixtures/s105_park_probe/` (models the Worker.runLoop shape:
poll→execute→park-when-empty), gate `scripts/s105_park_probe_check.sh`.
Pre-fix binary: rc=1, HALT-LOOP, PARK-YIELD=0, screen frozen at
"park-probe-start". Post-fix: rc=0 3/3, 8/8 checks PASS — worker active →
task1 exactly once → idle park (PARK-YIELD depth=1) → one rescan per
boundary → task2 (posted at 2.5s virtual while parked) executes exactly
once → worker terminates.

**Corpus (real APK impact)**:
```text
io.github.yamin8000.dooz v23   before = 17 errors (F084 halt family + Job
                                 ISE + nav NPE + unwinds, 2 APP BOUNDARY rows,
                                 2.2M+ instructions burned in the spin)
                               after  =  6 errors 3/3 — all six are the
                                 EXC-UNWIND bookkeeping of ONE handled
                                 kotlinx CancellationException (La; extends
                                 j.u.concurrent.CancellationException; its
                                 typed handler at Llo;.B catches it — real
                                 cancellation control flow, Fatal: NO);
                                 ZERO uncaught exceptions, ZERO halts,
                                 ZERO APP BOUNDARY rows; setContentView +
                                 deferred attach+measure path executes
                               screenshot SHA 59fdbfcd60b86a23 x3 (recorded
                                 blank-canvas SHA — NO visual claim made)
dooz_23_toplevel (same root)   before = 17 errors + HALT-LOOP (pre-fix
                                 binary)
                               after  =  6 errors 3/3, halt=0, PARK-YIELD x12
stopwatch_6 (timed-park ref)   0 errors before AND after (park path not on
                                 its active run path) — control unchanged
bouncy (LockSupport ref)       16 errors before AND after (pre-existing,
                                 park path not on its active run path) —
                                 control unchanged
```

**Regression**: BATTERY GATE ALL PASS (105 stages, rc=0) on the final tree.

**Fan-out (bytecode scan + execution)**: 42 on-disk corpus APKs scanned —
4 carry `LockSupport` refs (dooz x2, stopwatch, bouncy), 3 use timed park.
Execution-proven affected: dooz x2 (same root, both fixed). Controls:
stopwatch/bouncy unchanged. Presence != fan-out: only APKs whose active
path parks are affected.

**Ticket crosswalk**: P084 companion rows (F084 unwind family) SOLVED;
S104-r3 sub-frontiers (b) Job ISE and (c) nav NPE closed as downstream
cascades. Next queued root: R-005 DECOR-LINKAGE (GR-08, ticket #348).

## ROOT-005 / GR-08 — DECOR-LINKAGE (REPRODUCED → SOLVED S105)

**Law**: AOSP `PhoneWindow.setContentView` installs every view INSIDE the
window's decor hierarchy (DecorView → mContentParent → view); androidx
`AppCompatDelegateImpl.createSubDecor` ends with
`mWindow.setContentView(subDecor)`, making the sub-decor
(ActionBarOverlayLayout id=`decor_content_parent` → `action_bar` toolbar →
`action_bar_activity_content`) REACHABLE from `window.getDecorView()` —
which `WindowDecorActionBar.init` walks (`mOverlayLayout = decor.findViewById(
R.id.decor_content_parent)`, `mDecorToolbar = getDecorToolbar(decor.findViewById(
R.id.action_bar))`). Decor identity: ONE DecorView per Window per Activity
(PhoneWindow.mDecor created once, stable).

**Root cause (ballbreak v1.8.1 ground truth, S105 BEFORE)**: the engine
answered `Landroid/view/Window;->setContentView(View)` as a silent
unknown-method void — the sub-decor was never linked into the window decor
hierarchy (§12 silent-failure chain). Additionally the getDecorView law used
ONE global View singleton, leaking one activity's decor object into the
next (two live decor oids 70/203 in a single run). Result:
`WindowDecorActionBar.init → findViewById(decor_content_parent=0x7f080054,
search_root=<decor>) → NOT FOUND → getDecorToolbar(null) → ISE
"Can't make a decor toolbar out of null" → GameActivity.onCreate
APP BOUNDARY unwind` — Status: PARTIAL SUCCESS, composition dead
(S103's REPRODUCED #348, now root-caused and fixed).

**Fix (L5, two shared laws)**:
1. `Window.setContentView(View)` engine law (dalvik_engine.cpp): attaches
   the view under the CURRENT activity's window decor node —
   `[R005-DECOR]` evidence row; loud, never silent.
2. Per-activity decor map (`window_decor_for_activity_`): getDecorView
   allocates/reuses ONE decor per activity (AOSP identity law) instead of
   one global singleton.

**Real APK impact (de.georgsieber.ballbreak v1.8.1 vc10, SHA
e6e9f37293d3aaac… hash-verified against the S84 registry record)**:
```text
before (S104-r3 HEAD binary): ISE "Can't make a decor toolbar out of
                               null" 2/2 runs → GameActivity.onCreate
                               APP BOUNDARY → Status: PARTIAL SUCCESS
after:  Status: SUCCESS, Errors: 0, 3/3 runs; WindowDecorActionBar.init
        decor-walk answers FOUND (decor_content_parent=207, action_bar=232)
        from the decor root (receiver 0xcb=203) — ONE live scene; zero
        APP BOUNDARY rows
```
Controls (post-fix binary): dooz 6 (holds after ROOT-010), bouncy 16
(pre-existing, unchanged), unote 0. Battery 105/105 ALL PASS (rc=0) on the
final tree. Corpus fan-out (bytecode scan): 0/42 on-disk APKs carry the
WindowDecorActionBar+decor_content_parent family (the reproducer APK had
been cleaned from the corpus; re-fetched from the registry URL,
SHA-verified). The law also covers every multi-activity app via the
decor-identity fix.

**Ticket crosswalk**: #348 CLOSED (REPRODUCED → SOLVED); GR-08 status
REPRODUCED → SOLVED-L5. Next queued root: compose host/recomposition
frontier (S104-r3 GR-07 continuation).
