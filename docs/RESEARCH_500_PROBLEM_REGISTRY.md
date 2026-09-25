# RESEARCH 500 — PROBLEM REGISTRY (canonical living backlog)

> Single source of truth for P001..P500 tickets. Evidence detail lives in
> `docs/RESEARCH_500_AUDIT.json` (R500 audit ledger); this registry is the
> trackable ticket layer. One shared fix checks off EVERY ticket it
> resolves — individually (§6/§25 model).

## A. Input accounting

```text
claimed findings:        500
actually present:        136
duplicates (linked):     7
missing/truncated:       364  (INPUT_TRUNCATED — never invented)
registered tickets:      500  (P001..P136 real + P137..P500 TRUNCATED_INPUT)
```

## B. Ticket accounting

```text
unverified         0
researched         21
reproduced         28
confirmed          12
implemented        0
tested             0
observed           19
solved             31
partial            1
duplicate-concept  0
out_of_scope       20
false_lead         4
blocked            0
truncated_input    364
```

## Roots

| Root | Name | Status | Fixes |
|------|------|--------|-------|
| R-001 | ROOT-REFLECTION-FIELD-IDENTITY | FIXED (L5) | FIX-001, FIX-004 |
| R-002 | ROOT-VIEW-FRAME | FIXED (L5) | FIX-002 |
| R-003 | ROOT-PFQ-ORDER | FIXED (L5) | FIX-003 |
| R-004 | ROOT-CLASS-IDENTITY | REPRODUCED (22/59 fan-out, dual-identity law pending) | — |
| R-005 | ROOT-DECOR-LINKAGE | REPRODUCED (sub-decor attach pending) | — |
| R-006 | ROOT-ARSC-ENCODING | LATENT (0/54 corpus exposure) | — |
| R-007 | ROOT-GL-BRIDGE/GLSL/TEX-COMPRESSION/EGL-SHADOW | CLASSIFIED (corpus-demand gated) | — |
| R-008 | ROOT-THEME-PRODUCER | FIXED (S100/S101, held) | — |
| R-009 | ROOT-SWITCH-KEY-WIDENING | FIXED (L5, S104 commit 4feaaeda) | FIX-005 |
| R-NP | ROOT-NULL-PRODUCER (umbrella) | PARTIAL (largest slice = R-001, fixed) | — |
| R-OUT | HOST-ONLY LAYERS | OUT_OF_SCOPE (SurfaceFlinger/HWC/GraphicBuffer/Vulkan/vendor EGL/DRM/real JNI/AudioTrack) | — |

## Live matrix (P001..P136 real findings)

