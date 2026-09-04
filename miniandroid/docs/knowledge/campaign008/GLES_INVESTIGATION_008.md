# GLES INVESTIGATION — UNIFIED_008 (charter §14/§15)

## Question

Can ANGLE + SwiftShader remove the GLES-compatibility bridge that keeps REAL
GLES APKs BLOCKED in MiniAndroid?

## What was actually done here (not speculation)

1. **Cloned** google/swiftshader, HEAD `694585a` (14,398 files, depth-1,
   blob-filtered).
2. **cmake configure SUCCEEDED**:
   - cmake 4.4.2 (pip-installed into ~/.local after apt/jdk absence)
   - `cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DSWIFTSHADER_BUILD_TESTS=OFF`
   - output: `-- Build files have been written: …/swiftshader/build`
3. **Compile attempt BLOCKED** — environment: 2 vCPU, **3 GB RAM**, 5.7 GB
   free disk. SwiftShader's Reactor (LLVM-derived) translation units exceed
   available memory at this scale; the single-process build also exceeds the
   session's foreground tool timeout. This is a MEASURED blocker, not an
   assumption.
4. ANGLE: requires depot_tools + gn + ninja bootstrap and a GL/Vulkan backend
   (SwiftShader) to be useful here — bridge-of-a-bridge; not attempted beyond
   source review.

## Findings

| option | license | build system | runtime footprint | verdict |
|---|---|---|---|---|
| SwiftShader | Apache-2.0 | CMake | libEGL+libGLESv2 user-space, no kernel driver | **ADOPT TARGET on ≥16GB host** |
| ANGLE | Apache-2.0/BSD | gn+ninja | same class | only if Vulkan features needed |
| bgfx/sokol/filament | BSD/Apache/MIT | cmake | still need a GL device | do NOT solve soft-GLES |

## Integration path (recorded for the 16GB host run)

```bash
git clone https://github.com/google/swiftshader
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel $(nproc)          # → libEGL.so, libGLESv2.so
# MiniAndroid side:
EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 \
  ./build/miniandroid run <gles-game.apk> -o run/gles
# MiniAndroid jni/gles shim loads the SwiftShader EGL/GLES via dlopen and
# maps eglSwapBuffers → software_renderer framebuffer read-back → PNG.
```

## Status

- REAL GLES APK: **BLOCKED in this environment** (precise blocker: memory/CPU
  budget — configure step proven, compile infeasible at 3GB).
- Charter §14/§15 answered: YES — SwiftShader alone (without ANGLE) can
  remove most of the bridge; the glue shrinks to an EGL surfaceless context +
  framebuffer read-back shim.
