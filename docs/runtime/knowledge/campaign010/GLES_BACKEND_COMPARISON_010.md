# GLES_BACKEND_COMPARISON_010 — R9 evaluation record

## 1. Candidates and dispositions

| Backend | License | Disposition | Blocking evidence |
|---|---|---|---|
| **PortableGL** rswinkle@7cf39dc | MIT | **ADOPTED** | builds+links with plain gcc/g++; header-only; measured below |
| SwiftShader | Apache-2.0 | rejected here | 009 measurement: configure OK, compile >3GB RAM vs 3GB host |
| ANGLE | BSD-3 | rejected here | needs SwiftShader/Chromium toolchain (same RAM wall) |
| Mesa llvmpipe/lavapipe/Zink/OSMesa | MIT/X11 family | rejected here | build cost/RAM; future route for arbitrary GLSL |
| bgfx / sokol-gfx | BSD-2 / Zlib | not needed | abstraction layers OVER a rasterizer — PGL already provides the layer we need; adding bgfx adds indirection without removing code |
| Filament | Apache-2.0 | not needed | full PBR engine (huge); corpus GLES apps (retrowars/mindustry/SPD) use GLES2 surface, not PBR |

## 2. Measured PortableGL performance in MiniAndroid (this host)

Via `GLES20Bridge` (VBO path, depth test ON, Lambert fragment work):

| Resolution | Frames | Total draw | Per frame | FPS | Throughput | Cube coverage |
|---|---|---|---|---|---|---|
| 320×240 | 24 | 14.4 ms | 0.60 ms | 1,668 | 128.1 Mpx/s | 10.0% |
| 1080×1920 | 12 | 436.8 ms | 36.40 ms | 27.5 | 57.0 Mpx/s | 25.7% |

Artifacts: `evidence/uc010_gles_bench_320.txt`, `*_1080.txt`,
`uc010_gles_cube.png` (320×240 golden render), `uc010_gles_cube_1080.png`.

Verdict: interactive-class performance for GLES2-era 2D/3D game demand on
this host. Real APK GLES journeys additionally require the DEX-side GLES20
dispatch wiring (bridge exists; dalvik_engine hook point identified at the
framework-static if-chain, same pattern as `System.currentTimeMillis`).

## 3. GLSL honesty statement (binding)

PortableGL does not parse GLSL. In `GLES20Bridge`:
- `glCreateShader`/`glShaderSource` — real: source stored verbatim, counted
  (`glsl_bytes` stat; 476 bytes in the cube run).
- `glCompileShader` — **recorded, not compiled**; trace carries
  `glsl-not-compiled-by-pgl`.
- Program execution = registered C-function shaders (`pglCreateProgram`),
  which the golden cube uses as exact functional equivalents of its GLSL.

Therefore: **we do not claim arbitrary-APK-GLSL execution.** The two honest
routes when a real GLES APK journey is attempted:
1. GLSL→C translator at runtime-integration time (PGL's documented pattern;
   deterministic, testable per-shader), or
2. Mesa llvmpipe build when the RAM wall allows (full GLSL → GL pipeline).

## 4. R10 counterfactual ledger ("remove custom software 3D")

- Custom 3D renderer in recovered tree: **0 LoC** (history-only, archives).
- Custom rasterizer never written in 010: avoided 800–1,500 LoC (est.) by
  adopting PGL with ~350 LoC of glue. Net custom-renderer LoC delta: −0 (no
  legacy to delete) with GLES capability +1. This satisfies the §40 principle
  in its strongest form: compatibility up, custom code never created.
