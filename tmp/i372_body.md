# SUPPLEMENTARY DEEP ROOT-CAUSE CLOSEOUT — BLACK / WHITE / PARTIAL / LOAD FAILURES

## Mission

This issue is a **supplementary deep root-cause campaign** for MiniAndroid Compatibility Runtime.

It must complement Issue #371 and must NOT become a duplicate of the existing root registry.

The objective is broader than Telegram, games, WebView, EGL, or any one app:

> For any installed Android APK that launches white, black, partially, freezes, loads incorrectly, or fails before meaningful UI, determine the FIRST semantic divergence and fix the GENERIC Android law that caused it.

External research was cross-checked against MiniAndroid's current root registry/worklist. Only genuinely new or structurally under-covered contracts belong here.

Recent external evidence is especially relevant for:
- ABI advertisement vs actual native-bridge availability
- native translator/linker compatibility
- gralloc/buffer usage contracts
- synchronization fences
- HWC/composition
- Binder/system-service availability
- RRO/idmap/resource mutation
- display/surface/buffer consistency

AOSP explicitly describes gralloc usage-dependent buffer allocation and fence synchronization, while redroid documents a real case where advertising arm64-v8a without a translator lets ARM-only APKs install and then crash on launch. Waydroid documents black/crash-loop failures caused by missing Binder infrastructure, and AOSP RRO diagnostics show that overlay/idmap/user selection can change the resolved resource. 

---

# NON-NEGOTIABLE RULES

- Work under THIS ISSUE.
- Do not create another issue for these findings.
- Do not close Issue #371 or rewrite its historical evidence.
- Do not create duplicate R-NEW/F-NEW roots.
- Before implementing every candidate, compare it with:
  - root_registry.json
  - canonical/root_cause_registry.json
  - canonical/master_worklist.json
  - capability registry
  - current worklog
  - Issue #371
  - current source
  - current tests
- Every candidate must be classified:
  - A = already covered
  - B = same root, new external evidence
  - C = genuinely new sub-law
  - D = genuinely new root
  - E = not applicable
  - F = research/future only
- Only C/D may become implementation items.
- Do not turn an external project's workaround into MiniAndroid architecture.
- No app-specific conditionals.
- No package-name hacks.
- No screenshot-only claims.
- No "exit code 0" completion.
- No "PNG exists" completion.
- No "agent says fixed" completion.
- No silent fail-soft behavior where Android semantics require an error.
- Preserve all useful negative evidence.
- If blocked by a real external dependency, mark BLOCKED with exact reason.
- If a root is not proven, mark PARTIAL/UNPROVEN.
- Current HEAD must be tested.
- Every fix requires regression testing.
- Prefer source-first investigation over APK guessing.

---

# REQUIRED RESPONSE CONTRACT FOR THE CODER

For EVERY numbered item below, the coder MUST provide BOTH:

### 1. CHECKBOX
Exactly one final state:

- [ ] IMPLEMENTED
- [ ] TESTED
- [ ] VERIFIED
- [ ] OBSERVED
- [ ] PARTIAL
- [ ] BLOCKED
- [ ] NOT APPLICABLE
- [ ] DUPLICATE
- [ ] RESEARCH ONLY

### 2. WRITTEN CONFIRMATION

Immediately after the checkbox, write a concise evidence paragraph containing:

**RESULT:**  
**SOURCE:**  
**SEMANTIC LAW:**  
**MINIANDROID LOCATION:**  
**FIRST DIVERGENCE:**  
**TEST:**  
**REAL APP:**  
**RUNTIME TRACE:**  
**SCREENSHOT/PROVENANCE:**  
**3-RUN RESULT:**  
**REGRESSION:**  
**COMMIT:**

A checkbox WITHOUT the written confirmation is NOT complete.

A written confirmation WITHOUT the checkbox is NOT complete.

If something is not implemented, say why.

---

# TRUTH MODEL

Every target must be classified through these independent layers:

1. EXECUTION
2. STATE
3. VIEW TREE
4. GEOMETRY
5. DRAW
6. BUFFER
7. COMPOSITION
8. PRESENTATION
9. CAPTURE

Also permit:

10. OVERPAINT
11. WRONG WINDOW
12. WRONG SURFACE
13. WRONG RESOURCE
14. WRONG BACKEND
15. WRONG ABI
16. WRONG CONFIGURATION
17. WRONG USER/DOMAIN
18. WRONG PROCESS LIFETIME

Never collapse these into "rendering failed".

---

# PHASE 0 — CURRENT-STATE / DUPLICATION AUDIT

