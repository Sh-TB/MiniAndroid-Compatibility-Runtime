# WS-C4 → WS-C2 TRANSFER (tooling findings relevant to graphics/text/animation)

**FINDING ID:** C4TOC2-001
- **SOURCE:** WS-C4 research (mid-2026) + the internal WS-C2 POC
- **FINDING:** the FriBidi/HarfBuzz/FreeType trio is buildable and provable in the sandbox right now
  (POC: 4/4 Persian/RTL OK). SheenBidi 3.0.0 (Apache-2.0) is a permissive replacement for FriBidi (LGPL) in the future.
- **EXPECTED:** connected Persian/Arabic text with RTL in the framebuffer
- **ACTUAL:** successful POC; inside the runtime still BitmapFont without bidi
- **EVIDENCE:** `run/wsc2_text_pipeline.png` + metrics JSON
- **RELEVANT:** WS-C2
- **RECOMMENDATION:** FontBackend adapter (T1 in WS-C2_PRIMARY_TRANSFER)

**FINDING ID:** C4TOC2-002
- **SOURCE:** WS-C4 matrix
- **FINDING:** ThorVG v1.0 (MIT, C API) is a serious long-term rlottie successor (DEFER not USE);
  the existing libwebpdemux is ready for animated-WebP (only frame iteration remains).
- **RECOMMENDATION:** after the current RLottie stabilizes, a small ThorVG spike; complete
  animated-WebP on the AnimationBackend path (CM-027 future work).

**FINDING ID:** C4TOC2-003
- **SOURCE:** WS-C4 matrix
- **FINDING:** APNG has no healthy standalone C library → ADAPT on libpng (acTL/fcTL/fdAT)
- **RECOMMENDATION:** if the corpus wants APNG, write a small chunk-level parser rather than a new lib.

# WS-C4 → WS-C3 TRANSFER (tooling findings relevant to the framework/corpus)

**FINDING ID:** C4TOC3-001
- **SOURCE:** WS-C4 matrix + Robolectric research (WS-C5)
- **FINDING:** the single-file SQLite amalgamation (Public domain) + the Robolectric nativeruntime precedent
  (booting real SQLite for shadows) → a safe DatabaseBackend path.
- **RECOMMENDATION:** D1 in WS-C4_PRIMARY_TRANSFER — the next adoption.

**FINDING ID:** C4TOC3-002
- **SOURCE:** WS-C4 matrix
- **FINDING:** libdeflate 1.24 (MIT, ~0.1MB) inflates faster than zlib for the APK hot path.
- **RECOMMENDATION:** benchmark on Telegram v12; then an adapter with fallback.

**FINDING ID:** C4TOC3-003
- **SOURCE:** AppManager research (WS-C5)
- **FINDING:** dexlib2 (baksmali) is a battle-tested reference model of the DEX format — for cross-checking
  our own parser (especially after the C2-F11 lesson about tool misdecode).
- **RECOMMENDATION:** in CI: a structural class difftest between dexlib2 and our own dex_parser
  on the same v12 APK (schema-level, without linking Java in the runtime).
