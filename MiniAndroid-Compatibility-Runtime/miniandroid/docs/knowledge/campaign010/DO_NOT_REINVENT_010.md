# DO_NOT_REINVENT_010 — the standing law + ledger updates

## 1. The law (restated)

```
current custom implementation
        ↓
GitHub search (live verification: ls-remote + raw LICENSE)
        ↓
existing mature implementation
        ↓
build
        ↓
run tests
        ↓
benchmark
        ↓
integration experiment
        ↓
replace / wrap / keep
```

"famous" is not a criterion; "repository found" is not adoption. Adoption =
source inspected + build + test + integration attempt + measured benefit.

## 2. New DON'T-REINVENT entries established this campaign

1. **PNG decode/encode** — CLOSED. libpng adopted; custom codec deleted
   (−383 LoC). Anyone re-adding a hand PNG unfilter must beat libpng on the
   7,036-APK-PNG corpus + the 12-fixture PIL oracle first.
2. **Software rasterizer** — FORBIDDEN while PortableGL builds here. GLES
   capability enters ONLY through `src/gles/` (PGLBackend + GLES20Bridge).
   Estimated custom rasterizer (800–1,500 LoC perspective/depth/raster/shade)
   never written: that IS the reduction.
3. **LinearLayout measure/layout** — Yoga adapter proven (100% <8px agreement
   on real AXML, ~35× faster). The engine's weight/gravity-less fallback
   layout math must not grow; new layout features go through the Yoga path.
4. **Stack-trace frames** — the interpreter call stack is the only source;
   EXP-093's empty-array stub class of hacks is retired (root cause of the
   dooz Intrinsics livelock).
5. **Audio backends** — when audio returns, start from miniaudio 0.11.25
   (verified compiling + enumerating backends here), not a new decoder stack.

## 3. Standing oracle table (R22)

| Subsystem | MiniAndroid | Differential oracle | Status |
|---|---|---|---|
| PNG decode | libpng wrapper | stb_image v2.30 (independent) + PIL fixtures | 7,036/7,036 three-way agreement (libpng==stb everywhere; custom-era 3 tRNS bugs fixed) |
| Layout | Yoga adapter | custom measure_layout + AOSP semantics | 10/10 <8px on GMDice AXML |
| GLES | PortableGL | GLES spec conformance via golden cube pixels | golden cube + non-background metrics |
| ARSC config | res_config (AOSP port) | live AOSP source reads | 009 §6 proofs stand |
| Bidi | FriBidi | SheenBidi run (calibration pending) | §14 Persian proofs stand |
| DEX | our interpreter | androguard (static), Robolectric (UI semantics) | standing |
| Telegram auth chain | runtime | controlled TL response boundary | UNIFIED_002 PROVEN chain |

## 4. R32 marker classification (198 src hits)

- `dex/` 123: overwhelmingly `[HALT-LOOP]`, `STUBBED` trace strings and EXP
  diagnostics — logged behavior, not silent fakery. Any marker whose message
  claims SUCCESS without evidence is a bug: none found matching that pattern
  in this pass (spot-audited the top-30 files list in
  `database/uc010_source_audit.json`).
- `framework/` 22: comment references to EXP-09x stubs (documented shims).
- `runtime/` 21 + `api/` 13: trace labels for the stub-return path
  (`bridge_to_api` catch-all STUBBED defaults — intentional, type-aware,
  committed UC-CM-001).
- renderer 3 / resources 4 / jni 3 / mains 7: comments.
- Zero TODO/FIXME markers added by Campaign 010; Campaign 010 removed one
  documented hack class entirely (EXP-093 empty-array getStackTrace).

## 5. What NOT to build next (priority-ordered guards)

1. No GLSL compiler work by hand — GLSL→C translation or llvmpipe only.
2. No second image codec path.
3. No in-engine layout math growth — Yoga only.
4. No per-app fake UI for corpus APKs (corpus evidence = PARSED/DEX_EXECUTED/
   fallback-screen labeling; journeys only when real).
5. No replacement of the ARSC compatibility layer with ARSCLib wholesale —
   the Java library cannot run in-proc; only oracle differential tests.