### [ ] 001 — Read all governing laws
Read current constitution, lifecycle laws, graphics laws, filesystem/install laws, testing laws and current Issue #371 evidence.

### [ ] 002 — Read root registry
Read the complete current root registry and identify open/partial/unproven roots relevant to this campaign.

### [ ] 003 — Read master worklist
Map every candidate below to existing worklist rows.

### [ ] 004 — Read capability registry
Do not recreate an existing capability as a new root.

### [ ] 005 — Build external-to-internal cross-match
Create a table:
EXTERNAL FINDING → EXISTING ROOT → STATUS → DUPLICATE/NEW.

### [ ] 006 — Detect stale historical claims
Identify Issue #371 ledger entries that are stale relative to current HEAD.

### [ ] 007 — Establish clean baseline
Build from canonical bootstrap and record:
HEAD, binary SHA, APK SHA, toolchain identity, environment.

### [ ] 008 — Baseline battery
Run the canonical battery before modifying anything.

### [ ] 009 — Baseline screenshots
Record screenshot SHA/metrics for all baseline targets.

### [ ] 010 — Baseline determinism
At least 3 cold runs for selected targets.

---

# PHASE 1 — INSTALL / ABI / NATIVE EXECUTION

### [ ] 011 — ABI declaration truth
Verify advertised ABI equals an ABI the runtime can actually execute.

### [ ] 012 — ARM-only install semantics
ARM-only APK on x86 host: prove install decision and failure reason.

### [ ] 013 — ARM-only launch semantics
If accepted, prove native execution capability; otherwise fail honestly before launch.

### [ ] 014 — Multi-ABI selection
Verify exact primaryCpuAbi selection for multi-ABI APKs.

### [ ] 015 — Missing translator
Simulate advertised ABI + missing native bridge and verify explicit failure.

### [ ] 016 — Translator version compatibility
Verify translator/API compatibility instead of assuming presence means usable.

### [ ] 017 — native bridge property consistency
Cross-check native bridge properties against actual files/libraries.

### [ ] 018 — nativeLibraryDir truth
Verify extraction path is real, package-owned and accessible.

### [ ] 019 — Native dependency closure
Trace DT_NEEDED dependencies transitively.

### [ ] 020 — Linker namespace
Verify native library lookup obeys Android-like namespace/path semantics.

### [ ] 021 — Symbol resolution
Trace:
load → dependency → symbol → relocation → constructor → JNI_OnLoad.

### [ ] 022 — Native constructor failures
Prove constructor failure is observable and not converted into fake success.

### [ ] 023 — JNI_OnLoad contract
Verify JNI_OnLoad result and registration semantics.

### [ ] 024 — Native exception propagation
Native failure must reach the correct managed failure path.

### [ ] 025 — ABI negative matrix
Test ARM, x86, x86_64, multi-ABI and unavailable ABI cases.

### [ ] 026 — executable-launch argv semantics
Investigate short-name vs absolute-path native executable invocation.

### [ ] 027 — binfmt/translator launcher semantics
Only if MiniAndroid has an equivalent executable-launch surface.

### [ ] 028 — Native thread startup
Verify native-created threads receive valid runtime state.

### [ ] 029 — Native thread attach
Verify attach/detach semantics.

### [ ] 030 — Native library unload/lifetime
Verify no stale library/object state survives process recreation.

---

# PHASE 2 — SYSTEM SERVICE / BINDER PRE-RENDERING

### [ ] 031 — Binder availability
Prove binder/service transport availability before UI launch.

### [ ] 032 — ServiceManager lookup
Missing service must be explicit, not silently null.

### [ ] 033 — WindowManager service
Trace lookup → transaction → reply → state.

### [ ] 034 — SurfaceFlinger service
Trace lookup → availability → transaction → reply.

### [ ] 035 — PackageManager service
Verify package identity/ABI/resource information comes from coherent state.

### [ ] 036 — Input service
Verify input channel registration does not silently fail.

### [ ] 037 — Display service
Verify display information is coherent.

### [ ] 038 — Media service
Verify media clients get real service responses.

### [ ] 039 — Binder death
Verify service death/restart invalidates stale clients correctly.

### [ ] 040 — Service retry semantics
Verify retry/backoff does not create a permanent blank state.

---

# PHASE 3 — DISPLAY / WINDOW / SURFACE IDENTITY

### [ ] 041 — Activity → Window identity
Prove the Activity's authoritative Window.

### [ ] 042 — Window → Decor identity
Prove the actual DecorView belongs to the visible Window.

