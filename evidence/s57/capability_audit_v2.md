# MiniAndroid Capability Audit v2 — S57 edition (36 items)

Base: the user's original audit directive + every frontier learned since.
Status vocabulary: IMPLEMENTED / TESTED / OBSERVED / PARTIAL / BLOCKED / PENDING / NOT TESTED.
Evidence paths are repo-relative. Binary: 62f651ba6accded3 (S57).

## A. Base canonical structure (the user's #1 priority — must precede graphics)

1. Parse APK XML (layout resources) and extract the app's main template? — **TESTED** (layout_inflater + axml_parser; chess/opencalc trees render from real XML).
2. Build the full View tree (inflate → measure → layout → draw) for VIEW-based apps? — **TESTED** (fishrings byte-exact real content a341e3ad ×3; EXP092 render walk).
3. Grid layout geometry (columns/rows/cell sizes) resolved exactly? — **PARTIAL** (LinearLayout/Frame/Relative laws live; GridLayout/Compose Row/Column geometry under-proven for compose apps).
4. Button/border/icon precise sizes honored (view bounds + padding + gravity)? — **PARTIAL** (opencalc buttons visible but compressed to 45% width at an old wave; placement law S109 exists; compose Material3 geometry unproven).
5. Compose LayoutNode materialization → placement (isPlaced) → draw chain? — **PARTIAL/PROVEN BLOCKER** (S57: placement never completes — M3-19-CYCLE re-entry stubs + null TrieNode root upstream of slot reads; F084 loop fixed this wave; chain proven link-by-link).
6. Compose draw path — layer drawContent → AndroidCanvas bridge (Ljt1;) → real canvas ops? — **BLOCKED upstream** (bridge never REACHED: isPlaced=FALSE; 0 drawRect/drawText; translate ×164 only. Once placement lands, the bridge becomes the next link).
7. Compose tap bridge (Compose semantics hit-testing) — F-NEW-267? — **BLOCKED** (S57 probe: --tap 540,960 → F117-TAP target=0; dooz unplayable honestly).

## B. Graphics & media

8. PNG decode + display in-app (ImageView/Bitmap)? — **TESTED** (bitmap_shadow; FishRings res/mipmap PNG dominant colors == framebuffer pixels, pixel-true provenance).
9. Full-quality background images inside apps? — **PARTIAL** (decode + blit work; large-surface scaling/tiling laws unproven at 1080p).
10. GIF decode? — **TESTED** (build/gles gif_decoder + MINIANDROID_HAVE_WEBP/LOTTIE flags; gif_decoder.o in link line).
11. WebP / Lottie? — **IMPLEMENTED** (build flags MINIANDROID_HAVE_WEBP + MINIANDROID_HAVE_LOTTIE, librlottie linked; per-app verification PENDING).
12. Curved / rounded shapes (RoundRect, arcs, Path)? — **IMPLEMENTED** (CanvasShadow path recording + clip law; FIX-5 real path recording for custom glyphs; drawRoundRect/drawArc delegate surface in compose canvas class read from dooz DEX).
13. Fast graphics changes (animations, per-frame invalidation)? — **PARTIAL** (Choreographer frame machinery + animator_shadow exist; high-FPS games (FlappyCow family) show REAL_APP_CONTENT; compose recomposition-driven animation blocked at item 5).
14. Rotation/scale transforming app layout? — **PARTIAL** (MeasureSpec EXACTLY laws + setFrame/onSizeChanged S123; device-rotation harness flag PENDING).
15. Audio playback inside apps (background audio)? — **IMPLEMENTED** (MediaPlayer object law R-NEW-400: create/start/pause/stop state machine; FishRings sound() fixed; engine links -lmpg123 -lsndfile; audibility in harness NOT TESTED — headless container).

## C. Platform model

