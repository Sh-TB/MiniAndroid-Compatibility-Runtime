# OPEN_SOURCE_REJECTIONS_010 — candidates evaluated and not adopted (evidence-based)

Every rejection carries the measured reason. None of these are "not famous
enough" or vibes-based rejections (R11 rule).

| Candidate | License (verified live) | Verdict | Measured reason |
|---|---|---|---|
| **stb_image v2.30** as runtime PNG codec | Public domain / MIT dual | **REJECT for runtime, KEEP vendored** | Correctness 100% and 2.27× faster than custom — but rlottie's static lib exports the *same global stbi_* symbols from v2.19*; linking both collides (multiple-definition, observed at link). libpng wins on equal correctness + reference status (Android/Skia use libpng) + already-linked dep. stb v2.30 vendored at `third_party/stb/` for future use behind a prefix build. |
| **SwiftShader** | Apache-2.0 | REJECT (this machine) | Campaign 009 measured: configure OK, compile needs >3GB RAM — host has 3GB. Same evidence carries to 010 (RAM unchanged). |
| **Mesa llvmpipe/lavapipe/Zink, OSMesa** | MIT-ish per-component | REJECT (build cost) | Full Mesa build far exceeds this environment's RAM/time budget; no prebuilt packages available offline-equivalent for GLES-in-proc. Documented as the "arbitrary APK GLSL" future route. |
| **ANGLE** | BSD-3 | REJECT (this machine) | Requires SwiftShader/Chromium build chain; same RAM constraint as SwiftShader. |
| **Skia / SkiaUI2 / Skiko** | Skia BSD; SkiaUI2 identity unverified | REJECT (cost/identity) | Skia full build = hours + several GB (measured class of cost, same as Mesa family). "SkiaUI2" could NOT be verified as an existing, maintained repository via GitHub search/ls-remote during this campaign — per §1 no claims are made about it beyond "unverified"; the SkiaUI2 description in the instruction (measure/layout/draw + touch + ImageView/RecyclerView + Lottie + WebView + Compose integration) remains a candidate description to re-investigate when it can be located and license-checked. |
| **resvg** | Apache-2.0 (linebender/resvg @ 021d44b) | DEFER (E) | Rust toolchain build not present in env; no corpus APK currently blocked on arbitrary-SVG; nanosvg (Zlib, C) proven sufficient for the same need at far lower integration cost. |
| **Compose Multiplatform / Skiko direct adoption** | Apache-2.0 | DEFER (E) | Requires Skia binary; blocked by the same build-cost wall. Dooz path continues via DEX interpretation of the real Compose runtime (COMPOSE_DOOD_ANALYSIS_010.md). |
| **SheenBidi** | Apache-2.0 (9c048a3) | DEFER (E) — builds+links, harness calibration pending | FriBidi is the §14-PROVEN pipeline; SheenBidi differential must be re-run with matched base-direction semantics before an ADOPT/REJECT verdict. |
| **apk-parser (npm)** | MIT | REJECT for runtime | Archive-level JS parser — duplicative of our zip_reader + androguard oracle; no reduction available (different language ecosystem). |
| **Catch2 / GoogleTest (new adoption)** | BSL-1.0 / BSD-3 | NOT ADOPTED this campaign | Existing tests are script+golden based; Yoga ships gtest internally (built for libyogacore test target). Introducing a second test framework is net-negative until parser fuzz lands (R21 follow-up: libFuzzer on AXML/ARSC/DEX parsers). |
| **OpenAL Soft / SDL_audio** | GPL-2/LGPL, Zlib | REJECT for now | Heavier runtimes than miniaudio (single-header, PD) for the same need; miniaudio wins the license+size criteria (R11: never pick on fame). |
| **FFmpeg/GStreamer/mpv (video)** | LGPL/GPL | DEFER (E) | No corpus APK currently requires video decode at runtime; Media3/ExoPlayer demand recorded in 009's demand matrix for newpipe — revisit with the video corpus. |

## Kept-custom (deliberate, with the open-source oracle stated)

| Subsystem | Why kept | Oracle |
|---|---|---|
| DEX interpreter | IS the product; no embeddable OSS equivalent executes DEX under our control model | androguard (static), Robolectric (semantics) |
| ARSC/AXML/res_config | Android-specific resolution semantics must remain glue (R6 note: parser duplication is the target, not the compatibility layer); res_config already AOSP-ported @1cdfff5 | ARSCLib, androguard, aapt2 |
| Browser/job server | absent in recovered tree (009 §26-28 NOT RUN) | — |
| BitmapFont (8×16) | zero-dep rendering for the fallback renderer; FreeType path exists in exp tools | FreeType+HarfBuzz+FriBidi pipeline (R4 follow-up: real-TTF TextView path) |