### [ ] 043 — Decor race
Test background-thread Window construction and prevent orphan DecorView attachment.

### [ ] 044 — WindowManager.addView identity
Prove the ViewRoot actually attached to the visible Window.

### [ ] 045 — ViewRoot attachment
Verify mView, ViewRoot and Window identity agree.

### [ ] 046 — Topmost window identity
Prove captured/displayed layer belongs to intended app window.

### [ ] 047 — Starting window lifetime
Prove starting/splash window is removed when app content becomes authoritative.

### [ ] 048 — Window token consistency
Verify WindowToken does not point at stale/recreated state.

### [ ] 049 — Surface identity
Every rendered frame must identify its Surface.

### [ ] 050 — Surface replacement
Old Surface must not continue receiving frames after recreation.

### [ ] 051 — Surface handle generation
New Surface must receive a new valid identity.

### [ ] 052 — Surface destroy ordering
Destroy → stop rendering → release resources → recreate.

### [ ] 053 — Surface recreate
Rebind renderer to the new Surface.

### [ ] 054 — Surface 0×0
Detect zero-size surface before attempting meaningful rendering.

### [ ] 055 — Window 0×0
Detect zero-size Window separately from Surface 0×0.

### [ ] 056 — ViewRoot 0×0
Detect geometry collapse at ViewRoot level.

### [ ] 057 — Display 0×0
Detect invalid virtual/host display dimensions.

### [ ] 058 — Display/window/surface size agreement
Record all four dimensions and first mismatch.

### [ ] 059 — Resize propagation
Display resize → Window → Surface → ViewRoot → buffer.

### [ ] 060 — Rotation resize
Rotation must propagate to all geometry layers.

---

# PHASE 4 — TRAVERSAL / FIRST FRAME / THREADING

### [ ] 061 — requestLayout semantics
Verify layout request reaches traversal.

### [ ] 062 — invalidate semantics
Verify dirty region reaches traversal.

### [ ] 063 — Choreographer traversal callback
Verify traversal callback actually executes.

### [ ] 064 — Sync barrier semantics
Verify asynchronous traversal messages are not blocked incorrectly.

### [ ] 065 — Reentrant requestLayout
Verify nested requestLayout produces required additional pass.

### [ ] 066 — Multiple traversal passes
Verify state converges instead of being rendered prematurely.

### [ ] 067 — Main-thread identity
Verify UI mutations execute on authoritative UI thread.

### [ ] 068 — Handler/Looper identity
Verify messages reach correct Looper.

### [ ] 069 — Background callback ordering
Async callback must not overwrite newer UI state.

### [ ] 070 — First-frame settlement
Do not capture before the first authoritative frame is complete.

### [ ] 071 — Layout-complete vs draw-complete
Keep these states distinct.

### [ ] 072 — draw-complete vs presented
Keep these states distinct.

### [ ] 073 — Animation settlement
Verify deterministic settlement for animated UI.

### [ ] 074 — Virtual time
Verify delayed work does not remain permanently pending.

### [ ] 075 — Cancellation/restart
Verify canceled UI work cannot suppress the next frame.

---

# PHASE 5 — BUFFER / GRALLOC / FENCE / QUEUE

### [ ] 076 — Buffer allocation request
Record format + usage + dimensions.

### [ ] 077 — Buffer usage contract
CPU/GPU/read/write/texture/video usage must be explicit.

### [ ] 078 — Format negotiation
Producer and consumer must agree on usable format.

### [ ] 079 — IMPLEMENTATION_DEFINED semantics
Do not pretend an implementation-defined format is fixed RGBA.

### [ ] 080 — Stride correctness
Record allocated stride and effective row layout.

### [ ] 081 — Gralloc result
Trace request → allocation → actual backing.

### [ ] 082 — Mapper/import semantics
Trace buffer mapping/import if applicable.

### [ ] 083 — Buffer lock/unlock
Verify lock/unlock preserves data and lifetime.

### [ ] 084 — Acquire fence
Consumer must respect producer completion.

### [ ] 085 — Release fence
Producer must respect consumer completion.

### [ ] 086 — Fence signaling
Record creation, wait and signal.

### [ ] 087 — Fence timeout
A fence timeout must be diagnosable.

### [ ] 088 — Queue depth
Record producer/consumer queue state.

### [ ] 089 — Producer back-pressure
Detect blocked producer.

### [ ] 090 — Consumer starvation
Detect missing consumer release.

### [ ] 091 — Frame number ordering
Reject/diagnose stale frame ordering.