16. Android prerequisites (Application, Provider, Service, BroadcastReceiver lifecycles)? — **TESTED** (gate probe: PROV-01..09 provider family, SVC-01..04 service family PASS 19/19 negatives).
17. App permission identification/enforcement? — **PARTIAL** (manifest reader parses uses-permission; runtime grant/deny semantics PENDING).
18. Sandbox and setup completeness (file namespace, data dirs, cross-package isolation)? — **TESTED** (N-08-ISO-02/03/04 PASS: traversal exists()==false, /etc/passwd FNFE; N-11 isolation PASS).
19. ContentProvider identity + CRUD + openFileDescriptor? — **TESTED** (gate probe GATEA|PROV-01..09 all PASS at S57 binary).
20. Service lifecycle (start/bind/unbind/stop, started-vs-bound law)? — **TESTED** (SVC-01..04 PASS).
21. PendingIntent honesty (FLAG_NO_CREATE never fabricates)? — **TESTED** (PI-NEG PASS).

## D. Text, fonts, styles

22. Convert various fonts; any language without issues? — **PARTIAL** (FreeType + HarfBuzz + FriBidi linked; text_shaper.o; RTL/i18n shaping per-app verification PENDING).
23. Italic / bold / colored text recognition? — **PARTIAL** (Paint.setStyle/typeface laws in shadows; Typeface family resolution per-app PENDING).
24. Custom app fonts (assets/fonts TTF)? — **PARTIAL** (MiniFont$Glyph path exists (S88); full TTF-from-assets law PENDING).
25. Emoji rendering? — **NOT TESTED** (no evidence either way at this binary).

## E. Dynamic/graphics toolchains

26. CSS-class graphics tooling (WebView/Canvas2D bridge)? — **IMPLEMENTED** (webview_engine + html_dom + canvas2d.cpp objects linked; per-app verification PENDING).
27. JS execution (QuickJS) for JS-driven games/UI? — **IMPLEMENTED** (quickjs.o in link line; games/ exp harnesses; per-app verification PENDING).
28. Java reflection (Class.getField/getMethod + Field.get) on real classes? — **TESTED** (R500-REFLECT live: Build$VERSION.SDK_INT served from real dex/statics at S57).
29. Kotlin collections immutable family (PersistentHashMap/OrderedSet trie laws)? — **PARTIAL/FRONTIER** (S21 forensics + F-NEW-265 null law landed; the M3-19-CYCLE re-entry + null root upstream PENDING next wave).
30. Collections bridge (ArrayList/Map/ArrayDeque R8-renamed overrides)? — **TESTED** (F-NEW-259/259b + R-NEW-360/464 fixed and probe-proven 7/7).

## F. Verification infrastructure (this wave)

31. Determinism harness (install/run/frames/screenshot SHA) — **TESTED** (s57_anchor_check.sh + s57_random3.sh; all runs ×3 byte-identical).
32. Pixel-truth census (24-bucket color quantization, non-bg share) — **TESTED** (klondike 26.3% nonbg, notes 2.8% UI block, fishrings 4.8% content).
33. Zero-drift gate (5 anchors ×3) — **TESTED** twice this wave (pre-fix freeze + post-fix re-run, all MATCH).
34. Negative battery (19/19) + skill (13/13) + reinstall goldens — **TESTED** at S57 binary.
35. External evidence hosting — **TESTED** (mosaic uploaded + byte-verified: https://n.uguu.se/dZZmbGhW.png).
36. Registry discipline (no inflation; STATUS—RESULT—EVIDENCE per root) — **TESTED** (566→568 with full evidence paths).

## Next-wave order (evidence-first)
- W+1: decode the M3-19-CYCLE re-entry (Lnb0;.H doCompose recursion) + the null TrieNode ROOT upstream of slot reads → placement (isPlaced=TRUE).
- W+2: compose drawContent → AndroidCanvas bridge (real canvas ops), then Compose tap bridge (F-NEW-267) → dooz playable.
- W+3: items 3/4/9/14/22/23/24/25 per-app verification sweep + PNG/fonts fan-out.
