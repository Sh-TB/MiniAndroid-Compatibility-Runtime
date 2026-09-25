# R500 EXHAUSTIVE AUDIT — CANONICAL LEDGER

Input: claimed 500 / recoverable 136 / truncated 364 (INPUT_TRUNCATED — see docs/audit/input_inventory.md)

Counts by status: OBSERVED=19, OUT_OF_SCOPE=20, REGRESSION_TESTED=30, REJECTED=4, REPO_SUPPORTED=12, REPRODUCED=30, RESEARCHED=20, SOURCE_SUPPORTED=1

| ID | src | domain | item | status | level | cluster | evidence |
|---|---|---|---|---|---|---|---|
| R500-001 | U-001 | DEX/class-identity | androidx.appcompat.widget.Toolbar vs android.widget.Toolbar class identity | REPRODUCED | L3 | ROOT-CLASS-IDENTITY | docs/s103/S103_MAXEXT_EVIDENCE.md#u-001 (3/3 runs, real descriptor + instanceof TRUE + check-cast + ToolbarWidgetWrapper on view 232); first divergence (decor linkage) REPRODUCED; Toolbar slice remains L5 (S101) |
| R500-002 | U-002 | theme/resources | Theme.obtainStyledAttributes receiver returns null TypedArray / uninitialized Theme | REGRESSION_TESTED | L5 | ROOT-THEME-PRODUCER | docs/s103/S103_MAXEXT_EVIDENCE.md#u-002 (F-NEW-175 theme-backed values consumed in fresh ballbreak; S101 law holds) |
| R500-003 | U-003 | threads/looper | main Handler/Looper internal state never materialized | REGRESSION_TESTED | L5 | ROOT-PFQ-ORDER | docs/s103/S103_MAXEXT_EVIDENCE.md#u-003 (3/3: main Looper + Handler materialize; posted AND front-posted runnables EXECUTE; stale no-op comment corrected) |
| R500-004 | U-004 | view | View.getWidth returns 0 / NPE per report | REGRESSION_TESTED | L5 | ROOT-VIEW-FRAME | docs/s103/S103_MAXEXT_EVIDENCE.md#u-004 (W3 layout(10,20,210,120) -> w=0 h=0; W1 pre-layout 0 is CORRECT semantics; FL-005 NPE diagnosis DISPROVEN) |
| R500-005 | U-005 | reflection | Field.get(null) static-field semantics broken | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | docs/s103/S103_MAXEXT_EVIDENCE.md#u-005 (maxext_probe fixture, 3/3 deterministic) |
| R500-006 | U-006 | compose/coroutines | Compose navigation NPE chain is downstream of one low-level root | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | docs/s103/S103_MAXEXT_EVIDENCE.md#u-006 (solitaire APK dex disassembly = primary evidence; 30 static INSTANCE fields, 1 selector field) |
| R500-007 | U-007 | resources/ARSC | ARSC FLAG_OFFSET16/FLAG_COMPACT unhandled | REPRODUCED | L2 | ROOT-ARSC-ENCODING | docs/s103/S103_MAXEXT_EVIDENCE.md#u-007 (AOSP ResourceTypes.h pinned; scanner validated on ballbreak 152 types; corpus 0/54 APKs use any flag); latent: SOURCE_SUPPORTED + CORPUS_UNCONFIRMED (0/54) |
| R500-008 | U-008 | DEX/CDEX | CompactDex support unknown | REPRODUCED | L3 | - | docs/s103/S103_MAXEXT_EVIDENCE.md#u-008 (synthetic cdex001 fixture; corpus 119/119 standard magic; jumbo 0x1b x3,617 clean; invoke-polymorphic/custom 0) |
| R500-009 | N-001 | DEX/class-identity | Class-identity law across ALL name<->descriptor<->runtime-object conversion points | REPRODUCED | L2 | ROOT-CLASS-IDENTITY | docs/s103/S103_MAXEXT_EVIDENCE.md#u-001 N-001 corpus (run/s103/u001_typescan.json; engine instanceof FALSE vs real TRUE, check-cast optimistic dalvik_engine.cpp:13505); REPRODUCED; dual-identity instanceof law = next wave (ROOT-005) |
| R500-010 | N-002 | theme/resources | Uninitialized-framework-object law (exists + non-null + missing internal state) | REPRODUCED | L2 | ROOT-NULL-PRODUCER | docs/s103/S103_MAXEXT_EVIDENCE.md#u-002 (top null receivers Field.get x5, MarginLayoutParams.getMarginStart x5, Object.getClass x4) |
| R500-011 | N-003 | resources/ARSC | Full ARSC compatibility audit (flags/sparse/alignment/offset/string-pool boundaries) | REPRODUCED | L2 | ROOT-ARSC-ENCODING | docs/s103/S103_MAXEXT_EVIDENCE.md#u-007 |
| R500-012 | N-004 | DEX | DEX family audit (versions/CDEX/quickened/header/map_list/hidden API/multidex/jumbo/limits) | REPRODUCED | L3 | - | docs/s103/S103_MAXEXT_EVIDENCE.md#u-008 |
| R500-013 | N-005 | view | View lifecycle/geometry audit (0-semantic-correct vs 0-proves-layout-never-happened) | REGRESSION_TESTED | L5 | ROOT-VIEW-FRAME | docs/s103/S103_MAXEXT_EVIDENCE.md#u-004 |
| R500-014 | FL-001 | architecture | Full-Android-emulator boundary (no kernel/container) | REJECTED | L1 | - | docs/s103/S103_MAXEXT_EVIDENCE.md (boundary extraction only) |
| R500-015 | FL-002 | architecture | Full-JVM boundary (OpenJDK/libcore borrowable semantics) | REJECTED | L1 | - | docs/s103/S103_MAXEXT_EVIDENCE.md (boundary extraction only) |
| R500-016 | FL-003 | architecture | Skia/Cairo graphics boundary | REJECTED | L1 | - | miniandroid/src/renderer/software_renderer.cpp; miniandroid/src/gles/pgl_backend.cpp |
| R500-017 | FL-004 | threads/looper | Handler.postAtFrontOfQueue claimed as root cause | REJECTED | L3 | ROOT-PFQ-ORDER | docs/s103/S103_MAXEXT_EVIDENCE.md#u-003 (H6 order-final=-PF deterministic 2/2) |
| R500-018 | FL-005 | view | View.getWidth 'NPE' diagnosis | REGRESSION_TESTED | L5 | ROOT-VIEW-FRAME | docs/s103/S103_MAXEXT_EVIDENCE.md#u-004 |
| R500-019 | directive-§8 | graphics | EGL_BAD_ALLOC | REPO_SUPPORTED | L2 | ROOT-EGL-SHADOW | miniandroid/src/framework/gl_surface_shadow.cpp dispatch_egl: eglGetError always returns 0x3000 EGL_SUCCESS; no failure model exists |
| R500-020 | directive-§8 | graphics | Surface abandoned | OUT_OF_SCOPE | L0 | - | miniandroid/src/gles/pgl_backend.h (single software context); no BufferQueue symbols in engine |
| R500-021 | directive-§8 | graphics | DEVICE_LOST | OUT_OF_SCOPE | L0 | - | rg vulkan miniandroid/src: only exp004/exp005/exp007 mentions in unrelated probes; no VK headers, no loader |
| R500-022 | directive-§8 | graphics | surfaceless context | OUT_OF_SCOPE | L0 | ROOT-EGL-SHADOW | dispatch_egl: eglMakeCurrent/eglSwapBuffers answered true unconditionally |
| R500-023 | directive-§8 | graphics | glFramebufferTexture2D | REPO_SUPPORTED | L2 | ROOT-GL-BRIDGE | rg '"glFramebufferTexture2D"' miniandroid/src/gles miniandroid/src/framework: 0 dispatch sites (25-method bridge table lacks it); PortableGL itself implements FBOs at C level |
| R500-024 | directive-§8 | graphics | BitmapFactory OOM | RESEARCHED | L0 | - | OutOfMemoryError exists in dalvik_engine.cpp; OOM guards in application_runtime.cpp/execution_engine.cpp; decode path S95 density law |
| R500-025 | directive-§8 | graphics | EGL_CONTEXT_LOST | OUT_OF_SCOPE | L0 | ROOT-EGL-SHADOW | dispatch_egl eglGetError always EGL_SUCCESS; single PGL context process-wide (pgl_backend.h) |
| R500-026 | directive-§8 | graphics | preserve context on pause | OBSERVED | L0 | - | gl_surface_shadow.cpp setPreserveEGLContextOnPause accepted as plumbing (glPreserve); single context is never destroyed on pause, so the SEMANTIC (context survives) holds in the software model |
| R500-027 | directive-§8 | graphics | GraphicBuffer allocation | OUT_OF_SCOPE | L0 | - | No GraphicBuffer/ANativeWindow symbols in engine |
| R500-028 | directive-§8 | graphics | Skia allocation | OUT_OF_SCOPE | L0 | - | miniandroid/src/renderer/software_renderer.cpp is the owned rasterizer (FL-003 boundary) |
| R500-029 | directive-§8 | graphics | ETC1 | REPO_SUPPORTED | L2 | ROOT-TEX-COMPRESSION | rg ETC1 miniandroid/src: 0 hits. No ETC1 decode, no GL compressed-teximage dispatch |
| R500-030 | directive-§8 | graphics | external textures | OUT_OF_SCOPE | L0 | - | rg SurfaceTexture miniandroid/src: 0 hits |
| R500-031 | directive-§8 | graphics | NPOT textures | SOURCE_SUPPORTED | L1 | - | pgl_backend.cpp comment: PortableGL GL 3.x core semantics; core GL has no NPOT restriction |
| R500-032 | directive-§8 | graphics | glTexImage2D thread affinity | OUT_OF_SCOPE | L0 | - | std::thread only in main.cpp; rg '"glTexImage2D"' gles/framework: 0 dispatch sites |
| R500-033 | directive-§8 | graphics | RenderTexture recreation | OUT_OF_SCOPE | L0 | ROOT-GL-BRIDGE | No FBO dispatch (R500-023); single context never lost |
| R500-034 | directive-§8 | graphics | SurfaceTexture.updateTexImage | OUT_OF_SCOPE | L0 | - | rg SurfaceTexture: 0 hits |
| R500-035 | directive-§8 | graphics | glTexSubImage2D | REPO_SUPPORTED | L2 | ROOT-GL-BRIDGE | rg '"glTexSubImage2D"': 0 dispatch sites; PortableGL implements it at C level |
| R500-036 | directive-§8 | graphics | triple buffering | OUT_OF_SCOPE | L0 | - | pgl_backend.h: single backbuf_, frame_end presents it |
| R500-037 | directive-§8 | graphics | Vsync | OBSERVED | L0 | - | choreographer_shadow.cpp + execution_engine vsync hooks; S95 REFUTED frozen-animation claim: engine postDelayed/invalidation/frame machinery proven correct |
| R500-038 | directive-§8 | graphics | S3TC | REPO_SUPPORTED | L2 | ROOT-TEX-COMPRESSION | rg S3TC/DXT: 0 hits in engine |
| R500-039 | directive-§8 | graphics | ATC | REPO_SUPPORTED | L2 | ROOT-TEX-COMPRESSION | rg ATC: 0 hits |
| R500-040 | directive-§8 | graphics | PVRTC | REPO_SUPPORTED | L2 | ROOT-TEX-COMPRESSION | rg PVRTC: 0 hits |
| R500-041 | directive-§8 | graphics | BufferQueue | OUT_OF_SCOPE | L0 | - | No BufferQueue symbols |
| R500-042 | directive-§8 | graphics | fence sync | OUT_OF_SCOPE | L0 | - | rg FenceSync/eglCreateSyncKHR: 0 hits |
| R500-043 | directive-§8 | graphics | EGLImage | OUT_OF_SCOPE | L0 | - | rg EGLImage: 0 hits |
| R500-044 | directive-§8 | graphics | YUV | OUT_OF_SCOPE | L0 | - | No YUV conversion in engine; media.audio PARTIAL, video DECLARED |
| R500-045 | directive-§8 | graphics | sRGB | OBSERVED | L0 | - | S95 density/color laws: WRONG_COLOR eliminated on 3/4 mapped titles (docs/GRAPHICS_SOURCE_ROADMAP.md) |
| R500-046 | directive-§8 | graphics | texture arrays | REPO_SUPPORTED | L2 | ROOT-GL-BRIDGE | rg glTexStorage3D/glTexImage3D: 0 hits |
| R500-047 | directive-§8 | graphics | geometry/tessellation/compute shaders | REPO_SUPPORTED | L2 | ROOT-GLSL | GLES20 bridge only; PGL executes C-function shaders, GLSL stored verbatim (GLES_BACKEND_COMPARISON_010.md) |
| R500-048 | directive-§8 | graphics | blending | OBSERVED | L0 | - | glBlendFunc dispatched (gles20_bridge.cpp); software renderer alpha compositing exercised by corpus screenshots |
| R500-049 | directive-§8 | graphics | ColorFilter | RESEARCHED | L0 | - | ColorFilter present in android_shadows.cpp |
| R500-050 | directive-§8 | graphics | shaders | RESEARCHED | L0 | - | No Paint-Shader dispatch found in framework shadows (rg Shader -> only gles bridge) |
| R500-051 | directive-§8 | graphics | EGL config selection | REPO_SUPPORTED | L2 | ROOT-EGL-SHADOW | gl_surface_shadow.cpp: eglChooseConfig best-effort stores ONE canonical config object into configs[0]; no attribute matching |
| R500-052 | directive-§8 | graphics | EGL pbuffer | REPO_SUPPORTED | L2 | ROOT-EGL-SHADOW | dispatch_egl has no pbuffer branch (window surface only) |
| R500-053 | directive-§8 | graphics | swap interval | OUT_OF_SCOPE | L0 | ROOT-EGL-SHADOW | No eglSwapInterval in dispatch_egl |
| R500-054 | directive-§8 | graphics | sync primitives | OUT_OF_SCOPE | L0 | - | Same evidence as R500-042 |
| R500-055 | directive-§8 | graphics | glReadPixels | REPO_SUPPORTED | L2 | ROOT-GL-BRIDGE | rg '"glReadPixels"': 0 dispatch sites; PortableGL implements at C level |
| R500-056 | directive-§9 | reflection | Field.get | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R1-R4: null-object gets return defaults instead of NPE (docs/s103/S103_MAXEXT_EVIDENCE.md#u-005); FIXED: Field.get static/instance identity + NPE law (dalvik_engine.cpp R500 block); probe R1-R5 correct 3/3 |
| R500-057 | directive-§9 | reflection | Field.set | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R8: set is a silent no-op on some field kinds; FIXED: Field.set unbox+store-through (probe R8 after-set=43 via direct sget) |
| R500-058 | directive-§9 | reflection | Field.get(null) | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R1-R4 cover the null-receiver static case |
| R500-059 | directive-§9 | reflection | static fields | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R11: boxed static reads return pre-init defaults |
| R500-060 | directive-§9 | reflection | instance fields | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 ROOT LAW: FIELD IDENTITY FRAGMENTATION — reflection keys != interpreter sput/iput keys |
| R500-061 | directive-§9 | reflection | final fields | RESEARCHED | L0 | - | UNVERIFIED at runtime; libcore law: final instance writes blocked without access override |
| R500-062 | directive-§9 | reflection | private fields | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | getDeclaredField always succeeds today (allocates Field for nonexistent names) — code-level |
| R500-063 | directive-§9 | reflection | inherited fields | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103: getField NOT implemented -> default stub null -> Field.get NPE killing 5 real titles |
| R500-064 | directive-§9 | reflection | getField | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | Same as R500-063; top fan-out slice of the 30/61 null-producer family; FIXED: Class.getField superclass walk (probe R7 inherited=99); framework declared-field surface added: Build.VERSION.SDK_INT getField->Field->get=34 on chess/dooz/mancala/memory/mentalmath (fresh census logs) |
| R500-065 | directive-§9 | reflection | getDeclaredField | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R6: no NSFE — getDeclaredField ALWAYS succeeds; FIXED: getDeclaredField NSFE for dex-known classes (probe R6) |
| R500-066 | directive-§9 | reflection | missing fields | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R7: getField null -> NPE at .get (the exact census crash) |
| R500-067 | directive-§9 | reflection | wrong receiver | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R5: no NPE/IAE on null receiver for instance field get; FIXED: receiver-class IAE law (probe R4 = correct IAE) |
| R500-068 | directive-§9 | reflection | null receiver | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | Same as R500-067 |
| R500-069 | directive-§9 | reflection | boxing | OBSERVED | L0 | - | R11 involves boxed reads; boxing machinery exists engine-wide |
| R500-070 | directive-§9 | reflection | unboxing | OBSERVED | L0 | - | UNVERIFIED |
| R500-071 | directive-§9 | reflection | static initialization | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 probe R11: reads pre-init default |
| R500-072 | directive-§9 | reflection | field identity | REGRESSION_TESTED | L5 | ROOT-REFLECTION-FIELD-IDENTITY | S103 ROOT LAW statement + 8 probe divergences; FIXED: canonical field key; R8 identity proof: reflection set -> sget sees 43; battery 105/105; framework declared-field surface added: Build.VERSION.SDK_INT getField->Field->get=34 on chess/dooz/mancala/memory/mentalmath (fresh census logs) |
| R500-073 | directive-§10 | DEX | invoke-polymorphic | REPRODUCED | L3 | - | Interpreter lacks it; corpus 0 sites (R8-desugared) — docs/s103/S103_MAXEXT_EVIDENCE.md#u-008 |
| R500-074 | directive-§10 | DEX | invoke-custom | REPRODUCED | L3 | - | Same evidence as R500-073 |
| R500-075 | directive-§10 | DEX | jumbo strings | REPRODUCED | L3 | - | S103: 3,617 jumbo sites walked clean across corpus |
| R500-076 | directive-§10 | DEX | method IDs | REPRODUCED | L3 | - | S103: max method ids 64,422 across corpus — u32-safe |
| R500-077 | directive-§10 | DEX | field IDs | RESEARCHED | L0 | ROOT-REFLECTION-FIELD-IDENTITY | Table walk clean; SEMANTIC divergence lives in key usage (R500-072); FIXED via ROOT-REFLECTION-FIELD-IDENTITY |
| R500-078 | directive-§10 | DEX | type IDs | RESEARCHED | L0 | - | Class resolver verified by 61-title corpus; descriptor edge cases tracked in R500-086 |
| R500-079 | directive-§10 | DEX | string pool | RESEARCHED | L0 | - | Working corpus-wide; boundary fuzz not done this wave |
| R500-080 | directive-§10 | DEX | encoded values | RESEARCHED | L0 | - | Working (annotations/static values consumed corpus-wide) |
| R500-081 | directive-§10 | DEX | switch payloads | RESEARCHED | L0 | - | Both implemented in dalvik_engine |
| R500-082 | directive-§10 | DEX | packed-switch | REPRODUCED | L3 | ROOT-REFLECTION-FIELD-IDENTITY | Implemented; the WRONG-BRANCH divergence in solitaire is the SELECTOR FIELD read (field identity), not the opcode — docs/s103#u-006; FIXED via ROOT-REFLECTION-FIELD-IDENTITY (selector reads now hit canonical keys) |
| R500-083 | directive-§10 | DEX | sparse-switch | RESEARCHED | L0 | - | Implemented in dalvik_engine |
| R500-084 | directive-§10 | DEX | R8 merged lambdas | REPRODUCED | L3 | ROOT-REFLECTION-FIELD-IDENTITY | solitaire: LocalDensity$1 with 30 static INSTANCE fields, 1 selector field executes WRONG BRANCH; FIXED via ROOT-REFLECTION-FIELD-IDENTITY |
| R500-085 | directive-§10 | DEX | synthetic classes | RESEARCHED | L0 | - | Compose titles reach synthetic classes (S102 solitaire chain) |
| R500-086 | directive-§10 | DEX | class identity | REPRODUCED | L3 | ROOT-CLASS-IDENTITY | ROOT-CLASS-IDENTITY: S103 U-001 + N-001 corpus 22/59 |
| R500-087 | directive-§10 | DEX | check-cast | REPRODUCED | L2 | ROOT-CLASS-IDENTITY | check-cast deliberately optimistic (dalvik_engine.cpp:13505) — inconsistent with instanceof |
| R500-088 | directive-§10 | DEX | instanceof | REPRODUCED | L2 | ROOT-CLASS-IDENTITY | engine is_subclass_of answers FALSE for inflated AppCompat* views (S103 code-level + corpus sites) |
| R500-089 | directive-§10 | DEX | method resolution | REPRODUCED | L5 | - | S102 d963ff1e MULTIDEX-INTERFACE-CLOSURE law fixed secondary-dex interface index (10,002 classes invisible) |
| R500-090 | directive-§10 | DEX | field resolution | REPRODUCED | L3 | ROOT-REFLECTION-FIELD-IDENTITY | Resolution works; IDENTITY diverges (R500-072); FIXED via ROOT-REFLECTION-FIELD-IDENTITY |
| R500-091 | directive-§11 | view | ViewStub | RESEARCHED | L0 | - | ViewStub referenced in layout_inflater.cpp + android_shadows.cpp |
| R500-092 | directive-§11 | view | layout | REGRESSION_TESTED | L5 | ROOT-VIEW-FRAME | S103 W3: layout(10,20,210,120) -> getWidth()=0; FIXED: layout/setFrame materialize frame via shared ViewNode store (probe W3 w=200 h=100) |
| R500-093 | directive-§11 | view | setFrame | REGRESSION_TESTED | L5 | ROOT-VIEW-FRAME | Same W3 probe: frame never materialized for direct-layout views; FIXED: same law (W4 gone-layout w=50) |
| R500-094 | directive-§11 | view | measured dimensions | REGRESSION_TESTED | L5 | ROOT-VIEW-FRAME | S103 W2: measuredWidth not stored; FIXED: default onMeasure law + MeasureSpec EXACTLY/AT_MOST constant seeding (probe W2 mw=200) |
| R500-095 | directive-§11 | view | width/height | REGRESSION_TESTED | L5 | ROOT-VIEW-FRAME | S103 U-004: pre-layout 0 is CORRECT; post-layout 0 is the divergence; FIXED: getWidth=mRight-mLeft via frame store; W1/W2 keep honest 0 pre-layout |
| R500-096 | directive-§11 | view | decor root | REPRODUCED | L3 | ROOT-DECOR-LINKAGE | S103 U-001 NEW first divergence: WindowDecorActionBar.init findViewById on root=70 NOT FOUND while receiver=cf subtree HAS the Toolbar |
| R500-097 | directive-§11 | view | sub-decor | REPRODUCED | L3 | ROOT-DECOR-LINKAGE | Same trace: decor_content_parent 0x7f080054 not found from root |
| R500-098 | directive-§11 | view | Toolbar | REPRODUCED | L5 | - | S101 LAW 1 fixed + S103 3/3 positive proof (instanceof TRUE, check-cast OK, ToolbarWidgetWrapper constructed) |
| R500-099 | directive-§11 | view | findViewById | RESEARCHED | L0 | ROOT-DECOR-LINKAGE | Works within subtrees (receiver=cf finds view 232); root-scope linkage is ROOT-DECOR-LINKAGE |
| R500-100 | directive-§11 | view | Activity lifecycle | OBSERVED | L0 | - | lifecycle_controller.cpp; corpus-wide 61-title census passes lifecycle-bound apps |
| R500-101 | directive-§11 | view | pause/resume | OBSERVED | L0 | - | gl_surface_shadow handles lifecycle plumbing; games resume across frames |
| R500-102 | directive-§11 | view | Surface lifecycle | OBSERVED | L0 | - | GLSurfaceView shadow drives onDrawFrame directly; no destruction path |
| R500-103 | directive-§11 | view | GLThread | OBSERVED | L0 | - | gl_surface_shadow queueEvent (glQueuedEvent) + render loop; single-threaded engine |
| R500-104 | directive-§11 | view | render modes | OBSERVED | L0 | - | glRenderMode handled in gl_surface_shadow.cpp |
| R500-105 | directive-§12 | theme/resources | Theme.applyStyle | RESEARCHED | L0 | - | No applyStyle branch found in engine shadows (rg 'applyStyle': 0 hits) — likely default-stub |
| R500-106 | directive-§12 | theme/resources | TypedArray | REPRODUCED | L3 | ROOT-THEME-PRODUCER | S101 LAW 2 + S103 fresh ballbreak (F-NEW-175 theme-backed values consumed) |
| R500-107 | directive-§12 | theme/resources | style resolution | REPRODUCED | L5 | - | S100 THEME-GATE: max_parent_hops 8->32, ISE family gone |
| R500-108 | directive-§12 | theme/resources | resource IDs | OBSERVED | L0 | - | Corpus-wide resource resolution working (61 titles) |
| R500-109 | directive-§12 | theme/resources | drawable loading | OBSERVED | L0 | - | S95 vector/adaptive laws; bitmap decode PNG/JPEG/WebP/GIF |
| R500-110 | directive-§12 | theme/resources | density | REPRODUCED | L5 | - | S95 density law wired into decode_image_bytes; WRONG_COLOR eliminated on 3/4 titles |
| R500-111 | directive-§12 | theme/resources | dimensions | REPRODUCED | L5 | - | S101 getDimensionPixelSize NPE site fixed; theme-backed dims consumed |
| R500-112 | directive-§12 | theme/resources | colors | REPRODUCED | L5 | - | S95 DEFTHEME-1/TXTCLR-1/ICONBTN-1 laws |
| R500-113 | directive-§12 | theme/resources | resource aliases | RESEARCHED | L0 | - | UNVERIFIED — alias handling not audited in arsc_parser this wave |
| R500-114 | directive-§12 | theme/resources | configuration | OBSERVED | L0 | - | Qualifiers supported per capability registry framework.resources IMPLEMENTED + corpus evidence |
| R500-115 | directive-§12 | theme/resources | ARSC formats | REPRODUCED | L0 | ROOT-ARSC-ENCODING | S103 scanner validated on ballbreak 152 types; FLAG_SPARSE supported |
| R500-116 | directive-§12 | theme/resources | OFFSET16 | REPRODUCED | L3 | ROOT-ARSC-ENCODING | U-007: unhandled -> u16 table misread as u32; corpus 0/54 exposure |
| R500-117 | directive-§12 | theme/resources | COMPACT | REPRODUCED | L3 | ROOT-ARSC-ENCODING | U-007: unhandled; corpus 0/54 exposure |
| R500-118 | directive-§12 | theme/resources | string pools | RESEARCHED | L0 | - | Working corpus-wide; boundary fuzz not performed |
| R500-119 | directive-§13 | threads/looper | Looper | REGRESSION_TESTED | L5 | ROOT-PFQ-ORDER | S103 U-003: main Looper + Handler materialize (3/3) |
| R500-120 | directive-§13 | threads/looper | Handler | REGRESSION_TESTED | L5 | ROOT-PFQ-ORDER | Same |
| R500-121 | directive-§13 | threads/looper | post | REGRESSION_TESTED | L5 | ROOT-PFQ-ORDER | S103: posted runnables EXECUTE; stale 'no-op' comment corrected |
| R500-122 | directive-§13 | threads/looper | postAtFrontOfQueue | REGRESSION_TESTED | L5 | ROOT-PFQ-ORDER | S103 H6: order-final='-PF' -> tail enqueue, deterministic 2/2 — ORDER diverges from ART; FIXED: enqueue_front when=0 law + front-first tiebreak (probe H6 -FP 3/3) |
| R500-123 | directive-§13 | threads/looper | postDelayed | OBSERVED | L0 | - | S95: animation machinery proven correct (frozen claim REFUTED) |
| R500-124 | directive-§13 | threads/looper | callback ordering | REGRESSION_TESTED | L5 | ROOT-PFQ-ORDER | Same as R500-122 |
| R500-125 | directive-§13 | threads/looper | removeCallbacks | RESEARCHED | L0 | - | removeCallbacks present in android_shadows + choreographer_shadow |
| R500-126 | directive-§13 | threads/looper | thread affinity | OBSERVED | L0 | - | std::thread only in main.cpp; documented single-thread subset |
| R500-127 | directive-§13 | threads/looper | GL thread | OBSERVED | L0 | - | Same as R500-103 |
| R500-128 | directive-§13 | threads/looper | SurfaceTexture thread rules | OUT_OF_SCOPE | L0 | - | rg SurfaceTexture: 0 hits |
| R500-129 | directive-§13 | threads/looper | capture thread | OBSERVED | L0 | - | Capture runs synchronous in the engine loop; 3-run byte-identical evidence across S101-S103 |
| R500-130 | directive-§13 | threads/looper | background reflection | OBSERVED | L0 | - | Single-threaded engine: no background threads exist |
| R500-131 | directive-§13 | threads/looper | synchronization | REPRODUCED | L0 | - | S102 atomic_shadow laws + LockSupport ticket #352; atomic family tested |
| R500-132 | directive-§14 | JNI | @CriticalNative | OUT_OF_SCOPE | L0 | - | jni_bridge.h: NativeImplType.HOST_COMPATIBILITY_STUB model; no dlopen of real .so |
| R500-133 | directive-§14 | storage/SQLite | SQLite WAL | RESEARCHED | L0 | - | sqlite_shadow.cpp: wal_requested RECORDED, journal mode intentionally default (byte-determinism comment) |
| R500-134 | directive-§14 | storage/StrictMode | StrictMode | RESEARCHED | L0 | - | 1 mention in dalvik_engine.cpp — likely stub |
| R500-135 | directive-§14 | JNI | native registration | OUT_OF_SCOPE | L0 | - | jni_bridge.h HOST_COMPATIBILITY_STUB; native.jni capability = DECLARED |
| R500-136 | directive-§14 | audio | AudioTrack | RESEARCHED | L0 | - | audio_engine = SoundPool/MediaPlayer (media.audio PARTIAL); no AudioTrack shadow found |