### [ ] 092 — Buffer abandoned
Distinguish abandoned queue from render failure.

### [ ] 093 — Buffer size rejection
Distinguish rejected buffer from failed draw.

### [ ] 094 — Buffer lifetime
Do not recycle a buffer while still in use.

### [ ] 095 — Buffer provenance
Every presented frame must identify its originating buffer.

---

# PHASE 6 — COMPOSITION / HWC / PRESENTATION

### [ ] 096 — SurfaceControl transaction build
Record requested transaction.

### [ ] 097 — SurfaceControl transaction apply
Prove transaction reaches compositor state.

### [ ] 098 — Transaction commit
Distinguish built/applied/committed.

### [ ] 099 — Layer visibility
Prove intended layer is visible.

### [ ] 100 — Layer alpha
Prove compositor alpha does not make valid content invisible.

### [ ] 101 — Layer Z-order
Prove app layer is not covered by another layer.

### [ ] 102 — Layer crop
Prove crop is not removing content.

### [ ] 103 — Layer transform
Prove transform does not move content outside display.

### [ ] 104 — Composition type
Record client/device/other composition path.

### [ ] 105 — Unsupported composition fallback
Verify fallback is explicit and correct.

### [ ] 106 — HWC capability
Record requested vs supported HWC capabilities.

### [ ] 107 — Client composition
Verify GLES/client composition output reaches final layer.

### [ ] 108 — Display transform
Verify display transform preserves visible content.

### [ ] 109 — Presentation deadline
Record whether frame missed presentation deadline.

### [ ] 110 — Present fence
Prove final presentation completion.

### [ ] 111 — Presented frame ID
Record frame ID actually visible to capture.

### [ ] 112 — No extra swap owner
Exactly one authoritative presentation owner.

### [ ] 113 — Double-swap detection
Detect competing presentation paths.

### [ ] 114 — SurfaceFlinger equivalent
If MiniAndroid has no SurfaceFlinger equivalent, document the abstraction boundary rather than faking one.

---

# PHASE 7 — GLES / RENDER TARGET DEEP VALIDATION

### [ ] 115 — EGLConfig selection
Record requested and selected config.

### [ ] 116 — EGLSurface validity
Prove EGLSurface is tied to the intended Surface.

### [ ] 117 — Context identity
Prove rendering occurs in the intended EGL context.

### [ ] 118 — Current-context state
Detect accidental context loss.

### [ ] 119 — Framebuffer completeness
Check actual framebuffer status.

### [ ] 120 — Renderbuffer attachment
Verify render target attachment.

### [ ] 121 — Viewport
Detect 0×0/wrong viewport.

### [ ] 122 — Scissor
Detect accidental full-frame clipping.

### [ ] 123 — Blend state
Verify blend state does not erase content.

### [ ] 124 — Depth/stencil state
Verify depth/stencil cannot suppress all geometry.

### [ ] 125 — Texture binding
Record active texture unit and bound texture.

### [ ] 126 — Texture upload
Prove bytes reach GPU/renderer representation.

### [ ] 127 — Shader compile
Record compile result/log.

### [ ] 128 — Shader link
Record link result/log.

### [ ] 129 — Shader uniform state
Verify required uniforms are initialized.

### [ ] 130 — Vertex/index buffer
Verify actual geometry buffer contents.

### [ ] 131 — GL error chronology
Record first GL error, not just final error.

### [ ] 132 — GL state leakage
Detect state inherited from previous frame/app.

### [ ] 133 — Context recreation
Verify all required GL state is rebuilt after recreation.

### [ ] 134 — EGL swap
Prove draw → swap → queued buffer.

### [ ] 135 — Swap result
Do not treat swap success as presentation success.

---

# PHASE 8 — CANVAS / VIEW / DRAW PROVENANCE

### [ ] 136 — View visibility
Prove visibility state.

### [ ] 137 — View alpha
Prove alpha state.

### [ ] 138 — View bounds
Record actual bounds.

### [ ] 139 — Clip bounds
Record effective clip.

### [ ] 140 — Matrix
Record effective transformation matrix.

### [ ] 141 — Drawable bounds
Verify Drawable has non-zero drawable bounds.

### [ ] 142 — Drawable intrinsic size
Verify intrinsic dimensions are coherent.

### [ ] 143 — Background provenance
Record exact Drawable/background source.

### [ ] 144 — ColorFilter
Verify filter does not turn content into uniform output.

### [ ] 145 — Gradient/shader
Verify shader creation and effective bounds.

