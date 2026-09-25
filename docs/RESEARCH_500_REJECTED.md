# R500 REJECTED / OUT-OF-SCOPE LEDGER

Explicit dispositions for every finding that does NOT become a runtime fix.
Nothing silently disappears; the canonical ledger is
`docs/RESEARCH_500_AUDIT.json` (+ `.md`).

## A. REJECTED — the claim was tested and did not hold (2)

| ID | claim | what the runtime actually showed |
|---|---|---|
| R500-017 (FL-004) | Handler.postAtFrontOfQueue missing = root cause of handler failures | Runnables DO execute (S103 3/3, stale "no-op" source comment corrected). The only divergence was ORDER — fixed this wave (ROOT-003). |
| R500-018 (FL-005) | View.getWidth throws NPE | No NPE exists at getWidth. Real divergence = frame materialization (W2/W3 probes) — fixed this wave (ROOT-002). |
| R500-004 (U-004 partial) | getWidth returning 0 is itself the bug | Rejected as stated: pre-layout 0 is the CORRECT AOSP semantic (W1). Only the post-layout 0 diverged. |

## B. OUT_OF_SCOPE — host-Android layer MiniAndroid does not own (20)

Verified against the engine source (no such subsystem exists; capability
registry: `native.jni DECLARED`, `media.video DECLARED`):

| IDs | layer |
|---|---|
| R500-020, 036, 041 | BufferQueue / SurfaceFlinger / triple buffering (surface = PGL back buffer) |
| R500-021 | Vulkan (no loader, no headers — DEVICE_LOST unreachable) |
| R500-022, 025, 053 | EGL surfaceless / CONTEXT_LOST / swap interval (shadow EGL, one software context, no failure model) |
| R500-027, 043 | GraphicBuffer / EGLImage (no gralloc) |
| R500-028 | Skia allocator (MiniAndroid owns software_renderer, not Skia) |
| R500-030, 034, 044, 128 | SurfaceTexture / external textures / YUV (no camera/video producer exists) |
| R500-032 | glTexImage2D thread affinity (single-threaded engine; the upload-gap itself is ROOT-GL-BRIDGE) |
| R500-042, 054 | fence/sync primitives (no producer/consumer races single-threaded) |
| R500-130, 129 | background reflection / capture threading (single-threaded engine; capture synchronous) |
| R500-014, 015, 016 (FL-001..003) | system boundaries (full-Android emulator, full-JVM, Skia/Cairo) — architecture context, not bugs |
| R500-132, 135 | @CriticalNative / RegisterNatives + System.loadLibrary (HOST_COMPATIBILITY_STUB model; no dlopen of real .so) |

## C. API-ABSENT — engine lacks the surface; gated on measured corpus demand (12)

| IDs | surface | gate |
|---|---|---|
| R500-023, 035, 046, 055, 033 | glFramebufferTexture2D / glTexSubImage2D / texture arrays / glReadPixels / RenderTexture (PortableGL implements all at C level; the GLES bridge dispatch table does not) | corpus GL-title demand scan (run/r500) |
| R500-029, 038, 039, 040 | ETC1 / S3TC / ATC / PVRTC compressed textures | corpus asset scan (0 found so far) |
| R500-047 | geometry/tessellation/compute shaders | behind ROOT-GLSL (GLSL execution frontier) |
| R500-073, 074 | invoke-polymorphic / invoke-custom | corpus 0 sites (R8-desugared); re-test when a non-desugared APK arrives |

## D. NOT REPRODUCIBLE / MOOT in the MiniAndroid model (rest of the audited set)

| IDs | note |
|---|---|
| R500-037 (Vsync) | engine-driven frame loop + Choreographer shadow; S95 REFUTED the frozen-animation claim; no measurable divergence in the software model |
| R500-026 (preserve context on pause) | single context is never destroyed on pause — the semantic HOLDS in the software model |
| R500-045 (sRGB) | S95 color laws hold; no gamma-shift evidence in corpus |
| R500-048 (blending) | glBlendFunc dispatched; software alpha exercised corpus-wide |
| R500-126, 127 (thread affinity, GL thread) | documented single-threaded subset, OBSERVED |
| R500-075..083, 085 (jumbo/IDs/pools/switch payloads/synthetic) | supported and corpus-exercised (3,617 jumbo sites clean; 64,422 method ids u32-safe) |
| R500-089 (method resolution) | L5 — S102 MULTIDEX-INTERFACE-CLOSURE law |
| R500-098 (Toolbar) | L5 — S101 LAW 1 + S103 3/3 positive proof |
| R500-100/101/104 (lifecycle/pause/render modes) | OBSERVED across 61-title census |
| R500-108/109/114/118 (resource IDs/drawables/config/string pools) | OBSERVED corpus-wide |
| R500-119..121, 123 (Looper/Handler/post/postDelayed) | verified S103; animations proven |
| R500-125 (removeCallbacks) | implemented since EXP-088; battery scenario post/remove/drain verified |

## E. Latent-only (real code divergence, zero corpus exposure — deliberately unfixed)

| IDs | note |
|---|---|
| R500-007, 011, 116, 117 (ARSC OFFSET16/COMPACT) | SOURCE_SUPPORTED + REPO_SUPPORTED + CORPUS_UNCONFIRMED (0/54 APKs). Fix when a real APK needs it. |
| R500-008 (CDEX) | clean UNSUPPORTED rejection (PARSE_ERROR, correct behavior); corpus 119/119 standard DEX |
| R500-105 (Theme.applyStyle) | no producer found in engine shadows (code-level); runtime fixture pending |
| R500-133 (SQLite WAL) | wal_requested recorded, journal mode deliberately default (byte-determinism); corpus WAL-title check pending |
| R500-134 (StrictMode) | single stub mention; corpus need 0 observed |
| R500-136 (AudioTrack) | no shadow; media.audio PARTIAL covers SoundPool/MediaPlayer |

## F. Input-integrity dispositions

```text
TRUNCATED_INPUT  = 364 slots (claimed "500"; recoverable = 136 — no invented
                   findings; full accounting in docs/audit/input_inventory.md)
DUPLICATE-linked = 7 rows (R500-011→007, 018→004, 054→042, 068→067,
                   074→073, 124→122, 128→034, 127→103 — links kept in the
                   ledger; canonical rows carry the evidence)
```
