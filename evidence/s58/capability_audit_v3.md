# MiniAndroid Capability Audit v3 — S58 edition (40 items)

Improves capability_audit_v2.md (S57, 36 items): statuses re-measured at the S58 binary
7d8aa389ba6945c0 (byte-exact rebuild of the S57 merge binary), four new items (37-40)
added from this wave's decode. Status vocabulary unchanged.
New evidence this wave: run/s58/*, evidence/s58/*, mosaic
https://tmpfiles.org/wtAGZeLxw5wB/s58_mosaic.png (byte-verified 0089e8b27d87a2c8, 60-min TTL;
committed copy evidence/s58/s58_mosaic.png).

## A. Base canonical structure (the user's #1 priority — must precede graphics)

1. Parse APK XML and extract the app's main template? — **TESTED** (chess/opencalc/bmi trees render from real XML; opencalc full button panel from real layout XML at 180s).
2. Full View tree (inflate→measure→layout→draw) for VIEW-based apps? — **TESTED** (fishrings byte-exact a341e3ad ×3; BMI form fields + button; capaudit board 22/22).
3. Grid layout geometry exact? — **PARTIAL→IMPROVED** (opencalc button grid now spans ~95% width at 180s — was 45% at the CONT-56 measurement; GridLayout/Compose Row/Column geometry still under-proven for compose apps).
4. Button/border/icon precise sizes honored? — **PARTIAL→IMPROVED** (opencalc 24-button grid with glyphs; BMI 2 fields + Calculate button; capaudit 3 button-like regions; placement law S109 + the AOSP traversal gate R-NEW-441 live).
5. Compose LayoutNode materialization → placement (isPlaced) → draw chain? — **PARTIAL** (dooz180 c94da5a9 renders real Material3 Scaffold at 180s — the placement cascade completes late; 15s stays honestly blank 31ddd4d5; M3-19-CYCLE re-entry stubs remain on two sites: Lrz1;.j OPEN + Lho1;.b CYCLE, both re-observed this wave at the S58 binary).
6. Compose draw path — drawContent → AndroidCanvas bridge → real canvas ops? — **PARTIAL** (dooz180 face proves real canvas ops DO flow at 180s: 3.2% non-bg, bg 250,248,254, 3 button-like regions incl. a 410×148 bottom button; 15s bridge still unreachable).
7. Compose tap bridge (semantics hit-testing) — F-NEW-267? — **BLOCKED — decode advanced this wave (see item 37)** (S58 re-probe at 180s: TOUCHWIN-ANSWER isAttachedToWindow=1; transformMatrixToGlobal answered (0,0) fullscreen-correct; deferred measure/layout DRAINS during dispatch (Lzs0;.k ×2 batches via Lyo1;.first/remove); hit-test geometry legs execute (Low;.T roundToPx) but their px INPUTS are zero → hit list empty → target=0).

## B. Graphics & media

8. PNG decode + display in-app? — **TESTED** (capaudit png_rgba 64x64 cornerA=0 center=ff818180 pixel-exact ×3 at S58 binary, face byte-identical to CONT-67 cb6373f6).
9. Full-quality background images? — **TESTED** (capaudit bg rows + gradient/linear-gradient panels render; FishRings provenance pixel-true).
10. GIF decode? — **TESTED** (capaudit gif 48x48 center=ffff0000 frame-exact ×3).
11. WebP / Lottie? — **TESTED (WebP per-app) / IMPLEMENTED (Lottie, per-app PENDING)** (capaudit webp 64x64 px0=ff01ffff px32=ffff01ff pixel-exact ×3; MINIANDROID_HAVE_WEBP=1 built in).
12. Curved/rounded shapes (RoundRect, arcs, Path)? — **TESTED** (capaudit circle/ellipse/hatch-path rows render; canvas shadow path recording; drawRoundRect/drawArc live in dooz180 face).
13. Fast graphics changes (animation, per-frame invalidation)? — **PARTIAL** (Choreographer + animator shadows; flappycow/g2048 REAL_APP_CONTENT; compose recomposition animation blocked at item 5/6 for compose apps).
14. Rotation/scale transforms? — **PARTIAL→IMPROVED** (capaudit scale row: setScaleX/Y 2.0/1.5 get 2.0/1.5 EXACT ×3; device-rotation harness flag PENDING).
15. Audio playback in-app? — **TESTED (API law; audibility N/A headless)** (capaudit mediaplayer prepared 500ms playing=true; soundpool loaded id=1; tone.wav 8044B from assets — all ×3).

## C. Platform model

16. Android prerequisites (Application/Provider/Service/Receiver lifecycles)? — **TESTED** (probe PROV-01..09 + SVC-01..04; negatives 19/19 re-run at S58).
17. App permission identification/enforcement? — **PARTIAL** (manifest parses uses-permission; runtime grant/deny semantics PENDING).
18. Sandbox and setup completeness? — **TESTED** (capaudit sandbox ROUNDTRIP_OK 22B; negatives N-08-ISO-02/03/04 + N-11 PASS at S58).
19. ContentProvider identity + CRUD + openFileDescriptor? — **TESTED** (GATEA|PROV rows all PASS; gate_a_probe rebuilt 4be713e77e37e6fc, battery re-harvested).
20. Service lifecycle? — **TESTED** (SVC-01..04 PASS at S58).
21. PendingIntent honesty? — **TESTED** (PI-NEG PASS at S58).

## D. Text, fonts, styles

22. Any-language text without issues (RTL/i18n)? — **TESTED (Persian+CJK rendering; full i18n sweep PENDING)** (capaudit face: Persian مرحبا/سلام rendered RTL red + CJK 你好; text nodes at real positions EXP092-RENDER (540,612)/(900,612)).
23. Italic/bold/colored text? — **TESTED** (capaudit face: Bb bold + italic + Bl bold-italic rows in white/red/orange/yellow/green ×3 byte-identical).
24. Custom app fonts (assets TTF)? — **PARTIAL** (MiniFont$Glyph path S88; full TTF-from-assets law PENDING — capaudit does not load a custom TTF).
25. Emoji rendering? — **NOT TESTED** (capaudit draws emoji-like SHAPES; no color-emoji text glyph evidence yet).

## E. Dynamic/graphics toolchains

26. CSS-class graphics tooling (WebView/Canvas2D)? — **IMPLEMENTED (per-app PENDING)** (webview_engine + html_dom + canvas2d linked).
27. JS execution (QuickJS)? — **IMPLEMENTED (per-app PENDING)** (quickjs.o in link line).
28. Java reflection on real classes? — **TESTED** (R500-REFLECT live; fnew262 identity probes 11/11 at S58).
29. Kotlin immutable collections (PersistentHashMap family)? — **PARTIAL/FRONTIER** (F-NEW-265 null law + F-NEW-365 write-form law landed; M3-19-CYCLE re-entry + null TrieNode upstream PENDING).
30. Collections bridge (R8-renamed overrides)? — **TESTED** (F-NEW-259/259b probe 7/7; R-NEW-360/464).

## F. Verification infrastructure

31. Determinism harness? — **TESTED** (S58: 36/36 wall ×3 byte-identical at rebuilt binary run/s58/baseline.log; probe faces ×3).
32. Pixel-truth census? — **TESTED** (scripts/s58_pixel_census.py: dooz180 3.2% non-bg / 21 buckets / 3 button-regions; opencalc 62% non-bg; simplecalc 36.9%).
33. Zero-drift gate? — **TESTED** (36/36 at S58 — zero drift from the merge binary).
34. Negative battery + skill + goldens? — **TESTED** (19/19 with re-harvested probe verdicts; skill 13/13; goldens 5/5 identity src==inst==pkgaudit).
35. External evidence hosting? — **TESTED** (mosaic uploaded + byte-verified 0089e8b27d87a2c8).
36. Registry discipline? — **TESTED** (672 roots at S58 base; F-NEW-267 evidence refined without root inflation).

## G. New items (S58 wave)

37. Compose hit-test state plumbing (F-NEW-267 lever #2 refinement)? — **BLOCKED (decode advanced)**. S58 instruction-level findings at 180s: (a) the tap pipeline drains the deferred measure/layout queue DURING dispatch — Lzs0;.k runs twice (Lyo1;.isEmpty→first→remove); (b) the hit-test geometry legs execute (Low;.T = Density.roundToPx, callers Li31;.e/Lhl;.g/Lwc;.d/Ld;.i) but their px inputs are ZERO; (c) FIELD-TRACE over the whole run shows NO packed-IntOffset or position iput on Lel0;/Lbt0; layout objects — Lel0;.m/.H never written, Lel0;.R only 0/1 flag — placement geometry reaches the RENDER path as canvas translates but never lands in the DEX-visible delegate state the hit-test reads. The two stores are disconnected. Next lever: decode where R8'd placeAt writes position state (which field/method), then implement the position-store law. Evidence: run/s58/dooz180_tap*.log, run/s58/dooz180_ft.log (5895965+ window).
38. Dooz interaction attempts? — **BLOCKED honestly** (--tap 540,960 at 180s: full dispatch executes, target=0; the board also sits behind AnimatedVisibility(isGameStarted=false), reachable only through the tap — item 37's fix gates playability).
39. Calculator completeness matrix (user's کامل کامل lane)? — **MEASURED at S58**: simplecalc COMPLETE (display "0" + full panel); opencalc full panel + EMPTY display (gap: display text leg) + stray 47×170 white box; BMI real form right-aligned; tanana real settings face (F-NEW-308 rows DO paint — superseded confirmed); alex anchor face c8d69f81.
40. CONT-46 leftovers closure at HEAD? — **TESTED**: F-NEW-260 11/11 PASS (probe d1182acab3aadef3), F-NEW-262 11/11 PASS (probe e8153f6a16e09696), F-NEW-261 law live in BMI's real FragmentActivity form face; tripeaks honestly DEFAULT_BACKGROUND_ONLY (first_missing_stage=APP_DRAW_OPS); F-NEW-308 superseded (tanana rows paint).

## Next-wave order (evidence-first)
- W+1: the placeAt position-write decode (item 37's named lever) → hit-test store law → tap target≠0.
- W+2: dooz play attempt through isGameStarted (item 38) once tap lands; compose draw at 15s (items 5/6).
- W+3: opencalc display text leg (item 39's named gap); items 17/24/25/26/27 per-app probes.