### [ ] 146 — NinePatch
Verify chunk parsing and density scaling.

### [ ] 147 — Elevation/Z
Verify shadow/elevation does not create unexpected overpaint.

### [ ] 148 — Canvas save/restore
Detect unbalanced state changes.

### [ ] 149 — Clip stack
Detect permanent clipping caused by save/restore mismatch.

### [ ] 150 — PorterDuff/blend
Verify compositing mode.

### [ ] 151 — Bitmap density
Verify density scaling.

### [ ] 152 — BitmapConfig
Verify pixel format.

### [ ] 153 — Premultiplied alpha
Verify bitmap alpha semantics.

### [ ] 154 — Text baseline
Verify FontMetrics/baseline.

### [ ] 155 — Font fallback
Verify missing font does not silently produce invisible text.

### [ ] 156 — RTL/bidi
Verify text is not displaced outside visible bounds.

### [ ] 157 — Custom View onDraw
Prove onDraw actually executes.

### [ ] 158 — ViewGroup child dispatch
Prove children receive layout/draw dispatch.

### [ ] 159 — Recycler/list child creation
Prove adapters produce actual children.

### [ ] 160 — StateList/ColorStateList
Verify selected/pressed/disabled states resolve correctly.

---

# PHASE 9 — RESOURCES / ASSETS / OVERLAYS

### [ ] 161 — Resource ID validity
Verify ID maps to expected package/resource.

### [ ] 162 — Resource package identity
Do not resolve an ID against wrong package.

### [ ] 163 — Configuration selection
Record locale/density/orientation/uiMode selection.

### [ ] 164 — Default-resource fallback
Verify fallback semantics.

### [ ] 165 — Asset path ordering
Record AssetManager path precedence.

### [ ] 166 — Split resource precedence
Verify base/configuration split composition if applicable.

### [ ] 167 — RRO activation
Detect active/inactive overlays.

### [ ] 168 — RRO target package
Verify targetPackage match.

### [ ] 169 — RRO target resource
Verify target resource exists.

### [ ] 170 — idmap mapping
Record target ID → overlay ID mapping.

### [ ] 171 — RRO priority
Verify overlay precedence.

### [ ] 172 — RRO user domain
Verify foreground user vs system user semantics.

### [ ] 173 — Overlay disabled behavior
Verify target resource returns normally.

### [ ] 174 — Overlay invalid behavior
Failure must be explicit.

### [ ] 175 — Resource provenance
Every suspicious visual resource must report:
APK/package → path → resource ID → selected configuration → bytes.

### [ ] 176 — Compressed raw resource semantics
Verify openRawResourceFd limitations.

### [ ] 177 — Asset FD offset
Verify startOffset/length semantics.

### [ ] 178 — Asset read position
Verify seek/current-position semantics.

### [ ] 179 — Resource density
Verify density scaling.

### [ ] 180 — Wrong-resource detection
Detect valid-but-wrong resource resolution.

---

# PHASE 10 — MEDIA / SURFACE / YUV

### [ ] 181 — Decoder initialization
Trace codec selection.

### [ ] 182 — Decoder output format
Record actual output format.

### [ ] 183 — YUV format
Verify YUV plane semantics if target uses it.

### [ ] 184 — YUV→RGB conversion
Verify conversion.

### [ ] 185 — Video Surface attachment
Prove decoder output reaches intended Surface.

### [ ] 186 — Video buffer queue
Trace decoder → buffer → Surface.

### [ ] 187 — Video frame presentation
Distinguish decoding from visible frame.

### [ ] 188 — Surface recreation during playback
Verify decoder rebinds correctly.

### [ ] 189 — Audio/video divergence
Audio playing must not be treated as proof video is visible.

### [ ] 190 — Protected/secure content
Classify protected content separately from ordinary black rendering.

---

# PHASE 11 — WEBVIEW / COMPOSITOR / HYBRID UI

### [ ] 191 — DOM-ready vs visual-ready
Do not equate page load completion with visible pixels.

### [ ] 192 — WebView visual-state callback
Verify visual readiness.

### [ ] 193 — WebView compositor
Trace DOM → compositor → surface → capture.

### [ ] 194 — WebView layer mode
Compare hardware/software layer paths.

### [ ] 195 — WebView storage
Verify storage/provider availability does not stall rendering.

### [ ] 196 — WebView process lifetime
Detect stale WebView process state.

### [ ] 197 — Activity recreation
Verify WebView is attached to current Activity/window.

### [ ] 198 — Compose/WebView synchronization
If applicable, prove applyChanges/visual commit ordering.

