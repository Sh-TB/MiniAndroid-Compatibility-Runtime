# SECONDARY CAMPAIGN PHASE V9 — REUSABLE LIBRARY AUDIT

Campaign: SECONDARY (white/black/incomplete render roots) · Date: 2026-10-02
Base: HEAD 67064b95 (FINAL CAMPAIGN phases 5-20) · Role: Primary Coder
Directive: BEFORE writing new rendering/codec/resource code, compare the
current implementation against the 7 candidate library families, with the
8 mandated criteria per candidate. Do NOT replace Android semantics with a
generic library (V9 gate law).

---

## §0 Existing integration baseline (measured, not assumed)

| Component | Library | State | Evidence |
|---|---|---|---|
| WebView JS | QuickJS (third_party/quickjs) | **INTEGRATED, REAL** | P1-11/F-NEW-188: evaluateJavascript routes into WebViewEngine (QuickJS ES2020); S133 live z.ai JS-DATA PASS |
| PNG encode | own PNGWriter over zlib compress2 | INTEGRATED | EXP-086 Phase 3; every screenshot |
| PNG/JPEG decode | stb_image (third_party/stb) | INTEGRATED | software_renderer, gif_decoder, webview_engine |
| WebP decode | MINIANDROID_HAVE_WEBP build flag | INTEGRATED | Makefile line 84 build |
| 2D raster substrate | own FrameBuffer/SoftwareCanvas (~1.4k LOC) | INTEGRATED | authoritative render path (V8 audit: cmd_run → ExecutionEngine only) |
| Text shaping | FreeType + own TextShaper | INTEGRATED | fonts/text_shaper.cpp |
| GL | PortableGL (third_party/portablegl) | INTEGRATED | gles/pgl_backend |
| GIF | own gif_decoder.cpp (119 LOC) | MINIMAL | S93: 12 GIF titles need exact disposal semantics — open frontier |
| Vector | own vector_decode.cpp (949 LOC) + vector_inflater | INTEGRATED | L-S95-VECTOR-1 fixed hotdeath/bouncy real APKs |

Prior measured rejections (S132 reuse proof): **Yoga** (opencalculator
GridLayout — integration cost > native law; AOSP ConstraintLayout semantics
kept), **nanoSVG**, **FFmpeg** (RAM/size vs stb+Wuffs-class needs).

---

## §1 Candidate-by-candidate verdict (8 mandated criteria each)

### 1. Skia — 2D graphics, text, geometry, image rasterization
| Criterion | Assessment |
|---|---|
| LOC potentially removed | ~1,400 (SoftwareCanvas/FrameBuffer/BitmapFont) — but ONLY if the full Android draw-contract surface (clip stack, saveLayer, drawBitmap src/dst, drawText run shaping, state-list background draws, S68/S82/S86 draw laws) is reimplemented ON TOP of Skia anyway |
| RAM impact | +4–8 MB (Skia allocators, glyph cache defaults) |
| CPU | Neutral-to-better rasterization; but our pixel-ownership census (V1/V7) reads raw framebuffer — Skia GPU/deferred paths would break the compose-from-scratch law |
| Headless compat | Requires raster config; NDK-sized build; container bootstrap cost measured at S38 reset ≈ hours |
| License | BSD-style (skia) — OK |
| Semantic mismatch | HIGH: Android draw semantics are implemented as laws (L-S93-IMG-5 clip, S68 drawBitmap, S86 z-order); Skia is the substrate AOSP ITSELF uses, but our census/verdict layer needs deterministic from-scratch composition |
| Integration cost | 2–4 sessions (build system + census rewiring) |
| Testability | Goldens re-derived (all SHAs change) — regression cost high |
| **VERDICT** | **REJECTED (measured)** — LOC delta is small vs regression + census-law cost. Classification: REFERENCE_ONLY (law source: SkCanvas clip stack). |

### 2. libarsc / ARSCLib — resources.arsc parsing
| Criterion | Assessment |
|---|---|
| LOC potentially removed | arsc_parser.cpp + string_pool + res_config + res_id ≈ 4,800 LOC |
| RAM | Neutral |
| CPU | Neutral |
| Headless | Pure C++/Java — OK |
| License | Apache-2.0 (ARSCLib) — OK |
| Semantic mismatch | HIGH-RISK: our parser carries campaign-critical laws (ARSC-AUTHORITATIVE file-path law GOLDEN-03 §10/§11, config selection L-S94-DENSITY-1/2, theme-overlay scopes S124, framework_theme_attrs). ARSCLib models ARSC as an editor, not a runtime resolver |
| Integration cost | Java/ARSCLib = unusable headless-C++; libarsc C port = rewrite |
| Testability | headingcalc/unote/notes goldens all ride ARSC text/color laws |
| **VERDICT** | **REJECTED** — the parser IS a law carrier, not a codec. REFERENCE_ONLY. |

### 3. QuickJS — WebView JavaScript
| Criterion | Assessment |
|---|---|
| LOC potentially removed | 0 — ALREADY INTEGRATED (webview_engine) |
| RAM/CPU | measured S133: live z.ai pages run |
| Headless | Proven |
| License | MIT — OK |
| Semantic mismatch | None (ES2020 target) |
| Integration cost | Sunk; P1-11/F-NEW-188 ValueCallback contract complete |
| Testability | S133 browser wave evidence |
| **VERDICT** | **KEEP — the model reuse-first citizen.** |

