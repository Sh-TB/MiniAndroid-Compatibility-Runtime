# THE SQLITE RULE (S185, 2026-11-06) — VEND, DON'T REWRITE

Origin: user directive (S185): *"100% of the tools we need exist as free open-source
Android sources — whatever the app calls, bring the real thing in. The most important
part is that the program FIRST fully loads. If it gets bulky, fine — once execution is
complete we trace where everything loaded from and keep only the required roots."*

Every Coder (2–9) MUST apply this rule before writing ANY new engine code.

---

## The four clauses

### Clause 1 — VEND, DON'T REWRITE

When a title needs a component the engine does not have (a native library, a GL
driver, an audio stack, an image codec, a framework class), the FIRST move is never
"write a shim/simulation/stub". The first move is: **find the real open-source
implementation, build it for the host, and load it.**

- Precedent 1 — SQLite: we vendored real libsqlite3 instead of writing a SQL engine.
- Precedent 2 — libGDX (S183b): we rebuilt `libgdx64.so` + `libgdx-box2d64.so` +
  `libgdx-freetype64.so` (398 JNI symbols) from the real gdx-parent-1.9.10 sources
  (script: `scripts/s183_build_gdx_host.sh`, self-fetching since S185) instead of
  fighting the bionic-vs-glibc ABI with hand-written shims. Result: #11-real uncaught
  exceptions 8→0, 45 real freetype font loads, render loop cycling.
- Hand-written engine shims, synthetic stubs that "look right", and fixture-only
  evidence are FORBIDDEN as substitutes for a vendable real library.

### Clause 2 — LOAD-FIRST

Milestone 0 for any title is **full load**: the program's own code path runs to its
first real frame with no uncaught exceptions. Bulk is acceptable at this stage
(large .so, full source trees, debug symbols). Do not optimize size before the load
is real and complete.

### Clause 3 — TRACER, THEN PRUNE

Only AFTER a title fully loads: run the tracer, record which files/paths/symbols the
execution actually touches, then prune the vendored set down to the required roots.
Never prune blind (that is how white screens happen — S183 fine audit).

### Clause 4 — NOTHING BULKY IN GIT

The repo carries **knowledge, not bulk**. Every vend follows this storage law:

| item | in git | on disk |
|---|---|---|
| vend source | URL + pinned tag/hash + fetch step inside the build script (fetch-if-missing) | `/tmp` scratch, disposable |
| built .so / binaries | NEVER (`.gitignore`: `*.so`) | `tools/native_host/`, rebuilt by script |
| run dirs / raw traces / logs (`run_*`, `*.err`, `api_trace.json`) | NEVER | deleted after verdict extraction |
| evidence | verdict JSON + face JPG ≤100 KB (S38 law) | — |
| big generated JSON | `.gz` + updated readers, or regenerable-by-script | — |

If a reviewer cannot rebuild your artifact from `scripts/` + the pinned upstream URL,
the commit is incomplete. Enforced since S185: repo pack 139 MB → 82 MB, tree
260 MB → 163 MB (S185 three-pass `git filter-repo`; see
`evidence/s185_sqlite_rule/S185_APPLICABILITY.md`).

---

## Per-blocker playbook (the sqlite rule applied to every family)

| blocker | what the app actually calls | sqlite-law move | vend candidate (100% open-source) |
|---|---|---|---|
| **B1** bionic `DT_NEEDED` vs glibc dlopen (`libm.so: invalid ELF header`) | app-shipped `.so` (libgdx, SDL, mupdf, …) | rebuild the SAME upstream source for host; keep the B1 spawn law (`LD_LIBRARY_PATH=<nativeLibraryDir>/shims:<nativeLibraryDir>` at SPAWN) only for libs that cannot be rebuilt | upstream sources per library (libGDX 1.9.10 done; SDL2; mupdf; GNU bg) |
| **B2** GL/EGL surface (`AndroidGraphics.createGLSurfaceView`) | `libGLESv2.so` / `libEGL.so` | vend a real software GL for the host and back GLSurfaceView with it | **PortableGL** (MIT, single-lib software OpenGL 3.x) or **gl4es** (LGPL, GL 1.x/2.x → GL3) |
| **B3/B4** androidx lifecycle/Compose clinit storms | androidx classes | extract the REAL class source and port it (androidx IS open source; sources jars already vendored under `upstream/`) | AOSP + androidx source jars (`upstream/s43/…sources.jar` etc.) |
| **B5** missing framework classes (`android.graphics.Insets`, kotlin-reflect) | framework API | port the class from AOSP source (precedent: `docs/upstream/aosp/input_laws/View.java`); vend real kotlin-reflect | AOSP; kotlin-reflect (Apache-2.0) |
| **B6** bitmap/image assets decode flat (~0 decoded assets in B-STRUCTURED faces) | `BitmapFactory` / skia codecs | vend a real decoder behind BitmapFactory | **stb_image** (public domain, single header) or libpng + libjpeg-turbo (BSD) |
| **B7** OpenSL ES / audio natives | `libOpenSLES.so` | bridge to a real host audio lib; do not fake silence | **OpenAL soft** (LGPL-2.1) via a thin JNI bridge |

## Hard requirements (anti-patterns that void a "done")

1. No synthetic engine shim where a real open-source library exists.
2. No "loaded" claim without a full-load trace (uncaught = not loaded).
3. No bulk in git (Clause 4).
4. No pruning before the tracer has run (Clause 3).
5. Every vend records: upstream URL, pinned revision, build command path, output .so
   names, JNI symbol count — in the title's evidence JSON.