### [ ] 199 — WebView wrong surface
Prove WebView pixels target visible surface.

### [ ] 200 — WebView blank-with-healthy-DOM
Classify as compositor/presentation problem, not DOM failure.

---

# PHASE 12 — PROCESS / LIFECYCLE / STATE IDENTITY

### [ ] 201 — Process lifetime vs Activity lifetime
Verify statics do not incorrectly survive Activity recreation.

### [ ] 202 — Singleton Activity references
Detect stale Activity references.

### [ ] 203 — Singleton Window references
Detect stale Window references.

### [ ] 204 — Singleton View references
Detect stale View references.

### [ ] 205 — Classloader identity
Verify recreated application does not accidentally reuse wrong classloader state.

### [ ] 206 — Context identity
Verify application/activity/service contexts are distinct where required.

### [ ] 207 — Configuration recreation
Verify state migration after configuration change.

### [ ] 208 — Saved state
Verify state restoration.

### [ ] 209 — Intent/task restoration
Verify relaunch restores correct Activity/window.

### [ ] 210 — Background/resume
Verify rendering after background/foreground transition.

### [ ] 211 — Render thread restart
Verify renderer thread restarts against current surface/context.

### [ ] 212 — Coroutine/task restart
Verify canceled work cannot corrupt recreated UI.

---

# PHASE 13 — PERSISTENCE / INSTALL STATE / PACKAGE ISOLATION

### [ ] 213 — Package root
Verify real per-package filesystem root.

### [ ] 214 — dataDir
Verify physical directory exists.

### [ ] 215 — filesDir
Verify physical directory exists.

### [ ] 216 — cacheDir
Verify physical directory exists.

### [ ] 217 — databasesDir
Verify physical directory exists.

### [ ] 218 — sharedPrefsDir
Verify physical directory exists.

### [ ] 219 — nativeLibraryDir
Verify physical directory exists.

### [ ] 220 — sourceDir
Verify APK/source path is real.

### [ ] 221 — splitSourceDirs
Verify split paths are real.

### [ ] 222 — File.exists
Must test physical filesystem.

### [ ] 223 — File.length
Must report actual byte length.

### [ ] 224 — byte[] write
Must write actual bytes.

### [ ] 225 — byte[] read
Must return actual bytes.

### [ ] 226 — seek/offset
Verify file pointer semantics.

### [ ] 227 — SharedPreferences persistence
Write → process death → reinstall/run → read.

### [ ] 228 — SQLite persistence
Write → close → reopen → query.

### [ ] 229 — SQLite WAL
Verify WAL file/state semantics.

### [ ] 230 — Package isolation
App A cannot see App B private files.

### [ ] 231 — Reinstall semantics
Verify expected data preservation/deletion behavior.

### [ ] 232 — Fresh install semantics
No stale package state.

### [ ] 233 — Multi-app concurrency
Two apps must retain separate state.

### [ ] 234 — Media/file provenance
Physical bytes must trace back to APK/app-generated data.

---

# PHASE 14 — HIT TEST / INPUT / STATE CAUSALITY

### [ ] 235 — Coordinate transform
Input coordinates must map to View coordinates.

### [ ] 236 — Display-to-window transform
Verify window offset.

### [ ] 237 — Window-to-view transform
Verify nested offsets.

### [ ] 238 — Scroll transform
Verify scroll offsets.

### [ ] 239 — Scale transform
Verify density/scaling.

### [ ] 240 — Clip-aware hit testing
Do not hit invisible/clipped views.

### [ ] 241 — Topmost hit
Verify child ordering.

### [ ] 242 — Touch dispatch
Trace dispatch through hierarchy.

### [ ] 243 — ACTION_DOWN/UP lifecycle
Verify complete sequence.

### [ ] 244 — Gesture state
Verify gesture recognizers receive coherent events.

### [ ] 245 — Input → state change
Prove input causes actual application state change.

### [ ] 246 — State change → visual change
Prove state change reaches pixels.

---

# PHASE 15 — APP-FAMILY VALIDATION

### [ ] 247 — New simple app
Select one app not previously used as a root fixture.

### [ ] 248 — New complex app
Select one independent app family.

### [ ] 249 — New game
Select one new game.

### [ ] 250 — Second new game
Select another independent game engine/UI family.

### [ ] 251 — Random corpus app
Choose randomly from corpus.

### [ ] 252 — Random corpus game
Choose randomly from corpus.

### [ ] 253 — Telegram persistence target
Re-run Telegram persistence evidence.