| ID | Problem | Root | Level | Status | Repro | Impl | Tested | Solved | Fix |
|----|---------|------|-------|--------|-------|------|--------|--------|-----|
| P001 | androidx.appcompat.widget.Toolbar vs android.widget.Toolbar class identity | R-004 | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P002 | Theme.obtainStyledAttributes receiver returns null TypedArray / uninitialize | R-008 | L5 | SOLVED | Y | Y | Y | [x] | — |
| P003 | main Handler/Looper internal state never materialized | R-003 | L5 | SOLVED | Y | Y | Y | [x] | FIX-003 |
| P004 | View.getWidth returns 0 / NPE per report | R-002 | L5 | SOLVED | Y | Y | Y | [x] | FIX-002 |
| P005 | Field.get(null) static-field semantics broken | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P006 | Compose navigation NPE chain is downstream of one low-level root | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P007 | ARSC FLAG_OFFSET16/FLAG_COMPACT unhandled | R-006 | L2 | REPRODUCED | Y | — | — | [ ] | — |
| P008 | CompactDex support unknown | — | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P009 | Class-identity law across ALL name<->descriptor<->runtime-object conversion  | R-004 | L2 | REPRODUCED | Y | — | — | [ ] | — |
| P010 | Uninitialized-framework-object law (exists + non-null + missing internal sta | R-NP | L2 | REPRODUCED | Y | — | — | [ ] | — |
| P011 | Full ARSC compatibility audit (flags/sparse/alignment/offset/string-pool bou | R-006 | L2 | REPRODUCED | Y | — | — | [ ] | — |
| P012 | DEX family audit (versions/CDEX/quickened/header/map_list/hidden API/multide | — | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P013 | View lifecycle/geometry audit (0-semantic-correct vs 0-proves-layout-never-h | R-002 | L5 | SOLVED | Y | Y | Y | [x] | FIX-002 |
| P014 | Full-Android-emulator boundary (no kernel/container) | — | L1 | FALSE_LEAD | — | — | — | [ ] | — |
| P015 | Full-JVM boundary (OpenJDK/libcore borrowable semantics) | — | L1 | FALSE_LEAD | — | — | — | [ ] | — |
| P016 | Skia/Cairo graphics boundary | — | L1 | FALSE_LEAD | — | — | — | [ ] | — |
| P017 | Handler.postAtFrontOfQueue claimed as root cause | R-003 | L3 | FALSE_LEAD | — | — | — | [ ] | FIX-003 |
| P018 | View.getWidth 'NPE' diagnosis | R-002 | L5 | SOLVED | Y | Y | Y | [x] | FIX-002 |
| P019 | EGL_BAD_ALLOC | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P020 | Surface abandoned | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P021 | DEVICE_LOST | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P022 | surfaceless context | R-007 | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P023 | glFramebufferTexture2D | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P024 | BitmapFactory OOM | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P025 | EGL_CONTEXT_LOST | R-007 | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P026 | preserve context on pause | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P027 | GraphicBuffer allocation | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P028 | Skia allocation | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P029 | ETC1 | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P030 | external textures | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P031 | NPOT textures | — | L1 | RESEARCHED | — | — | — | [ ] | — |
| P032 | glTexImage2D thread affinity | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P033 | RenderTexture recreation | R-007 | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P034 | SurfaceTexture.updateTexImage | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P035 | glTexSubImage2D | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P036 | triple buffering | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P037 | Vsync | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P038 | S3TC | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P039 | ATC | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P040 | PVRTC | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P041 | BufferQueue | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P042 | fence sync | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P043 | EGLImage | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P044 | YUV | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P045 | sRGB | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P046 | texture arrays | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P047 | geometry/tessellation/compute shaders | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P048 | blending | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P049 | ColorFilter | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P050 | shaders | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P051 | EGL config selection | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P052 | EGL pbuffer | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P053 | swap interval | R-007 | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P054 | sync primitives | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P055 | glReadPixels | R-007 | L2 | CONFIRMED | — | — | — | [ ] | — |
| P056 | Field.get | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P057 | Field.set | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P058 | Field.get(null) | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P059 | static fields | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P060 | instance fields | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P061 | final fields | — | L0 | RESEARCHED | — | — | — | [ ] | FIX-001 |
| P062 | private fields | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P063 | inherited fields | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P064 | getField | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P065 | getDeclaredField | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P066 | missing fields | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P067 | wrong receiver | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P068 | null receiver | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P069 | boxing | — | L0 | OBSERVED | — | — | — | [ ] | FIX-001 |
| P070 | unboxing | — | L0 | OBSERVED | — | — | — | [ ] | FIX-001 |
| P071 | static initialization | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P072 | field identity | R-001 | L5 | SOLVED | Y | Y | Y | [x] | FIX-001 |
| P073 | invoke-polymorphic | — | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P074 | invoke-custom | — | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P075 | jumbo strings | — | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P076 | method IDs | — | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P077 | field IDs | R-001 | L0 | RESEARCHED | — | — | — | [ ] | FIX-001 |
| P078 | type IDs | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P079 | string pool | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P080 | encoded values | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P081 | switch payloads | R-009 | L2 | RESEARCHED | — | — | — | [ ] | FIX-005 |
| P082 | packed-switch | R-009 | L5 | SOLVED | Y | Y | Y | [x] | FIX-005 |
| P083 | sparse-switch | R-009 | L2 | RESEARCHED | — | — | — | [ ] | FIX-005 |
| P084 | R8 merged lambdas | R-009 | L4 | PARTIAL | Y | Y | — | [ ] | FIX-005 |
| P085 | synthetic classes | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P086 | class identity | R-004 | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P087 | check-cast | R-004 | L2 | REPRODUCED | Y | — | — | [ ] | — |
| P088 | instanceof | R-004 | L2 | REPRODUCED | Y | — | — | [ ] | — |
| P089 | method resolution | — | L5 | REPRODUCED | Y | — | — | [ ] | — |
| P090 | field resolution | R-001 | L3 | REPRODUCED | Y | — | — | [ ] | FIX-001 |
| P091 | ViewStub | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P092 | layout | R-002 | L5 | SOLVED | Y | Y | Y | [x] | FIX-002 |
| P093 | setFrame | R-002 | L5 | SOLVED | Y | Y | Y | [x] | FIX-002 |
| P094 | measured dimensions | R-002 | L5 | SOLVED | Y | Y | Y | [x] | FIX-002 |
| P095 | width/height | R-002 | L5 | SOLVED | Y | Y | Y | [x] | FIX-002 |
| P096 | decor root | R-005 | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P097 | sub-decor | R-005 | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P098 | Toolbar | — | L5 | REPRODUCED | Y | — | — | [ ] | — |
| P099 | findViewById | R-005 | L0 | RESEARCHED | — | — | — | [ ] | — |
| P100 | Activity lifecycle | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P101 | pause/resume | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P102 | Surface lifecycle | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P103 | GLThread | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P104 | render modes | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P105 | Theme.applyStyle | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P106 | TypedArray | R-008 | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P107 | style resolution | — | L5 | REPRODUCED | Y | — | — | [ ] | — |
| P108 | resource IDs | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P109 | drawable loading | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P110 | density | — | L5 | REPRODUCED | Y | — | — | [ ] | — |
| P111 | dimensions | — | L5 | REPRODUCED | Y | — | — | [ ] | — |
| P112 | colors | — | L5 | REPRODUCED | Y | — | — | [ ] | — |
| P113 | resource aliases | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P114 | configuration | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P115 | ARSC formats | R-006 | L0 | REPRODUCED | Y | — | — | [ ] | — |
| P116 | OFFSET16 | R-006 | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P117 | COMPACT | R-006 | L3 | REPRODUCED | Y | — | — | [ ] | — |
| P118 | string pools | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P119 | Looper | R-003 | L5 | SOLVED | Y | Y | Y | [x] | FIX-003 |
| P120 | Handler | R-003 | L5 | SOLVED | Y | Y | Y | [x] | FIX-003 |
| P121 | post | R-003 | L5 | SOLVED | Y | Y | Y | [x] | FIX-003 |
| P122 | postAtFrontOfQueue | R-003 | L5 | SOLVED | Y | Y | Y | [x] | FIX-003 |
| P123 | postDelayed | — | L0 | OBSERVED | — | — | — | [ ] | FIX-003 |
| P124 | callback ordering | R-003 | L5 | SOLVED | Y | Y | Y | [x] | FIX-003 |
| P125 | removeCallbacks | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P126 | thread affinity | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P127 | GL thread | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P128 | SurfaceTexture thread rules | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P129 | capture thread | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P130 | background reflection | — | L0 | OBSERVED | — | — | — | [ ] | — |
| P131 | synchronization | — | L0 | REPRODUCED | Y | — | — | [ ] | — |
| P132 | @CriticalNative | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P133 | SQLite WAL | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P134 | StrictMode | — | L0 | RESEARCHED | — | — | — | [ ] | — |
| P135 | native registration | — | L0 | OUT_OF_SCOPE | — | — | — | [ ] | — |
| P136 | AudioTrack | — | L0 | RESEARCHED | — | — | — | [ ] | — |

## Truncated range (P137..P500)

The supplied source ends before item 500: **364 slots are
`TRUNCATED_INPUT`** — no missing finding is invented (§2). Each is a
completed audit row: the range is explicitly accounted for and will be
registered only if the full source surfaces.

```text
[ ] P137..P500  TRUNCATED_INPUT × 364  (present in registry as explicit rows)
```

## Legacy checkbox view (S103-real findings)

[ ] P001 androidx.appcompat.widget.Toolbar vs android.widget.Toolbar class identity
[x] P002 Theme.obtainStyledAttributes receiver returns null TypedArray / uninitialized Th
[x] P003 main Handler/Looper internal state never materialized
[x] P004 View.getWidth returns 0 / NPE per report
[x] P005 Field.get(null) static-field semantics broken
[x] P006 Compose navigation NPE chain is downstream of one low-level root
[ ] P007 ARSC FLAG_OFFSET16/FLAG_COMPACT unhandled
[ ] P008 CompactDex support unknown
[ ] P009 Class-identity law across ALL name<->descriptor<->runtime-object conversion poin
[ ] P010 Uninitialized-framework-object law (exists + non-null + missing internal state)
[ ] P011 Full ARSC compatibility audit (flags/sparse/alignment/offset/string-pool boundar
[ ] P012 DEX family audit (versions/CDEX/quickened/header/map_list/hidden API/multidex/ju
[x] P013 View lifecycle/geometry audit (0-semantic-correct vs 0-proves-layout-never-happe
[ ] P014 Full-Android-emulator boundary (no kernel/container)
[ ] P015 Full-JVM boundary (OpenJDK/libcore borrowable semantics)
[ ] P016 Skia/Cairo graphics boundary
[ ] P017 Handler.postAtFrontOfQueue claimed as root cause
[x] P018 View.getWidth 'NPE' diagnosis
[ ] P019 EGL_BAD_ALLOC
[ ] P020 Surface abandoned
[ ] P021 DEVICE_LOST
[ ] P022 surfaceless context
[ ] P023 glFramebufferTexture2D
[ ] P024 BitmapFactory OOM
[ ] P025 EGL_CONTEXT_LOST
[ ] P026 preserve context on pause
[ ] P027 GraphicBuffer allocation
[ ] P028 Skia allocation
[ ] P029 ETC1
[ ] P030 external textures
[ ] P031 NPOT textures
[ ] P032 glTexImage2D thread affinity
[ ] P033 RenderTexture recreation
[ ] P034 SurfaceTexture.updateTexImage
[ ] P035 glTexSubImage2D
[ ] P036 triple buffering
[ ] P037 Vsync
[ ] P038 S3TC
[ ] P039 ATC
[ ] P040 PVRTC
[ ] P041 BufferQueue
[ ] P042 fence sync
[ ] P043 EGLImage
[ ] P044 YUV
[ ] P045 sRGB
[ ] P046 texture arrays
[ ] P047 geometry/tessellation/compute shaders
[ ] P048 blending
[ ] P049 ColorFilter
[ ] P050 shaders
[ ] P051 EGL config selection
[ ] P052 EGL pbuffer
[ ] P053 swap interval
[ ] P054 sync primitives
[ ] P055 glReadPixels
[x] P056 Field.get
[x] P057 Field.set
[x] P058 Field.get(null)
[x] P059 static fields
[x] P060 instance fields
[ ] P061 final fields
[x] P062 private fields
[x] P063 inherited fields
[x] P064 getField
[x] P065 getDeclaredField
[x] P066 missing fields
[x] P067 wrong receiver
[x] P068 null receiver
[ ] P069 boxing
[ ] P070 unboxing
[x] P071 static initialization
[x] P072 field identity
[ ] P073 invoke-polymorphic
[ ] P074 invoke-custom
[ ] P075 jumbo strings
[ ] P076 method IDs
[ ] P077 field IDs
[ ] P078 type IDs
[ ] P079 string pool
[ ] P080 encoded values
[ ] P081 switch payloads
[x] P082 packed-switch
[ ] P083 sparse-switch
[ ] P084 R8 merged lambdas
[ ] P085 synthetic classes
[ ] P086 class identity
[ ] P087 check-cast
[ ] P088 instanceof
[ ] P089 method resolution
[ ] P090 field resolution
[ ] P091 ViewStub
[x] P092 layout
[x] P093 setFrame
[x] P094 measured dimensions
[x] P095 width/height
[ ] P096 decor root
[ ] P097 sub-decor
[ ] P098 Toolbar
[ ] P099 findViewById
[ ] P100 Activity lifecycle
[ ] P101 pause/resume
[ ] P102 Surface lifecycle
[ ] P103 GLThread
[ ] P104 render modes
[ ] P105 Theme.applyStyle
[ ] P106 TypedArray
[ ] P107 style resolution
[ ] P108 resource IDs
[ ] P109 drawable loading
[ ] P110 density
[ ] P111 dimensions
[ ] P112 colors
[ ] P113 resource aliases
[ ] P114 configuration
[ ] P115 ARSC formats
[ ] P116 OFFSET16
[ ] P117 COMPACT
[ ] P118 string pools
[x] P119 Looper
[x] P120 Handler
[x] P121 post
[x] P122 postAtFrontOfQueue
[ ] P123 postDelayed
[x] P124 callback ordering
[ ] P125 removeCallbacks
[ ] P126 thread affinity
[ ] P127 GL thread
[ ] P128 SurfaceTexture thread rules
[ ] P129 capture thread
[ ] P130 background reflection
[ ] P131 synchronization
[ ] P132 @CriticalNative
[ ] P133 SQLite WAL
[ ] P134 StrictMode
[ ] P135 native registration
[ ] P136 AudioTrack

