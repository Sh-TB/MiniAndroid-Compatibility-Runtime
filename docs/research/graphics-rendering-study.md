# Graphics / Rendering Study — Canvas, Paint, Path, and the software pipeline

Sources:
- AOSP frameworks/base graphics stack (mirror `1cdfff55`): Canvas.java,
  Paint.java, Path.java, RenderNode.java, RecordingCanvas.java
- MiniAndroid: `src/framework/canvas_shadow.cpp`,
  `src/renderer/software_renderer.cpp`, `view_renderer.cpp`
- CrosVM `ARCHITECTURE.md`, qemu `android/android-emu` + `android-emugl`
  (host graphics abstraction models), cuttlefish host/guest rendering split

## GFX-001 — Canvas API surface parity checklist (AOSP-012 extended)
Entry points pinned at exact locations in `graphics/java/android/graphics/Canvas.java`:
save(L443) / restore(L660) / clipPath(L1077) / drawArc(L1550, L1579 two
overloads) / drawPath(L1929) / drawRoundRect(L2068 RectF + L2080 ltrbo
overloads). MiniAndroid's canvas shadow implements the corpus-required
subset with regression coverage; the two-overload duality (RectF vs
component floats) is an API-completeness item for any drawX not yet paired.
- Status: VERIFIED for implemented set; overload pairing audit queued
  (mechanical; low risk).

## GFX-002 — Style + winding interaction (AOSP-010/011 applied)
Paint.Style FILL_AND_STROKE's documented counter-clockwise caveat +
Path.FillType WINDING/EVEN_ODD/INVERSE_* numeric ABI ("must match
SkPath.h"). MiniAndroid Cycle E implemented cubicTo/rMoveTo/rLineTo/winding
rules/drawOval/drawArc/offsets/fill-stroke with pixel-discriminated
fixtures and deterministic replay.
- Status: VERIFIED at prior HEAD (Cycle E) — revalidation at current HEAD
  queued as first-class audit item (see gap analysis: Cycle E fixture tool
  `$(find)` inner-class error was the last known open build issue).

## GFX-003 — RenderNode / RecordingCanvas: what a userspace renderer may skip
- Source: `RenderNode.java` L195 (final class, property setters like
  setAlpha L994); `RecordingCanvas extends BaseRecordingCanvas` L36.
- Mechanism: modern Android draws by RECORDING display lists into
  RenderNodes, then replaying on the GPU thread. Properties (alpha,
  translation, rotation) can change WITHOUT re-recording.
- MiniAndroid position: our software renderer draws immediately (like
  Skia's legacy CPU backend / the emulator's swiftshader path). Compose
  apps (dooz) go through ComposeView→AndroidComposeView→RenderNode chains —
  our shadows must ACCEPT those calls (they do) and collapse to immediate
  draws. The study conclusion: RenderNode property semantics matter only
  as much as corpus apps set them (alpha/translation on compose hosts).
  - Status: ARCHITECTURE DOCUMENTED; property-collapse shadow verified on
    dooz prior runs; deeper compose coverage = compose-study.md.

## GFX-004 — Host graphics abstraction patterns (emulator family)
- qemu `android/android-emu/` (GL translation: android-emugl translates
  GLES guest commands to host GL; grpc UI channel; webrtc streaming) and
  cuttlefish host (renderserver + vsock input hal) vs guest (hals).
- The shared idea across emulator/cuttlefish/crosvm/waydroid: the GUEST
  (or app) issues a small, stable command surface; the HOST owns pixels and
  input injection points. MiniAndroid already follows this split
  (view tree → software_renderer → framebuffer; input → dispatch probe);
  what the big projects add is SEPARATION OF PROCESSES (crosvm:
  process-per-device with minijail seccomp; cuttlefish: host/guest vsock)
  — relevant only when MiniAndroid sandboxes untrusted APKs.
- Status: METHODOLOGY NOTED (sandboxing roadmap; see external-gap-analysis).

## GFX-005 — Deterministic replay as the renderer contract
MiniAndroid's frame-hash law (identical input → identical framebuffer
bytes) has a direct analogue in droidsaw's byte-exact DEX round-trip and
in emulator snapshot determinism tests. The invariant survived Cycles A–E
as an explicit regression gate (golden frames per fixture).
- Status: VERIFIED (regression law); continue per §28.