### [ ] 254 — LibGDX target
Use tictactoedeluxe or another valid libGDX target.

### [ ] 255 — WebView target
Use a WebView-heavy app.

### [ ] 256 — Native-heavy target
Use a real app requiring native libraries.

### [ ] 257 — Media target
Use an app with actual bitmap/media rendering.

### [ ] 258 — Filesystem target
Use an app that creates physical files.

---

# PHASE 16 — CAUSAL A/B

### [ ] 259 — Preserve BASE binary
Record exact SHA.

### [ ] 260 — BASE synthetic failure
Run target before fix.

### [ ] 261 — PATCH synthetic result
Run same target after fix.

### [ ] 262 — BASE real app
Run affected real app.

### [ ] 263 — PATCH real app
Run same app.

### [ ] 264 — Isolated evidence directories
Do not mix BASE/PATCH artifacts.

### [ ] 265 — Screenshot SHA comparison
Record exact differences.

### [ ] 266 — Runtime trace comparison
Show first divergence disappears.

### [ ] 267 — Negative control
Unaffected target must remain unchanged.

### [ ] 268 — Regression battery
Run complete battery after patch.

---

# PHASE 17 — DETERMINISM / REGRESSION

### [ ] 269 — Three cold runs
All high-priority fixes.

### [ ] 270 — Screenshot byte identity
Where deterministic.

### [ ] 271 — Pixel metrics
Record non-background percentage / entropy / unique colors as appropriate.

### [ ] 272 — Runtime trace identity
Compare key trace markers.

### [ ] 273 — Negative tests
Verify failure paths remain correct.

### [ ] 274 — Reinstall tests
Verify clean install.

### [ ] 275 — Multi-app tests
Verify isolation.

### [ ] 276 — Existing golden tests
No drift without explanation.

### [ ] 277 — Existing corpus tests
No regressions.

### [ ] 278 — Build reproducibility
Build from clean environment.

### [ ] 279 — Binary SHA
Record final binary SHA.

### [ ] 280 — APK/toolchain hygiene
No prohibited binaries committed.

---

# PHASE 18 — OBSERVABILITY / VISUAL LOGGER

### [ ] 281 — Execution logger
Record launch/class/method/native boundaries.

### [ ] 282 — ViewTree logger
Record hierarchy identity.

### [ ] 283 — Geometry logger
Record bounds/clip/matrix.

### [ ] 284 — Draw logger
Record draw source and target.

### [ ] 285 — Resource provenance logger
Record APK/resource origin.

### [ ] 286 — Buffer logger
Record buffer ID/size/format/usage.

### [ ] 287 — Surface logger
Record Surface identity/lifecycle.

### [ ] 288 — Composition logger
Record layer/Z/alpha/visibility.

### [ ] 289 — Presentation logger
Record swap/queue/fence/present.

### [ ] 290 — Capture logger
Record capture target/frame ID.

### [ ] 291 — First-divergence marker
Automatically mark first failed semantic transition.

### [ ] 292 — White-screen classifier
Classify white symptom by first divergence.

### [ ] 293 — Black-screen classifier
Classify black symptom by first divergence.

### [ ] 294 — Partial-screen classifier
Classify partial rendering.

### [ ] 295 — Overpaint classifier
Detect valid content covered by later layer.

---

# PHASE 19 — FINAL ROOT QUALITY

### [ ] 296 — Source law cited
Every implemented root has source evidence.

### [ ] 297 — Algorithm identified
Explain actual MiniAndroid algorithm.

### [ ] 298 — Semantic law stated
One precise Android law.

### [ ] 299 — First divergence identified
No vague "somewhere in rendering".

### [ ] 300 — Runtime target identified
Name exact app/probe.

### [ ] 301 — Regression target identified
Name unrelated target.

### [ ] 302 — Evidence directory
Give exact evidence path.

### [ ] 303 — Screenshot hash
Give SHA.

### [ ] 304 — Trace excerpt
Give relevant runtime trace.

### [ ] 305 — Three-run evidence
Give all run outcomes.

### [ ] 306 — Commit evidence
Give exact commit SHA.

### [ ] 307 — Current HEAD verification
Confirm commit is actually on tested HEAD.

### [ ] 308 — Duplicate audit
Confirm no duplicate root was created.

### [ ] 309 — No app-specific logic
Explicitly confirm.

### [ ] 310 — No fake fallback
Explicitly confirm.

---

# FINAL REQUIRED CHECKLIST SUMMARY

### [ ] 311 — All 310 checks reviewed
No unchecked item may be silently omitted.

