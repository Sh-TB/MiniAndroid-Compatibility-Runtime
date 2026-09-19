# S67 · FOUNDATION HARDENING — RECON (Wave 0, read-only, no code changes)

Campaign law (user directive): BREADTH paused. No new apps. No new spotlight.
Goal: `BASE CONTRACT → UPSTREAM LAW → MINIANDROID IMPLEMENTATION → MICRO TEST → REAL APK
→ PIXEL/STATE/TRACE PROOF → REGRESSION → ONLY THEN IMPLEMENTATION`.

Snapshot at campaign start:

| Item | Value |
|---|---|
| HEAD | `289e33d3` (S66 visual forensics, F-120 button-gravity law) |
| origin/main | `289e33d3` — **ahead=0, push debt ZERO** |
| dirty tree | 0 files |
| battery | 92/94 + EXT-01/02 environmental |
| engine build | rebuilt this session from tracked Makefile → `miniandroid/build/miniandroid` |
| toolchain | restored via `scripts/build/bootstrap_toolchain.sh` (aapt2/ecj/r8/android-34) |
| registry | 372 (R-NEW-388 latest) |

## 1. Real architecture graph (from live build sources, Makefile:42-57)

The shipped binary compiles exactly these subsystem files (view_renderer.cpp and
real_layout.cpp are NOT in the build; api_dispatcher.cpp IS in the build but is a
legacy EXP-036 stub, not the live dispatch path — the live path is
dalvik_engine.cpp + shadow_registry):

```text
APK
 ↓ apk/apk_parser.cpp            (ZIP central-directory law, cached extraction)
 ↓ apk/manifest_reader.cpp       (binary AXML + plain-XML fallback)
 ↓ resources/string_pool.cpp
 ↓ resources/arsc_parser.cpp     (packages/types/configs, ResTable_config port)
 ↓ resources/axml_parser.cpp     (attribute types)
 ↓ resources/resource_runtime.cpp(styles/theme/windowBackground)
 ↓ resources/layout_inflater.cpp (AXML→ViewNode tree, measure_layout: bottom-up
 │                                children-first + AOSP getChildMeasureSpec port,
 │                                LL weight 2-pass, RL edge solver→replay, FL gravity)
 ↓ dex/dex_parser.cpp            (classes/fields/methods/code)
 ↓ dex/class_resolver.cpp        (class/superclass/interface/method/field resolution)
 ↓ dex/dex_interpreter_batch.cpp (batch fetch/decode helpers)
 ↓ dex/dalvik_engine.cpp         (30,390 lines: interpreter, opcode families via
 │                                macros, API shadows, F-029 reflection law, F-118
 │                                activity ctor law, startActivity, Handler/Looper)
 ↓ framework/shadow_registry.cpp (dispatch loop; CanvasShadow registered at :277)
 ↓ framework/canvas_shadow.cpp   (record-then-replay DrawOps; translation-only state)
 ↓ framework/touch_dispatcher.cpp(MotionEvent DOWN/MOVE/UP/CANCEL, hit-test,
 │                                onClick via real DEX, CheckForLongPress)
 ↓ renderer/software_renderer.cpp(SoftwareCanvas→FrameBuffer RGBA stride=width,
 │                                blend src-over alpha→255; PNGWriter=libpng RGB)
 ↓ fonts/text_shaper.cpp         (FriBidi→HarfBuzz→FreeType, NotoColorEmoji CBDT)
 ↓ runtime/execution_engine.cpp  (stage_render_frame ViewShadow walk; stage_capture_
                                  output: pump frames→PNG/PPM 1:1 identity)
```

State/input path:

```text
Input file/click-test
 → MotionEvent (touch_dispatcher.cpp)
 → hit test on node->x/y (execution_engine.cpp:4028)
 → child routing / onTouchListener-first law (li.mOnTouchListener, :46-48)
 → ACTION_UP → performClick → real DEX onClick (touch_dispatcher.cpp:348)
 → app state mutation (DEX heap)
 → ViewShadow fields (setText etc.)
 → next frame: stage_render_frame re-measures whole tree iff rt.loaded()||layout_dirty
    (execution_engine.cpp:1790-1807; invalidate/requestLayout = handled_void no-ops
     android_shadows.cpp:3300; layout_dirty raised only by tree mutations)
 → framebuffer → PNG
```

## 2. Subsystem census (evidence-backed, file:line in the matrices)

Renderer: record/replay canvas, translation-only transform, no clip stack, no matrix,
no saveLayer. TextView text = full shaping stack; Canvas text = 8x16 ASCII bitmap
(non-ASCII silently blank). Capture = libpng RGB (alpha dropped), proven faithful S66.

Layout: 3-stage (parse→field→measure/layout) coverage broad; LL weights AOSP-exact;
RL solver→replay closed by b60f753c (R-NEW-388 as phrased REFUTED; residual
programmatic-RL + render-without-measure paths). No ScrollView scrolling. No setX /
AbsoluteLayout x-y. INVISIBLE(4) drawn.

Resources: ARSC multi-package/type/config OK; ?attr not at inflate; @android: not
resolvable; dimen seeding unconverted; getDimensionPixelSize 24px fallback; manifest
label/icon gaps; view-level android:theme absent.

DEX runtime: 95 distinct Opcode:: sites + family macros (ARITH_2ADDR/23X/LIT8/LIT16,
ARRAY_GET/PUT x7, IF/CMPL, etc.); exceptions via exception_system (try/catch tables,
propagation); reflection F-029 law; arrays incl. primitive/multi-dim (F-119).

Images: libpng (palette/gray/alpha/Adam7), libwebp (gated), libjpeg, rlottie;
silent non-PNG-magic drop at execution_engine.cpp:2322-2373; BitmapFactory.* absent;
assets images not decodable.

Dead/trap code: view_renderer.cpp (won't compile vs ViewNode), real_layout.cpp
(orphan), api_dispatcher.cpp (EXP-036 stub — grep trap), exp124 build script stale.

Build drift: CMake exp088_a4 target links pre-libpng lib set; Makefile authoritative.
