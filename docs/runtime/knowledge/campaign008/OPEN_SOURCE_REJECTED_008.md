# OPEN SOURCE REJECTED — UNIFIED_008 (with reasons, charter §36/§29)

Rejection is a decision, not a dismissal — each entry was scored against the
scorecard (license / platform / size / integration complexity / benefit).

| project | score | reason for rejection |
|---|---|---|
| Flutter (flutter/flutter) | 3/10 | Dart VM + own widget tree — no path to interpret Android DEX UI |
| bgfx (bkaradzic/bgfx) | 4/10 | no CPU rasterizer; still requires a GL/Vulkan device — does not remove the bridge |
| sokol (floooh/sokol) | 4/10 | same class as bgfx for our purpose |
| Filament (google/filament) | 3/10 | PBR engine, wrong abstraction for 2D UI + overkill for GLES compat |
| MoltenVK | 2/10 | Apple-only |
| ultralight (ultralight-ux) | 2/10 | **license**: proprietary/commercial — auto-REJECT on license audit |
| Soot (Sable/soot) | 3/10 | research IR framework; JVM-heavy for runtime embedding |
| Boost (boostorg/boost) | 3/10 | dependency surface too large for what vendored code replaces |
| gRPC | 3/10 | full RPC stack; REST + JSON already sufficient for job server |
| Glide / Picasso / OkHttp / Retrofit | 2/10 | Android-java runtime libs — we ARE the runtime |
| SDL | 4/10 | whole platform layer for audio+window; we only wanted audio decode, already covered by mpg123/libsndfile |
| SheenBidi (Tehreer/SheenBidi) | 6/10 | good modern bidi/shaper — but FriBidi+HarfBuzz already PROVEN in-runtime; swap cost > benefit |
| miniaudio | 5/10 | nice single-header; system mpg123+libsndfile already green 47/47 — no LoC to remove |
| stb_image | 5/10 | would replace nothing — libpng/jpeg-turbo/webp already external |
| SkiaUI2/wangyugz | 4/10 | promising (View/Text/Lottie on Skia+Yoga) but single-maintainer, no test suite, license unclear at inspection time — re-evaluate later |
| Compose Multiplatform port | 4/10 | technically the RIGHT target for Dooz, but Composer/SlotTable/Material3 draw = multi-month; recorded as precise blocker instead of half-implementation (depth-first rule) |
| ANGLE (google/angle) | 5/10 | needs depot_tools+gn toolchain and a Vulkan backend (SwiftShader) anyway — bridge-of-a-bridge; SwiftShader directly is simpler here |
| Rive (rive-app/rive-cpp) | 5/10 | capable animation runtime — rlottie already wired and proven on-screen |
| Catch2 / googletest | 6/10 | fine frameworks — current zero-dep harness is green and tiny; not worth churn mid-campaign |
| sqlite (job store) | 6/10 | upgrade path when job queries get complex; nlohmann store passed 10/10 E2E incl. SIGKILL restart |
| github gh CLI | 4/10 | not installed, no credentials available in env; git ls-remote covers the need |
| docker/moby/containerd | 1/10 | unavailable in environment |
| JDK-full vendoring | n/a | downloaded OUTSIDE archive (licensing GPL+CE fine, size policy §32) |