### [ ] 312 — All A/B items classified
Duplicate evidence is documented.

### [ ] 313 — All C/D items implemented or honestly blocked
No vague completion.

### [ ] 314 — All BLOCKED items have exact blocker
Include dependency/version/ABI/environment.

### [ ] 315 — All PARTIAL items have next concrete divergence
No "needs more work".

### [ ] 316 — Root registry updated
Only genuinely new roots.

### [ ] 317 — Worklist updated
No duplicate work.

### [ ] 318 — Evidence index updated
Every claim points to evidence.

### [ ] 319 — Final regression clean
Current HEAD.

### [ ] 320 — Final corpus sample passed
Apps + games + random selections.

### [ ] 321 — Final persistence passed
Including Telegram.

### [ ] 322 — Final native passed
Including real native target.

### [ ] 323 — Final media/bitmap provenance passed
Actual app-owned content.

### [ ] 324 — Final black/white/partial classification passed
At least one example of each symptom.

### [ ] 325 — Final first-divergence report
Demonstrate the classifier works.

### [ ] 326 — Final 3-run determinism
High-priority targets.

### [ ] 327 — Final golden regression
No unexplained drift.

### [ ] 328 — Final negative regression
Failure semantics preserved.

### [ ] 329 — Final clean build
From canonical bootstrap.

### [ ] 330 — Final repository hygiene
No APK/AAB/toolchain binaries.

---

# REQUIRED FINAL WRITTEN CONFIRMATION

At the end of this Issue, the coder MUST write a final narrative confirmation.

Use exactly this structure:

## FINAL CLOSEOUT

**HEAD:**  
**FINAL BINARY SHA:**  
**BASELINE SHA:**  
**FINAL BUILD:** PASS/FAIL  
**REGRESSION:** PASS/FAIL  
**DETERMINISM:** PASS/FAIL  
**GOLDENS:** PASS/FAIL  
**NEGATIVES:** PASS/FAIL  
**REINSTALL:** PASS/FAIL  
**MULTI-APP:** PASS/FAIL  

### ROOT ACCOUNTING

**Existing roots reused:**  
**New C roots:**  
**New D roots:**  
**Duplicates rejected:**  
**Research-only:**  
**Not applicable:**  
**Blocked:**  
**Partial:**  

### SYMPTOM COVERAGE

**White screen:**  
**Black screen:**  
**Partial rendering:**  
**Load failure:**  
**Native failure:**  
**Media failure:**  
**Persistence failure:**  
**WebView failure:**  
**Surface recreation:**  

### REAL APP PROOF

List every real app/game used and for each:

APP:
VERSION:
APK SHA:
RESULT:
FIRST DIVERGENCE:
TRACE:
SCREENSHOT:
3-RUN:
REGRESSION:

### CAUSALITY

For every implemented root:

BASE RESULT:
PATCH RESULT:
FIRST DIVERGENCE REMOVED:
NEGATIVE CONTROL:
3-RUN:

### HONEST LIMITATIONS

List everything not proven.

Do NOT say "all fixed" if anything is PARTIAL/BLOCKED/UNPROVEN.

### FINAL STATEMENT

The coder must explicitly answer:

1. Can MiniAndroid now distinguish execution failure from rendering failure?
2. Can it distinguish rendering from buffer failure?
3. Can it distinguish buffer failure from composition/presentation failure?
4. Can it distinguish real black output from capture blackness?
5. Can it identify the first divergence?
6. Can it prove the fix causally?
7. Can it reproduce the result three times?
8. Can it do this on more than one app family?
9. Which generic Android contracts remain unimplemented?
10. Which remaining limitations are environmental rather than MiniAndroid defects?

The answer must be evidence-based.

---

# DEFINITION OF DONE

This Issue is NOT complete because the checkbox count is high.

It is complete only when:

SOURCE LAW
→ IMPLEMENTATION
→ RUNTIME TRACE
→ STATE CHANGE
→ VIEW/BUFFER/COMPOSITOR PROVENANCE
→ REAL APP RESULT
→ SCREENSHOT METRICS/SHA
→ 3-RUN REPEAT
→ REGRESSION
→ CURRENT HEAD

form a continuous evidence chain.

If any link is missing, mark the item PARTIAL/BLOCKED/UNPROVEN.

No fabricated completion.
No app-specific workaround.
No silent fail-soft.
No duplicate root.

The purpose is not to make one screenshot non-white.

The purpose is to make MiniAndroid capable of explaining and fixing the generic Android semantic reason why an APK is white, black, partial, or unable to load.