### 4. Yoga — Flexbox/Compose-like layout ONLY
| Criterion | Assessment |
|---|---|
| LOC potentially removed | LinearLayout/Frame/Relative/Table/Grid/ScrollView measure laws ≈ 900 LOC of layout_inflater.cpp |
| RAM | +1–2 MB |
| CPU | Neutral |
| Headless | C — OK |
| License | MIT — OK |
| Semantic mismatch | HIGH for View-world: Yoga is flexbox, NOT Android measure/spec (EXACTLY/AT_MOST/UNSPECIFIED + weight + gravity + RelativeLayout rules + WRAP_CONTENT-with-min laws). R-NEW-438 (ConstraintLayout onMeasure incomplete-emulation law) proved the native container laws ARE the authority for library containers |
| Integration cost | S132 measured-and-rejected on opencalculator GridLayout |
| Testability | Every layout golden would shift |
| **VERDICT** | **REJECTED (measured, S132).** Android measure/layout semantics stay native. |

### 5. Lottie — Lottie animation
| Criterion | Assessment |
|---|---|
| LOC potentially removed | 0 (no Lottie runtime exists in-repo) |
| Demand | Corpus census: lottie-json assets appear in flagship families (Forkgram/WhatsApp stickers ride Lottie) |
| RAM/CPU | +2–3 MB, JSON parse cost per anim |
| Headless | C++ (rlottie) OK; license MIT/Apache-2 dual |
| Semantic mismatch | Low for its scope (it is a renderer of its own format) — but zero current pixel path consumes it; entry point = drawable family |
| Integration cost | 1 session to PARK a decoded-frame provider into the BitmapStore provenance path (V5 IMAGE_DIRECT_PIXELS) |
| Testability | Needs a corpus APK with a reachable Lottie drawable |
| **VERDICT** | **PENDING (demand-gated)** — first corpus face with a reachable Lottie drawable triggers rlottie → BitmapStore integration. No speculative code. |

### 6. existing GIF/WebP/PNG libraries (Wuffs / stb / libwebp)
| Criterion | Assessment |
|---|---|
| LOC potentially removed | gif_decoder.cpp 119 LOC → wuffs-generated C (self-contained) removes disposal-law risk |
| RAM | Neutral |
| CPU | Wuffs measured faster (intel gif_decode benches) |
| Headless | Generated C, no deps — ideal |
| License | Apache-2.0 — OK |
| Semantic mismatch | LOW: wuffs implements the exact GIF disposal semantics S93 flagged as our gap (restore-to-background/previous) |
| Integration cost | 1 session (drop-in decoder behind the same StoredBitmap API) |
| Testability | docs/EXECUTED_GIFS.md corpus = direct regression set |
| **VERDICT** | **ADOPT-CANDIDATE (highest LOC/risk ratio)** — queue as GIF-disposal wave; the only candidate where upstream is STRICTLY more correct than our code. |

### 7. Filament — Surface/3D ONLY
| Criterion | Assessment |
|---|---|
| LOC potentially removed | 0 (GLSurfaceView family uses PortableGL) |
| RAM | +20 MB+ (PBR engine) — disqualifying for a compatibility runtime |
| Headless | EGL required |
| License | Apache-2.0 |
| Semantic mismatch | HIGH: Android SurfaceView/GLSurfaceView apps use raw GLES; Filament is a scene-graph PBR renderer |
| Integration cost | Weeks |
| Testability | Boxcars/libGDX corpus already passes through PortableGL |
| **VERDICT** | **REJECTED** — PortableGL covers the Surface/3D contract. |

---

## §2 Mandated summary table

| Candidate | LOC removable | RAM | CPU | Headless | License | Semantic mismatch | Integration | Testability | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Skia | ~1,400 gross, ~0 net | +4–8 MB | neutral | raster-only | BSD | HIGH (census law) | 2–4 sessions | goldens re-derived | REJECTED |
| libarsc/ARSCLib | ~4,800 gross | neutral | neutral | Java-only | Apache-2.0 | HIGH (law carrier) | rewrite | goldens | REJECTED |
| QuickJS | 0 (integrated) | sunk | proven | proven | MIT | none | sunk | proven | KEEP |
| Yoga | ~900 | +1–2 MB | neutral | OK | MIT | HIGH (measure/spec) | measured | goldens | REJECTED (S132) |
| Lottie/rlottie | 0 | +2–3 MB | per-anim | OK | MIT/Apache | LOW (scoped) | 1 session | demand-gated | PENDING |
| Wuffs (GIF) | 119 net negative | neutral | better | generated C | Apache-2.0 | LOW (strictly better disposal) | 1 session | EXECUTED_GIFS corpus | ADOPT-CANDIDATE |
| Filament | 0 | +20 MB | heavy | EGL | Apache-2.0 | HIGH | weeks | PortableGL covers | REJECTED |

## §3 LOC reduction ledger (honest)

- **True reduction available now:** 0 enforced — V8 audit classified
  view_renderer.cpp (685 LOC) as REFERENCE_ONLY dead code; deletion is
  gated by the no-blind-delete law (its measure_view documents historical
  EXP-122 layout semantics referenced by census evidence). Proposed
  disposition: keep, header-annotated REFERENCE_ONLY (done in V8 audit),
  revisit after V10 wave lands.
- **Future reduction (post-adoption):** −119 (gif_decoder) +Wuffs-gen C,
  net repo −119 while REMOVING the S93 disposal-law gap.
- No other candidate reduces LOC without breaking law-carrier code.
