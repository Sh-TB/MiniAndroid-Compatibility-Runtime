# Font Runtime Study — Typeface resolution, shaping, measurement, rendering

Sources:
- AOSP frameworks/base `graphics/java/android/graphics/Typeface.java`
  (mirror `1cdfff55`), Paint.java, Canvas text entry points
- MiniAndroid's own chain (`src/fonts/text_shaper.cpp`,
  `src/framework/android_shadows.cpp` Typeface shadows,
  `src/renderer/software_renderer.cpp`)
- WineDroid (no font pipeline yet — confirms this is frontier territory for
  userspace runtimes; their roadmap places UI after reflection)

## FONT-001 — Typeface.create(String, int) exact semantics
- Source: `Typeface.java` L931: `create(familyName, style) →
  create(getSystemDefaultTypeface(familyName), style)`; L952: style masked
  (`(style & ~STYLE_MASK) != 0 → NORMAL`); null family → default; same
  family+style → SAME cached instance (`sStyledTypefaceCache` keyed by
  native_instance then style).
- MiniAndroid mapping: our Typeface.create shadow (Cycle B) implements
  request→family+style→fallback→system default. The two AOSP subtleties to
  pin: (a) invalid style silently normalizes (never throws), (b) identity
  caching means `create("sans-serif", NORMAL) == DEFAULT` behavior —
  pixel-invisible but API-visible. Status: PARTIALLY VERIFIED → fixture
  candidate (invalid style normalization).

## FONT-002 — createFromAsset's two distinct failure modes (Case F evidence)
- Source: `Typeface.java` L1127: Builder first; if Builder yields null:
  open the asset — if it does NOT exist → `RuntimeException("Font asset not
  found " + path)`; if it EXISTS but cannot be built → returns
  `Typeface.DEFAULT` SILENTLY.
- Why it matters: real Android itself distinguishes
  (a) missing font file → loud exception, vs
  (b) corrupt/unbuildable font file present → silent DEFAULT fallback.
  This is direct upstream evidence for the campaign's §27 law that
  "requested font cannot be loaded" (Case F) and "system/default font
  served" (Case E) must be reported as DIFFERENT events — Android itself
  treats them differently depending on presence vs. buildability.
- MiniAndroid mapping: our font discovery pipeline (Cycle B, corpus-verified
  for tictactoe assets/fonts and openlauncher root-assets) must emit
  distinct diagnostics for: source-selected-missing → error-level;
  source-present-unloadable → warning + DEFAULT + explicit event. Status:
  DISCOVERED → diagnostics spec pinned; fixture queued.

## FONT-003 — The resolution order (AOSP-confirmed)
Effective order an app's text ends up with: explicit asset/res font
(createFromAsset / res/font via Builder / ResourcesCompat) →
Typeface.create(family, style) → XML fontFamily attribute → theme
textAppearance → default (sans-serif) → system fallback list (Roboto +
Noto families per config). DEFAULT_BOLD etc. are STATIC finals built from
the default family at class-init (`nativeForceSetStaticFinalField`).
- MiniAndroid mapping: identical order implemented (Cycle A/B fixtures
  distinguish pixel-differentiated sources). sDefaults[style] indexing is
  the API-level law behind bundled fallbacks. Status: VERIFIED for
  Cases A–E at prior HEAD; Case F diagnostics per FONT-002.

## FONT-004 — Required pipeline invariant (campaign §27 restated with sources)
APK font request → requested family/style/weight → source selection
(assets/fonts → res/font → Typeface API → bundled → system/default) →
fallback decision (must LOG the deciding step) → FreeType face → shaping
(MiniAndroid: text_shaper) → metrics → measurement → layout → draw →
framebuffer. Every stage must be independently observable, because the
two historical failure classes this campaign inherited were exactly
(a) "font file opened" ≠ "glyphs rendered from that font" and
(b) `register_app_font_memory` use-after-free (FT_Face built on unstable
memory — fixed Cycle B).
- MiniAndroid status: chain verified for the bundled-asset class
  (tictactoe 1/1, openlauncher 6/6 registered, NO_FONT_DIRECTORY → SYSTEM
  proven). res/font (Case B/C distinction) still needs a synthetic-ARSC
  fixture; Typeface fixtures D/E queued. Revalidation at current HEAD.

## FONT-005 — Metrics discipline
AOSP text drawing flows through Paint → measureText/multi-text measurement
(FontsManager/FontMetrics in newer stacks) with ascent/descent/leading
driving TextView's baseline math (`Paint.ascent()` negative convention).
- MiniAndroid mapping: our `fonts::layout_text` + effective_text() metrics
  feed measure/layout (Cycle A) — the negative-ascent convention matches
  TextView expectations in our layout fixtures. Status: VERIFIED (prior
  HEAD fixtures; re-run queued).
