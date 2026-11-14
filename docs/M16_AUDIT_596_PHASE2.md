# M-16 Phase-2 audit record (#596) — audit-only, no runtime change

Branch base: ba184db9 (the immutable baseline named by #596). main at audit
time: a5eb0bc7 = ba184db9 + 3 script-only commits (no runtime/rules change;
verified: the ba184db9..a5eb0bc7 diff touches only scripts/*.py, +277 lines).

## §2.1 architecture (verified from source)
- src/webview/ EXISTS: webview_engine.{h,cpp} (338,897 B), html_dom.{h,cpp}
  (32,555 B), canvas2d.{h,cpp} (23,714 B) — hand-rolled HTML/DOM/CSS engine.
- QuickJS 2024-01-13 vendored, wired at webview_engine.cpp L220/L2050/L2179
  (per canonical/m16_webview_decision.json).
- WV_DIAG + webview_resource_trace.json instrumentation present
  (webview_engine.cpp L150/L180-194, gated on WV_DIAG + WV_DIAG_DIR env).
- Manifest parity: src/webview/{webview_engine,html_dom,canvas2d}.cpp all in
  core_sources.manifest.

## §2.2 the CSS-failing 2048 APK — NOT IDENTIFIED (BLOCKED)
- org.secuso.privacyfriendly2048_100.apk (sha256 02c799d3...): S195 record
  re-read — frame_analysis NO_ROOT x2, uncaught 2, NameNotFoundException 1,
  route VIEW primary, zero HTML assets. First divergence = content root
  absent BEFORE Measure/Layout. NOT a CSS failure (re-verified 2026-11-14).
- org.andstatus.game2048_47.apk (sha256 2d6707624623fe88...): korge-based
  (korlibs.korge.ViewsCompleter in META-INF services), ZERO html/css/js
  assets. NOT a WebView/CSS failure.
- games/2048 (repo native) + s80/s83 g2048 builds: custom-View, no WebView.
- The coder's reported WebView/CSS 2048 APK is not among the artifacts —
  BLOCKED until the exact APK (or its sha256/URL) is provided.

## §2.3 fetch/parse/cascade/layout/paint separation
Instrumentation to reuse: WV_DIAG resource trace (exists, format preserved).
The per-stage CSS diagnostics (parse errors, matched/unmatched selectors,
specificity, !important, custom properties, first unconsumed computed
property, first layout/paint divergence) are designed but NOT implemented —
PENDING, gated on the §2.2 target APK.

## §2.4 litehtml — upstream verified + MEASURED (2026-11-14)
- Upstream HEAD ebb9d32b28cb (github.com/litehtml/litehtml, 1,106 commits).
- License: BSD-3-Clause (litehtml) + bundled gumbo Apache-2.0 (src/gumbo,
  C99). Core build needs NO external libraries; Cairo/Pango/GTK/curl/fontconfig
  optional and OFF by default.
- Measured source size: 66,137 LOC across src+include (src 2.9 MB,
  include 476 KB). NOTE: the M-16 decision record's "~30k LOC" is OUTDATED.
- CMake >= 3.20. CSS Grid: PARTIAL support (doc/css_support.md).
- It is a layout engine, not a browser/JS/paint backend — QuickJS and
  Canvas2D stay (per decision, S131 REUSE-FIRST law).

## §2.5 prototype — PENDING (this wave is audit-only, honestly)
Not implemented in this pass. The integration contract for the next pass:
1. Pin litehtml ebb9d32b28cb under miniandroid/third_party/litehtml (vendored,
   no fetch at build time).
2. CMake option MINIANDROID_USE_LITEHTML (OFF by default) -> builds the
   static lib + the adapter TU only when ON.
3. Document-container adapter implementing the litehtml callbacks on the
   EXISTING font/image/software-render/clipping primitives (no second paint
   stack); no host browser required.
4. DOM ownership: html_dom stays the JS-facing DOM (QuickJS mutations);
   litehtml's DOM is RENDER-ONLY and rebuilt/invalidated on JS style/layout
   mutations (invalidation points: html_dom.cpp set_attribute/style/class
   paths). One mutation direction, one owner — no unsynchronized DOM pair.
5. A/B control: the option OFF = byte-identical old path; ON = litehtml
   render for document-class routes only.
6. Focused tests: CSS parse/cascade unit rows + one document-class fixture
   APK; regression gate = the existing 124-stage battery must stay green.

## §2.6 host-browser optional backend — evaluated, BLOCKED/absent here
- Linux WebKitGTK: ABSENT in this sandbox (pkg-config webkit2gtk-4.1 fails).
  The evaluation (runtime availability, headless, determinism, Android
  WebView bridge gaps) = PENDING on a host with WebKitGTK installed.
- Windows WebView2: BLOCKED — no Windows environment in this sandbox.
- The webview/webview wrapper stays OUT of the runtime (host diagnostic
  only). Host browser output = comparison oracle, never proof.

## §2.7/§2.8 cross-platform matrix + regressions
- Windows x64 build: BLOCKED (no Windows in the sandbox).
- Linux x86_64: the audit branch builds nothing new (audit-only) — the
  prototype build/measure is PENDING with §2.5.
- The 12-item test matrix: PENDING on the prototype (§2.5).
- Regression exposure of THIS branch: ZERO runtime change (audit docs only)
  — S100/S112/S114/S133 + the 124-stage battery untouched by construction.
